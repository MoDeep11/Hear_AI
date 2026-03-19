"""
FastAPI 메인 애플리케이션
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# 프로젝트 경로 설정
current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, "..", ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

sys.path.insert(0, os.path.dirname(__file__) + '/../..')

# 라우터 불러오기
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

# 라우터 등록 및 정적 파일 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(chat_init_router)
app.include_router(diary_router)
app.include_router(diary_api_router)
app.include_router(feedback_router)
app.include_router(report_router)
app.include_router(Yuwon_router)


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "ok"}


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "HEAR! AI Server",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    
    # 환경변수에서 설정 로드
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "True").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
    )

