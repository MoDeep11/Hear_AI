import logging
import uuid
import aiofiles
import os
from ai.pipelines.diary_generator import DiaryGenerator
from ai.voice.stt import STTService
from ai.voice.tts import TTSService

# 로깅 설정
logger = logging.getLogger(__name__)

class DiaryService:
    def __init__(self, generator: DiaryGenerator, stt_service: STTService, tts_service: TTSService):
        self.generator = generator
        self.stt_service = stt_service
        self.tts_service = tts_service
        # 임시 파일 및 오디도 저장 경로
        self.temp_dir = "static/temp"
        os.makedirs(self.temp_dir, exist_ok=True)

    async def process_voice_diary(self, file, session_id: str, user_data: dict):
        temp_file_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}.wav")
        
        try:
            content = await file.read()
            async with aiofiles.open(temp_file_path, 'wb') as f:
                await f.write(content)
            # STT 단계 유저 음성 -> 텍스트 변환
            user_transcription = await self.stt_service.transcribe(temp_file_path)
            
            if not user_transcription:
                user_transcription = "인식된 내용이 없습니다"

            # user_data에서 필요한 정보 추출
            history = user_data.get("history", [])
            user_info = user_data.get("userInfo", {})

            # generator 호출
            ai_result = await self.generator.generate_response(
                user_text=user_transcription,
                history=history,
                user_info=user_info
            )
            
            ai_response_text = ai_result.get("aiResponseText", "")
            ai_audio_url = None
            if ai_response_text:
                ai_audio_url = await self.tts_service.generate_audio_url(ai_response_text)
            final_response = {
                "userTranscription": user_transcription,
                "aiResponseText": ai_response_text,
                "aiAudioUrl": ai_audio_url,
                "status": ai_result.get("status"),       # "CONTINUE" 또는 "FINISH"
                "suggestion": ai_result.get("suggestion"), # "IMAGE_UPLOAD" 또는 null
                "sessionId": session_id
            }

            logger.info(f"Success processing diary for session: {session_id}")
            return final_response

        except Exception as e:
            logger.error(f"Error in DiaryService: {str(e)}")
            # 에러 발생 시 최소한의 응답 보장
            return {
                "userTranscription": "오류 발생",
                "aiResponseText": "죄송해요, 잠시 문제가 생겼어요. 다시 말씀해 주시겠어요?",
                "aiAudioUrl": None,
                "status": "CONTINUE",
                "suggestion": None,
                "sessionId": session_id
            }
        finally:
            if os.path.exists(temp_file_path): # 사용이 끝난 임시 음성 파일 삭제
              os.remove(temp_file_path)