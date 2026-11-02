
"""Enterprise AI Support - LangGraph ticket workflow."""

import logging
import os
from typing import Literal, TypedDict

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from app.agents.triage_agent import classify_with_ai
from app.agents.diagnosis_agent import diagnose_incident
from app.agents.source_validator import validate_sources
from app.rag.retriever import search_knowledge

load_dotenv()

logger = logging.getLogger(__name__)


# -------------------------------------------------
# 1. LangGraph shared state
# -------------------------------------------------

class TicketState(TypedDict, total=False):
    ticket_id: str
    description: str
    category: str
    priority: str
    evidence: list[str]
    recommendation: str
    approval: str
    status: str


# -------------------------------------------------
# 2. Default knowledge base
# -------------------------------------------------

KB = {
    "integration": (
        "Verify upstream API status, request IDs, payload "
        "schema, and retry policy before retrying."
    ),
    "authentication": (
        "Check identity-provider health, token expiry, "
        "and role permissions; never expose credentials."
    ),
    "database": (
        "Inspect pool saturation, slow queries, and recent "
        "schema migrations before changing data."
    ),
    "general": (
        "Collect reproduction steps, timestamps, environment, "
        "and relevant sanitized logs."
    ),
}


# -------------------------------------------------
# 3. Rule-based ticket classification
# -------------------------------------------------

def rule_based_classify(state: TicketState) -> TicketState:
    description = state["description"].lower()

    if any(
        term in description
        for term in ("sync", "integration", "api", "webhook")
    ):
        category = "integration"

    elif any(
        term in description
        for term in ("login", "password", "token", "auth")
    ):
        category = "authentication"

    elif any(
        term in description
        for term in ("sql", "database", "query", "deadlock")
    ):
        category = "database"

    else:
        category = "general"

    priority = (
        "high"
        if any(
            term in description
            for term in (
                "outage",
                "down",
                "500",
                "production",
                "data loss",
            )
        )
        else "normal"
    )

    return {
        "category": category,
        "priority": priority,
        "status": "triaged",
    }


# -------------------------------------------------
# 4. AI ticket classification
# -------------------------------------------------

def classify(state: TicketState) -> TicketState:
    baseline = rule_based_classify(state)

    if os.getenv("AI_TRIAGE_ENABLED", "false").lower() != "true":
        return baseline

    try:
        result = classify_with_ai(state["description"])

        # Preserve a recognized business-rule category.
        category = (
            baseline["category"]
            if baseline["category"] != "general"
            else result.category
        )

        # Never downgrade a high-priority incident.
        priority = (
            "high"
            if baseline["priority"] == "high"
            else result.priority
        )

        return {
            "category": category,
            "priority": priority,
            "status": "triaged",
        }

    except Exception:
        logger.exception(
            "AI classification failed for ticket %s",
            state.get("ticket_id"),
        )
        return baseline


# -------------------------------------------------
# 5. RAG document retrieval
# -------------------------------------------------

def retrieve(state: TicketState) -> TicketState:
    fallback = KB.get(
        state["category"],
        KB["general"],
    )

    if os.getenv("RAG_ENABLED", "false").lower() != "true":
        return {"evidence": [fallback]}

    try:
        results = search_knowledge(
            query=state["description"],
            k=3,
        )

        if results:
            return {"evidence": results}

        return {"evidence": [fallback]}

    except Exception:
        logger.exception(
            "Knowledge retrieval failed for ticket %s",
            state.get("ticket_id"),
        )
        return {"evidence": [fallback]}


# -------------------------------------------------
# 6. Default recommendation
# -------------------------------------------------

def rule_based_recommend(state: TicketState) -> TicketState:
    evidence = state.get("evidence", [])

    runbook = (
        evidence[0]
        if evidence
        else KB.get(state.get("category", "general"), KB["general"])
    )

    return {
        "recommendation": (
            f"Investigate {state['category']} issue. "
            f"Suggested runbook: {runbook}"
        ),
        "status": (
            "awaiting_review"
            if state["priority"] == "high"
            else "recommendation_ready"
        ),
    }


