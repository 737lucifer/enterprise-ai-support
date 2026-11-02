
from app import workflow
from app.agents.diagnosis_agent import DiagnosisResult


def test_ai_diagnosis(monkeypatch):
    monkeypatch.setenv("AI_DIAGNOSIS_ENABLED", "true")

    monkeypatch.setattr(
        workflow,
        "diagnose_incident",
        lambda description, evidence: DiagnosisResult(
            probable_cause="Invalid candidate payload",
            confidence="medium",
            recommended_steps=[
                "Inspect API response",
                "Validate required fields",
            ],
            source_ids=["INC001"],
        ),
    )

    state = {
        "description": "Candidate sync returns HTTP 500",
        "evidence": [
            "Source: INC001\nContent: Invalid candidate payload"
        ],
        "category": "integration",
        "priority": "high",
    }

    result = workflow.recommend(state)

    assert "Invalid candidate payload" in result["recommendation"]
    assert "INC001" in result["recommendation"]
