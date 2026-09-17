FROM python:3.11-slim

# Note: this image now includes torch + sentence-transformers + faiss for
# real embeddings/vector search, so the first build takes noticeably
# longer (~5-10 min) and the image is ~3-4GB, mostly torch. This is
# expected -- not a misconfiguration.

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN mkdir -p /app/app/storage /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
