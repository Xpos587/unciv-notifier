FROM python:3.12-slim

WORKDIR /app

# Установка необходимых пакетов
RUN apt-get update && \
  apt-get install -y --no-install-recommends ca-certificates curl && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -q httpx python-dotenv
COPY main.py .

CMD ["python", "main.py"]
