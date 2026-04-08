from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from server.app.service import chat_service

router = APIRouter(prefix="/internal/v1/chat", tags=["Chat/Diary"])


class UserInfo(BaseModel):
    userID: int
    nickname: str
    current_streak: int
    total_diaries: int
    max_streak: int

class InitSessionRequest(BaseModel):
    sessionId: str
    userInfo: UserInfo


@router.post("/init-session")
async def init_session(request: InitSessionRequest): # 타입을 dict 대신 모델로 지정
    try:
        result = await chat_service.initialize_session(request.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))