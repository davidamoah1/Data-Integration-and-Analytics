"""AI Memory — conversation history management with summarization.

Manages message history for conversations, with automatic summarization
when conversations get long to stay within token limits.
"""

from typing import Optional
from sqlalchemy.orm import Session as DbSession

from ai.models import AIConversation, AIMessage
from ai.config import AI_MEMORY_MAX_MESSAGES, AI_MEMORY_SUMMARY_THRESHOLD


class AIMemory:
    """Manages conversation memory with automatic summarization."""

    def __init__(self, db: DbSession):
        self.db = db

    def get_history(self, conversation_id: int, limit: int = AI_MEMORY_MAX_MESSAGES) -> list[dict]:
        """Get recent message history for a conversation."""
        messages = self.db.query(AIMessage).filter(
            AIMessage.conversation_id == conversation_id,
        ).order_by(AIMessage.id.desc()).limit(limit).all()

        # Reverse to chronological order (id ascending)
        messages = list(reversed(messages))

        # Filter out system messages (they're reconstructed by the gateway)
        result = []
        for msg in messages:
            if msg.role in ("user", "assistant"):
                result.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        return result

    def add_message(self, conversation_id: int, role: str, content: str,
                    tokens_used: int = 0, model_used: str = "",
                    provider: str = "", response_time_ms: int = None,
                    citations: list = None, confidence_score: float = None) -> AIMessage:
        """Add a message to a conversation."""
        msg = AIMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens_used=tokens_used,
            model_used=model_used,
            provider=provider,
            response_time_ms=response_time_ms,
            citations=citations,
            confidence_score=confidence_score,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)

        # Check if summarization is needed
        self._maybe_summarize(conversation_id)

        return msg

    def _maybe_summarize(self, conversation_id: int):
        """Summarize old messages if conversation is too long."""
        count = self.db.query(AIMessage).filter(
            AIMessage.conversation_id == conversation_id,
            AIMessage.role != "system",
        ).count()

        if count > AI_MEMORY_SUMMARY_THRESHOLD * 2:
            # Get older messages to summarize
            old_messages = self.db.query(AIMessage).filter(
                AIMessage.conversation_id == conversation_id,
                AIMessage.role != "system",
            ).order_by(AIMessage.created_at.asc()).limit(
                count - AI_MEMORY_MAX_MESSAGES
            ).all()

            if old_messages:
                # Create a summary message
                summary_parts = []
                for msg in old_messages:
                    prefix = "User" if msg.role == "user" else "AI"
                    summary_parts.append(f"{prefix}: {msg.content[:100]}")
                summary = "Previous conversation summary: " + " | ".join(summary_parts)

                # Mark old messages as summarized by deleting them
                for msg in old_messages:
                    self.db.delete(msg)

                # Add summary as a system message
                summary_msg = AIMessage(
                    conversation_id=conversation_id,
                    role="system",
                    content=summary,
                    tokens_used=0,
                )
                self.db.add(summary_msg)
                self.db.commit()

    def get_conversations(self, user_id: int, assistant_type: Optional[str] = None,
                          limit: int = 50) -> list[dict]:
        """List conversations for a user."""
        query = self.db.query(AIConversation).filter(
            AIConversation.user_id == user_id,
            AIConversation.is_active == True,
        )
        if assistant_type:
            query = query.filter(AIConversation.assistant_type == assistant_type)
        conversations = query.order_by(AIConversation.updated_at.desc()).limit(limit).all()
        return [
            {
                "id": c.id,
                "assistant_type": c.assistant_type,
                "title": c.title,
                "is_active": c.is_active,
                "created_at": str(c.created_at) if c.created_at else None,
                "updated_at": str(c.updated_at) if c.updated_at else None,
            }
            for c in conversations
        ]

    def get_conversation_messages(self, conversation_id: int, limit: int = 100) -> list[dict]:
        """Get all messages in a conversation."""
        messages = self.db.query(AIMessage).filter(
            AIMessage.conversation_id == conversation_id,
        ).order_by(AIMessage.created_at.asc()).limit(limit).all()
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "tokens_used": m.tokens_used,
                "model_used": m.model_used,
                "provider": m.provider,
                "confidence_score": m.confidence_score,
                "feedback": m.feedback,
                "created_at": str(m.created_at) if m.created_at else None,
            }
            for m in messages
        ]

    def set_feedback(self, message_id: int, feedback: str) -> bool:
        """Set feedback (positive/negative) on a message."""
        msg = self.db.query(AIMessage).filter(AIMessage.id == message_id).first()
        if not msg:
            return False
        msg.feedback = feedback
        self.db.commit()
        return True

    def delete_conversation(self, conversation_id: int) -> bool:
        """Soft-delete a conversation."""
        conv = self.db.query(AIConversation).filter(AIConversation.id == conversation_id).first()
        if not conv:
            return False
        conv.is_active = False
        self.db.commit()
        return True
