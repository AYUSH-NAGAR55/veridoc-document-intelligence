# Single-container build: React frontend + FastAPI backend served from one
# process on one port. Built for free single-port hosts (Hugging Face
# Spaces, and similar) where you can't run two separate services.
#
# For normal local development or a host that supports multiple services,
# use docker-compose.yml instead — it runs the frontend and backend as
# separate containers with hot-reload.

# ---- Stage 1: build the React frontend ----
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

# ---- Stage 2: backend + built frontend, one process ----
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY --from=frontend-build /frontend/dist ./app/static

RUN mkdir -p /app/app/storage /app/data
ENV VERIDOC_DB_PATH=/app/data/veridoc.db

# Hugging Face Spaces expects the app on port 7860 by default.
# Most other free hosts read $PORT and set it for you at runtime.
ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
