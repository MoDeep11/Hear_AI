FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirment.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirment.txt
RUN pip install --no-cache-dir openai-whisper

COPY . .

RUN mkdir -p static/audio static/temp

CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "8000"]