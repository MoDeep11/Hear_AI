"""
일기 관련 라우터
이미지, 스티커, 해시태그 생성 엔드포인트를 정의합니다.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Header
from typing import Optional, List
import uuid
import sys
import os

# 프로젝트 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from server.app.service.diary_service import diary_service, DiaryServiceRequest
from pydantic import BaseModel


# 요청/응답 모델
class StickerGenerateRequest(BaseModel):
    userId: int
    diaryId: int
    emotion: str
    content: str
    count: int = 1


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


# 라우터 생성
router = APIRouter(
    prefix="/internal",
)

# 진행 중인 작업들을 추적하기 위한 간단한 저장소
tasks_store = {}


@router.post("/v1/sticker/generate", response_model=AsyncResponse, status_code=202, tags=["stickers"])
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
        count=request.count,
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


@router.post("/images/generate", response_model=AsyncResponse, status_code=202, tags=["diarys"])
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


@router.get("/task/{task_id}", tags=["tasks"])
async def get_task_status(task_id: str):
    """
    작업 상태 조회
    
    - task_id: 작업 ID
    """
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    
    return tasks_store[task_id]


# 백그라운드 작업 함수들
async def process_sticker_generation(
    task_id: str,
    user_id: int,
    diary_id: int,
    emotion: str,
    content: str,
    count: int,
):
    """스티커 생성 백그라운드 작업"""
    print(f"[Router] process_sticker_generation started (task_id={task_id})")
    try:
        result = await diary_service.generate_stickers(user_id, diary_id, emotion, content, count)
        print(f"[Router] generate_stickers result: {result}")
        # 스티커 생성이 완료되면 Spring 서버에 콜백
        print(f"[Router] calling patch_sticker_callback for task_id={task_id}")
        await diary_service.patch_sticker_callback(
            diary_id=diary_id,
            task_id=task_id,
            user_id=user_id,
            stickers=result.get("stickers", []),
        )
        tasks_store[task_id] = {
            "taskId": task_id,
            "status": "completed",
            "data": result,
        }
        print(f"[Router] process_sticker_generation completed (task_id={task_id})")
        return result
    except Exception as e:
        print(f"[Router] process_sticker_generation failed (task_id={task_id}): {e}")
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
        await diary_service.patch_image_callback(
            diary_id=diary_id,
            task_id=task_id,
            user_id=user_id,
            imageUrls=result.get("imageUrls", []),
        )
        tasks_store[task_id] = {
            "taskId": task_id,
            "status": "completed",
            "data": result,
        }
        print(f"[Router] process_image_generation completed (task_id={task_id})")
        return result
    except Exception as e:
        print(f"[Router] process_image_generation failed (task_id={task_id}): {e}")
        tasks_store[task_id] = {
            "taskId": task_id,
            "status": "failed",
            "error": str(e),
        }
        return {"taskId": task_id, "status": "failed", "error": str(e)}


async def process_diary_creation(
    task_id: str,
    service_request: DiaryServiceRequest,
    access_token: str,
):
    """일기 생성 및 백엔드 전송 백그라운드 작업"""
    try:
        # 1. AI 컨텐츠 생성 (이미 이미 수행됐을 수 있음)
        ai_results = await diary_service.generate_all(service_request, task_id)
        
        # 2. Spring 백엔드로 데이터 전송
        backend_result = await diary_service.send_to_backend(service_request, access_token)
        
        tasks_store[task_id] = {
            "taskId": task_id,
            "status": "completed",
            "data": {
                "ai_generation": ai_results,
                "backend_response": backend_result,
            },
        }
    except Exception as e:
        tasks_store[task_id] = {
            "taskId": task_id,
            "status": "failed",
            "error": str(e),
        }