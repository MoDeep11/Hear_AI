FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \ 
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --upgrade pip && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir faster-whisper

COPY . .
RUN mkdir -p static/audio static/temp

CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "8000"]