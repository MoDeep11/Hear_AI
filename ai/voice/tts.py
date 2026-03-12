
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

    asyncio.run(_speak_async(text))

    pygame.mixer.music.load("voice.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pass
