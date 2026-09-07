# VeriDoc

**Turn documents into verified knowledge.**

VeriDoc is a document intelligence platform built around one idea: an AI answer is only
useful if you can trust where it came from. Instead of "upload a PDF and chat with it,"
VeriDoc extracts information, independently validates it, routes anything uncertain to a
human reviewer, and only then makes it searchable — so every answer VeriDoc gives comes
with a source, evidence, and a confidence score.

```
Upload → Understand → Extract → Validate → Confidence → Human Review → Verified Knowledge
        → Chunk → Embed → Vector Search → RAG → Grounded Answer + Source + Evidence
```

---

## Features

- **Multi-format ingestion** — PDF (with per-page OCR fallback for scanned pages), DOCX,
  TXT, CSV, JSON, and images (PNG/JPG via OCR). Each format keeps its own kind of
  provenance: page, section/paragraph, sheet/row/column, or line.
- **Structured extraction** — an LLM extracts fields with confidence and evidence,
  validated against a strict schema so malformed output never crashes the app.
- **Independent validation engine** — deterministic Python checks (arithmetic
  consistency, missing fields, implausible dates/values, conflicting extractions) that
  never simply trust the model's self-reported confidence.
- **Human review queue** — low-confidence or validation-failed fields wait for a human
  decision: Accept, Correct, or Reject. Corrections never overwrite the original AI value
  — both are preserved with a full audit trail.
- **Verified knowledge layer** — RAG and exports only ever read from `VerifiedValue`
  rows, not raw, unchecked extractions.
- **Real RAG** — Sentence-Transformers embeddings + FAISS vector search, with grounded,
  cited answers. If the answer isn't in your documents, VeriDoc says so.
- **Multi-document RAG & comparison** — ask questions across several documents at once,
  or diff two verified documents field by field.
- **Duplicate detection, anomaly detection, PII detection, document quality scoring,**
  audit trail, CSV/JSON export, and a dashboard with key metrics.
- **Provider-agnostic LLM layer** — OpenAI-compatible APIs, Ollama for local dev, or a
  fully offline mock provider so the app works end-to-end with **no API key**.

---

## Architecture

```
veridoc/
├── backend/                 FastAPI application
│   ├── app/
│   │   ├── api/routes/      REST endpoints (documents, review, query, compare, analytics)
│   │   ├── models/          SQLAlchemy models (normalized document model)
│   │   ├── schemas/         Pydantic schemas (incl. strict LLM output validation)
│   │   ├── services/
│   │   │   ├── llm/         Provider abstraction: OpenAI / Ollama / mock
│   │   │   ├── processors/  Format-aware document processors
│   │   │   ├── extraction_service.py
│   │   │   ├── validation_service.py     ← independent validation engine
│   │   │   ├── confidence_service.py
│   │   │   ├── rag_service.py            ← chunking + FAISS + grounded answers
│   │   │   ├── vector_store.py           ← persistent FAISS wrapper
│   │   │   ├── comparison_service.py
│   │   │   ├── duplicate_service.py
│   │   │   ├── anomaly_service.py
│   │   │   ├── pii_service.py
│   │   │   ├── audit_service.py
│   │   │   └── pipeline.py               ← orchestrates the full workflow
│   │   └── main.py
│   └── requirements.txt
├── frontend/                 React + TypeScript + Tailwind + Framer Motion
│   └── src/
│       ├── pages/            Landing, Dashboard, Documents, DocumentDetail,
│       │                     ReviewQueue, AskVeriDoc, Compare, Analytics, About,
│       │                     Contact, FAQ, NotFound, Settings
│       └── components/
├── docker-compose.yml
├── render.yaml
└── README.md
```

---

## Local installation

### Prerequisites
- Python 3.11+
- Node.js 20+
- Tesseract OCR installed locally (`brew install tesseract` / `apt install tesseract-ocr`)
  — only needed if you'll upload scanned PDFs or images.

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- Leave `LLM_PROVIDER=mock` to try VeriDoc fully offline with no API key, **or**
- Set `LLM_PROVIDER=openai` and `LLM_API_KEY=sk-...` to use a real model, **or**
- Set `LLM_PROVIDER=ollama` with Ollama running locally.

```bash
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000` (docs at `/docs`).

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env   # defaults to the Vite proxy, no edits needed for local dev
npm run dev
```

Open `http://localhost:5173`.

---

