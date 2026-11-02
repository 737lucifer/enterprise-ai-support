from uuid import uuid4
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langgraph.types import Command
from app.workflow import graph
from app.db.ticket_repository import save_ticket, find_ticket
app = FastAPI(title="Enterprise AI Support Engineer - Phase 1", version="0.1.0")

class TicketIn(BaseModel):
    description: str = Field(min_length=8, max_length=5000)

class ApprovalIn(BaseModel):
    decision: str


def present(ticket_id: str, result: dict) -> dict:
    interrupted = result.get("__interrupt__", ())
    state = graph.get_state({"configurable": {"thread_id": ticket_id}}).values
    return {
        "ticket_id": ticket_id,
        "status": state.get("status"),
        "category": state.get("category"),
        "priority": state.get("priority"),
        "evidence": state.get("evidence", []),
        "recommendation": state.get("recommendation"),
        "approval": state.get("approval"),
        "requires_approval": bool(interrupted),
    }


@app.get("/")
def home():
    return {
        "message": "Enterprise AI Support API",
        "status": "running",
        "docs": "/docs"
    }
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/tickets", status_code=201)
def create_ticket(ticket: TicketIn):
    ticket_id = str(uuid4())
    config = {"configurable": {"thread_id": ticket_id}}
    result = graph.invoke({"ticket_id": ticket_id, "description": ticket.description}, config=config)
    #return present(ticket_id, result)
    response = present(ticket_id, result)
    save_ticket(response, ticket.description)
    return response

@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    state = graph.get_state({"configurable": {"thread_id": ticket_id}})
    '''if not state.values:
        raise HTTPException(status_code=404, detail="Ticket not found")'''
    if not state.values:
        saved = find_ticket(ticket_id)

        if saved is None:
            raise HTTPException(
                status_code=404,
                detail="Ticket not found",
            )

        return {
            **saved,
            "ticket_id": str(saved["ticket_id"]),
        }
    return present(ticket_id, {"__interrupt__": state.tasks if state.next else ()})

@app.post("/tickets/{ticket_id}/approval")
def approve(ticket_id: str, approval: ApprovalIn):
    if approval.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=422, detail="Use approved or rejected")
    config = {"configurable": {"thread_id": ticket_id}}
    state = graph.get_state(config)
    if not state.values:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if "approval" not in state.next:
        raise HTTPException(status_code=409, detail="Ticket is not awaiting approval")
    result = graph.invoke(Command(resume=approval.decision), config=config)
    response = present(ticket_id, result)
    save_ticket(
    response,
    state.values["description"],
    )
    return response
