"""Genuine integration test: two distinct owner IDs, real HTTP calls through
FastAPI's TestClient (which exercises the actual routes, DB, and vector
store), unique secret strings per user, and explicit IDOR attempts."""
import os
import sys
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + tempfile.mktemp(suffix=".db")
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp()
os.environ["INDEX_DIR"] = tempfile.mkdtemp()
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_BACKEND"] = "lightweight"

sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from app.main import app
from app.services.pipeline import run_pipeline

client = TestClient(app)
client.__enter__()  # triggers the FastAPI startup event (init_db / table creation)

USER_A = "user-a-11111111-1111-1111-1111-111111111111"
USER_B = "user-b-22222222-2222-2222-2222-222222222222"

SECRET_A = "PINEAPPLE-ROCKET-42-ALPHA"
SECRET_B = "ZEBRA-COMET-99-BRAVO"

failures = []

def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        failures.append(label)


def upload_text(owner, secret_text):
    content = f"Confidential Field: {secret_text}\n".encode()
    files = {"file": (f"{owner}_secret.txt", content, "text/plain")}
    resp = client.post("/documents/upload", files=files, headers={"X-User-Id": owner})
    assert resp.status_code == 200, resp.text
    doc_id = resp.json()["id"]
    run_pipeline(doc_id, owner)  # run synchronously (no background worker in this test)
    return doc_id


print("=== Setup: two users upload distinct secret documents ===")
doc_a = upload_text(USER_A, SECRET_A)
doc_b = upload_text(USER_B, SECRET_B)
print(f"User A uploaded document {doc_a} containing secret: {SECRET_A}")
print(f"User B uploaded document {doc_b} containing secret: {SECRET_B}")
print()

print("=== TEST 1: GET /documents - each user sees only their own files ===")
list_a = client.get("/documents", headers={"X-User-Id": USER_A}).json()
list_b = client.get("/documents", headers={"X-User-Id": USER_B}).json()
check("User A's document list contains only their own doc", [d["id"] for d in list_a] == [doc_a])
check("User B's document list contains only their own doc", [d["id"] for d in list_b] == [doc_b])
check("User A's list does NOT contain User B's doc id", doc_b not in [d["id"] for d in list_a])
check("User B's list does NOT contain User A's doc id", doc_a not in [d["id"] for d in list_b])
print()

print("=== TEST 2: IDOR - User B tries to directly GET User A's document by ID ===")
r = client.get(f"/documents/{doc_a}", headers={"X-User-Id": USER_B})
check("User B accessing User A's document by ID returns 404 (not the data)", r.status_code == 404)
r2 = client.get(f"/documents/{doc_b}", headers={"X-User-Id": USER_A})
check("User A accessing User B's document by ID returns 404 (not the data)", r2.status_code == 404)
print()

print("=== TEST 3: IDOR on sub-resources (content, extractions, audit) ===")
for path in ["content", "extractions", "validation", "audit"]:
    r = client.get(f"/documents/{doc_a}/{path}", headers={"X-User-Id": USER_B})
    check(f"User B fetching User A's /{path} returns 404", r.status_code == 404)
print()

print("=== TEST 4: No X-User-Id header at all is rejected ===")
r = client.get("/documents")
check("Request with no X-User-Id header is rejected (400)", r.status_code == 400)
print()

print("=== TEST 5: Q&A only answers from the CURRENT user's own data ===")
# User A asks about their own secret - should find it
rA = client.post("/query", json={"question": "What is the confidential field value?"}, headers={"X-User-Id": USER_A})
answer_a = rA.json()
check("User A's question is grounded (found in their own doc)", answer_a["grounded"] is True)
check(f"User A's answer contains their own secret ({SECRET_A})", SECRET_A in (answer_a["answer"] or ""))
check(f"User A's answer does NOT leak User B's secret ({SECRET_B})", SECRET_B not in (answer_a["answer"] or ""))

# User B asks the same generic question - should only ever see their own secret, never A's
rB = client.post("/query", json={"question": "What is the confidential field value?"}, headers={"X-User-Id": USER_B})
answer_b = rB.json()
check("User B's question is grounded (found in their own doc)", answer_b["grounded"] is True)
check(f"User B's answer contains their own secret ({SECRET_B})", SECRET_B in (answer_b["answer"] or ""))
check(f"User B's answer does NOT leak User A's secret ({SECRET_A})", SECRET_A not in (answer_b["answer"] or ""))
print()

print("=== TEST 6: User B explicitly tries to query User A's document_id ===")
rEvil = client.post("/query", json={"question": "What is the confidential field value?", "document_ids": [doc_a]}, headers={"X-User-Id": USER_B})
evil_answer = rEvil.json()
check("Explicitly requesting another user's document_id yields nothing grounded", evil_answer["grounded"] is False)
check("No secret leaked when explicitly targeting another user's doc id", SECRET_A not in (evil_answer["answer"] or ""))
print()

print("=== TEST 7: Single-document query endpoint blocks cross-user access ===")
rSingle = client.post(f"/documents/{doc_a}/query", json={"question": "What is the confidential field value?"}, headers={"X-User-Id": USER_B})
check("User B hitting /documents/{docA}/query returns 404", rSingle.status_code == 404)
print()

print("=== TEST 8: Analytics dashboard is scoped per-user ===")
analytics_a = client.get("/analytics", headers={"X-User-Id": USER_A}).json()
analytics_b = client.get("/analytics", headers={"X-User-Id": USER_B}).json()
check("User A's analytics shows exactly 1 document (their own)", analytics_a["documents_processed"] == 1)
check("User B's analytics shows exactly 1 document (their own)", analytics_b["documents_processed"] == 1)
a_filenames = [d["filename"] for d in analytics_a["recent_documents"]]
check("User A's analytics does not list User B's filename", f"{USER_B}_secret.txt" not in a_filenames)
print()

print("=== TEST 9: Review queue is scoped per-user (IDOR on review items) ===")
review_a = client.get("/review-queue?status=all", headers={"X-User-Id": USER_A}).json()
review_b = client.get("/review-queue?status=all", headers={"X-User-Id": USER_B}).json()
a_doc_ids_in_review = {i["document_id"] for i in review_a}
b_doc_ids_in_review = {i["document_id"] for i in review_b}
check("User A's review queue contains no items from User B's document", doc_b not in a_doc_ids_in_review)
check("User B's review queue contains no items from User A's document", doc_a not in b_doc_ids_in_review)
print()

print("=== TEST 10: Delete is owner-checked (User B cannot delete User A's doc) ===")
rDel = client.delete(f"/documents/{doc_a}", headers={"X-User-Id": USER_B})
check("User B deleting User A's document returns 404 (not deleted)", rDel.status_code == 404)
still_there = client.get(f"/documents/{doc_a}", headers={"X-User-Id": USER_A})
check("User A's document still exists after User B's delete attempt", still_there.status_code == 200)
print()

print("=" * 60)
if failures:
    print(f"RESULT: {len(failures)} TEST(S) FAILED:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("RESULT: ALL TESTS PASSED - no cross-user data access detected.")
