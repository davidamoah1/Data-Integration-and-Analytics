"""AI Gateway — central orchestrator for all AI requests.

This is the single entry point for all AI operations across the platform.
It coordinates providers, memory, context, security, usage tracking, caching,
and audit logging.
"""

import hashlib
import json
import time
from collections.abc import Generator

from sqlalchemy.orm import Session as DbSession

from ai.cache import AICache
from ai.config import (
    AI_CACHE_ENABLED,
    AI_ENFORCE_PERMISSIONS,
)
from ai.context_builder import ContextBuilder
from ai.memory import AIMemory
from ai.model_router import ModelRouter
from ai.models import AIAuditLog, AIConversation
from ai.prompts.templates import PromptManager
from ai.providers.manager import ProviderManager
from ai.security import AISecurityLayer
from ai.usage import UsageTracker


class AIGateway:
    """Central AI orchestrator — routes requests through the full AI stack."""

    def __init__(self, db: DbSession):
        self.db = db
        self.provider_manager = ProviderManager(db)
        self.prompt_manager = PromptManager(db)
        self.memory = AIMemory(db)
        self.context_builder = ContextBuilder(db)
        self.security = AISecurityLayer(db)
        self.usage_tracker = UsageTracker(db)
        self.cache = AICache() if AI_CACHE_ENABLED else None
        self.model_router = ModelRouter(db)

    def chat(
        self,
        user_message: str,
        assistant_type: str = "data_copilot",
        user_id: int | None = None,
        conversation_id: int | None = None,
        context: dict | None = None,
        stream: bool = False,
        permissions: list[str] | None = None,
        organization_id: int | None = None,
    ) -> dict | Generator[str, None, None]:
        """Process a chat request through the full AI stack.

        Flow:
        1. Validate input (security)
        2. Build platform context
        3. Get/create conversation
        4. Load conversation memory
        5. Construct messages (system + context + memory + user)
        6. Check cache
        7. Route to appropriate provider/model
        8. Track usage
        9. Log audit trail
        10. Return response

        Returns:
            Dict with conversation_id, message_id, response, tokens, etc.
            Or generator if stream=True.
        """
        start_time = time.time()

        # 1. Security validation
        if AI_ENFORCE_PERMISSIONS:
            self.security.validate_input(user_message)
            self.security.check_permissions(assistant_type, permissions or [])

        # 2. Build platform context
        platform_context = self.context_builder.build_context(
            assistant_type=assistant_type,
            user_id=user_id,
            extra_context=context,
        )

        # 3. Get or create conversation
        if conversation_id:
            conversation = (
                self.db.query(AIConversation).filter(AIConversation.id == conversation_id).first()
            )
            if not conversation:
                conversation = self._create_conversation(
                    user_id, assistant_type, user_message, organization_id
                )
        else:
            conversation = self._create_conversation(
                user_id, assistant_type, user_message, organization_id
            )

        conversation_id = conversation.id

        # 4. Load memory
        history = self.memory.get_history(conversation_id)

        # 5. Construct messages
        system_prompt = self.prompt_manager.get_system_prompt(assistant_type)
        messages = [{"role": "system", "content": system_prompt}]

        # Add platform context as system message
        if platform_context:
            messages.append(
                {
                    "role": "system",
                    "content": f"Platform Context:\n{json.dumps(platform_context, default=str)[:3000]}",
                }
            )

        # Add conversation history
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add user message
        messages.append({"role": "user", "content": user_message})

        # 6. Check cache
        cache_key = None
        if self.cache:
            cache_key = self._make_cache_key(messages, assistant_type)
            cached = self.cache.get(cache_key)
            if cached:
                # Save user message and cached response
                self.memory.add_message(conversation_id, "user", user_message)
                msg = self.memory.add_message(
                    conversation_id,
                    "assistant",
                    cached["content"],
                    tokens_used=cached.get("total_tokens", 0),
                    model_used=cached.get("model", ""),
                    provider=cached.get("provider", ""),
                )
                return {
                    "conversation_id": conversation_id,
                    "message_id": msg.id,
                    "response": cached["content"],
                    "citations": None,
                    "confidence_score": None,
                    "tokens_used": cached.get("total_tokens", 0),
                    "model_used": cached.get("model", ""),
                    "provider": cached.get("provider", ""),
                    "cached": True,
                }

        # 7. Route to provider
        provider_name, model = self.model_router.route(assistant_type, user_message)

        # Save user message
        self.memory.add_message(conversation_id, "user", user_message)

        if stream:
            return self._stream_response(
                messages,
                provider_name,
                model,
                conversation_id,
                user_id,
                assistant_type,
                start_time,
            )

        # Non-streaming
        response = self.provider_manager.chat(
            messages=messages,
            provider_name=provider_name,
            model=model,
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        # 8. Track usage
        self.usage_tracker.track(
            user_id=user_id,
            provider=response.provider,
            model=response.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            request_type=f"chat_{assistant_type}",
            duration_ms=elapsed_ms,
        )

        # 9. Save assistant message
        msg = self.memory.add_message(
            conversation_id,
            "assistant",
            response.content,
            tokens_used=response.total_tokens,
            model_used=response.model,
            provider=response.provider,
            response_time_ms=elapsed_ms,
        )

        # 10. Audit log
        self._audit_log(
            user_id=user_id,
            action="chat",
            assistant_type=assistant_type,
            input_summary=user_message[:200],
            output_summary=response.content[:200],
            success=True,
        )

        # Cache the response
        if self.cache and cache_key:
            self.cache.set(
                cache_key,
                {
                    "content": response.content,
                    "total_tokens": response.total_tokens,
                    "model": response.model,
                    "provider": response.provider,
                },
            )

        return {
            "conversation_id": conversation_id,
            "message_id": msg.id,
            "response": response.content,
            "citations": None,
            "confidence_score": None,
            "tokens_used": response.total_tokens,
            "model_used": response.model,
            "provider": response.provider,
            "cached": False,
        }

    def _stream_response(
        self, messages, provider_name, model, conversation_id, user_id, assistant_type, start_time
    ) -> Generator[str, None, None]:
        """Stream response chunks to the client."""
        chunks = []
        try:
            for chunk in self.provider_manager.chat(
                messages=messages,
                provider_name=provider_name,
                model=model,
                stream=True,
            ):
                chunks.append(chunk)
                yield chunk
        except Exception as e:
            yield f"\n[Error: {str(e)}]"
            self._audit_log(
                user_id=user_id,
                action="chat_stream",
                assistant_type=assistant_type,
                input_summary="streaming request",
                success=False,
                error_message=str(e),
            )
            return

        full_response = "".join(chunks)
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Save assistant message
        self.memory.add_message(
            conversation_id,
            "assistant",
            full_response,
            tokens_used=0,  # Streaming doesn't return token counts
            model_used=model,
            provider=provider_name,
            response_time_ms=elapsed_ms,
        )

        # Audit log
        self._audit_log(
            user_id=user_id,
            action="chat_stream",
            assistant_type=assistant_type,
            input_summary="streaming request",
            output_summary=full_response[:200],
            success=True,
        )

    def _create_conversation(
        self,
        user_id: int,
        assistant_type: str,
        first_message: str,
        organization_id: int | None = None,
    ) -> AIConversation:
        """Create a new conversation."""
        # Resolve organization_id from user if not provided
        if organization_id is None and user_id and self.db:
            from authentication.models import User

            user_obj = self.db.query(User).filter(User.id == user_id).first()
            if user_obj:
                organization_id = user_obj.organization_id

        title = first_message[:50] + ("..." if len(first_message) > 50 else "")
        conv = AIConversation(
            user_id=user_id,
            assistant_type=assistant_type,
            title=title,
            is_active=True,
            organization_id=organization_id,
        )
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def _make_cache_key(self, messages: list[dict], assistant_type: str) -> str:
        """Generate a cache key from messages."""
        # Only cache based on the last user message + assistant type
        last_user_msg = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_user_msg = msg["content"]
                break
        key_str = f"{assistant_type}:{last_user_msg}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _audit_log(
        self,
        user_id: int | None,
        action: str,
        assistant_type: str,
        input_summary: str = "",
        output_summary: str = "",
        success: bool = True,
        error_message: str = "",
    ):
        """Create an audit log entry."""
        log = AIAuditLog(
            user_id=user_id,
            action=action,
            assistant_type=assistant_type,
            input_summary=input_summary,
            output_summary=output_summary,
            success=success,
            error_message=error_message,
        )
        self.db.add(log)
        self.db.commit()
