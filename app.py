"""
Loan Support Agent — Streamlit Application

A Hindi-first conversational AI agent that guides loan customers through
a structured confirmation flow using LangGraph + GPT-4o.
"""

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

from agent.graph import build_agent
from db import supabase_client as db

load_dotenv()

# ──────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="लोन सहायक | Loan Support Agent",
    page_icon="🏦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# Custom CSS for premium Hindi UI
# ──────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;500;600;700&display=swap');

    /* Global */
    .stApp {
        font-family: 'Noto Sans Devanagari', 'Segoe UI', sans-serif;
    }

    /* Header */
    .app-header {
        text-align: center;
        padding: 1.5rem 0 1rem;
    }
    .app-header h1 {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1e3a5f 0%, #2d7dd2 50%, #1e3a5f 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .app-header p {
        color: #6b7280;
        font-size: 0.95rem;
    }

    /* Login card */
    .login-card {
        max-width: 420px;
        margin: 2rem auto;
        padding: 2.5rem 2rem;
        background: linear-gradient(145deg, #ffffff, #f0f4f8);
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    }
    .login-card h2 {
        text-align: center;
        color: #1e3a5f;
        margin-bottom: 1.5rem;
        font-weight: 600;
    }

    /* Chat area */
    .chat-container {
        max-width: 720px;
        margin: 0 auto;
    }

    /* Loan info badge */
    .loan-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4rem 1rem;
        background: linear-gradient(135deg, #eef2ff, #e0e7ff);
        border: 1px solid #c7d2fe;
        border-radius: 999px;
        font-size: 0.85rem;
        color: #3730a3;
        font-weight: 500;
        margin-bottom: 1rem;
    }

    /* Status bar */
    .status-bar {
        display: flex;
        justify-content: center;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin: 0.75rem 0 1.5rem;
    }
    .status-chip {
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .status-chip.done {
        background: #d1fae5;
        color: #065f46;
        border: 1px solid #a7f3d0;
    }
    .status-chip.active {
        background: #dbeafe;
        color: #1e40af;
        border: 1px solid #93c5fd;
        animation: pulse 2s infinite;
    }
    .status-chip.pending {
        background: #f3f4f6;
        color: #6b7280;
        border: 1px solid #e5e7eb;
    }
    .status-chip.escalated {
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #fca5a5;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Streamlit overrides */
    .stChatMessage {
        font-family: 'Noto Sans Devanagari', sans-serif !important;
    }
    div[data-testid="stChatInput"] textarea {
        font-family: 'Noto Sans Devanagari', sans-serif !important;
    }
    .stButton > button {
        font-family: 'Noto Sans Devanagari', sans-serif !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ──────────────────────────────────────────────
# Helper: extract display-ready messages
# ──────────────────────────────────────────────
def get_display_messages(agent_messages: list, skip_first_human: bool = True) -> list:
    """
    Filter LangChain messages to only user-visible ones.
    Skips tool calls/results and the initial trigger message.
    """
    display = []
    first_human_skipped = False
    for msg in agent_messages:
        if isinstance(msg, HumanMessage):
            if skip_first_human and not first_human_skipped:
                first_human_skipped = True
                continue
            display.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage) and msg.content:
            display.append({"role": "assistant", "content": msg.content})
    return display


# ──────────────────────────────────────────────
# Helper: render step progress bar
# ──────────────────────────────────────────────
STEP_LABELS = {
    "loan_amount": "💰 राशि",
    "tranches": "📊 ट्रांच",
    "emi": "📅 EMI",
    "bank": "🏦 बैंक",
    "completed": "✅ पूर्ण",
}

def render_progress(confirmed_steps: list, current_step: str, is_escalated: bool = False):
    """Render a visual progress bar of the confirmation flow."""
    chips_html = ""
    for step_key, label in STEP_LABELS.items():
        if step_key in confirmed_steps or step_key == "completed" and "bank" in confirmed_steps:
            cls = "done"
        elif is_escalated:
            cls = "escalated"
        elif step_key == current_step:
            cls = "active"
        else:
            cls = "pending"
        chips_html += f'<span class="status-chip {cls}">{label}</span>'

    st.markdown(f'<div class="status-bar">{chips_html}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════
def show_login_page():
    st.markdown(
        """
        <div class="app-header">
            <h1>🏦 लोन सहायक</h1>
            <p>Loan Support Agent — अपने लोन की जानकारी सत्यापित करें</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="login-card"><h2>लॉग इन करें</h2></div>', unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        loan_id = st.text_input(
            "लोन आईडी (Loan ID)",
            placeholder="e.g. SFC202508986",
            help="आपके लोन दस्तावेज़ पर दिया गया लोन आईडी दर्ज करें",
        )
        submitted = st.form_submit_button("🔑 लॉग इन करें", use_container_width=True)

    if submitted and loan_id:
        loan_id = loan_id.strip().upper()
        with st.spinner("लोन डेटा खोज रहे हैं..."):
            loan_data = db.fetch_loan_by_id(loan_id)

        if loan_data:
            st.session_state.authenticated = True
            st.session_state.loan_id = loan_id
            st.session_state.loan_data = loan_data
            st.session_state.agent_messages = []
            st.session_state.chat_started = False
            st.session_state.conversation_id = None
            st.session_state.confirmed_steps = []
            st.session_state.current_step = "greet"
            st.session_state.is_escalated = False

            # Check for existing active conversation (resume logic)
            existing_conv = db.get_active_conversation(loan_id)
            if existing_conv:
                st.session_state.conversation_id = existing_conv["id"]
                st.session_state.confirmed_steps = existing_conv.get("confirmed_steps", [])
                st.session_state.current_step = existing_conv.get("current_step", "greet")
                st.session_state.resume_context = {
                    "confirmed_steps": existing_conv.get("confirmed_steps", []),
                    "conversation_summary": existing_conv.get("conversation_summary", ""),
                    "current_step": existing_conv.get("current_step", "greet"),
                }
            else:
                # Create new conversation
                new_conv = db.create_conversation(loan_id)
                st.session_state.conversation_id = new_conv["id"]
                st.session_state.resume_context = None

            st.rerun()
        else:
            st.error("❌ यह लोन आईडी हमारे रिकॉर्ड में नहीं मिला। कृपया सही आईडी दर्ज करें।")
    elif submitted:
        st.warning("कृपया लोन आईडी दर्ज करें।")


# ══════════════════════════════════════════════
# CHAT PAGE
# ══════════════════════════════════════════════
def show_chat_page():
    loan_data = st.session_state.loan_data
    loan_id = st.session_state.loan_id

    # ── Header ──
    st.markdown(
        """
        <div class="app-header">
            <h1>🏦 लोन सहायक</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Loan badge ──
    st.markdown(
        f'<div style="text-align:center">'
        f'<span class="loan-badge">📋 Loan: {loan_id} | '
        f'👤 {loan_data["borrower_name"]}</span></div>',
        unsafe_allow_html=True,
    )

    # ── Progress bar ──
    render_progress(
        st.session_state.confirmed_steps,
        st.session_state.current_step,
        st.session_state.is_escalated,
    )

    # ── Build or retrieve agent ──
    if "agent" not in st.session_state:
        st.session_state.agent = build_agent(
            loan_id=loan_id,
            conversation_id=st.session_state.conversation_id,
            loan_data=loan_data,
            resume_context=st.session_state.get("resume_context"),
        )

    agent = st.session_state.agent

    # ── Trigger initial greeting ──
    if not st.session_state.chat_started:
        # Localize spinner and initial trigger based on customer's preferred language
        preferred_lang = (loan_data.get("preferred_language") or "hi").strip().lower()
        use_english = preferred_lang.startswith("en")
        spinner_text = "Agent is preparing..." if use_english else "एजेंट तैयार हो रहा है..."
        with st.spinner(spinner_text):
            if st.session_state.get("resume_context"):
                trigger_text = (
                    "I'm back. Please tell me the remaining details of my loan. Please reply only in English."
                    if use_english
                    else "मैं वापस आया हूँ। कृपया मेरे लोन की बाकी जानकारी बताएं। कृपया केवल हिन्दी में उत्तर दें।"
                )
            else:
                trigger_text = (
                    "Hello, please tell me about my loan details. Please reply only in English."
                    if use_english
                    else "नमस्ते, कृपया मेरे लोन की जानकारी बताएं। कृपया केवल हिन्दी में उत्तर दें।"
                )

            result = agent.invoke({"messages": [HumanMessage(content=trigger_text)]})
            st.session_state.agent_messages = list(result["messages"])
            st.session_state.chat_started = True

            # Sync confirmed steps from DB after agent might have called tools
            _sync_progress()

    # ── Render chat history ──
    display_msgs = get_display_messages(st.session_state.agent_messages)
    for msg in display_msgs:
        avatar = "👤" if msg["role"] == "user" else "🏦"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # ── Check if conversation ended ──
    if st.session_state.current_step == "completed":
        st.success("✅ सभी जानकारी सफलतापूर्वक सत्यापित हो गई है! धन्यवाद।")
        _show_logout_button()
        return

    if st.session_state.is_escalated:
        st.warning("🚨 आपका मामला सहायता टीम को भेज दिया गया है। वे जल्द संपर्क करेंगे।")
        _show_logout_button()
        return

    # ── Chat input ──
    # Localize chat input placeholder
    preferred_lang = (loan_data.get("preferred_language") or "hi").strip().lower()
    use_english = preferred_lang.startswith("en")
    placeholder = "Type your message here..." if use_english else "अपना संदेश यहाँ लिखें..."

    if user_input := st.chat_input(placeholder):
        # Display user message immediately
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        # Invoke agent
        st.session_state.agent_messages.append(HumanMessage(content=user_input))
        with st.spinner("सोच रहा हूँ..."):
            result = agent.invoke(
                {"messages": st.session_state.agent_messages}
            )
            st.session_state.agent_messages = list(result["messages"])

        # Sync progress from DB
        _sync_progress()

        # Display new assistant messages
        new_ai_msgs = [
            m for m in result["messages"]
            if isinstance(m, AIMessage) and m.content
        ]
        if new_ai_msgs:
            last_ai = new_ai_msgs[-1]
            with st.chat_message("assistant", avatar="🏦"):
                st.markdown(last_ai.content)

        st.rerun()


def _sync_progress():
    """Fetch latest conversation state from Supabase and update session."""
    conv = db.get_active_conversation(st.session_state.loan_id)
    if not conv:
        # Conversation might have been marked escalated/completed
        from db.supabase_client import get_client
        client = get_client()
        result = (
            client.table("conversations")
            .select("*")
            .eq("id", st.session_state.conversation_id)
            .execute()
        )
        if result.data:
            conv = result.data[0]

    if conv:
        st.session_state.confirmed_steps = conv.get("confirmed_steps", [])
        st.session_state.current_step = conv.get("current_step", "greet")
        if conv.get("status") == "escalated":
            st.session_state.is_escalated = True
        if conv.get("status") == "completed":
            st.session_state.current_step = "completed"


def _show_logout_button():
    """Show a button to start a new session."""
    st.divider()
    if st.button("🔄 नया सत्र शुरू करें (New Session)", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ══════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════
def main():
    if st.session_state.get("authenticated"):
        show_chat_page()
    else:
        show_login_page()


if __name__ == "__main__":
    main()
else:
    main()
