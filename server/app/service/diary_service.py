# import logging
# import uuid
# import aiofiles
# import os
# from ai.pipelines.diary_generator import DiaryGenerator
# from ai.voice.stt import STTService
# from ai.voice.tts import TTSService

# # 로깅 설정
# logger = logging.getLogger(__name__)

# class DiaryService:
#     def __init__(self, generator: DiaryGenerator, stt_service: STTService, tts_service: TTSService):
#         self.generator = generator
#         self.stt_service = stt_service
#         self.tts_service = tts_service
#         # 임시 파일 및 오디도 저장 경로
#         self.temp_dir = "static/temp"
#         os.makedirs(self.temp_dir, exist_ok=True)

#     async def process_voice_diary(self, file, session_id: str, user_data: dict):
#         temp_file_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}.wav")
        
#         try:
#             content = await file.read()
#             async with aiofiles.open(temp_file_path, 'wb') as f:
#                 await f.write(content)
#             # STT 단계 유저 음성 -> 텍스트 변환
#             user_transcription = await self.stt_service.transcribe(temp_file_path)
            
#             if not user_transcription:
#                 user_transcription = "인식된 내용이 없습니다"

#             # user_data에서 필요한 정보 추출
#             history = user_data.get("history", [])
#             user_info = user_data.get("userInfo", {})

#             # generator 호출
#             ai_result = await self.generator.generate_response(
#                 user_text=user_transcription,
#                 history=history,
#                 user_info=user_info
#             )
            
#             ai_response_text = ai_result.get("aiResponseText", "")
#             ai_audio_url = None
#             if ai_response_text:
#                 ai_audio_url = await self.tts_service.generate_audio_url(ai_response_text)
#             final_response = {
#                 "userTranscription": user_transcription,
#                 "aiResponseText": ai_response_text,
#                 "aiAudioUrl": ai_audio_url,
#                 "status": ai_result.get("status"),       # "CONTINUE" 또는 "FINISH"
#                 "suggestion": ai_result.get("suggestion"), # "IMAGE_UPLOAD" 또는 null
#                 "sessionId": session_id
#             }

#             logger.info(f"Success processing diary for session: {session_id}")
#             return final_response

#         except Exception as e:
#             logger.error(f"Error in DiaryService: {str(e)}")
#             # 에러 발생 시 최소한의 응답 보장
#             return {
#                 "userTranscription": "오류 발생",
#                 "aiResponseText": "죄송해요, 잠시 문제가 생겼어요. 다시 말씀해 주시겠어요?",
#                 "aiAudioUrl": None,
#                 "status": "CONTINUE",
#                 "suggestion": None,
#                 "sessionId": session_id
#             }
#         finally:
#             if os.path.exists(temp_file_path): # 사용이 끝난 임시 음성 파일 삭제
#               os.remove(temp_file_path)


import logging
import uuid
import aiofiles
import os
import httpx
# 절대 자기 자신(DiaryService)을 여기서 import 하지 마세요!

# 프로젝트 루트가 sys.path에 추가되어 있으므로 아래와 같이 접근합니다.
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
            # 1. 유저 음성 처리 (URL 다운로드 방식)
            if chat_data.userAudioUrl:
                async with httpx.AsyncClient() as client:
                    response = await client.get(chat_data.userAudioUrl)
                    if response.status_code == 200:
                        async with aiofiles.open(temp_file_path, 'wb') as f:
                            await f.write(response.content)
                        # STT 실행
                        user_transcription = await self.stt_service.transcribe(temp_file_path)
            
            # 2. 음성이 없으면 텍스트 메시지 사용
            if not user_transcription and chat_data.message:
                user_transcription = chat_data.message

            if not user_transcription:
                user_transcription = "내용 없음"
            user_info_dict = chat_data.userInfo.dict()
            # generator가 내부에서 {session_id}를 채울 수 있도록 sessionId도 넣어줌
            user_info_dict['sessionId'] = session_id_val
            # 3. AI 답변 생성
            # Pydantic 모델을 dict로 변환하여 generator에 전달
            ai_result = await self.generator.generate_response(
                user_text=user_transcription,
                history=[h.dict() for h in chat_data.history],
                user_info=chat_data.userInfo.dict()
            )
            
            ai_response_text = ai_result.get("aiResponseText", "")
            
            # 4. TTS 생성
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