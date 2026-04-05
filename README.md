# Hear_AI

## 프로젝트 개요
Hear_AI는 감정 기반 AI 일기 작성 / 이미지 및 스티커 생성 서비스입니다. FastAPI 서버에서 음성 및 텍스트 기반 일기 입력을 처리하고, Google Gemini API 를 활용하여 이미지/스티커를 생성한 뒤 Spring 백엔드에 콜백합니다.

## 아키텍처 요약
- FastAPI 기반 웹 서버 (`server/app`)
  - 라우터: `server/app/router/diary_router.py` 등
  - 서비스: `server/app/service/diary_service.py` 등
- AI 모듈 (`ai`)
  - 이미지: `ai/image/image_generator.py`, `ai/image/sticker_generator.py`
  - 파이프라인: `ai/pipelines/diary_generator.py`
  - 음성: `ai/voice/stt.py`, `ai/voice/tts.py`
- 프롬프트 템플릿: `ai/prompts/*.txt`

## 주요 기능
1. 음성 및 텍스트 일기 처리
   - STT, Diary Generator, TTS 연계
   - `/internal/v1/chats/messages` 엔드포인트
2. 이미지 생성 비동기 작업
   - `/internal/images/generate` 엔드포인트
   - `image_task_<diaryId>_<userId>` 비동기 처리
3. 스티커 생성 비동기 작업
   - `/internal/v1/sticker/generate` 엔드포인트
   - `sticker_task_<diaryId>_<userId>` 비동기 처리
4. Spring 백엔드 콜백
   - `/internal/diary/{diaryId}/ai-image` 호출
   - `patch_image_callback`, `patch_sticker_callback`

## 설정
1. `.env` 파일 필수
   - `GEMINI_API_KEY` (Gemini API 키)
   - `IMAGE_GEMINI_API_KEY` (AI 이미지 API 키)
2. 종속성
   - Python 패키지: `requirements.txt` 참고

## 실행 방법
Docker:
```bash
docker-compose up --build
```

## 엔드포인트
- POST `/internal/v1/chats/messages`: 음성/텍스트 일기 대화
- POST `/api/v1/diaries`: 일기 생성
- POST `/internal/images/generate`: 이미지 생성 ## 비동기
- POST `/internal/v1/sticker/generate`: 스티커 생성 ## 비동기
- GET `/internal/task/{task_id}`: 작업 상태 조회

## 경로 / 파일 상관관계
- `ai/prompts/image_generation.txt` : 이미지 프롬프트 템플릿
- `ai/prompts/sticker_generation.txt` : 스티커 프롬프트 템플릿
- `ai/image/image_generator.py`, `ai/image/sticker_generator.py` : Gemini API 호출 및 저장
- `server/app/service/diary_service.py` : generate + callback 로직
- `server/app/router/diary_router.py` : 비동기 작업 큐 + 상태 저장


