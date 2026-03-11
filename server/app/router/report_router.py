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

if __name__ == "__main__":
    # 테스트용 가짜 데이터 생성
    test_data = MonthlyReportRequest(
        userId=1,
        yearMonth="2026-03",
        diaries=[
            DiaryEntry(diaryId=1, date="2026-03-01", content="오늘 정말 행복했다!", emotion="Joy"),
            DiaryEntry(diaryId=2, date="2026-03-05", content="업무가 너무 많아 힘들었다.", emotion="Sadness")
        ],
        monthlyDiaryCount=2,
        monthlyPhotoCount=1,
        totalDiaries=100,
        maxStreak=5,
        currentStreak=2
    )

    async def run_test():
        print("\n=== AI 리포트 생성 테스트 시작 ===")
        print(f"대상 달: {test_data.yearMonth}")
        result = await create_monthly_report(test_data)
        print("\n=== 생성된 결과 ===")
        print(result["aiReportContent"])
        print("==============================\n")

    asyncio.run(run_test())