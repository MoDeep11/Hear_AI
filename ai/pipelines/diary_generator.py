from google import genai
import json
import os
import asyncio

class DiaryGenerator:
    def __init__(self, api_key: str):
        # 최신 SDK Client 객체 생성
        self.client = genai.Client(api_key=api_key)
        self.model_id = 'models/gemini-2.5-flash' 
        self.prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "diary_generation.txt")

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
            print(f"Gemini API 호출 에러: {str(e)}")
            return {
                "status": "CONTINUE", 
                "aiResponseText": "잠시 통신이 원활하지 않아요. 다시 시도해 주세요!", 
                "suggestion": None
            }