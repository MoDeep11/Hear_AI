# HEAR! AI Server

Gemini API를 활용한 일기 기반 AI 컨텐츠 생성 서버

## 기능

### 1. 스티커 생성 (AI Sticker Generation)
- **엔드포인트**: `POST /internal/v1/sticker/generate`
- **설명**: 일기의 감정과 내용을 분석하여 어울리는 스티커(이모지)를 생성
- **요청**:
  ```json
  {
    "userId": 123,
    "emotion": "HAPPY",
    "content": "오늘 친구랑 한강에서 자전거 탔다.",
    "count": 3
  }
  ```
- **응답**: 202 (작업 접수됨) + taskId 포함

### 2. 이미지 생성 (AI Image Generation)
- **엔드포인트**: `POST /internal/images/generate`
- **설명**: 일기 내용을 바탕으로 고해상도 디지털 아트 이미지 생성
- **요청**:
  ```json
  {
    "diaryId": 2026,
    "userId": 123,
    "emotion": "HAPPY",
    "content": "한강에서 자전거를 타고 노을을 보았다."
  }
  ```
- **응답**: 202 + taskId

### 3. 해시태그 생성 (Hashtag Generation)
- **엔드포인트**: `POST /internal/diary/generate-all`
- **설명**: 일기 내용에 맞는 트렌디한 한글 해시태그 생성
- **요청**:
  ```json
  {
    "userId": 123,
    "diaryId": 2026,
    "emotion": "HAPPY",
    "content": "오늘 정말 행복한 하루였다",
    "generateImage": true,
    "generateSticker": true,
    "generateHashtag": true,
    "stickerCount": 3,
    "hashtagCount": 10
  }
  ```

### 4. 작업 상태 조회 (Task Status)
- **엔드포인트**: `GET /internal/task/{taskId}`
- **설명**: 생성 작업의 현재 상태 조회

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 설정
`.env` 파일 생성 및 Gemini API 키 설정:
```env
GEMINI_API_KEY=your_api_key_here
HOST=0.0.0.0
PORT=8000
RELOAD=True
```

Gemini API 키는 [Google AI Studio](https://aistudio.google.com/app/apikey)에서 발급받을 수 있습니다.

### 3. 서버 실행
```bash
python -m uvicorn server.app.main:app --reload
```

또는
```bash
python server/app/main.py
```

## API 호출 예제

### cURL
```bash
# 스티커 생성
curl -X POST http://localhost:8000/internal/v1/sticker/generate \
  -H "Content-Type: application/json" \
  -d '{
    "userId": 123,
    "emotion": "HAPPY",
    "content": "오늘 친구한테 선물을 받아서 기분이 좋다!",
    "count": 3
  }'

# 이미지 생성
curl -X POST http://localhost:8000/internal/images/generate \
  -H "Content-Type: application/json" \
  -d '{
    "diaryId": 2026,
    "userId": 123,
    "emotion": "HAPPY",
    "content": "맑은 하늘 아래 공원에서 시간을 보냈다"
  }'

# 모든 컨텐츠 생성
curl -X POST http://localhost:8000/internal/diary/generate-all \
  -H "Content-Type: application/json" \
  -d '{
    "userId": 123,
    "diaryId": 2026,
    "emotion": "HAPPY",
    "content": "오늘 정말 행복한 하루였다",
    "generateImage": true,
    "generateSticker": true,
    "generateHashtag": true,
    "stickerCount": 3,
    "hashtagCount": 10
  }'

# 작업 상태 조회
curl http://localhost:8000/internal/task/sticker_task_abc123
```

### Python
```python
import requests
import json

# 스티커 생성
response = requests.post(
    "http://localhost:8000/internal/v1/sticker/generate",
    headers={"Content-Type": "application/json"},
    json={
        "userId": 123,
        "emotion": "HAPPY",
        "content": "오늘 정말 행복했다!",
        "count": 3
    }
)
print(response.json())
```

## 지원하는 감정 타입

- `HAPPY`: 밝고 긍정적인 분위기
- `SAD`: 차분하고 진지한 분위기
- `ANGRY`: 강렬하고 동적인 분위기
- `ANXIOUS`: 불안하고 신비로운 분위기
- `CALM`: 평온하고 고요한 분위기
- `CONFUSED`: 추상적이고 혼란스러운 분위기

## 아키텍처

### 비동기 처리
- asyncio.gather를 사용한 병렬 처리
- 백그라운드 작업으로 장시간 작업 처리
- 202 응답으로 클라이언트에게 빠른 피드백 제공

### Gemini API 활용
- gemini-2.0-flash 모델 사용
- 감정별 커스텀 프롬프트 생성
- 한글/영문 이중 지원

## 파일 구조

```
HEAR_AI/
├── ai/
│   ├── image/
│   │   ├── image_generator.py      # 이미지 생성
│   │   └── sticker_generator.py    # 스티커 생성
│   ├── pipelines/
│   │   └── hashtag_generator.py    # 해시태그 생성
│   └── voice/
├── server/
│   └── app/
│       ├── main.py                 # FastAPI 앱
│       ├── service/
│       │   └── diary_service.py    # 비즈니스 로직
│       └── router/
│           └── diary_router.py     # 엔드포인트 정의
├── test/
├── .env                            # 환경변수
├── requirements.txt                # 의존성
└── README.md                       # 이 파일
```

## 개발 담당

- 이미지 + 스티커 생성: 유원
- 해시태그 생성: 유원
- 프롬프트 작성: 하원

## 라이선스

MIT