## Environment variables (backend)

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLite / PostgreSQL / MySQL connection string | `sqlite:///./storage/veridoc.db` |
| `UPLOAD_DIR` / `INDEX_DIR` | Local storage paths | `./storage/uploads`, `./storage/index` |
| `MAX_UPLOAD_SIZE_MB` | Upload size limit | `25` |
| `LLM_PROVIDER` | `openai` \| `ollama` \| `mock` | `mock` |
| `LLM_API_KEY` / `LLM_API_BASE` / `LLM_MODEL` | OpenAI-compatible provider config | — |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | Local Ollama config | — |
| `EMBEDDING_MODEL` | Sentence-Transformers model name | `all-MiniLM-L6-v2` |
| `CONFIDENCE_AUTO_ACCEPT_THRESHOLD` | Below this, a field goes to review | `0.70` |
| `CORS_ORIGINS` | Comma-separated allowed origins | — |
| `SECRET_KEY` | App secret | — |

### Switching database engines
`DATABASE_URL` is the only thing that changes:
```
sqlite:///./storage/veridoc.db
postgresql://user:password@host:5432/veridoc
mysql+pymysql://user:password@host:3306/veridoc
```
(PostgreSQL/MySQL drivers are already in `requirements.txt`.)

---

## Docker (local, both services)

```bash
cp backend/.env.example backend/.env   # then edit as needed
docker compose up --build
```
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

> Note: `VITE_API_URL` is baked in at frontend build time. If you change it, rebuild the
> frontend image (`docker compose build frontend`).

---

## Deploying to Render

1. Push this repo to GitHub.
2. In Render, choose **New → Blueprint** and point it at the repo — `render.yaml` defines
   both services plus a managed PostgreSQL database.
3. Set the `LLM_API_KEY` secret in the Render dashboard (marked `sync: false` in the
   blueprint so it's never committed).
4. Update `CORS_ORIGINS` on the backend and `VITE_API_URL` on the frontend once you know
   your final Render URLs, then redeploy.

If you'd rather deploy manually instead of via Blueprint: create a Docker-based Web
Service from `backend/Dockerfile` with a persistent disk mounted at `/app/storage`, and a
Static Site from `frontend/` with build command `npm install && npm run build` and
publish directory `dist`.

---

## Example workflow

1. Upload `financial_report.pdf`.
2. VeriDoc detects it's a PDF, extracts text/tables per page, and OCRs any scanned pages.
3. An LLM extracts fields (Revenue, Expenses, Profit, ...) with confidence and evidence.
4. The validation engine checks arithmetic consistency, dates, and plausibility —
   independently of the model's confidence.
5. Anything below the confidence threshold, or that fails validation, goes to the
   **Review Queue** for Accept / Correct / Reject.
6. Verified values are chunked, embedded, and indexed into FAISS.
7. Ask: *"What was the company's revenue in 2025?"* → VeriDoc retrieves the relevant
   chunk and returns an answer with **source** (e.g. "Page 17 — Financial Summary"),
   **evidence** (the exact retrieved text), and a **confidence score**.
8. Compare this year's report against last year's to see exactly what changed.

---

## Testing

There's no bundled test suite (kept out to avoid bloat), but the recommended manual
smoke test covers:

- Upload one file of each supported type (PDF, DOCX, TXT, CSV, JSON, PNG/JPG)
- A scanned/image-only PDF to confirm the OCR fallback fires
- A document with intentionally inconsistent numbers (subtotal + tax ≠ total) to confirm
  it lands in the Review Queue
- Accept, Correct, and Reject flows in the Review Queue, then check Audit History
- Ask a question that *is* answerable from a document, and one that isn't
- Compare two documents with a changed numeric field
- Delete a document and confirm no orphaned review items/chunks remain

## Troubleshooting

- **"LLM_PROVIDER is 'openai' but LLM_API_KEY is empty"** — set `LLM_API_KEY` in
  `backend/.env`, or switch to `LLM_PROVIDER=mock` for offline demo mode.
- **OCR produces empty text** — confirm Tesseract is installed and on your `PATH`
  (`tesseract --version`), or set `TESSERACT_CMD` to its full path.
- **CORS errors in the browser console** — make sure `CORS_ORIGINS` in the backend `.env`
  includes your frontend's exact origin.
- **Uploads fail immediately** — check `MAX_UPLOAD_SIZE_MB` and that the file extension
  is one of: pdf, docx, txt, csv, json, png, jpg, jpeg.

---

## License

This project is provided as-is for demonstration and development purposes.
