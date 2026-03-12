import edge_tts
import asyncio
import pygame

pygame.init()
pygame.mixer.init()

async def _speak_async(text):
    communicate = edge_tts.Communicate(
        text=text,
        voice="ko-KR-HyunsuMultilingualNeural",
        rate="+20%",
        volume="+100%"
    )
    await communicate.save("voice.mp3")

def speak(text):
    # TTS 생성
    asyncio.run(_speak_async(text))
