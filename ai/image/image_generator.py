"""
Gemini API를 사용한 이미지 생성 모듈
일기 내용을 바탕으로 AI 이미지를 생성합니다.
"""
import logging
import os
import dotenv
import asyncio
from typing import Optional
from pydantic import BaseModel
from IPython.display import display, Markdown
import pathlib

from google import genai
from google.genai import types
from ai.utils.s3_uploader import s3_uploader

from boto3 import client
import io
from PIL import Image
import uuid

dotenv.load_dotenv()  # .env 파일에서 환경 변수 로드
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

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
  for part in response.parts:
    if image:= part.as_image():
    #   image.save(path)
        upload_to_s3(convert_image_to_bytes(image), AWS_S3_BUCKET, path)

s3_client = client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name="ap-northeast-2",
)
 
def upload_to_s3(file: io.BytesIO, bucket_name: str, file_name: str) -> None:
    s3_client.upload_fileobj(
        file,
        bucket_name,
        file_name,
        ExtraArgs={"ContentType": "image/png"},
    )

def convert_image_to_bytes(image: Image) -> io.BytesIO:
    img_byte = io.BytesIO()
    image.save(img_byte, "png", quality=70)
    img_byte.seek(0)
    return img_byte

# 로컬 저장 경로 정의 (절대 경로)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
TEMP_DIR = os.path.join(BASE_DIR, "static", "temp")

# Gemini API 설정
dotenv.load_dotenv()  # .env 파일에서 환경 변수 로드
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI3_MODEL_ID = "gemini-3-flash-preview"
NANO_BANANA_MODEL = "gemini-3.1-flash-image-preview"

class ImageGenerationRequest(BaseModel):
    diaryId: int
    userId: int
    emotion: str
    content: str


class ImageGenerator:
    """Gemini API를 사용한 이미지 생성 클래스"""
    
    def __init__(self):
        # 실제 호출 시 아래 주석 해제
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self.emotion_prompts = {
            "HAPPY": "행복함",
            "SAD": "슬픔",
            "ANGRY": "화남",
            "ANXIETY": "불안함",
            "NEUTRAL": "평범함",
        }
    
    def generate_prompt(self, emotion: str, content: str) -> str:
        """일기 내용과 감정에 맞춘 프롬프트 생성 (image_generation.txt에서 템플릿 읽음)"""
        emotion_desc = self.emotion_prompts.get(emotion, "없음")
        
        # image_generation.txt에서 프롬프트 템플릿 읽기
        prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/image_generation.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
        
        # 템플릿에 실제 값 적용
        return prompt_template.format(content=content, emotion_desc=emotion_desc)

    async def generate(self, request: ImageGenerationRequest) -> dict:
        """이미지 생성 요청 처리 (비동기 테스트용)"""
        prompt = self.generate_prompt(request.emotion, request.content)

        try:
            # 실제 Gemini 호출 (테스트 시 주석 유지)
            response = self.client.models.generate_content(
                model=GEMINI3_MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["Text"],
                ),
            )
            response = self.client.models.generate_content(
                model=NANO_BANANA_MODEL,
                contents=response.text,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )
            os.makedirs(TEMP_DIR, exist_ok=True)
            id1 = uuid.uuid4()
            id2 = uuid.uuid4()
            local_file = os.path.join(TEMP_DIR, f"generated_image_{id1}_{id2}.png")
            await save_image(response, local_file)

            s3_key = f"ai-gen/images/diary_{id1}_{id2}.png"
            s3_url = await s3_uploader.upload_file(local_file, s3_key)
            image_urls = [s3_url] if s3_url else [
                f"HEAR_AI/static/temp/generated_image_{id1}_{id2}.png"
            ]

            # S3 업로드 후 로컬 파일 삭제
            if os.path.exists(local_file):
                os.remove(local_file)

            return {
                "imageUrls": image_urls,
                "localPath": local_file,
            }

        except Exception as e:
            logging.exception("이미지 생성 중 예외 발생")
            return {
                "imageUrls": [],
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                },
            }


# 싱글톤 인스턴스
image_generator = ImageGenerator()