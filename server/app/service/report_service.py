import os
import sys
import json
from dotenv import load_dotenv

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

from ai.pipelines.report_generator import MonthylyReportGenerator

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
PROMPT_FILE_PATH = os.path.join(project_root, "ai/prompts/monthly_report.txt")

# 생성자 호출
generator = MonthylyReportGenerator(api_key=API_KEY, prompt_path=PROMPT_FILE_PATH)

async def generate_monthly_ai_report(data):
    # 일기 데이터를 텍스트로 가공
    diary_summary = "\n".join([
        f"Date: {d.date}, Emotion: {d.emotion}, Content: {d.content}" 
        for d in data.diaries
    ])
    
    # 파이프라인에 보낼 변수 정리
    input_variables = {
        "yearMonth": data.yearMonth,
        "monthlyDiaryCount": data.monthlyDiaryCount,
        "maxStreak": data.maxStreak,
        "totalDiaries": data.totalDiaries,
        "diary_summary": diary_summary
    }
    
    try:
        # AI 엔진 호출
        ai_response = await generator.generate_report(input_variables)
        print(f"[DEBUG] ai_response 타입: {type(ai_response)}")
        print(f"[DEBUG] ai_response 키 목록: {list(ai_response.keys())}")
        print(f"[DEBUG] ai_response 전체: {ai_response}")
        
        result_data = ai_response
        if isinstance(result_data, str):
            try:
                result_data = json.loads(result_data)
            except:
                pass

        final_dict = {}
        if isinstance(result_data, dict):
            for k, v in result_data.items():
                # 키에서 모든 공백, 줄바꿈, 따옴표 제거
                clean_k = str(k).replace('\n', '').replace('"', '').replace("'", "").strip()
                final_dict[clean_k] = v
        
        report_content = final_dict.get("aiReportContent", "분석 내용을 찾을 수 없습니다.")
        
        if report_content == "분석 내용을 찾을 수 없습니다.":
            print(f"DEBUG: 현재 인식된 키들 -> {list(final_dict.keys())}")

        return report_content
        
    except Exception as e:
        print(f"서비스 계층 에러: {e}")
        # 진짜 마지막 수단
        if 'ai_response' in locals():
            print(f"AI 응답 원본 타입: {type(ai_response)}")
            print(f"AI 응답 원본 내용: {ai_response}")
        return "리포트 생성 중 오류가 발생했습니다."