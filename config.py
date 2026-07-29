import os

from dotenv import load_dotenv

load_dotenv()

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _resolve_path(path_str: str) -> str:
    """Resolve a path string relative to BASE_DIR if not absolute."""
    if os.path.isabs(path_str):
        return path_str
    return os.path.join(BASE_DIR, path_str)


# Data paths — production must set RAW_DATA_PATH explicitly (no default sample data)
RAW_DATA_PATH = _resolve_path(os.getenv("RAW_DATA_PATH", ""))
PROCESSED_DATA_PATH = _resolve_path(
    os.getenv("PROCESSED_DATA_PATH", "data/processed/cleaned_data.csv")
)

# Demo / onboarding datasets — opt-in only, never used in production automatically
DEMO_DATASETS_DIR = _resolve_path(os.getenv("DEMO_DATASETS_DIR", "demo_datasets"))
SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "false").lower() in ("true", "1", "yes")

# Smart Data Capture — original + enhanced uploaded document storage
CAPTURE_STORAGE_DIR = _resolve_path(os.getenv("CAPTURE_STORAGE_DIR", "storage/capture"))
if os.getenv("VERCEL", "").lower() in ("1", "true", "yes") and not os.path.isabs(
    os.getenv("CAPTURE_STORAGE_DIR", "")
):
    CAPTURE_STORAGE_DIR = os.path.join("/tmp", "capture")
CAPTURE_MAX_FILE_SIZE_MB = int(os.getenv("CAPTURE_MAX_FILE_SIZE_MB", "25"))
CAPTURE_LOW_CONFIDENCE_THRESHOLD = float(os.getenv("CAPTURE_LOW_CONFIDENCE_THRESHOLD", "0.75"))
CAPTURE_RETENTION_DAYS = int(os.getenv("CAPTURE_RETENTION_DAYS", "365"))
# Path to the Tesseract OCR binary. Leave unset to use the system PATH.
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")

# Database
DB_TYPE = os.getenv("DB_TYPE", "").lower()

if DB_TYPE == "mysql":
    _mysql_host = os.getenv("MYSQL_HOST", "localhost")
    _mysql_port = os.getenv("MYSQL_PORT", "3306")
    _mysql_db = os.getenv("MYSQL_DATABASE", "")
    _mysql_user = os.getenv("MYSQL_USER", "")
    _mysql_pass = os.getenv("MYSQL_PASSWORD", "")
    DB_URL = (
        f"mysql+pymysql://{_mysql_user}:{_mysql_pass}"
        f"@{_mysql_host}:{_mysql_port}/{_mysql_db}?charset=utf8mb4"
    )
elif DB_TYPE == "sqlite":
    _sqlite_path = _resolve_path(os.getenv("SQLITE_DB_PATH", "database/etl_database.db"))
    # Vercel's filesystem is read-only; use /tmp for SQLite so tables can be created.
    if os.getenv("VERCEL", "").lower() in ("1", "true", "yes") and not os.path.isabs(_sqlite_path):
        _sqlite_path = os.path.join("/tmp", _sqlite_path)
    DB_URL = f"sqlite:///{_sqlite_path}"
elif DB_TYPE:
    raise ValueError(
        "DB_TYPE environment variable must be set to 'mysql' or 'sqlite'. "
        "Use 'mysql' for production and 'sqlite' only for local development/testing."
    )
else:
    # Default to SQLite for local dev and serverless cold starts when not configured.
    # Production deployments should explicitly set DB_TYPE=mysql.
    DB_TYPE = "sqlite"
    _sqlite_path = _resolve_path(os.getenv("SQLITE_DB_PATH", "database/etl_database.db"))
    if os.getenv("VERCEL", "").lower() in ("1", "true", "yes") and not os.path.isabs(_sqlite_path):
        _sqlite_path = os.path.join("/tmp", _sqlite_path)
    DB_URL = f"sqlite:///{_sqlite_path}"

# --- Connection Pool Settings (MySQL) ---
POOL_SIZE = int(os.getenv("POOL_SIZE", "10"))
POOL_TIMEOUT = int(os.getenv("POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("POOL_RECYCLE", "3600"))
MAX_OVERFLOW = int(os.getenv("MAX_OVERFLOW", "20"))

# --- Redis / Performance (Phase 10) ---
REDIS_URL = os.getenv("REDIS_URL", "")
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_DEFAULT_TTL = int(os.getenv("CACHE_DEFAULT_TTL", "300"))
CACHE_KEY_PREFIX = os.getenv("CACHE_KEY_PREFIX", "aedip")

# Background workers
WORKER_MIN_WORKERS = int(os.getenv("WORKER_MIN_WORKERS", "2"))
WORKER_MAX_WORKERS = int(os.getenv("WORKER_MAX_WORKERS", "20"))
WORKER_SCALE_UP_THRESHOLD = int(os.getenv("WORKER_SCALE_UP_THRESHOLD", "10"))
WORKER_SCALE_DOWN_THRESHOLD = int(os.getenv("WORKER_SCALE_DOWN_THRESHOLD", "2"))
WORKER_SCALE_CHECK_INTERVAL = int(os.getenv("WORKER_SCALE_CHECK_INTERVAL", "30"))

# Chunked query default size
CHUNK_SIZE_DEFAULT = int(os.getenv("CHUNK_SIZE_DEFAULT", "5000"))

# Logging
LOG_PATH = _resolve_path(os.getenv("LOG_PATH", "logs/pipeline.log"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Schedule (24-hour format)
PIPELINE_RUN_TIME = os.getenv("PIPELINE_RUN_TIME", "08:00")

# --- Security / JWT ---
_JWT_DEFAULT_SECRET = "change-this-to-a-strong-random-secret-min-32-chars"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", _JWT_DEFAULT_SECRET)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "30"))
JWT_REFRESH_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))

# --- Password Policy ---
PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
PASSWORD_REQUIRE_UPPERCASE = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"
PASSWORD_REQUIRE_LOWERCASE = os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true"
PASSWORD_REQUIRE_DIGIT = os.getenv("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true"
PASSWORD_REQUIRE_SPECIAL = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"
PASSWORD_HISTORY_COUNT = int(os.getenv("PASSWORD_HISTORY_COUNT", "5"))

# --- Account Lockout ---
ACCOUNT_LOCKOUT_THRESHOLD = int(os.getenv("ACCOUNT_LOCKOUT_THRESHOLD", "5"))
ACCOUNT_LOCKOUT_DURATION_MINUTES = int(os.getenv("ACCOUNT_LOCKOUT_DURATION_MINUTES", "30"))

# --- CORS ---
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://localhost:3000")

# --- AI Platform (Phase 6) ---
AI_DEFAULT_PROVIDER = os.getenv("AI_DEFAULT_PROVIDER", "openai")
AI_DEFAULT_MODEL = os.getenv("AI_DEFAULT_MODEL", "gpt-4o-mini")
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "4096"))
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))
AI_REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT", "60"))

