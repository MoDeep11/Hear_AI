"""
일기 관련 라우터
이미지, 스티커, 해시태그 생성 엔드포인트를 정의합니다.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Header
from typing import Optional, List
import uuid
import sys
import os
from pydantic import BaseModel
import logging
from dotenv import load_dotenv

# 프로젝트 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, "..", "..", ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)
print(f"DEBUG: Root path is {root_path}")
print(sys.path)

from server.app.service.diary_service import DiaryServiceRequest
from ai.pipelines.diary_generator import DiaryGenerator
from server.app.service.diary_service import DiaryService
from ai.voice.stt import STTService
from ai.voice.tts import TTSService

# 로깅 및 환경 변수 설정
logger = logging.getLogger(__name__)
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")

# Pydantic 모델 정의 (JSON Request Body 매핑)
class MessageHistory(BaseModel):
    role: str
    content: str

class UserInfo(BaseModel):
    userId: int
    nickname: str
    streakDays: int
    totalDiaries: int
    maxStreak: int

class ChatRequest(BaseModel):
    userInfo: UserInfo
    message: Optional[str] = None
    userAudioUrl: Optional[str] = None
    history: List[MessageHistory] = []
    sessionId: str

class StickerGenerateRequest(BaseModel):
    userId: int
    diaryId: int
    emotion: str
    content: str


class ImageGenerateRequest(BaseModel):
    diaryId: int
    userId: int
    emotion: str
    content: str


class DiaryCreateRequest(BaseModel):
    """일기 생성 요청"""
    content: str
    emotion: str
    tags: Optional[List[str]] = None
    sourceType: str = "AI_CHAT"
    generateImage: bool = True
    generateSticker: bool = True
    generateHashtag: bool = True
    stickerCount: int = 3
    hashtagCount: int = 10


class AsyncResponse(BaseModel):
    taskId: str
    status: str
    message: str

# 라우터 설정
Yuwon_router = APIRouter(
    prefix="/internal",
)
router = APIRouter(prefix="/internal/v1/chats", tags=["Chat/Diary"])

# 서비스 초기화
stt_service = STTService()
tts_service = TTSService()
generator = DiaryGenerator(api_key=API_KEY)
diary_service = DiaryService(generator=generator, stt_service=stt_service, tts_service=tts_service)


@router.post("/messages")
async def handle_voice_message(request: ChatRequest):
    """
    JSON 형식의 요청을 받아 STT -> AI -> TTS 과정을 처리합니다.
    """
    try:
        # 서비스 호출 (Pydantic 모델 객체를 그대로 전달)
        result = await diary_service.process_voice_diary(chat_data=request)
        return result

    except Exception as e:
        logger.error(f"Router Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# API 엔드포인트 for AI diary creation + emotion inference
api_router = APIRouter(prefix="/api/v1", tags=["Chat/Diary"])

class CreateDiaryRequest(BaseModel):
    userInfo: UserInfo
    userAudioUrls: Optional[List[str]] = []
    aiAudioUrls: Optional[List[str]] = []
    history: List[MessageHistory] = []

class CreateDiaryResponse(BaseModel):
    userInfo: UserInfo
    content: str
    emotion: str
    tags: List[str] = []

@api_router.post("/diaries", response_model=CreateDiaryResponse)
async def create_diary(request: CreateDiaryRequest):

    diary_data = await diary_service.create_diary(
        user_info=request.userInfo.dict(),
        history=[h.dict() for h in request.history],
        user_audio_urls=request.userAudioUrls,
        ai_audio_urls=request.aiAudioUrls
    )

    return CreateDiaryResponse(
        userInfo=request.userInfo,
        content=diary_data.get("content", ""),
        emotion=diary_data.get("emotion", "NEUTRAL"),
        tags=diary_data.get("tags", []) 
    )

# 진행 중인 작업들을 추적하기 위한 간단한 저장소
tasks_store = {}

@Yuwon_router.post("/v1/sticker/generate", response_model=AsyncResponse, status_code=202, tags=["stickers"])
async def generate_sticker(request: StickerGenerateRequest, background_tasks: BackgroundTasks):
    """
    스티커 생성 요청
    
    - userId: 사용자 ID
    - emotion: 감정 (HAPPY, SAD, ANGRY, ANXIOUS, NORMAL)
    - content: 일기 내용
    - count: 생성할 스티커 개수 (기본: 1, 최대: 5)
    """
    task_id = f"sticker_task_{request.diaryId}_{request.userId}"

    # 백그라운드 작업으로 실행
    background_tasks.add_task(
        process_sticker_generation,
        task_id=task_id,
        user_id=request.userId,
        diary_id=request.diaryId,
        emotion=request.emotion,
        content=request.content,
    )

    tasks_store[task_id] = {
        "taskId": task_id,
        "status": "pending",
        "message": "스티커 생성 작업이 접수되었습니다.",
    }

    return AsyncResponse(
        taskId=task_id,
        status="pending",
        message="스티커 생성 작업이 접수되었습니다.",
    )


@Yuwon_router.post("/images/generate", response_model=AsyncResponse, status_code=202, tags=["Image"])
async def generate_image(request: ImageGenerateRequest, background_tasks: BackgroundTasks):
    """
    이미지 생성 요청
    
    - diaryId: 일기 ID
    - userId: 사용자 ID
    - emotion: 감정 (HAPPY, SAD, ANGRY, ANXIOUS, NORMAL)
    - content: 일기 내용
    """
    task_id = f"image_task_{request.diaryId}_{request.userId}"

    background_tasks.add_task(
        process_image_generation,
        task_id=task_id,
        diary_id=request.diaryId,
        user_id=request.userId,
        emotion=request.emotion,
        content=request.content,
    )

    tasks_store[task_id] = {
        "taskId": task_id,
        "status": "pending",
        "message": "이미지 생성이 시작되었습니다.",
    }

    return AsyncResponse(
        taskId=task_id,
        status="pending",
        message="이미지 생성이 시작되었습니다.",
    )




# 백그라운드 작업 함수들
async def process_sticker_generation(
    task_id: str,
    user_id: int,
    diary_id: int,
    emotion: str,
    content: str
):
    """스티커 생성 백그라운드 작업"""
    print(f"[Router] process_sticker_generation started (task_id={task_id})")
    try:
        result = await diary_service.generate_stickers(user_id, diary_id, emotion, content)
        print(f"[Router] generate_stickers result: {result}")
        # 스티커 생성이 완료되면 Spring 서버에 콜백
        print(f"[Router] calling patch_sticker_callback for task_id={task_id}")
        try:
            await diary_service.patch_sticker_callback(
                diary_id=diary_id,
                task_id=task_id,
                user_id=user_id,
                stickers=result.get("stickers", []),
            )
            print(f"[Router] patch_sticker_callback succeeded (task_id={task_id})")
        except Exception as callback_error:
            print(f"[Router] patch_sticker_callback error (task_id={task_id}): {callback_error}")
            logger.error(f"[Router] callback error: {callback_error}")
            # 콜백 실패해도 작업은 완료로 표시
        
        tasks_store[task_id] = {
            "taskId": task_id,
            "status": "completed",
            "data": result,
        }
        print(f"[Router] process_sticker_generation completed (task_id={task_id})")
        return result
    except Exception as e:
        print(f"[Router] process_sticker_generation failed (task_id={task_id}): {e}")
        logger.error(f"[Router] sticker generation error: {e}")
        tasks_store[task_id] = {
            "taskId": task_id,
            "status": "failed",
            "error": str(e),
        }
        return {"taskId": task_id, "status": "failed", "error": str(e)}


async def process_image_generation(
    task_id: str,
    diary_id: int,
    user_id: int,
    emotion: str,
    content: str,
):
    """이미지 생성 백그라운드 작업"""
    print(f"[Router] process_image_generation started (task_id={task_id})")
    try:
        result = await diary_service.generate_image(user_id, diary_id, emotion, content)
        print(f"[Router] generate_image result: {result}")
        # 이미지 생성이 완료되면 Spring 서버에 콜백
        print(f"[Router] calling patch_image_callback for task_id={task_id}")
        try:
            await diary_service.patch_image_callback(
                diary_id=diary_id,
                task_id=task_id,
                user_id=user_id,
                imageUrls=result.get("imageUrls", []),
            )
            print(f"[Router] patch_image_callback succeeded (task_id={task_id})")
        except Exception as callback_error:
            print(f"[Router] patch_image_callback error (task_id={task_id}): {callback_error}")
            logger.error(f"[Router] callback error: {callback_error}")
            # 콜백 실패해도 작업은 완료로 표시
        
        tasks_store[task_id] = {
            "taskId": task_id,
            "status": "completed",
            "data": result,
        }
        print(f"[Router] process_image_generation completed (task_id={task_id})")
        return result
    except Exception as e:
        print(f"[Router] process_image_generation failed (task_id={task_id}): {e}")
        logger.error(f"[Router] image generation error: {e}")
        tasks_store[task_id] = {
            "taskId": task_id,
            "status": "failed",
            "error": str(e),
        }
        return {"taskId": task_id, "status": "failed", "error": str(e)}

