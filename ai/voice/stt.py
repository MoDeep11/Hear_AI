from faster_whisper import WhisperModel
import os

class STTService:
    def __init__(self):
        self.model_size = "base" 
        
        self.model = WhisperModel(
            self.model_size, 
            device="cpu", 
            compute_type="int8",
            download_root="./models" # 모델 저장 경로 지정 (선택사항)
        )

    async def transcribe(self, file_path: str) -> str:
        try:
            segments, info = self.model.transcribe(
                file_path, 
                language="ko", 
                beam_size=5
            )

            text = "".join([segment.text for segment in segments])
            return text.strip()
            
        except Exception as e:
            print(f"STT Error: {e}")
            return ""