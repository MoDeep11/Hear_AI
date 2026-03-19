"""
일기 관련 서비스 로직
이미지, 스티커, 해시태그 생성을 담당합니다.
"""

import asyncio
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import sys
import os
import httpx

# 프로젝트 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from ai.image.image_generator import image_generator, ImageGenerationRequest
from ai.image.sticker_generator import sticker_generator, StickerGenerationRequest
from ai.pipelines.hashtag_generator import hashtag_generator, HashtagGenerationRequest


class DiaryServiceRequest(BaseModel):
    """일기 서비스 통합 요청"""
    userId: int
    diaryId: Optional[int] = None
    emotion: str
    content: str
    tags: Optional[List[str]] = None
    sourceType: str = "AI_CHAT"
    generateImage: bool = True
    generateSticker: bool = True
    generateHashtag: bool = True
    stickerCount: int = 3
    hashtagCount: int = 10


class DiaryService:
    """일기 생성 및 AI 컨텐츠 생성 서비스"""
    
    def __init__(self):
        self.backend_url = os.getenv("SPRING_BACKEND_URL", "http://localhost:8080")
        self.api_key = os.getenv("API_KEY", "")
    
    async def generate_image(self, user_id: int, diary_id: int, emotion: str, content: str) -> Dict:
        """이미지 생성"""
        request = ImageGenerationRequest(
            diaryId=diary_id,
            userId=user_id,
            emotion=emotion,
            content=content,
        )
        return await image_generator.generate(request)
    
    async def generate_stickers(self, user_id: int, diary_id: int, emotion: str, content: str, count: int) -> Dict:
        """스티커 생성"""
        request = StickerGenerationRequest(
            userId=user_id,
            diaryId=diary_id,
            emotion=emotion,
            content=content,
            count=count,
        )
        return await sticker_generator.generate(request)
    
    async def generate_hashtags(self, user_id: int, emotion: str, content: str, count: int) -> Dict:
        """해시태그 생성"""
        request = HashtagGenerationRequest(
            userId=user_id,
            emotion=emotion,
            content=content,
            count=count,
        )
        return await hashtag_generator.generate(request)

    async def generate_all(self, request: DiaryServiceRequest, task_id: str) -> Dict[str, Any]:
        """모든 AI 컨텐츠를 병렬로 생성"""
        tasks = []
        results = {}
        
        # 생성할 작업 추가
        if request.generateImage and request.diaryId:
            tasks.append(
                self.generate_image(
                    request.userId,
                    request.diaryId,
                    request.emotion,
                    request.content,
                )
            )
            results['image_task'] = None
        
        if request.generateSticker and request.diaryId:
            tasks.append(
                self.generate_stickers(
                    request.userId,
                    request.diaryId,
                    request.emotion,
                    request.content,
                    request.stickerCount,
                )
            )
            results['sticker_task'] = None
        
        if request.generateHashtag:
            tasks.append(
                self.generate_hashtags(
                    request.userId,
                    request.emotion,
                    request.content,
                    request.hashtagCount,
                )
            )
            results['hashtag_task'] = None
        
        # 병렬 처리
        if tasks:
            responses = await asyncio.gather(*tasks)
            
            # 결과 매핑
            task_names = [name for name in results.keys()]
            for task_name, response in zip(task_names, responses):
                results[task_name] = response
        
        # 기본 return structure
        return {
            "taskId": task_id,
            "status": "pending",
            "message": "AI 컨텐츠 생성이 시작되었습니다.",
            "data": results,
        }

    def _build_backend_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def patch_image_callback(self, diary_id: int, task_id: str, user_id: int, imageUrls: list):
        """Spring 백엔드에 이미지 생성 완료를 알리는 콜백"""
        url = f"{self.backend_url}/internal/diary/{diary_id}/ai-image"
        payload = {
            "diaryId": diary_id,
            "taskId": task_id,
            "userId": user_id,
            "imageUrls": imageUrls,
        }

        # 비동기 흐름 확인용 로그
        print(f"[DiaryService] patch_image_callback called (task_id={task_id})")
        print(f"[DiaryService] patch_image_callback payload={payload}")

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.patch(url, json=payload, headers=self._build_backend_headers())
            response.raise_for_status()
            print(f"[DiaryService] patch_image_callback response={response.status_code}")
            return response.json()

    async def patch_sticker_callback(self, diary_id: int, task_id: str, user_id: int, stickers: list):
        """Spring 백엔드에 스티커 생성 완료를 알리는 콜백"""
        url = f"{self.backend_url}/internal/diary/{diary_id}/ai-image"
        payload = {
            "diaryId": diary_id,
            "taskId": task_id,
            "userId": user_id,
            "stickers": stickers,
        }

        # 비동기 흐름 확인용 로그
        print(f"[DiaryService] patch_sticker_callback called (task_id={task_id})")
        print(f"[DiaryService] patch_sticker_callback payload={payload}")

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.patch(url, json=payload, headers=self._build_backend_headers())
            response.raise_for_status()
            print(f"[DiaryService] patch_sticker_callback response={response.status_code}")
            return response.json()

    async def send_to_backend(self, request: DiaryServiceRequest, access_token: str) -> Dict[str, Any]:
        """일기 생성 시 Spring 백엔드로 데이터 전송 (기존 구현 대비 최소화)"""
        url = f"{self.backend_url}/internal/diary/{request.diaryId}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=request.dict(), headers=headers)
            response.raise_for_status()
            return response.json()


# 싱글톤 인스턴스
diary_service = DiaryService()