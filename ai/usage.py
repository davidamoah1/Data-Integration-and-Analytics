"""AI Usage Tracker — tracks token usage and costs per request.

Provides:
- Per-request usage logging
- Aggregated usage statistics
- Cost estimation per provider/model
- Usage limits enforcement
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session as DbSession

from ai.config import AI_DAILY_TOKEN_LIMIT, AI_MONTHLY_COST_LIMIT_USD, get_cost_estimate
from ai.models import AIUsageLog


class UsageTracker:
    """Tracks AI usage and costs."""

    def __init__(self, db: DbSession):
        self.db = db

    def track(
        self,
        user_id: int | None,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        request_type: str = "chat",
        duration_ms: int | None = None,
    ) -> AIUsageLog:
        """Log a usage entry."""
        cost = get_cost_estimate(provider, model, total_tokens)

        log = AIUsageLog(
            user_id=user_id,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost,
            request_type=request_type,
            duration_ms=duration_ms,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_stats(self, days: int = 30) -> dict:
        """Get aggregated usage statistics."""
        since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

        logs = (
            self.db.query(AIUsageLog)
            .filter(
                AIUsageLog.created_at >= since,
            )
            .all()
        )

        total_requests = len(logs)
        total_tokens = sum(log.total_tokens for log in logs)
        total_cost = sum(log.estimated_cost_usd for log in logs)

        by_provider = {}
        by_request_type = {}
        for log in logs:
            by_provider[log.provider] = by_provider.get(log.provider, 0) + log.total_tokens
            by_request_type[log.request_type or "unknown"] = (
                by_request_type.get(log.request_type or "unknown", 0) + 1
            )

        daily_average = total_requests / max(days, 1)

        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "by_provider": by_provider,
            "by_request_type": by_request_type,
            "daily_average": round(daily_average, 2),
        }

    def get_user_usage(self, user_id: int, days: int = 30) -> dict:
        """Get usage for a specific user."""
        since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        logs = (
            self.db.query(AIUsageLog)
            .filter(
                AIUsageLog.user_id == user_id,
                AIUsageLog.created_at >= since,
            )
            .all()
        )
        return {
            "total_requests": len(logs),
            "total_tokens": sum(log.total_tokens for log in logs),
            "total_cost_usd": round(sum(log.estimated_cost_usd for log in logs), 4),
        }

    def check_limits(self, user_id: int) -> dict:
        """Check if user is within usage limits."""
        today = datetime.now(timezone.utc).replace(tzinfo=None).date()
        month_start = today.replace(day=1)

        today_logs = (
            self.db.query(AIUsageLog)
            .filter(
                AIUsageLog.user_id == user_id,
                func.date(AIUsageLog.created_at) == today,
            )
            .all()
        )

        month_logs = (
            self.db.query(AIUsageLog)
            .filter(
                AIUsageLog.user_id == user_id,
                func.date(AIUsageLog.created_at) >= month_start,
            )
            .all()
        )

        daily_tokens = sum(log.total_tokens for log in today_logs)
        monthly_cost = sum(log.estimated_cost_usd for log in month_logs)

        return {
            "daily_tokens_used": daily_tokens,
            "daily_token_limit": AI_DAILY_TOKEN_LIMIT,
            "daily_remaining": max(AI_DAILY_TOKEN_LIMIT - daily_tokens, 0),
            "monthly_cost_usd": round(monthly_cost, 4),
            "monthly_cost_limit": AI_MONTHLY_COST_LIMIT_USD,
            "within_limits": daily_tokens < AI_DAILY_TOKEN_LIMIT
            and monthly_cost < AI_MONTHLY_COST_LIMIT_USD,
        }
