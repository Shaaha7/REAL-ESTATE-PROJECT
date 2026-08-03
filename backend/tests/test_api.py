import sys; sys.path.insert(0,'.')
import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import app as app_module

# TestClient(app) as a context manager triggers the real lifespan - this
# actually boots the XGBoost model, RAG pipeline (torch/sentence-transformers)
# and orchestrator, same as a real run. Module-scoped so it only pays that
# startup cost once for the whole file.
@pytest.fixture(scope="module")
def client():
    with TestClient(app_module.app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert body["agents"]["lead_scoring"] is True
    assert body["rag_chunks"] > 0


def test_root(client):
    r = client.get("/api")
    assert r.status_code == 200
    assert r.json()["service"] == "PropAI Real Estate Platform"


def test_properties_list(client):
    r = client.get("/api/properties")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 10
    assert len(body["properties"]) == 10


def test_property_not_found(client):
    r = client.get("/api/properties/P999")
    assert r.status_code == 404


def test_properties_search_respects_budget(client):
    r = client.post("/api/properties/search", json={"budget_max": 1_000_000})
    assert r.status_code == 200
    for p in r.json()["properties"]:
        assert p["price"] <= 1_000_000


def test_lead_score_validation_rejects_missing_name(client):
    r = client.post("/api/leads/score", json={"budget_aed": 2_000_000})
    assert r.status_code == 422  # pydantic validation, client_name is required


def test_lead_score_end_to_end(client):
    r = client.post("/api/leads/score", json={
        "client_name": "Test Client", "budget_aed": 2_500_000, "property_type": "villa",
        "location_preference": "Dubai Hills", "bedrooms": 3, "timeline_months": 1,
        "num_interactions": 8, "avg_response_hours": 0.5, "message_quality_score": 0.9,
    })
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["score"] <= 100
    assert body["tier"] in ("HOT", "WARM", "COLD")
    assert isinstance(body["shap_top_features"], list) and len(body["shap_top_features"]) > 0


def test_mortgage_calculator_is_deterministic_math(client):
    # pure math, no LLM involved - safe to assert exact behaviour
    r = client.post("/api/tools/mortgage", json={
        "property_price_aed": 2_000_000, "monthly_income_aed": 50_000,
        "down_payment_pct": 25.0, "interest_rate_pct": 4.0, "tenure_years": 25,
        "is_resident": True,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["down_payment_aed"] == 500_000
    assert body["loan_amount_aed"] == 1_500_000
    assert body["monthly_payment_aed"] > 0
    assert "dld_transfer_fee_aed" in body["closing_costs"]


def test_rag_rebuild_requires_admin_key(client):
    r = client.post("/api/rag/rebuild")
    assert r.status_code == 401


def test_rag_index_requires_admin_key(client):
    r = client.post("/api/rag/index", json={"documents": []})
    assert r.status_code == 401


def test_rag_index_rejects_oversized_batch_with_valid_key(client):
    key = app_module._ADMIN_API_KEY
    docs = [{"content": f"doc {i}", "source": f"{i}.txt"} for i in range(201)]
    r = client.post("/api/rag/index", json={"documents": docs}, headers={"X-API-Key": key})
    assert r.status_code == 413


def test_rate_limit_kicks_in():
    # Deliberately NOT going through the real endpoint: each real call to a
    # rate-limited route can take 3-4s under LLM retry backoff (e.g. when a
    # provider's daily quota is exhausted, which happened while writing this
    # test), so `limit` real calls can span more than the 60s window and
    # never actually trip it. That's a timing artifact of the LLM call, not
    # the limiter - so test the limiter's own logic directly and fast.
    fake_host = "test-rate-limit-client"
    app_module._rate_limit_hits.pop(fake_host, None)
    fake_request = SimpleNamespace(client=SimpleNamespace(host=fake_host))
    limit = app_module.settings.rate_limit_per_minute
    try:
        for _ in range(limit):
            asyncio.run(app_module.rate_limit_dep(fake_request))  # should all pass
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(app_module.rate_limit_dep(fake_request))
        assert exc_info.value.status_code == 429
    finally:
        app_module._rate_limit_hits.pop(fake_host, None)
