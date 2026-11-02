from app import workflow
from app.agents.triage_agent import TriageResult


def test_ai_triage(monkeypatch):
    monkeypatch.setenv("AI_TRIAGE_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_ai(description):
        return TriageResult(
            category="authentication",
            priority="normal",
            reasoning="Login issue detected",
        )

    monkeypatch.setattr(
        workflow, "classify_with_ai", fake_ai
    )

    result = workflow.classify({
        "description": "Users cannot log in to portal"
    })

    assert result["category"] == "authentication"
    assert result["priority"] == "normal"


def test_high_priority_not_downgraded(monkeypatch):
    monkeypatch.setenv("AI_TRIAGE_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    monkeypatch.setattr(
        workflow,
        "classify_with_ai",
        lambda description: TriageResult(
            category="integration",
            priority="normal",
            reasoning="Integration issue",
        ),
    )

    result = workflow.classify({
        "description": "Production API returns 500"
    })

    assert result["priority"] == "high"


def test_fallback_when_ai_fails(monkeypatch):
    monkeypatch.setenv("AI_TRIAGE_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def failing_ai(description):
        raise RuntimeError("Simulated API failure")

    monkeypatch.setattr(
        workflow, "classify_with_ai", failing_ai
    )

    result = workflow.classify({
        "description": "Production API returns 500"
    })

    assert result["category"] == "integration"
    assert result["priority"] == "high"
