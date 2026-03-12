import logging
from ai.pipelines.diary_generator import DiaryGenerator

# 로깅 설정
logger = logging.getLogger(__name__)

class DiaryService:
    def __init__(self, generator: DiaryGenerator):
        self.generator = generator

    async def process_voice_diary(self, file, session_id: str, user_data: dict):
        
        try:
            # STT 단계 유저 음성 -> 텍스트 변환
            # TODO: STT 브랜치에서 만든 함수를 임포트하여 연결
            # 예: user_transcription = await stt_service.transcribe(file)
            user_transcription = "오늘 하루는 정말 평범했는데, 점심에 먹은 파스타가 맛있었어." # 테스트용 임시 데이터

            # Gemini 단계 상황 판단 및 답변/일기 생성
            # user_data에서 필요한 정보 추출
            history = user_data.get("history", [])
            user_info = user_data.get("userInfo", {})

            # generator 호출
            ai_result = await self.generator.generate_response(
                user_text=user_transcription,
                history=history,
                user_info=user_info
            )

            # TTS 단계 AI 답변 텍스트 -> 음성 파일 URL 생성
            # TODO: TTS 브랜치 담당자가 만든 함수를 임포트하여 연결
            # ai_audio_url = await tts_service.generate_url(ai_result["aiResponseText"])
            ai_audio_url = None # 아직 구현 전이라면 null 유지

            # 4. 최종 JSON 객체 조립 (Spring 서버 규격)
            final_response = {
                "userTranscription": user_transcription,
                "aiResponseText": ai_result.get("aiResponseText"),
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