import os
import json
import google.generativeai as genai

PROMPT_FILE_PATH = "ai/prompts/monthly_report.txt"

async def generate_monthly_ai_report(data):
    if not os.path.exists(PROMPT_FILE_PATH):
        return "프롬프트를 찾을 수 없습니다"
    
    with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
        report_prompt = f.read()
        
    diary_summary = "\n".join([f"- {d.date}: {d.content} (감정: {d.emotion})" for d in data.diaries])
    
    final_prompt = report_prompt.format(
        yearMonth=data.yearMonth,
        diary_summary=diary_summary,
        monthlyDiaryCount=data.monthlyDiaryCount,
        maxStreak=data.maxStreak,
        totalDiaries=data.totalDiaries
    )
    
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    response = await model.generate_content_async(final_prompt)
    
    try:
        res_json = json.loads(response.text)
        return f"{res_json['summary']}\n\n 조언: {res_json['advice']}"
    except:
        return response.text