"""
LangGraph tools for the Loan Support Agent.

Tools are created via a factory so that loan_id and conversation_id
are captured in closures — the LLM never needs to guess them.
"""

from __future__ import annotations
import json
from langchain_core.tools import tool
from db import supabase_client as db


# Ordered step sequence — used to determine the "next" step.
STEP_SEQUENCE = ["greet", "loan_amount", "tranches", "emi", "bank", "completed"]

# Allowed loan fields that can be updated by tools.
ALLOWED_LOAN_FIELDS = {
    "loan_amount",
    "insurance_premium",
    "processing_fee",
    "effective_loan_amount",
    "tranches",
    "bank_account_masked",
    "bank_name",
    "branch_name",
    "ifsc_code",
    "state",
    "emi_amount",
    "emi_start_date",
    "pre_emi_amount",
    "pre_emi_date",
    "nach_registered",
    "loan_date",
}

NUMERIC_LOAN_FIELDS = {
    "loan_amount",
    "insurance_premium",
    "processing_fee",
    "effective_loan_amount",
    "emi_amount",
    "pre_emi_amount",
}

BOOLEAN_LOAN_FIELDS = {"nach_registered"}


def create_tools(loan_id: str, conversation_id: int, preferred_language: str = "hi"):
    """
    Return a list of LangChain tools bound to a specific loan / conversation.

    Parameters
    ----------
    loan_id : str
        The loan ID this session is about.
    conversation_id : int
        The conversation row ID in Supabase.
    """

    @tool
    def request_missing_loan_detail(field_name: str, reason: str) -> str:
        """Log and request a missing loan detail from the customer.

        Call this tool when the system data is missing for a field that
        is required to proceed.

        Args:
            field_name: The missing field (e.g., 'emi_amount', 'ifsc_code').
            reason: Short reason why this field is required.
        """
        if field_name not in ALLOWED_LOAN_FIELDS:
            return "Error: Unsupported field for missing data request."

        conv = db.get_active_conversation(loan_id)
        if conv:
            existing_summary = conv.get("conversation_summary", "")
            note = f"• Missing field requested: {field_name} — {reason}"
            new_summary = f"{existing_summary}\n{note}" if existing_summary else note
            db.update_conversation(
                conversation_id,
                {"conversation_summary": new_summary},
            )
        # Respect preferred language in the message
        lang = (preferred_language or "hi").strip().lower()
        if lang.startswith("en"):
            return (
                "Please help us calmly — we do not have this information on file. "
                f"{reason} Please provide the correct {field_name}."
            )
        else:
            return (
                "कृपया शांतिपूर्वक सहायता करें। हमारे रिकॉर्ड में यह जानकारी नहीं है। "
                f"{reason} कृपया इसकी सही जानकारी साझा करें।"
            )

    @tool
    def save_loan_detail(field_name: str, field_value: str) -> str:
        """Save a missing loan detail into the loans table.

        Call this tool after the customer provides the missing value.

        Args:
            field_name: The loan field to update.
            field_value: The value to store, normalized for DB storage.
        """
        if field_name not in ALLOWED_LOAN_FIELDS:
            return "Error: Unsupported field for update."

        updates: dict = {}
        raw_value = field_value.strip() if isinstance(field_value, str) else field_value

        if field_name in NUMERIC_LOAN_FIELDS:
            if isinstance(raw_value, str):
                cleaned = raw_value.replace(",", "").replace("₹", "").strip()
            else:
                cleaned = raw_value
            try:
                updates[field_name] = float(cleaned)
            except (TypeError, ValueError):
                return "Error: Invalid numeric value provided."
        elif field_name in BOOLEAN_LOAN_FIELDS:
            if isinstance(raw_value, str):
                value_lower = raw_value.strip().lower()
                if value_lower in {"yes", "true", "हाँ", "हां"}:
                    updates[field_name] = True
                elif value_lower in {"no", "false", "नहीं", "नही"}:
                    updates[field_name] = False
                else:
                    return "Error: Invalid boolean value provided."
            else:
                updates[field_name] = bool(raw_value)
        elif field_name == "tranches":
            try:
                updates[field_name] = json.loads(raw_value)
            except (TypeError, ValueError):
                return "Error: Invalid tranches JSON provided."
        else:
            updates[field_name] = raw_value

        db.update_loan_fields(loan_id, updates)
        lang = (preferred_language or "hi").strip().lower()
        if lang.startswith("en"):
            return f"✅ Missing field '{field_name}' saved successfully."
        else:
            return f"✅ फ़ील्ड '{field_name}' सफलतापूर्वक सहेज दी गई है।"

    @tool
    def confirm_step(step_name: str, summary: str) -> str:
        """Mark a conversation step as confirmed and save progress to the database.

        Call this tool EVERY TIME the customer confirms a step.

        Args:
            step_name: The step being confirmed. Must be one of:
                       'loan_amount', 'tranches', 'emi', 'bank', 'completed'.
            summary: A brief 1-line summary in Hindi of what was confirmed,
                     e.g. 'ग्राहक ने लोन राशि ₹9,82,658 की पुष्टि की'
        """
        # Fetch current conversation state
        conv = db.get_active_conversation(loan_id)
        if not conv:
            return "Error: No active conversation found."

        confirmed_steps: list = conv.get("confirmed_steps", [])
        if isinstance(confirmed_steps, str):
            confirmed_steps = json.loads(confirmed_steps)

        # Add step if not already confirmed
        if step_name not in confirmed_steps:
            confirmed_steps.append(step_name)

        # Determine next step
        current_idx = STEP_SEQUENCE.index(step_name) if step_name in STEP_SEQUENCE else -1
        if current_idx + 1 < len(STEP_SEQUENCE):
            next_step = STEP_SEQUENCE[current_idx + 1]
        else:
            next_step = "completed"

        # Build cumulative summary
        existing_summary = conv.get("conversation_summary", "")
        if existing_summary:
            new_summary = f"{existing_summary}\n• {summary}"
        else:
            new_summary = f"• {summary}"

        # Update Supabase
        status = "completed" if step_name == "completed" else "active"
        db.update_conversation(
            conversation_id,
            {
                "current_step": next_step,
                "confirmed_steps": confirmed_steps,
                "conversation_summary": new_summary,
                "status": status,
            },
        )

        return f"✅ Step '{step_name}' confirmed and saved. Proceed to next step: {next_step}."

    @tool
    def escalate_to_support(
        issue_type: str,
        description: str,
        user_claim: str,
        system_value: str,
    ) -> str:
        """Escalate a discrepancy between customer-reported data and system records
        to the human support team.

        Call this tool when the customer disputes any information.

        Args:
            issue_type: Category of the issue. Must be one of:
                        'amount_mismatch', 'bank_mismatch', 'emi_dispute',
                        'tranch_dispute', 'other'.
            description: A clear description of the discrepancy in Hindi.
            user_claim: What the customer says the value should be.
            system_value: What the system records show.
        """
        esc = db.create_escalation(
            loan_id=loan_id,
            conversation_id=conversation_id,
            issue_type=issue_type,
            description=description,
            user_claim=user_claim,
            system_value=system_value,
        )

        lang = (preferred_language or "hi").strip().lower()
        if lang.startswith("en"):
            return (
                f"🚨 Escalation #{esc['id']} created successfully.\n"
                f"Type: {issue_type}\n"
                f"The conversation has been marked as escalated.\n"
                f"Inform the customer that the support team will contact them. End the conversation politely."
            )
        else:
            return (
                f"🚨 एस्केलेशन #{esc['id']} सफलतापूर्वक बनाया गया है।\n"
                f"प्रकार: {issue_type}\n"
                f"वार्तालाप को " + "escalated" + " कर दिया गया है।\n"
                f"ग्राहक को सूचित करें कि सपोर्ट टीम उनसे संपर्क करेगी। कृपया विनम्रतापूर्वक वार्तालाप समाप्त करें।"
            )

    return [
        request_missing_loan_detail,
        save_loan_detail,
        confirm_step,
        escalate_to_support,
    ]
