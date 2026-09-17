# VeriDoc

Turns messy, multi-format documents into verified, searchable knowledge — and lets you ask questions about them with source-backed, evidence-cited answers.

Upload a PDF, Word doc, spreadsheet, CSV, JSON file, text file, or image. VeriDoc figures out what it's looking at, extracts structure with an LLM (not a rigid template), independently validates what it found, routes anything uncertain to a human review queue, and only then makes the document searchable through grounded retrieval-augmented generation.

## Architecture

```
Upload
  -> File type detection
  -> Format-specific processor (PDF / DOCX / TXT / CSV / XLSX / JSON / Image)
  -> Normalized content units (each with flexible provenance: page, section,
     paragraph, sheet, row, column, table, image region, or line)
  -> LLM structured extraction (Ollama, Pydantic-validated, no-hallucination prompt)
  -> Independent validation (arithmetic cross-checks, date/number sanity checks)
  -> Confidence scoring (validation failure always forces review, regardless
     of how confident the LLM was)
  -> Human review (Accept / Reject / Correct, full audit trail, original AI
     value preserved forever)
  -> Verified knowledge layer
  -> Chunking -> Sentence-Transformers embeddings -> FAISS index
  -> Question -> retrieval -> grounded LLM prompt -> answer + sources + evidence + confidence
```

## Running it

You need three things running: **Ollama** (the LLM), the **backend**, and the **frontend**.

### 1. Install and start Ollama

Download from **https://ollama.com**, then:
```bash
ollama serve
ollama pull llama3
```
Leave `ollama serve` running in its own terminal.

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows; use `source venv/bin/activate` on Mac/Linux
pip install -r requirements.txt
cp ../.env.example .env      # edit if you want a different model/URL
uvicorn app.main:app --reload --port 8000
```
The first time it starts, it'll try to download the embedding model (`all-MiniLM-L6-v2`, ~90MB) from Hugging Face — this needs an internet connection once, then it's cached locally.

**Optional, for scanned documents/images:** install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki (Windows) or `brew install tesseract` (Mac). Without it, everything else still works — scanned pages just won't have text extracted.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**.

## Configuration

Everything is controlled by environment variables — see `.env.example` at the project root. The important ones:

| Variable | Default | What it does |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | Where your Ollama server is running |
| `OLLAMA_MODEL` | `llama3` | Which model to use for extraction and Q&A |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Any Sentence-Transformers model name |
| `VERIDOC_REVIEW_THRESHOLD` | `0.70` | Confidence below this (or any failed validation check) goes to human review |
| `VERIDOC_MAX_UPLOAD_MB` | `25` | Upload size limit |

Swapping in a different local model is just changing `OLLAMA_MODEL` — no code changes. Swapping to a cloud LLM API instead of Ollama would mean replacing the body of `backend/app/llm/ollama_client.py`; the rest of the pipeline (validation, review, chunking, retrieval) doesn't know or care where the JSON came from.

## What's real vs. what I could verify in a sandbox

Every piece of this — the 7 format processors, the Ollama HTTP client, Pydantic-validated extraction with retry-on-malformed-JSON, the FAISS vector index with real per-document deletion, the validation/confidence/review/audit-trail system — is genuine working code, not a mock or a simplified stand-in.

What I want to be upfront about: this was built in a sandboxed environment with no network access to `ollama.com` or `huggingface.co`, so I could not personally run a real Ollama model or download real embedding weights to test the absolute final mile. I verified the integration code is correct by testing it against a fake local server standing in for each (confirmed: HTTP request/response handling, JSON validation, retry logic, and FAISS operations all work correctly against real requests and real vectors) — but the actual quality of a real Llama3 model's extractions, or a real Sentence-Transformer's semantic search quality, is not something I've personally observed. On your machine, with Ollama actually installed, this is designed to just work — that's the reason it's written against the real HTTP API throughout rather than mocked.

## Supported formats

PDF (including scanned pages, via OCR), DOCX, TXT, CSV, XLSX/XLS, JSON, PNG/JPG/JPEG.

## Project structure

```
veridoc/
├── backend/
│   └── app/
│       ├── processors/       # One adapter per file format -> NormalizedDocument
│       ├── llm/               # Ollama client + Pydantic-validated extraction
│       ├── embeddings/        # Sentence-Transformers loader + FAISS index
│       ├── pipeline/          # normalized.py (Location/ContentUnit), validator, qa, orchestrator
│       ├── routers/           # documents, review, chat, dashboard
│       ├── models.py          # SQLAlchemy models (flexible location JSON, audit trail)
│       └── config.py          # All environment variables in one place
├── frontend/
│   └── src/
│       ├── components/        # ConfidenceRing, ReviewItem, DocumentChat, FileTypeIcon, etc.
│       ├── pages/              # DashboardPage, DocumentsPage, DocumentDetailPage
│       └── lib/api.js
├── .env.example
└── docker-compose.yml
```
