import os
from google import genai
from datetime import datetime

class FeedbackGenerator:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # 프롬프트 파일 읽기
        with open("ai/prompts/diary_feedback.txt", "r", encoding="utf-8") as f:
            self.system_instruction_template = f.read()

    def generate(self, nickname: str, content: str, emotion: str):
        today_str = datetime.now().strftime("%Y년 %m월 %d일")
        
        # 템플릿에 데이터 주입 (간단한 치환 방식)
        instruction = self.system_instruction_template.format(
            today_str=today_str,
            nickname=nickname,
            emotion_str=emotion,
            diary_text=content
        )

        try:
            response = self.client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=instruction
            )
            return response.text
        except Exception as e:
            return f"피드백 생성 중 오류가 발생했습니다: {str(e)}"