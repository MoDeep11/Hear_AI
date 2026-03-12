from google import genai
import json
import os

class DiaryGenerator:
    def __init__(self, api_key: str):
        # 최신 SDK에서는 Client 객체를 하나 생성하여 관리
        self.client = genai.Client(api_key=api_key)
        self.model_id = 'models/gemini-2.5-flash'
        self.prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "diary_generation.txt")

    async def generate_response(self, user_text, history, user_info):
        # txt 파일 읽기
        if not os.path.exists(self.prompt_path):
            raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {self.prompt_path}")
            
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
        
        prompt = template.format(
            user_info=json.dumps(user_info, ensure_ascii=False),
            history=json.dumps(history, ensure_ascii=False),
            user_text=user_text,
            diary_content_or_question=user_text,
            session_id=user_info.get("sessionId", "unknown")
        )
        
        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt
        )
        
        # JSON 파싱
        content = response.text.strip()
        
        # 마크다운 코드 블록 제거 로직
        if content.startswith("```"):
            lines = content.splitlines()
            # 첫 줄(```json)과 마지막 줄(```)을 제외한 나머지 합치기
            content = "\n".join(lines[1:-1]) if lines[0].startswith("```") else content
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 혹시나 JSON 형식이 아닐 경우를 대비한 예외 처리
            print(f"JSON 파싱 에러 발생. 원문: {content}")
            return {"status": "CONTINUE", "aiResponseText": "죄송해요, 다시 한번 말씀해 주시겠어요?", "suggestion": None}