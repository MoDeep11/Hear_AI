import os
from google import genai
from typing import Dict
import asyncio
import dotenv
import time


class ChatGenerator:
    _client = None
    model_id = 'gemini-3-flash-preview'
    prompt_path = os.path.join(
        os.path.dirname(__file__), "..", "prompts", "chat_init.txt"
    )

    @classmethod
    def _get_client(cls):
        if cls._client is None:
            dotenv.load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
            print(api_key)
            cls._client = genai.Client(api_key=api_key)
        return cls._client

    @classmethod
    def _load_prompt(cls) -> str:
        with open(cls.prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    @classmethod
    async def generate_initial_greeting(cls, user_info: Dict) -> str:
        max_retries = 3
        base_delay = 1.0  # 1 second
        
        for attempt in range(max_retries):
            try:
                prompt_template = cls._load_prompt()
                final_prompt = prompt_template.format(
                    nickname=user_info.get("nickname"),
                    current_streak=user_info.get("streakDays"),
                    total_diaries=user_info.get("totalDiaries"),
                    max_streak=user_info.get("maxStreak")
                )
                client = cls._get_client()
                response = client.models.generate_content(
                    model=cls.model_id,
                    contents=final_prompt
                )

                if response and response.text:
                    return response.text.strip()
                else:
                    return f"안녕, {user_info.get('nickname')}! 오늘 하루는 어땠어?"

            except Exception as e:
                error_str = str(e)
                
                # 503 UNAVAILABLE - 모델 과부하, 재시도
                if "503" in error_str or "UNAVAILABLE" in error_str:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # exponential backoff
                        print(f"Model temporarily unavailable (attempt {attempt + 1}/{max_retries}). Retrying in {delay:.1f}s...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        print(f"Model still unavailable after {max_retries} attempts. Using fallback greeting.")
                        return f"{user_info.get('nickname')}님 반가워요! 오늘 어떤 일이 있었나요?"
                
                # 429 RESOURCE_EXHAUSTED - 쿼터 초과, 즉시 폴백
                elif "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    print("API quota exceeded. Using fallback greeting.")
                    return f"{user_info.get('nickname')}님 반가워요! 오늘 어떤 일이 있었나요?"
                
                # 기타 오류
                else:
                    print(f"Unexpected error generating greeting: {e}")
                    return f"{user_info.get('nickname')}님 반가워요! 오늘 어떤 일이 있었나요?"