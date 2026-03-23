"""
일기 관련 서비스 로직
이미지, 스티커, 해시태그 생성을 담당합니다.
"""

import logging
import uuid
import aiofiles
import os
import httpx
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import sys
from ai.pipelines.diary_generator import DiaryGenerator
from ai.voice.stt import STTService
from ai.voice.tts import TTSService
import asyncio

logger = logging.getLogger(__name__)

# 프로젝트 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from ai.image.image_generator import image_generator, ImageGenerationRequest
from ai.image.sticker_generator import sticker_generator, StickerGenerationRequest


class DiaryServiceRequest(BaseModel):
    """일기 서비스 통합 요청"""
    userId: int
    diaryId: Optional[int] = None
    emotion: str
    content: str
    tags: Optional[List[str]] = None
    sourceType: str = "AI_CHAT"
    generateImage: bool = True
    generateSticker: bool = True
    generateHashtag: bool = True
    stickerCount: int = 3
    hashtagCount: int = 10


class DiaryService:
    """일기 생성 및 AI 컨텐츠 생성 서비스"""
    def __init__(self, generator: DiaryGenerator, stt_service: STTService, tts_service: TTSService):
        self.generator = generator
        self.stt_service = stt_service
        self.tts_service = tts_service
        self.temp_dir = "static/temp"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir, exist_ok=True)
        self.backend_url = os.getenv("SPRING_BACKEND_URL", "http://localhost:8080")
        self.api_key = os.getenv("API_KEY", "")

    async def process_voice_diary(self, chat_data):
        """
        chat_data: diary_router에서 전달받은 ChatRequest Pydantic 모델
        """
        session_id_val = chat_data.sessionId
        temp_file_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}.wav")
        user_transcription = ""

        try:
            if chat_data.userAudioUrl:
                async with httpx.AsyncClient() as client:
                    response = await client.get(chat_data.userAudioUrl)
                    if response.status_code == 200:
                        async with aiofiles.open(temp_file_path, 'wb') as f:
                            await f.write(response.content)
                        # STT 실행
                        user_transcription = await self.stt_service.transcribe(temp_file_path)

            if not user_transcription and chat_data.message:
                user_transcription = chat_data.message

            if not user_transcription:
                user_transcription = "내용 없음"

            ai_result = await self.generator.generate_response(
                user_text=user_transcription,
                history=[h.dict() for h in chat_data.history],
                user_info=chat_data.userInfo.dict()
            )

            ai_response_text = ai_result.get("aiResponseText", "")

            ai_audio_url = None
            if ai_response_text:
                ai_audio_url = await self.tts_service.generate_audio_url(ai_response_text)

            return {
                "userTranscription": user_transcription,
                "aiResponseText": ai_response_text,
                "aiAudioUrl": ai_audio_url,
                "status": ai_result.get("status", "CONTINUE"),
                "suggestion": ai_result.get("suggestion"),
                "sessionId": session_id_val
            }

        except Exception as e:
            logger.error(f"DiaryService Error: {str(e)}")
            return {
                "userTranscription": user_transcription,
                "aiResponseText": "죄송해요, 대화 도중 오류가 발생했습니다.",
                "aiAudioUrl": None,
                "status": "CONTINUE",
                "suggestion": None,
                "sessionId": session_id_val
            }

        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    async def create_diary(self, user_info, history, user_audio_urls=None, ai_audio_urls=None):
        try:
            diary_data = await self.generator.create_diary(
                user_info=user_info,
                history=history,
                user_audio_urls=user_audio_urls,
                ai_audio_urls=ai_audio_urls
            )
            return diary_data

        except Exception as e:
            logger.error(f"DiaryService create_diary Error: {str(e)}")
            return {
                "content": "죄송합니다. 일기 생성 중 오류가 발생했습니다.",
                "emotion": "NEUTRAL",
                "tags": []
            }        
    
    async def generate_image(self, user_id: int, diary_id: int, emotion: str, content: str) -> Dict:
        """이미지 생성"""
        request = ImageGenerationRequest(
            diaryId=diary_id,
            userId=user_id,
            emotion=emotion,
            content=content,
        )
        return await image_generator.generate(request)
    
    async def generate_stickers(self, user_id: int, diary_id: int, emotion: str, content: str, count: int) -> Dict:
        """스티커 생성"""
        request = StickerGenerationRequest(
            userId=user_id,
            diaryId=diary_id,
            emotion=emotion,
            content=content,
            count=count,
        )
        return await sticker_generator.generate(request)

    def _build_backend_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def patch_image_callback(self, diary_id: int, task_id: str, user_id: int, imageUrls: list):
        """Spring 백엔드에 이미지 생성 완료를 알리는 콜백"""
        url = f"{self.backend_url}/internal/diary/{diary_id}/ai-image"
        payload = {
            "diaryId": diary_id,
            "taskId": task_id,
            "userId": user_id,
            "imageUrls": imageUrls,
        }

        # 비동기 흐름 확인용 로그
        print(f"[DiaryService] patch_image_callback called (task_id={task_id})")
        print(f"[DiaryService] patch_image_callback payload={payload}")
        print(f"[DiaryService] patch_image_callback backend_url={url}")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.patch(url, json=payload, headers=self._build_backend_headers())
                response.raise_for_status()
                print(f"[DiaryService] patch_image_callback response={response.status_code}")
                return response.json()
        except httpx.TimeoutException as e:
            logger.error(f"[DiaryService] patch_image_callback timeout: {str(e)}")
            return {"status": "callback_timeout", "error": str(e)}
        except httpx.ConnectError as e:
            logger.error(f"[DiaryService] patch_image_callback connection error: {str(e)}")
            return {"status": "callback_connection_error", "error": str(e)}
        except Exception as e:
            logger.error(f"[DiaryService] patch_image_callback error: {str(e)}")
            return {"status": "callback_error", "error": str(e)}

    async def patch_sticker_callback(self, diary_id: int, task_id: str, user_id: int, stickers: list):
        """Spring 백엔드에 스티커 생성 완료를 알리는 콜백"""
        url = f"{self.backend_url}/internal/diary/{diary_id}/ai-image"
        payload = {
            "diaryId": diary_id,
            "taskId": task_id,
            "userId": user_id,
            "stickers": stickers,
        }

        # 비동기 흐름 확인용 로그
        print(f"[DiaryService] patch_sticker_callback called (task_id={task_id})")
        print(f"[DiaryService] patch_sticker_callback payload={payload}")
        print(f"[DiaryService] patch_sticker_callback backend_url={url}")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.patch(url, json=payload, headers=self._build_backend_headers())
                response.raise_for_status()
                print(f"[DiaryService] patch_sticker_callback response={response.status_code}")
                return response.json()
        except httpx.TimeoutException as e:
            logger.error(f"[DiaryService] patch_sticker_callback timeout: {str(e)}")
            return {"status": "callback_timeout", "error": str(e)}
        except httpx.ConnectError as e:
            logger.error(f"[DiaryService] patch_sticker_callback connection error: {str(e)}")
            return {"status": "callback_connection_error", "error": str(e)}
        except Exception as e:
            logger.error(f"[DiaryService] patch_sticker_callback error: {str(e)}")
            return {"status": "callback_error", "error": str(e)}

    async def send_to_backend(self, request: DiaryServiceRequest, access_token: str) -> Dict[str, Any]:
        """일기 생성 시 Spring 백엔드로 데이터 전송 (기존 구현 대비 최소화)"""
        url = f"{self.backend_url}/internal/diary/{request.diaryId}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=request.dict(), headers=headers)
            response.raise_for_status()
            return response.json()

    
