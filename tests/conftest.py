
import pytest



@pytest.fixture(autouse=True)
def disable_external_ai(monkeypatch):
    monkeypatch.setenv("AI_TRIAGE_ENABLED", "false")
    monkeypatch.setenv("RAG_ENABLED", "false")
    monkeypatch.setenv("AI_DIAGNOSIS_ENABLED", "false")

@pytest.fixture(autouse=True)
def disable_live_ai_for_tests(monkeypatch):
    monkeypatch.setenv("AI_TRIAGE_ENABLED", "false")
    monkeypatch.setenv("RAG_ENABLED", "false")

    