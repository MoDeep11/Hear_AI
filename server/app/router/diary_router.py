# from fastapi import APIRouter, UploadFile, File, Form, HTTPException
# from dotenv import load_dotenv
# import json
# import sys
# import os
# import logging

# current_path = os.path.dirname(os.path.abspath(__file__))
# root_path = os.path.abspath(os.path.join(current_path, "..", ".."))
# if root_path not in sys.path:
#     sys.path.insert(0, root_path)
# print(f"DEBUG: Root path is {root_path}")

# from ai.pipelines.diary_generator import DiaryGenerator
# from server.app.service.diary_service import DiaryService
# from ai.voice.stt import STTService
# from ai.voice.tts import TTSService

# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/internal/v1/chats", tags=["Chat/Diary"])

# load_dotenv()
# API_KEY = os.getenv("GEMINI_API_KEY")
# if not API_KEY:
#     raise ValueError("API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")

# stt_service = STTService()
# tts_service = TTSService()
# generator = DiaryGenerator(api_key=API_KEY)
# diary_service = DiaryService(generator=generator, stt_service=stt_service, tts_service=tts_service)

# @router.post("/messages")
# async def handle_voice_message(
#     file: UploadFile = File(...),
#     sessionId: str = Form(...),
#     userInfo: str = Form(...),
#     # userAudioUrl: str = Form(None)
# ):
#     try:
#         # JSON 문자열로 들어온 userInfo 파싱
#         try:
#             user_data = json.loads(userInfo)
#             # user_data["userAudioUrl"] = userAudioUrl
#             user_data["sessionId"] = sessionId
#         except json.JSONDecodeError:
#             raise HTTPException(status_code=400, detail="userInfo must be a valid JSON string")

#         # 서비스 호출 (모든 비즈니스 로직은 여기서 처리됨)
#         # STT -> Gemini -> TTS 과정이 내부에서 일어남
#         result = await diary_service.process_voice_diary(
#             file=file, 
#             session_id=sessionId, 
#             user_data=user_data
#         )

#         return result

#     except Exception as e:
#         logger.error(f"Router Error: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import logging
from dotenv import load_dotenv


current_path = os.path.dirname(os.path.abspath(__file__))
# root_path = os.path.abspath(os.path.join(current_path, "..", ".."))
root_path = os.path.abspath(os.path.join(current_path, "..", "..", ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)
print(f"DEBUG: Root path is {root_path}")

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

# 라우터 설정
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