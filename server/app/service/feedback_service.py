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
