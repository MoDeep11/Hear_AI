from google import genai
import json
import os
import asyncio
import traceback

class DiaryGenerator:
    def __init__(self, api_key: str):
        # 최신 SDK Client 객체 생성
        self.client = genai.Client(api_key=api_key)
        self.model_id = 'gemini-2.5-flash'
        self.prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "diary_generation.txt")
        self.create_diary_prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "create_diary.txt")

    def _log_error(self, context: str, error: Exception):
        print(f"[DiaryGenerator] {context} - {type(error).__name__}: {error}")
        traceback.print_exc()
        if "503" in str(error) or "UNAVAILABLE" in str(error).upper():
            print("[DiaryGenerator] Gemini 503 / UNAVAILABLE 오류 감지됨")

    async def generate_response(self, user_text, history, user_info):
        """
        Gemini API를 호출하여 유저의 입력에 대한 응답을 생성합니다.
        """
        # 프롬프트 템플릿 읽기
        if not os.path.exists(self.prompt_path):
            raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {self.prompt_path}")
            
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
        
        # 템플릿 변수 치환
        # 유저 정보와 대화 기록을 JSON 문자열로 변환하여 프롬프트에 주입
        current_sid = user_info.get("sessionId") or user_info.get("session_id") or "unknown"
        prompt = template.format(
            user_info=json.dumps(user_info, ensure_ascii=False),
            history=json.dumps(history, ensure_ascii=False),
            user_text=user_text,
            diary_content_or_question=user_text,
            session_id=current_sid  
        )
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt
                )
            )
            
            content = response.text.strip()
            
            # 마크다운 코드 블록(```json ... ```) 제거
            if content.startswith("```"):
                lines = content.splitlines()
                if lines[0].startswith("```"):
                    # 첫 줄과 마지막 줄 제외
                    content = "\n".join(lines[1:-1])

            # 5. JSON 파싱
            return json.loads(content)

        except json.JSONDecodeError as je:
            print(f"JSON 파싱 에러: {str(je)} | 원문: {content}")
            return {
                "status": "CONTINUE", 
                "aiResponseText": "음, 방금 말씀하신 내용을 제가 잘 이해하지 못했어요. 다시 한 번 이야기해 주실래요?", 
                "suggestion": None
            }
        except Exception as e:
            self._log_error("Gemini API 호출 에러(generate_response)", e)
            return {
                "status": "CONTINUE", 
                "aiResponseText": "잠시 통신이 원활하지 않아요. 다시 시도해 주세요!", 
                "suggestion": None
            }

    async def create_diary(self, user_info, history, user_audio_urls=None, ai_audio_urls=None):
        """
        사용자 대화 이력을 바탕으로 감정 추론과 일기 본문을 생성합니다.
        """

        user_audio_urls = user_audio_urls or []
        ai_audio_urls = ai_audio_urls or []

        if not os.path.exists(self.create_diary_prompt_path):
            raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {self.create_diary_prompt_path}")

        with open(self.create_diary_prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        prompt = prompt_template
        prompt = prompt.replace("{user_info}", json.dumps(user_info, ensure_ascii=False))
        prompt = prompt.replace("{history}", json.dumps(history, ensure_ascii=False))
        prompt = prompt.replace("{user_audio_urls}", json.dumps(user_audio_urls, ensure_ascii=False))
        prompt = prompt.replace("{ai_audio_urls}", json.dumps(ai_audio_urls, ensure_ascii=False))

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt
                )
            )
            content = response.text.strip()

            if content.startswith("```"):
                lines = content.splitlines()
                if lines[0].startswith("```"):
                    content = "\n".join(lines[1:-1])

            diary_data = json.loads(content)

            if not isinstance(diary_data, dict):
                raise ValueError("Diary 생성 결과는 JSON 객체여야 합니다.")

            # 필드 기본값
            diary_data.setdefault("content", "")
            diary_data.setdefault("emotion", "NEUTRAL")
            diary_data.setdefault("tags", [])

            # tags 타입 보정: 문자열이면 리스트로, None이면 빈 리스트
            if diary_data.get("tags") is None:
                diary_data["tags"] = []
            elif isinstance(diary_data.get("tags"), str):
                diary_data["tags"] = [t.strip() for t in diary_data["tags"].split(",") if t.strip()]
            elif not isinstance(diary_data.get("tags"), list):
                diary_data["tags"] = []

            return diary_data

        except json.JSONDecodeError as je:
            print(f"Diary JSON 파싱 에러: {str(je)} | 원문: {content}")
            return {
                "content": "죄송합니다. 현재 일기를 생성할 수 없습니다.",
                "emotion": "NEUTRAL"
            }
        except Exception as e:
            print(f"Diary 생성 중 에러: {str(e)}")
            return {
                "content": "죄송합니다. 현재 일기를 생성할 수 없습니다.",
                "emotion": "NEUTRAL"
            }