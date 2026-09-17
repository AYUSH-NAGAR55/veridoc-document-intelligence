"""Tests the ACTUAL network integration code (OllamaProvider -> httpx -> HTTP
-> JSON parsing) against a fake server that speaks Ollama's real /api/chat
wire format. This exercises every line of new code, including the exact
request shape sent and response shape parsed - the only thing it can't test
is a genuine model's language understanding, since no real LLM runs here.
"""
import json
import os
import re
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

os.environ["DATABASE_URL"] = "sqlite:///" + tempfile.mktemp(suffix=".db")
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp()
os.environ["INDEX_DIR"] = tempfile.mkdtemp()
os.environ["LLM_PROVIDER"] = "ollama"
os.environ["OLLAMA_BASE_URL"] = "http://127.0.0.1:11555"
os.environ["OLLAMA_MODEL"] = "llama3.1"
os.environ["EMBEDDING_BACKEND"] = "lightweight"

sys.path.insert(0, ".")


# ---------------------------------------------------------------------------
# Fake Ollama server - mimics real Ollama's /api/chat response envelope:
# {"message": {"role": "assistant", "content": "..."}, "done": true, ...}
# ---------------------------------------------------------------------------
class FakeOllamaHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # silence default request logging

    def do_POST(self):
        assert self.path == "/api/chat", f"Expected /api/chat, got {self.path}"
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        assert body["model"] == "llama3.1"
        assert body["stream"] is False
        messages = body["messages"]
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        system_prompt, user_prompt = messages[0]["content"], messages[1]["content"]

        content = self._simulate_model(system_prompt, user_prompt)

        response = {
            "model": "llama3.1",
            "created_at": "2026-01-01T00:00:00Z",
            "message": {"role": "assistant", "content": content},
            "done": True,
        }
        payload = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    @staticmethod
    def _simulate_model(system_prompt: str, user_prompt: str) -> str:
        """Stands in for a real LLM: extracts genuine field lines for the
        extraction task, and answers strictly from the given context for the
        RAG task - simulating what a well-behaved local model should do."""
        if "extraction engine" in system_prompt.lower():
            doc_text = user_prompt.split("DOCUMENT TEXT")[-1].split("TABLES")[0]
            fields = []
            for i, line in enumerate(doc_text.splitlines()):
                m = re.match(r"^\s*([A-Z][A-Za-z ]{2,30}):\s*(.+?)\s*$", line)
                if m:
                    fields.append({
                        "field_name": m.group(1).strip(),
                        "field_value": m.group(2).strip(),
                        "value_type": "string",
                        "confidence": 0.93,
                        "source_location": {"line": i + 1},
                        "evidence_text": line.strip(),
                    })
            return json.dumps({"document_kind": "general_document", "fields": fields})

        if "ONLY the provided CONTEXT" in system_prompt:
            question = user_prompt.split("QUESTION")[-1].split("CONTEXT")[0].strip().lower()
            context = user_prompt.split("CONTEXT")[-1]
            q_words = {w for w in re.findall(r"\w+", question) if len(w) > 3}
            best_line, best_score = None, 0
            for line in context.splitlines():
                words = set(re.findall(r"\w+", line.lower()))
                score = len(q_words & words)
                if score > best_score:
                    best_score, best_line = score, line
            if not best_line:
                return json.dumps({"answer": None, "confidence": 0.0, "found": False})
            clean = re.sub(r"^\[\d+\]\s*\([^)]*\)\s*", "", best_line).strip()
            return json.dumps({"answer": clean, "confidence": 0.96, "found": True})

        return json.dumps({})


server = HTTPServer(("127.0.0.1", 11555), FakeOllamaHandler)
threading.Thread(target=server.serve_forever, daemon=True).start()

# ---------------------------------------------------------------------------
# Run the actual app against the fake server
# ---------------------------------------------------------------------------
from fastapi.testclient import TestClient
from app.main import app
from app.services.pipeline import run_pipeline
from app.services.llm.factory import get_llm_provider

client = TestClient(app)
client.__enter__()

failures = []
def check(label, condition):
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    if not condition:
        failures.append(label)

print("=== Confirm provider selection ===")
provider = get_llm_provider()
check("Active provider is Ollama", provider.name.startswith("ollama:"))
print(f"    provider.name = {provider.name}")
print()

OWNER = "viva-test-user"
doc_text = (
    "Networking Fundamentals\n"
    "Topic: Broadcast\n"
    "Definition: Broadcast is a communication method where a single sender transmits data to all receivers on a network simultaneously.\n"
    "Related Term: Unicast\n"
    "Related Definition: Unicast is one sender to one receiver.\n"
    "Author: Dr Rao\n"
    "Published Date: 2024-01-10\n"
)

print("=== Upload + process a real document through the full pipeline (with fake Ollama) ===")
files = {"file": ("networking.pdf".replace(".pdf", ".txt"), doc_text.encode(), "text/plain")}
resp = client.post("/documents/upload", files=files, headers={"X-User-Id": OWNER})
check("Upload succeeded", resp.status_code == 200)
doc_id = resp.json()["id"]
run_pipeline(doc_id, OWNER)

doc = client.get(f"/documents/{doc_id}", headers={"X-User-Id": OWNER}).json()
check("Document reached 'ready' status", doc["status"] == "ready")
print()

print("=== Ask a question that IS answerable from the document ===")
r = client.post("/query", json={"question": "What is broadcast?"}, headers={"X-User-Id": OWNER})
result = r.json()
print(json.dumps(result, indent=2))
check("Answer is grounded", result["grounded"] is True)
check("Answer text is about broadcast (from the document)", "broadcast" in (result["answer"] or "").lower())
check("Confidence is present and > 0", result["confidence"] > 0)
check("At least one source is returned", len(result["sources"]) >= 1)
check("Source includes filename", "networking" in result["sources"][0]["label"])
check("Evidence text is present and non-empty", len(result["sources"][0]["evidence"]) > 0)
print()

print("=== Ask a question NOT answerable from the document ===")
r2 = client.post("/query", json={"question": "What is the capital of France?"}, headers={"X-User-Id": OWNER})
result2 = r2.json()
print(json.dumps(result2, indent=2))
check('Unanswerable question returns the exact required message', result2["answer"] == "Not found in the uploaded document.")
check("Unanswerable question is not marked grounded", result2["grounded"] is False)
print()

print("=" * 60)
if failures:
    print(f"RESULT: {len(failures)} TEST(S) FAILED:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("RESULT: ALL TESTS PASSED - Ollama wire integration verified end-to-end.")
