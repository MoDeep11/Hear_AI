import os
import sys
import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

from server.app.service.report_service import generate_monthly_ai_report

router = APIRouter(prefix="/internal/v1/statistics", tags=["Report"])

class DiaryEntry(BaseModel):
    diaryId: int
    date: str
    content: str
    emotion: str
    
class MonthlyReportRequest(BaseModel):
    userId: int
    yearMonth: str
    diaries: List[DiaryEntry]
    monthlyDiaryCount: int
    monthlyPhotoCount: int
    totalDiaries: int
    maxStreak: int
    currentStreak: int

@router.post("/reports")
async def create_monthly_report(request: MonthlyReportRequest):
    report_content = await generate_monthly_ai_report(request)
    return {
        "userId": request.userId,
        "yearMonth": request.yearMonth,
        "aiReportContent": report_content
    }