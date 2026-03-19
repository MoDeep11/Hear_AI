"""
FastAPI 메인 애플리케이션
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# 프로젝트 경로 설정
sys.path.insert(0, os.path.dirname(__file__) + '/../..')

from server.app.router.diary_router import router as diary_router

# FastAPI 앱 초기화
app = FastAPI(
    title="HEAR! AI Server",
    description="일기 기반 AI 컨텐츠 생성 서버",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(diary_router)


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
