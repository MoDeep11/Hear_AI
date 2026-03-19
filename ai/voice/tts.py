# import edge_tts
# import asyncio
# import pygame

# pygame.init()
# pygame.mixer.init()

# async def _speak_async(text):
#     communicate = edge_tts.Communicate(
#         text=text,
#         voice="ko-KR-HyunsuMultilingualNeural",
#         rate="+20%",
#         volume="+100%"
#     )
#     await communicate.save("voice.mp3")

# def speak(text):
#     # TTS 생성
#     asyncio.run(_speak_async(text))

#     # MP3 재생
#     pygame.mixer.music.load("voice.mp3")
#     pygame.mixer.music.play()

#     while pygame.mixer.music.get_busy():
#         pass


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