"""
Test suite for the RapidRelief demo application.

NOTE FOR REVIEWERS: this is the real pytest suite for demo_target. It is
intentionally realistic-but-incomplete: every fixture assumes a
first_name + last_name applicant, and there is NO test covering a
missing surname, missing address, or an international phone number —
even though POLICY.md requires all three to work. This gap is exactly
what test_agent.py detects.
"""
from fastapi.testclient import TestClient

from demo_target.backend import database
from demo_target.backend.main import app


def setup_function():
    database.reset_db()


client = TestClient(app)


def make_payload(**overrides):
    # ASSUMPTION: every test fixture has both first_name and last_name.
    payload = {
        "first_name": "Maria",
        "last_name": "Gonzalez",
        "address": "123 Main St, Springfield",
        "phone": "(555) 123-4567",
    }
    payload.update(overrides)
    return payload


def test_create_application_happy_path():
    res = client.post("/applications", json=make_payload())
    assert res.status_code == 201
    body = res.json()
    assert body["first_name"] == "Maria"
    assert body["last_name"] == "Gonzalez"
    assert body["status"] == "submitted"


def test_get_application_not_found():
    res = client.get("/applications/9999")
    assert res.status_code == 404


def test_missing_first_name_rejected():
    payload = make_payload()
    del payload["first_name"]
    res = client.post("/applications", json=payload)
    assert res.status_code == 422


def test_list_applications_returns_created_rows():
    client.post("/applications", json=make_payload())
    res = client.get("/applications")
    assert res.status_code == 200
    assert len(res.json()) >= 1


# --- Coverage gaps intentionally left for Assumption Zero to discover ---

def test_applicant_without_surname_is_accepted():
    """Regression test for POLICY.md REQ-1 (single legal name / no surname)."""
    payload = make_payload()
    payload["last_name"] = None
    res = client.post("/applications", json=payload)
    assert res.status_code == 201


def test_applicant_without_address_is_accepted():
    """Regression test for POLICY.md REQ-2 (no permanent address)."""
    payload = make_payload()
    payload["address"] = None
    res = client.post("/applications", json=payload)
    assert res.status_code == 201


def test_international_phone_number_is_accepted():
    """Regression test for POLICY.md REQ-3 (international phone support)."""
    payload = make_payload()
    payload["phone"] = "+923001234567"
    res = client.post("/applications", json=payload)
    assert res.status_code == 201


def test_retried_submission_with_same_idempotency_key_is_not_duplicated():
    """Regression test for POLICY.md REQ-4 (no duplicate on retry)."""
    payload = make_payload()
    headers = {"Idempotency-Key": "test-key-123"}
    first = client.post("/applications", json=payload, headers=headers)
    second = client.post("/applications", json=payload, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]


def test_applicant_with_non_latin_name_is_accepted():
    """Regression test for POLICY.md REQ-5 (non-Latin script names)."""
    payload = make_payload()
    payload["first_name"] = "نور"  # "Noor" written in Urdu/Arabic script
    res = client.post("/applications", json=payload)
    assert res.status_code == 201
