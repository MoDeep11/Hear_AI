import whisper
import torch

class   STTService:
    def __init__(self):
        # GPU 사용 가능 시 GPU 사용, 아니면 CPU 사용
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = whisper.load_model("base").to(self.device)

    async def transcribe(self, file_path: str) -> str:
        try:
            # fp16=False는 CPU 환경에서 경고를 방지하기 위함
            result = self.model.transcribe(file_path, language="ko", fp16=False)
            return result["text"].strip()
        except Exception as e:
            print(f"STT Error: {e}")
            return ""