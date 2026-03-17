import logging
import uuid
import aiofiles
import os
import httpx
from ai.pipelines.diary_generator import DiaryGenerator
from ai.voice.stt import STTService
from ai.voice.tts import TTSService

logger = logging.getLogger(__name__)

class DiaryService:
    def __init__(self, generator: DiaryGenerator, stt_service: STTService, tts_service: TTSService):
        self.generator = generator
        self.stt_service = stt_service
        self.tts_service = tts_service
        self.temp_dir = "static/temp"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir, exist_ok=True)

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
            user_info_dict = chat_data.userInfo.dict()
            user_info_dict['sessionId'] = session_id_val
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