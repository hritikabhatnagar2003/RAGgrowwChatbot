import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    os.environ["TEST_MODE"] = "1"
    from phase4_backend_api.main import app  # noqa: E402
    with TestClient(app) as c:
        yield c


def test_pii_pan_blocked(client: TestClient):
    r = client.post("/api/chat", json={"query": "My PAN is ABCDE1234F, check my investment"})
    assert r.status_code == 200
    data = r.json()
    assert data["refused"] is True
    assert data["query_type"] == "PII_DETECTED"


def test_pii_account_number_blocked(client: TestClient):
    r = client.post("/api/chat", json={"query": "My account 123456789012 please verify"})
    assert r.status_code == 200
    data = r.json()
    assert data["refused"] is True
    assert data["query_type"] == "PII_DETECTED"


def test_rate_limit_triggers(client: TestClient):
    # Temporarily set to small limit by re-importing app with env.
    os.environ["RATE_LIMIT_PER_MINUTE"] = "3"
    os.environ["TEST_MODE"] = "1"
    from importlib import reload
    import phase4_backend_api.main as main_mod

    reload(main_mod)
    with TestClient(main_mod.app) as limited_client:
        for _ in range(3):
            ok = limited_client.post("/api/chat", json={"query": "What is expense ratio?"})
            assert ok.status_code == 200

        blocked = limited_client.post("/api/chat", json={"query": "What is expense ratio?"})
        assert blocked.status_code == 429


def test_output_guardrail_blocks_unsafe(client: TestClient, monkeypatch):
    from phase4_backend_api import main as main_mod

    class UnsafeGen:
        def generate(self, system_prompt: str, user_prompt: str, context_metadata: list):
            return {
                "answer": "You should invest in this fund because it is better than others.",
                "status": "success",
                "retries": 0,
            }

    monkeypatch.setattr(main_mod, "generator", UnsafeGen(), raising=False)

    r = client.post("/api/chat", json={"query": "Tell me something factual"})
    assert r.status_code == 200
    data = r.json()
    assert data["refused"] is True
    assert data["query_type"] == "SAFETY_BLOCK"