# -------------------------------------------------
# 7. AI diagnosis with source validation
# -------------------------------------------------

def recommend(state: TicketState) -> TicketState:
    baseline = rule_based_recommend(state)

    if (
        os.getenv("AI_DIAGNOSIS_ENABLED", "false").lower()
        != "true"
    ):
        return baseline

    evidence = state.get("evidence", [])

    # Only source-tagged records are eligible for
    # an evidence-backed AI diagnosis.
    has_retrieved_sources = any(
        document.startswith("Source:")
        for document in evidence
    )

    if not has_retrieved_sources:
        logger.warning(
            "No source-tagged evidence for ticket %s",
            state.get("ticket_id"),
        )
        return baseline

    try:
        result = diagnose_incident(
            description=state["description"],
            evidence=evidence,
        )

        # Accept only source IDs present in retrieved evidence.
        validated_sources = validate_sources(
            evidence=evidence,
            claimed_sources=result.source_ids,
        )

        # Suppress unsupported AI diagnoses.
        if not validated_sources:
            logger.warning(
                "AI diagnosis has no validated sources "
                "for ticket %s",
                state.get("ticket_id"),
            )

            return {
                "recommendation": (
                    "AI diagnosis requires human verification. "
                    "No retrieved source IDs were validated. "
                    "Review the incident logs and available "
                    "runbooks before taking action."
                ),
                "status": baseline["status"],
            }

        steps = "\n".join(
            f"{i}. {step}"
            for i, step in enumerate(
                result.recommended_steps,
                start=1,
            )
        )

        recommendation = (
            f"Probable cause: {result.probable_cause}\n"
            f"Confidence: {result.confidence}\n"
            f"Recommended steps:\n{steps}\n"
            f"Sources: {', '.join(validated_sources)}"
        )

        return {
            "recommendation": recommendation,
            "status": baseline["status"],
        }

    except Exception:
        logger.exception(
            "AI diagnosis failed for ticket %s",
            state.get("ticket_id"),
        )
        return baseline


# -------------------------------------------------
# 8. Conditional routing
# -------------------------------------------------

def route(state: TicketState) -> Literal["approval", "finish"]:
    if state["priority"] == "high":
        return "approval"

    return "finish"


# -------------------------------------------------
# 9. Human approval node
# -------------------------------------------------

def approval(state: TicketState) -> TicketState:
    decision = interrupt({
        "ticket_id": state["ticket_id"],
        "recommendation": state["recommendation"],
        "question": (
            "Approve this recommendation for analyst review? "
            "No action is automatically executed."
        ),
    })

    if decision not in ("approved", "rejected"):
        raise ValueError(
            "Decision must be approved or rejected"
        )

    return {
        "approval": decision,
        "status": (
            "approved_for_review"
            if decision == "approved"
            else "rejected"
        ),
    }


# -------------------------------------------------
# 10. Normal ticket completion
# -------------------------------------------------

def finish(state: TicketState) -> TicketState:
    return {"status": "recommendation_ready"}


# -------------------------------------------------
# 11. Build LangGraph workflow
# -------------------------------------------------

builder = StateGraph(TicketState)

builder.add_node("classify", classify)
builder.add_node("retrieve", retrieve)
builder.add_node("recommend", recommend)
builder.add_node("approval", approval)
builder.add_node("finish", finish)

builder.add_edge(START, "classify")
builder.add_edge("classify", "retrieve")
builder.add_edge("retrieve", "recommend")

builder.add_conditional_edges("recommend", route)

builder.add_edge("approval", END)
builder.add_edge("finish", END)

# Development-only checkpoint storage.
# Replace with persistent checkpoints before deployment.
graph = builder.compile(
    checkpointer=InMemorySaver()
)
