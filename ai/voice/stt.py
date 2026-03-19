# import whisper
# import pyaudio
# import wave
# import tts

# model = whisper.load_model("base")

# # 녹음 설정
# CHUNK = 1024
# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# RATE = 16000
# RECORD_SECONDS = 2
# WAVE_OUTPUT_FILENAME = "temp_recording.wav"

# audio = pyaudio.PyAudio()

# stream = audio.open(format=FORMAT,
#                     channels=CHANNELS,
#                     rate=RATE,
#                     input=True,
#                     frames_per_buffer=CHUNK)

# print("음성 인식 시작... (Ctrl+C로 종료)")

# try:
#     while True:
#         frames = []
#         # 녹음
#         for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
#             data = stream.read(CHUNK, exception_on_overflow=False)
#             frames.append(data)

#         # 파일 저장
#         with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
#             wf.setnchannels(CHANNELS)
#             wf.setsampwidth(audio.get_sample_size(FORMAT))
#             wf.setframerate(RATE)
#             wf.writeframes(b''.join(frames))

#         # STT 실행
#         result = model.transcribe(WAVE_OUTPUT_FILENAME, language="ko", fp16=False)
#         text = result["text"].strip()

#         if text:
#             print(f"인식 결과: {text}")
#             # TTS로 읽기
#             tts.speak(text)

# except KeyboardInterrupt:
#     print("\n사용자에 의해 종료되었습니다.")
# finally:
#     stream.stop_stream()
#     stream.close()
#     audio.terminate()
    
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