# AI Provider API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GLM_API_KEY = os.getenv("GLM_API_KEY", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")

# AI Provider Base URLs
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
GLM_BASE_URL = os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
CLAUDE_BASE_URL = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com/v1")
LOCAL_LLM_BASE_URL = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")

# AI Memory & Cache
AI_MEMORY_MAX_MESSAGES = int(os.getenv("AI_MEMORY_MAX_MESSAGES", "20"))
AI_CACHE_ENABLED = os.getenv("AI_CACHE_ENABLED", "true").lower() == "true"
AI_CACHE_TTL_SECONDS = int(os.getenv("AI_CACHE_TTL_SECONDS", "3600"))

# AI Security
AI_ENFORCE_PERMISSIONS = os.getenv("AI_ENFORCE_PERMISSIONS", "true").lower() == "true"
AI_MAX_INPUT_LENGTH = int(os.getenv("AI_MAX_INPUT_LENGTH", "10000"))
AI_DATA_RETENTION_DAYS = int(os.getenv("AI_DATA_RETENTION_DAYS", "90"))

# AI Usage Limits
AI_DAILY_TOKEN_LIMIT = int(os.getenv("AI_DAILY_TOKEN_LIMIT", "1000000"))
AI_MONTHLY_COST_LIMIT_USD = float(os.getenv("AI_MONTHLY_COST_LIMIT_USD", "100.0"))

# AI Document Chat
AI_DOC_MAX_SIZE_MB = int(os.getenv("AI_DOC_MAX_SIZE_MB", "20"))
AI_DOC_ALLOWED_TYPES = os.getenv("AI_DOC_ALLOWED_TYPES", "pdf,docx,xlsx,csv,pptx,txt").split(",")

# AI Forecasting
AI_FORECAST_CONFIDENCE_LEVEL = float(os.getenv("AI_FORECAST_CONFIDENCE_LEVEL", "0.95"))
AI_FORECAST_MAX_HORIZON = int(os.getenv("AI_FORECAST_MAX_HORIZON", "365"))

# AI Anomaly Detection
AI_ANOMALY_SENSITIVITY = float(os.getenv("AI_ANOMALY_SENSITIVITY", "2.0"))
AI_ANOMALY_MIN_DATA_POINTS = int(os.getenv("AI_ANOMALY_MIN_DATA_POINTS", "10"))


def validate_config() -> None:
    """Validate production-critical configuration at startup.

    Fail fast when required settings are missing or insecure. SQLite is only
    permitted for development and testing; production deployments must use
    MySQL.

    Validation can be disabled by setting DISABLE_CONFIG_VALIDATION=1 for
    serverless cold starts where only a subset of the app is exercised.
    """
    if os.getenv("DISABLE_CONFIG_VALIDATION", "").lower() in ("1", "true", "yes"):
        return

    if DB_TYPE not in {"mysql", "sqlite"}:
        raise ValueError("DB_TYPE must be set to 'mysql' (production) or 'sqlite' (dev/test).")

    if DB_TYPE == "mysql":
        required = {
            "MYSQL_HOST": os.getenv("MYSQL_HOST", ""),
            "MYSQL_DATABASE": os.getenv("MYSQL_DATABASE", ""),
            "MYSQL_USER": os.getenv("MYSQL_USER", ""),
            "MYSQL_PASSWORD": os.getenv("MYSQL_PASSWORD", ""),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(
                f"MySQL production configuration incomplete. Missing: {', '.join(missing)}"
            )

    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY must be set to a strong secret.")

    if JWT_SECRET_KEY == _JWT_DEFAULT_SECRET:
        if DB_TYPE == "mysql":
            raise ValueError("JWT_SECRET_KEY must be set to a strong secret for production.")
        import warnings

        warnings.warn(
            "JWT_SECRET_KEY is using the default value. Set a strong secret for production.",
            stacklevel=2,
        )

    if DB_TYPE == "mysql" and len(JWT_SECRET_KEY) < 32:
        raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production.")

    if CORS_ORIGINS == "*":
        raise ValueError(
            "CORS_ORIGINS cannot be '*'. Set allowed origins explicitly."
        )
