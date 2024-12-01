FROM python:3.11-slim
WORKDIR /app
LABEL org.opencontainers.image.source=https://github.com/jon-mey/discord-music-bot

COPY cookie.txt cookie.txt
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

RUN apt-get update && apt-get install -y ffmpeg

CMD ["python3", "main.py"]