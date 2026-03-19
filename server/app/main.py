import os
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, "..", ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

# 라우터 불러오기
from server.app.router.chat_router import router as chat_init_router
from server.app.router.diary_router import router as diary_router, api_router as diary_api_router
from server.app.router.feedback_router import router as feedback_router
from server.app.router.report_router import router as report_router

# .env 파일을 읽어오는 함수
load_dotenv()

# 환경 변수에서 키 가져오기
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("경고: GEMINI_API_KEY를 찾을 수 없습니다.")
else:
    print("Gemini API 연결 설정 완료")

app = FastAPI(title="Hear_AI API Server")


app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(chat_init_router)
app.include_router(diary_router)
app.include_router(diary_api_router)
app.include_router(feedback_router)
app.include_router(report_router)