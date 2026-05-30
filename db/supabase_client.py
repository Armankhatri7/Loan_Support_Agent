"""
Supabase client singleton and database operations for the Loan Support Agent.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_client: Client | None = None


def get_client() -> Client:
    """Return a singleton Supabase client."""
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env file."
            )
        _client = create_client(url, key)
    return _client


# ──────────────────────────────────────────────
# Loan operations
# ──────────────────────────────────────────────

def fetch_loan_by_id(loan_id: str) -> dict | None:
    """Fetch a single loan record by its loan_id. Returns None if not found."""
    client = get_client()
    result = client.table("loans").select("*").eq("loan_id", loan_id).execute()
    if result.data:
        return result.data[0]
    return None


# ──────────────────────────────────────────────
# Conversation operations
# ──────────────────────────────────────────────

def get_active_conversation(loan_id: str) -> dict | None:
    """Return the most recent active conversation for this loan, or None."""
    client = get_client()
    result = (
        client.table("conversations")
        .select("*")
        .eq("loan_id", loan_id)
        .eq("status", "active")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]
    return None


def create_conversation(loan_id: str) -> dict:
    """Create a new active conversation and return the row."""
    client = get_client()
    result = (
        client.table("conversations")
        .insert({"loan_id": loan_id, "current_step": "greet", "status": "active"})
        .execute()
    )
    return result.data[0]


def update_conversation(conversation_id: int, updates: dict) -> None:
    """Update a conversation row with the given fields."""
    client = get_client()
    client.table("conversations").update(updates).eq("id", conversation_id).execute()


def update_loan_fields(loan_id: str, updates: dict) -> None:
    """Update a loan row with the given fields."""
    client = get_client()
    client.table("loans").update(updates).eq("loan_id", loan_id).execute()


def mark_conversation_status(conversation_id: int, status: str) -> None:
    """Set conversation status (active / completed / escalated / abandoned)."""
    update_conversation(conversation_id, {"status": status})


# ──────────────────────────────────────────────
# Escalation operations
# ──────────────────────────────────────────────

def create_escalation(
    loan_id: str,
    conversation_id: int,
    issue_type: str,
    description: str,
    user_claim: str = "",
    system_value: str = "",
) -> dict:
    """Insert an escalation record and return the row."""
    client = get_client()
    result = (
        client.table("escalations")
        .insert(
            {
                "loan_id": loan_id,
                "conversation_id": conversation_id,
                "issue_type": issue_type,
                "description": description,
                "user_claim": user_claim,
                "system_value": system_value,
                "status": "open",
            }
        )
        .execute()
    )
    # Also mark the conversation as escalated
    mark_conversation_status(conversation_id, "escalated")
    return result.data[0]


def create_feedback(
    loan_id: str,
    conversation_id: int,
    feedback_type: str,
    description: str,
) -> dict:
    """Insert a feedback record into escalations WITHOUT changing conversation status.

    Used for health check issues and additional queries — logs the concern
    but allows the conversation flow to continue.
    """
    client = get_client()
    result = (
        client.table("escalations")
        .insert(
            {
                "loan_id": loan_id,
                "conversation_id": conversation_id,
                "issue_type": "other",
                "description": f"[{feedback_type}] {description}",
                "user_claim": "",
                "system_value": "",
                "status": "open",
            }
        )
        .execute()
    )
    return result.data[0]
