"""
FastAPI 메인 애플리케이션
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from io import BytesIO
from matplotlib import pyplot as plt
from PIL import Image

# 프로젝트 경로 설정
current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, "..", ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

sys.path.insert(0, os.path.dirname(__file__) + '/../..')

# 라우터 불러오기
from ai.utils import s3_uploader
from server.app.router.chat_router import router as chat_init_router
from server.app.router.diary_router import router as diary_router, api_router as diary_api_router
from server.app.router.feedback_router import router as feedback_router
from server.app.router.report_router import router as report_router
from server.app.router.diary_router import Yuwon_router

# .env 파일을 읽어오는 함수
load_dotenv()

# 환경 변수에서 키 가져오기
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("경고: GEMINI_API_KEY를 찾을 수 없습니다.")
else:
    print("Gemini API 연결 설정 완료")

# FastAPI 앱 초기화
app = FastAPI(title="Hear_AI API Server")


# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
TEMP_DIR = os.path.join(BASE_DIR, "static", "temp")
@app.post("/upload_test")
async def upload_test():
    local_file = os.path.join(TEMP_DIR, f"generated_image_{123}_{1233}.png")
    s3_key = f"ai-gen/images/diary_{123}_{1233}.png"
    s3_url = await s3_uploader.s3_uploader.upload_file(local_file, s3_key)
    a = s3_uploader.s3_uploader.get_file(s3_key)
    print(type(a))
    # print(a.decode())
    plt.imshow(Image.open(BytesIO(a)))
    plt.show()

# 라우터 등록 및 정적 파일 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(chat_init_router)
app.include_router(diary_router)
app.include_router(diary_api_router)
app.include_router(feedback_router)
app.include_router(report_router)
app.include_router(Yuwon_router)