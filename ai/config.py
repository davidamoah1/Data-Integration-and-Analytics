"""AI Platform configuration â€” reads from environment variables with sensible defaults."""

import os

from dotenv import load_dotenv

load_dotenv()

# --- AI Provider Settings ---
AI_DEFAULT_PROVIDER = os.getenv("AI_DEFAULT_PROVIDER", "openai")
AI_DEFAULT_MODEL = os.getenv("AI_DEFAULT_MODEL", "gpt-4o-mini")
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS") or "4096")
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE") or "0.7")
AI_REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT") or "60")

# --- Provider API Keys (read from env, stored encrypted in DB) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GLM_API_KEY = os.getenv("GLM_API_KEY", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")

# --- Provider Base URLs (for self-hosted / proxy) ---
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
GLM_BASE_URL = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
CLAUDE_BASE_URL = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com/v1")
LOCAL_LLM_BASE_URL = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")

# --- AI Memory ---
AI_MEMORY_MAX_MESSAGES = int(os.getenv("AI_MEMORY_MAX_MESSAGES") or "20")
AI_MEMORY_SUMMARY_THRESHOLD = int(os.getenv("AI_MEMORY_SUMMARY_THRESHOLD") or "10")

# --- AI Cache ---
AI_CACHE_ENABLED = os.getenv("AI_CACHE_ENABLED", "true").lower() == "true"
AI_CACHE_TTL_SECONDS = int(os.getenv("AI_CACHE_TTL_SECONDS") or "3600")
AI_CACHE_MAX_ENTRIES = int(os.getenv("AI_CACHE_MAX_ENTRIES") or "1000")

# --- AI Security ---
AI_ENFORCE_PERMISSIONS = os.getenv("AI_ENFORCE_PERMISSIONS", "true").lower() == "true"
AI_MAX_INPUT_LENGTH = int(os.getenv("AI_MAX_INPUT_LENGTH") or "10000")
AI_DATA_RETENTION_DAYS = int(os.getenv("AI_DATA_RETENTION_DAYS") or "90")

# --- AI Usage Limits ---
AI_DAILY_TOKEN_LIMIT = int(os.getenv("AI_DAILY_TOKEN_LIMIT") or "1000000")
AI_MONTHLY_COST_LIMIT_USD = float(os.getenv("AI_MONTHLY_COST_LIMIT_USD") or "100.0")

# --- AI Streaming ---
AI_STREAM_ENABLED = os.getenv("AI_STREAM_ENABLED", "true").lower() == "true"

# --- AI Document Chat ---
AI_DOC_MAX_SIZE_MB = int(os.getenv("AI_DOC_MAX_SIZE_MB") or "20")
AI_DOC_ALLOWED_TYPES = os.getenv("AI_DOC_ALLOWED_TYPES", "pdf,docx,xlsx,csv,pptx,txt").split(",")

# --- AI Forecasting ---
AI_FORECAST_CONFIDENCE_LEVEL = float(os.getenv("AI_FORECAST_CONFIDENCE_LEVEL") or "0.95")
AI_FORECAST_MAX_HORIZON = int(os.getenv("AI_FORECAST_MAX_HORIZON") or "365")

# --- AI Anomaly Detection ---
AI_ANOMALY_SENSITIVITY = float(os.getenv("AI_ANOMALY_SENSITIVITY") or "2.0")  # std deviations
AI_ANOMALY_MIN_DATA_POINTS = int(os.getenv("AI_ANOMALY_MIN_DATA_POINTS") or "10")

# --- Cost Estimates (per 1K tokens, USD) ---
AI_COST_PER_1K = {
    "openai": {
        "gpt-4o": 0.005,
        "gpt-4o-mini": 0.00015,
        "gpt-4-turbo": 0.01,
        "gpt-3.5-turbo": 0.0005,
    },
    "gemini": {"gemini-1.5-pro": 0.00125, "gemini-1.5-flash": 0.000075},
    "deepseek": {"deepseek-chat": 0.00014, "deepseek-coder": 0.00014},
    "glm": {"glm-4": 0.0005, "glm-4-flash": 0.0001},
    "claude": {"claude-3-5-sonnet-20241022": 0.003, "claude-3-haiku-20240307": 0.00025},
    "local": {"default": 0.0},
}


def get_cost_estimate(provider: str, model: str, total_tokens: int) -> float:
    """Estimate cost for a given provider/model/token combination."""
    provider_costs = AI_COST_PER_1K.get(provider, {})
    per_1k = provider_costs.get(model, provider_costs.get("default", 0.0))
    return round((total_tokens / 1000) * per_1k, 6)
