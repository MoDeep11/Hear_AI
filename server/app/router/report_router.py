from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from app.service.report_service import generate_monthly_ai_report

router = APIRouter(prefix="/internal/v1/statistics")

class DiaryEntry(BaseModel):
    diaryId: int
    date: str
    content: str
    emotion: str
    
class MonthlyReportRequest(BaseModel):
    userId: int
    yearMonth: str
    diaries: List[DiaryEntry]
    monthlyDiaryCount: 12
    monthlyPhotoCount: 11
    totalDiaries: 126
    maxStreak: 34
    currentStreak: 8

    

@router.post("/reports")
async def create_monthly_report(request: MonthlyReportRequest):
    report_content = await generate_monthly_ai_report(request)
    
    return{
        "userId": request.userId,
        "yearMonth": request.yearMonth,
        "aiReportContent": report_content
    }