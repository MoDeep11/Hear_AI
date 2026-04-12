import os
import sys

current_file = os.path.abspath(__file__)
router_dir = os.path.dirname(current_file)        # router/
app_dir = os.path.dirname(router_dir)            # app/
project_root = os.path.dirname(os.path.dirname(app_dir))  # Hear_AI/

if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from service.feedback_service import FeedbackService

# 스키마 정의
class DiaryFeedbackRequest(BaseModel):
    diaryId: int
    userId: int
    nickname: str
    emotion: str
    content: str
    imageUrls: Optional[List[str]] = []

class DiaryFeedbackResponse(BaseModel):
    diaryId: int
    aiComment: str

# 라우터 설정
router = APIRouter(prefix="/internal/v1/diaries", tags=["Diary Feedback"])
feedback_service = FeedbackService()

@router.post("/comment", response_model=DiaryFeedbackResponse)
async def create_feedback(request: DiaryFeedbackRequest):
    # 서비스 레이어 호출
    ai_comment = await feedback_service.get_diary_feedback(request)
    
    if "오류" in ai_comment:
        raise HTTPException(status_code=500, detail=ai_comment)
        
    return DiaryFeedbackResponse(
        diaryId=request.diaryId,
        aiComment=ai_comment
    )