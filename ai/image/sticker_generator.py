"""
Gemini API를 사용한 스티커 이미지 생성 모듈
일기 감정과 내용을 바탕으로 스티커를 생성합니다.
"""

import PIL
from google import genai
from google.genai import types
import os
import asyncio
from typing import List, Optional
from pydantic import BaseModel
from IPython.display import display, Markdown, HTML
import pathlib
import dotenv
import re
from ai.utils.s3_uploader import s3_uploader

# Loop over all parts and display them either as text or images
def display_response(response):
  for part in response.parts:
    if part.thought: # We don't want to see the thoughts
      continue
    if part.text:
      display(Markdown(part.text))
    elif image:= part.as_image():
      image.show()

  # Display grounding sources if available
  if response.candidates and response.candidates[0].grounding_metadata and response.candidates[0].grounding_metadata.search_entry_point:
      display(HTML(response.candidates[0].grounding_metadata.search_entry_point.rendered_content))

# Save the image
# If there are multiple ones, only the last one will be saved
async def save_image(response, path):
  # Create parent directory if it doesn't exist
  os.makedirs(os.path.dirname(path), exist_ok=True)
  for part in response.parts:
    if image:= part.as_image():
      image.save(path)

# 로컬 저장 경로 정의 (절대 경로)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
TEMP_DIR = os.path.join(BASE_DIR, "static", "temp")

# Gemini API 설정
dotenv.load_dotenv()  # .env 파일에서 환경 변수 로드
GOOGLE_API_KEY = os.getenv("IMAGE_GEMINI_API_KEY")
GEMINI3_MODEL_ID = "gemini-3-flash-preview"
NANO_BANANA_MODEL = "gemini-3.1-flash-image-preview"


class StickerGenerationRequest(BaseModel):
    userId: int
    diaryId: int
    emotion: str
    content: str


class StickerGenerator:
    """Gemini API를 사용한 스티커 생성 클래스"""
    
    def __init__(self):
        # 실제 호출 시 아래 주석 해제
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self.emotion_styles = {
            "HAPPY": "행복함",
            "SAD": "슬픔",
            "ANGRY": "화남",
            "ANXIETY": "불안함",
            "NEUTRAL": "평범함",
        }
    
    def generate_prompts(self, emotion: str, content: str) -> str:
        """감정과 내용에 맞춘 스티커 프롬프트 생성 (sticker_generation.txt에서 템플릿 읽음)"""
        prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/sticker_generation.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        # 단일 스티커 생성 기준으로 count 고정 1
        base_prompt = prompt_template.format(content=content, emotion=emotion, count=1)
        return base_prompt
    
    async def generate(self, request: StickerGenerationRequest) -> dict:
        """스티커 생성 요청 처리 (비동기 테스트용)"""
        # 단일 스티커 생성만 허용
        count = 1

        prompt = self.generate_prompts(request.emotion, request.content)
        response = self.client.models.generate_content(
                model=GEMINI3_MODEL_ID,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT"],
                ),
        )

        # 텍스트 파트만 추출하여 설명 얻기
        text_parts = [part.text for part in response.parts if part.text]
        full_text = " ".join(text_parts)

        descriptions = re.split(r'\d+\.\s*', full_text)[1:]
        if not descriptions:
            descriptions = [full_text.strip()]

        desc = descriptions[0].strip()
        if not desc:
            desc = request.content

        # 감정명 정규화 (ANXIOUS -> ANXIETY 등)
        normalized_emotion = self._normalize_emotion(request.emotion)
        emotion_image = PIL.Image.open(f'./ai/image/emotion_characters/{normalized_emotion}.png')
        keyword_path = os.path.join(os.path.dirname(__file__), "../prompts/sticker_generation.txt")
        with open(keyword_path, "r", encoding="utf-8") as f:
            keyword_gen = f.read()

        image_response = self.client.models.generate_content(
            model=NANO_BANANA_MODEL,
            contents=[desc, keyword_gen, emotion_image],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        os.makedirs(TEMP_DIR, exist_ok=True)
        local_file = os.path.join(TEMP_DIR, f"generated_sticker_{request.diaryId}_{request.userId}_1.png")
        await save_image(image_response, local_file)

        image_text_parts = [part.text for part in image_response.parts if part.text]
        description = " ".join(image_text_parts)

        s3_key = f"ai-gen/stickers/sticker_{request.diaryId}_{request.userId}_1.png"
        s3_url = await s3_uploader.upload_file(local_file, s3_key)

        stickers = [{
            "imageUrl": s3_url,
            "keyword": description,
            "localPath": local_file,
        }]

        return {
            "stickers": stickers,
        }
    
    def _normalize_emotion(self, emotion: str) -> str:
        """감정 이름 정규화 (예: ANXIOUS -> ANXIETY)"""
        # 가능한 감정 매핑
        emotion_map = {
            "ANXIOUS": "ANXIETY",
            "ANXIETY": "ANXIETY",
            "HAPPY": "HAPPY",
            "SAD": "SAD",
            "ANGRY": "ANGRY",
            "NEUTRAL": "NEUTRAL",
        }
        return emotion_map.get(emotion, emotion)


# 싱글톤 인스턴스
sticker_generator = StickerGenerator()