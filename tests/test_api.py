from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    assert client.get("/health").json() == {"status": "ok"}

def test_normal_ticket():
    r = client.post("/tickets", json={"description": "Candidate sync is delayed"})
    assert r.status_code == 201
    body = r.json()
    assert body["category"] == "integration"
    assert body["status"] == "recommendation_ready"
    assert body["requires_approval"] is False

def test_high_priority_approval():
    r = client.post("/tickets", json={"description": "Production API returns 500 during candidate sync"})
    assert r.status_code == 201
    body = r.json()
    assert body["priority"] == "high"
    assert body["requires_approval"] is True
    ticket_id = body["ticket_id"]
    result = client.post(f"/tickets/{ticket_id}/approval", json={"decision": "approved"})
    assert result.status_code == 200
    assert result.json()["status"] == "approved_for_review"
    duplicate = client.post(f"/tickets/{ticket_id}/approval", json={"decision": "approved"})
    assert duplicate.status_code == 409

def test_invalid_and_unknown():
    assert client.post("/tickets", json={"description": "short"}).status_code == 422
    assert client.get("/tickets/unknown").status_code == 404
