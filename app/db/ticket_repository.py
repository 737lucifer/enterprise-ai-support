
import json
import os
from uuid import UUID

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()


def get_connection():
    # Uses the same PostgreSQL server as pgvector,
    # but uses the synchronous psycopg driver.
    return psycopg.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "5433")),
        dbname=os.getenv("DB_NAME", "ai_support"),
        user=os.getenv("DB_USER", "ai_support"),
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
        row_factory=dict_row,
    )


def save_ticket(ticket: dict, description: str):
    query = """
        INSERT INTO support_tickets (
            ticket_id, description, status,
            category, priority, evidence,
            recommendation, approval, requires_approval
        )
        VALUES (
            %(ticket_id)s, %(description)s, %(status)s,
            %(category)s, %(priority)s, %(evidence)s,
            %(recommendation)s, %(approval)s, %(requires_approval)s
        )
        ON CONFLICT (ticket_id)
        DO UPDATE SET
            status = EXCLUDED.status,
            category = EXCLUDED.category,
            priority = EXCLUDED.priority,
            evidence = EXCLUDED.evidence,
            recommendation = EXCLUDED.recommendation,
            approval = EXCLUDED.approval,
            requires_approval = EXCLUDED.requires_approval,
            updated_at = NOW()
    """

    params = {
        "ticket_id": UUID(ticket["ticket_id"]),
        "description": description,
        "status": ticket["status"],
        "category": ticket.get("category"),
        "priority": ticket.get("priority"),
        "evidence": json.dumps(ticket.get("evidence", [])),
        "recommendation": ticket.get("recommendation"),
        "approval": ticket.get("approval"),
        "requires_approval": ticket.get(
            "requires_approval", False
        ),
    }

    # Cast JSON text to JSONB in the SQL statement.
    query = query.replace(
        "%(evidence)s,",
        "%(evidence)s::jsonb,",
        1,
    )

    with get_connection() as conn:
        conn.execute(query, params)


def find_ticket(ticket_id: str):
    try:
        parsed_id = UUID(ticket_id)
    except (ValueError, AttributeError):
        return None

    with get_connection() as conn:
        return conn.execute(
            """
            SELECT ticket_id, description, status,
                   category, priority, evidence,
                   recommendation, approval, requires_approval
            FROM support_tickets
            WHERE ticket_id = %s
            """,
            (parsed_id,),
        ).fetchone()
