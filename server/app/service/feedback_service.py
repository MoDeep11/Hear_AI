import os
from dotenv import load_dotenv
from google import genai
from datetime import datetime

# 1. 환경 변수 로드
load_dotenv()

# 2. 클라이언트 설정 (os.getenv가 .env 파일의 키를 읽어옵니다)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_feedback(nickname, diary_text):
    today_str = datetime.now().strftime("%Y년 %m월 %d일")

    try:
        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            config={
                "system_instruction": f"""
                1. 당신은 따뜻한 일기 가이드임.
                2. 첫 문장은 반드시 "{today_str}은 ~한 하루였군요, {nickname}님!"으로 시작할 것.
                3. 사용자의 일기를 읽고 3-4문장으로 다정한 피드백을 작성할 것.
                """
            },
            contents=diary_text
        )
        return response.text
    except Exception as e:
        return f"피드백을 생성하는 중 오류가 발생했습니다: {e}"


# 테스트 실행
if __name__ == "__main__":
    print(generate_feedback("성환", "아 드디어 학교가 끝났다 이제 집에가서 커피 빨면서 쉬고싶다ㅠㅠ"))