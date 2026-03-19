import os
from google import genai
from typing import Dict
import asyncio


class ChatGenerator:
    _client = None
    model_id = 'models/gemini-2.5-flash'
    prompt_path = os.path.join(
        os.path.dirname(__file__), "..", "prompts", "chat_init.txt"
    )

    @classmethod
    def _get_client(cls):
        if cls._client is None:
            api_key = os.getenv("GEMINI_API_KEY")
            cls._client = genai.Client(api_key=api_key)
        return cls._client

    @classmethod
    def _load_prompt(cls) -> str:
        with open(cls.prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    @classmethod
    async def generate_initial_greeting(cls, user_info: Dict) -> str:
        try:
            prompt_template = cls._load_prompt()
            final_prompt = prompt_template.format(
                nickname=user_info.get("nickname"),
                current_streak=user_info.get("current_streak"),
                total_diaries=user_info.get("total_diaries"),
                max_streak=user_info.get("max_streak")
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
            print(f"Error generating greeting: {e}")
            return f"{user_info.get('nickname')}님 반가워요! 오늘 어떤 일이 있었나요?"