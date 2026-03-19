"""
Gemini API를 사용한 해시태그 생성 모듈
일기 내용을 분석하여 어울리는 해시태그를 생성합니다.
"""

import google.genai as genai
from google.genai import types
import os
import json
from typing import List
from pydantic import BaseModel

# Gemini API 설정
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI3_MODEL_ID = "gemini-3.0-flash"


class HashtagGenerationRequest(BaseModel):
    userId: int
    emotion: str
    content: str
    count: int = 10


class HashtagGenerator:
    """Gemini API를 사용한 해시태그 생성 클래스"""
    
    def __init__(self):
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
    
    def generate_prompt(self, emotion: str, content: str, count: int) -> str:
        """일기 내용과 감정에 맞춘 해시태그 생성 프롬프트"""
        return f"""
                당신은 소셜미디어 해시태그 전문가입니다.
                다음 일기 내용을 분석하여 가장 어울리는 한글 해시태그를 생성하세요.

                일기 내용: {content}
                감정: {emotion}

                요구사항:
                - 해시태그는 {count}개 생성
                - 모두 한글로 작성 (#포함, 예: #행복한하루)
                - 일기 내용의 핵심 감정과 상황을 잘 반영
                - 트렌디하고 유행하는 스타일
                - JSON 형식으로 ["#해시태그1", "#해시태그2", ...] 형태로 제공

                응답은 JSON 배열만 반환 (다른 설명 없음):"""
    async def generate(self, request: HashtagGenerationRequest) -> dict:
        """해시태그 생성 요청 처리"""
        count = min(max(request.count, 3), 15)  # 3~15개 제한
        prompt = self.generate_prompt(request.emotion, request.content, count)
        
        try:
            response = self.client.models.generate_content(
                model=GEMINI3_MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                response_modalities=["TEXT"],
                )
            )
            response_text = response.text.strip()
            
            # JSON 파싱 시도
            try:
                hashtags = json.loads(response_text)
                if not isinstance(hashtags, list):
                    hashtags = [response_text]
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트 처리
                hashtags = [tag.strip() for tag in response_text.split('\n') if tag.strip().startswith('#')]
            
            return {
                "status": "success",
                "userId": request.userId,
                "hashtags": hashtags[:count],
                "emotion": request.emotion,
                "count": len(hashtags[:count]),
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "userId": request.userId,
            }


# 싱글톤 인스턴스
hashtag_generator = HashtagGenerator()
