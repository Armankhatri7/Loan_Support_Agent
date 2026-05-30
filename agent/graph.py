"""
LangGraph agent graph for the Loan Support Agent.

Uses `create_react_agent` from langgraph.prebuilt — a pre-built ReAct loop:
  Agent (LLM + tools)  ←→  Tool executor
The system prompt drives the structured 5-step conversation flow.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent.prompts import build_system_prompt
from agent.tools import create_tools


def build_agent(
    loan_id: str,
    conversation_id: int,
    loan_data: dict,
    resume_context: dict | None = None,
):
    """
    Build and return a compiled LangGraph ReAct agent.

    Parameters
    ----------
    loan_id : str
        Active loan ID.
    conversation_id : int
        Supabase conversation row ID.
    loan_data : dict
        Full loan record from Supabase.
    resume_context : dict, optional
        Context for resuming a dropped conversation.
        Keys: confirmed_steps, conversation_summary, current_step.

    Returns
    -------
    CompiledGraph
        A LangGraph agent ready for `.invoke({"messages": [...]})`.
    """
    # 1. Determine preferred language and build tools bound to this session
    preferred_language = loan_data.get("preferred_language", "hi")
    tools = create_tools(loan_id, conversation_id, preferred_language)

    # 2. Build dynamic system prompt with loan data + optional resume context
    system_prompt = build_system_prompt(loan_data, resume_context, preferred_language)

    # 3. Create the LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,      # Low temperature for consistent, factual responses
        max_tokens=1024,
    )

    # 4. Create the ReAct agent graph
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
    )

    return agent
