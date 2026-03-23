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
    count: int = 1


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
    
    def generate_prompts(self, emotion: str, content: str, count: int) -> List[str]:
        """감정과 내용에 맞춘 스티커 프롬프트 생성 (sticker_generation.txt에서 템플릿 읽음)"""
        # sticker_generation.txt에서 프롬프트 템플릿 읽기
        prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/sticker_generation.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
        
        # 템플릿에 실제 값 적용
        base_prompt = prompt_template.format(content=content, emotion=emotion, count=count)
        
        return [base_prompt] * count
    
    async def generate(self, request: StickerGenerationRequest) -> dict:
        """스티커 생성 요청 처리 (비동기 테스트용)"""
        count = min(request.count, 5)  # 최대 5개 제한
        prompt = self.generate_prompts(request.emotion, request.content, count)
        response = self.client.models.generate_content(
                model=GEMINI3_MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT"],
                ),
        )

        # 텍스트 파트만 추출하여 경고 방지
        text_parts = [part.text for part in response.parts if part.text]
        full_text = " ".join(text_parts)

        stickers = []

        # full_text를 (숫자.)으로 구분하여 설명 리스트 추출
        descriptions = re.split(r'\d+\.\s*', full_text)[1:]  # 첫 번째 빈 문자열 제거
        emotion_image = PIL.Image.open(f'./ai/image/emotion_characters/{request.emotion}.png')
        keyword_path = os.path.join(os.path.dirname(__file__), "../prompts/sticker_generation.txt")
        with open(keyword_path, "r", encoding="utf-8") as f:
            keyword_gen = f.read()
        for i, desc in enumerate(descriptions[:count], 1):  # count만큼 제한
            desc = desc.strip()
            # 각 설명으로 이미지 생성
            image_response = self.client.models.generate_content(
                model=NANO_BANANA_MODEL,
                contents=[desc, keyword_gen, emotion_image],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )

            await save_image(image_response, f"./static/temp/generated_sticker_{request.diaryId}_{request.userId}_{i}.png")
            # 이미지 응답에서도 텍스트 파트만 추출
            image_text_parts = [part.text for part in image_response.parts if part.text]
            description = " ".join(image_text_parts)
            stickers.append({
                "imageUrl": f"https://s3.ap-northeast-2.amazonaws.com/bucket/ai-gen/sticker_{request.diaryId}_{request.userId}_{i}.png",
                "keyword": description,
            })
            
        return {
            "stickers": stickers,
        }


# 싱글톤 인스턴스
sticker_generator = StickerGenerator()