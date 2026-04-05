import edge_tts
import uuid
import os

class TTSService:
    def __init__(self, output_dir: str = "static/audio"):
        self.output_dir = output_dir
        self.base_url = os.getenv("AI_SERVER_URL", "http://localhost:8000")
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_audio_url(self, text: str) -> str:
        file_name = f"ai_{uuid.uuid4()}.mp3"
        file_path = os.path.join(self.output_dir, file_name)

        communicate = edge_tts.Communicate(text, "ko-KR-HyunsuMultilingualNeural")
        await communicate.save(file_path)

        # 클라이언트가 접근 가능한 URL 경로 반환
        return f"{self.base_url}/static/audio/{file_name}"