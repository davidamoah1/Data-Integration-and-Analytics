"""AI Copilot surface for the Streamlit dashboard.

Provides an inline chat panel that lets users ask questions about their data,
dashboards, ETL pipelines, and more — directly from the dashboard UI.

The copilot calls the AIGateway directly via a DB session, avoiding the need
to bridge the dashboard's session-based auth with the API's JWT auth.
"""

import streamlit as st

from ai.assistants.assistants import list_assistants
from ai.gateway import AIGateway
from shared.database import get_session_factory


def _get_db_session():
    """Create a short-lived DB session for AI gateway calls."""
    factory = get_session_factory()
    return factory()


def _get_user_id() -> int:
    """Return a numeric user ID for the AI gateway.

    The dashboard uses simple session auth without a database user record.
    We use a sentinel ID of 1 (typically the seeded admin user) so that
    conversation history is still persisted per-user in the AI tables.
    """
    return st.session_state.get("ai_user_id", 1)


def _init_copilot_state():
    """Initialize copilot-related session state keys."""
    if "copilot_messages" not in st.session_state:
        st.session_state["copilot_messages"] = []
    if "copilot_conversation_id" not in st.session_state:
        st.session_state["copilot_conversation_id"] = None
    if "copilot_assistant" not in st.session_state:
        st.session_state["copilot_assistant"] = "data_copilot"


def _send_message(message: str, assistant_type: str, conversation_id: int | None):
    """Send a message to the AI gateway and return the result dict."""
    db = _get_db_session()
    try:
        gateway = AIGateway(db)
        result = gateway.chat(
            user_message=message,
            assistant_type=assistant_type,
            user_id=_get_user_id(),
            conversation_id=conversation_id,
            stream=False,
            permissions=[],
        )
        return result
    finally:
        db.close()


def render_copilot_panel():
    """Render the AI Copilot chat panel in the dashboard sidebar or main area.

    Call this function from app.py to embed the copilot.
    """
    _init_copilot_state()

    st.markdown("### AI Copilot")
    st.markdown(
        '<p style="color:rgba(255,255,255,0.5);font-size:0.8rem;">'
        "Ask questions about your data, dashboards, pipelines, and more."
        "</p>",
        unsafe_allow_html=True,
    )

    assistants = list_assistants()
    assistant_names = [a.get("name", a.get("id", "Unknown")) for a in assistants]
    assistant_map = {
        a.get("name", a.get("id", "Unknown")): a.get("id", "data_copilot") for a in assistants
    }

    current_name = st.session_state.get(
        "copilot_assistant_name", assistant_names[0] if assistant_names else "Data Copilot"
    )
    sel_name = st.selectbox(
        "Assistant",
        assistant_names,
        index=assistant_names.index(current_name) if current_name in assistant_names else 0,
        label_visibility="collapsed",
    )
    st.session_state["copilot_assistant"] = assistant_map.get(sel_name, "data_copilot")
    st.session_state["copilot_assistant_name"] = sel_name

    chat_container = st.container()
    with chat_container:
        for msg in st.session_state["copilot_messages"]:
            role = msg["role"]
            with st.chat_message(role):
                st.markdown(msg["content"])
                if role == "assistant" and msg.get("citations"):
                    with st.expander("Supporting Evidence"):
                        for cite in msg["citations"]:
                            st.markdown(f"- {cite}")
                if role == "assistant" and msg.get("confidence") is not None:
                    st.caption(f"Confidence: {msg['confidence']:.0%}")

    user_input = st.chat_input("Ask the AI Copilot...")

    if user_input:
        st.session_state["copilot_messages"].append({"role": "user", "content": user_input})
        with chat_container, st.chat_message("user"):
            st.markdown(user_input)

        try:
            with st.spinner("Thinking..."):
                result = _send_message(
                    user_input,
                    st.session_state["copilot_assistant"],
                    st.session_state["copilot_conversation_id"],
                )
            st.session_state["copilot_conversation_id"] = result.get("conversation_id")

            assistant_msg = {
                "role": "assistant",
                "content": result.get("response", "No response received."),
                "citations": result.get("citations"),
                "confidence": result.get("confidence_score"),
            }
            st.session_state["copilot_messages"].append(assistant_msg)

            with chat_container, st.chat_message("assistant"):
                st.markdown(assistant_msg["content"])
                if assistant_msg["citations"]:
                    with st.expander("Supporting Evidence"):
                        for cite in assistant_msg["citations"]:
                            st.markdown(f"- {cite}")
                if assistant_msg["confidence"] is not None:
                    st.caption(f"Confidence: {assistant_msg['confidence']:.0%}")
        except PermissionError as e:
            st.error(f"Permission denied: {e}")
        except ValueError as e:
            st.error(f"Invalid request: {e}")
        except Exception as e:
            st.error(f"AI request failed: {e}")

    if st.session_state["copilot_messages"] and st.button("Clear Chat", use_container_width=True):
        st.session_state["copilot_messages"] = []
        st.session_state["copilot_conversation_id"] = None
        st.rerun()
