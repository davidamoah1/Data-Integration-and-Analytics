import os
import tempfile

from dotenv import load_dotenv

load_dotenv()

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Application environment: development | testing | production
APP_ENV = os.getenv("APP_ENV", "development").lower()
IS_PRODUCTION = APP_ENV == "production"
IS_TESTING = APP_ENV == "testing"


def _resolve_path(path_str: str) -> str:
    """Resolve a path string relative to BASE_DIR if not absolute."""
    if os.path.isabs(path_str):
        return path_str
    return os.path.join(BASE_DIR, path_str)


# Data paths â€” production must set RAW_DATA_PATH explicitly (no default sample data)
RAW_DATA_PATH = _resolve_path(os.getenv("RAW_DATA_PATH", ""))
PROCESSED_DATA_PATH = _resolve_path(
    os.getenv("PROCESSED_DATA_PATH", "data/processed/cleaned_data.csv")
)

# Demo / onboarding datasets â€” opt-in only, never used in production automatically
DEMO_DATASETS_DIR = _resolve_path(os.getenv("DEMO_DATASETS_DIR", "demo_datasets"))
SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "false").lower() in ("true", "1", "yes")

# Serverless detection (Vercel or any platform where the filesystem is read-only
# and startup tasks are skipped). Render runs a persistent process, so this is
# False on Render unless explicitly set via DISABLE_STARTUP_TASKS.
IS_SERVERLESS = os.getenv("VERCEL", "").lower() in ("1", "true", "yes") or os.getenv(
    "DISABLE_STARTUP_TASKS", ""
).lower() in ("1", "true", "yes")

# Smart Data Capture â€” original + enhanced uploaded document storage
CAPTURE_STORAGE_DIR = _resolve_path(os.getenv("CAPTURE_STORAGE_DIR", "storage/capture"))
if IS_SERVERLESS and not os.path.isabs(os.getenv("CAPTURE_STORAGE_DIR", "")):
    CAPTURE_STORAGE_DIR = os.path.join(tempfile.gettempdir(), "capture")
CAPTURE_MAX_FILE_SIZE_MB = int(os.getenv("CAPTURE_MAX_FILE_SIZE_MB") or "25")
CAPTURE_LOW_CONFIDENCE_THRESHOLD = float(os.getenv("CAPTURE_LOW_CONFIDENCE_THRESHOLD") or "0.75")
CAPTURE_RETENTION_DAYS = int(os.getenv("CAPTURE_RETENTION_DAYS") or "365")
# Path to the Tesseract OCR binary. Leave unset to use the system PATH.
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")

# Smart Data Capture — maximum files per batch upload.
CAPTURE_MAX_BATCH_SIZE = int(os.getenv("CAPTURE_MAX_BATCH_SIZE") or "50")

# Certificate Intelligence — maximum files per normal batch upload.
# Large batches (500+) should use background processing.
CERTIFICATE_MAX_BATCH_SIZE = int(os.getenv("CERTIFICATE_MAX_BATCH_SIZE") or "50")

# Database
# DATABASE_URL takes precedence over individual MYSQL_* / SQLITE_* vars.
# Example: mysql+pymysql://user:pass@host:3306/dbname?charset=utf8mb4
DATABASE_URL = os.getenv("DATABASE_URL", "")
DB_TYPE = os.getenv("DB_TYPE", "").lower()

if DATABASE_URL:
    # Use the explicit connection URL â€” infer DB_TYPE from the scheme
    if DATABASE_URL.startswith("mysql"):
        DB_TYPE = "mysql"
    elif DATABASE_URL.startswith("sqlite"):
        DB_TYPE = "sqlite"
    DB_URL = DATABASE_URL
elif DB_TYPE == "mysql":
    from urllib.parse import quote_plus

    _mysql_host = os.getenv("MYSQL_HOST", "localhost")
    _mysql_port = os.getenv("MYSQL_PORT", "3306")
    _mysql_db = os.getenv("MYSQL_DATABASE", "")
    _mysql_user = os.getenv("MYSQL_USER", "")
    _mysql_pass = os.getenv("MYSQL_PASSWORD", "")
    _mysql_connect_timeout = os.getenv("MYSQL_CONNECT_TIMEOUT", "10")
    DB_URL = (
        f"mysql+pymysql://{quote_plus(_mysql_user)}:{quote_plus(_mysql_pass)}"
        f"@{_mysql_host}:{_mysql_port}/{quote_plus(_mysql_db)}"
        f"?charset=utf8mb4&connect_timeout={_mysql_connect_timeout}"
    )
elif DB_TYPE == "sqlite":
    _sqlite_path = _resolve_path(os.getenv("SQLITE_DB_PATH", "database/etl_database.db"))
    # Serverless platforms have a read-only filesystem; use tempfile for SQLite.
    if IS_SERVERLESS and not os.path.isabs(_sqlite_path):
        _sqlite_path = os.path.join(tempfile.gettempdir(), _sqlite_path)
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
    if IS_SERVERLESS and not os.path.isabs(_sqlite_path):
        _sqlite_path = os.path.join(tempfile.gettempdir(), _sqlite_path)
    DB_URL = f"sqlite:///{_sqlite_path}"

# --- Connection Pool Settings (MySQL) ---
POOL_SIZE = int(os.getenv("POOL_SIZE") or "10")
POOL_TIMEOUT = int(os.getenv("POOL_TIMEOUT") or "30")
POOL_RECYCLE = int(os.getenv("POOL_RECYCLE") or "3600")
MAX_OVERFLOW = int(os.getenv("MAX_OVERFLOW") or "20")

# --- Query Optimization ---
SLOW_QUERY_THRESHOLD_MS = int(os.getenv("SLOW_QUERY_THRESHOLD_MS") or "500")
QUERY_TIMEOUT_SECONDS = int(os.getenv("QUERY_TIMEOUT_SECONDS") or "30")
ENABLE_QUERY_LOGGING = os.getenv("ENABLE_QUERY_LOGGING", "false").lower() in ("true", "1", "yes")

# --- Backup Strategy ---
BACKUP_ENABLED = os.getenv("BACKUP_ENABLED", "false").lower() in ("true", "1", "yes")
BACKUP_SCHEDULE = os.getenv("BACKUP_SCHEDULE", "0 2 * * *")  # Daily at 2 AM
BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS") or "30")
BACKUP_STORAGE_PATH = _resolve_path(os.getenv("BACKUP_STORAGE_PATH", "backups"))
BACKUP_COMPRESS = os.getenv("BACKUP_COMPRESS", "true").lower() in ("true", "1", "yes")

# --- Redis / Performance (Phase 10) ---
REDIS_URL = os.getenv("REDIS_URL", "")
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_DEFAULT_TTL = int(os.getenv("CACHE_DEFAULT_TTL") or "300")
CACHE_KEY_PREFIX = os.getenv("CACHE_KEY_PREFIX", "aedip")

# --- File Storage (Phase 12) ---
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local").lower()  # local | r2 | s3 | supabase
STORAGE_LOCAL_DIR = _resolve_path(os.getenv("STORAGE_LOCAL_DIR", "storage/files"))
STORAGE_PUBLIC_URL = os.getenv("STORAGE_PUBLIC_URL", "")

# Cloudflare R2
R2_BUCKET = os.getenv("R2_BUCKET", "")
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID", "")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY", "")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY", "")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "")

# AWS S3
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
S3_PUBLIC_URL = os.getenv("S3_PUBLIC_URL", "")

# Supabase Storage
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "files")
SUPABASE_STORAGE_PUBLIC_URL = os.getenv("SUPABASE_STORAGE_PUBLIC_URL", "")

# Background workers
WORKER_MIN_WORKERS = int(os.getenv("WORKER_MIN_WORKERS") or "2")
WORKER_MAX_WORKERS = int(os.getenv("WORKER_MAX_WORKERS") or "20")
WORKER_SCALE_UP_THRESHOLD = int(os.getenv("WORKER_SCALE_UP_THRESHOLD") or "10")
WORKER_SCALE_DOWN_THRESHOLD = int(os.getenv("WORKER_SCALE_DOWN_THRESHOLD") or "2")
WORKER_SCALE_CHECK_INTERVAL = int(os.getenv("WORKER_SCALE_CHECK_INTERVAL") or "30")

# Chunked query default size
CHUNK_SIZE_DEFAULT = int(os.getenv("CHUNK_SIZE_DEFAULT") or "5000")

# Logging
LOG_PATH = _resolve_path(os.getenv("LOG_PATH", "logs/pipeline.log"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# --- Monitoring (Phase 18) ---
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE") or "0.1")
SENTRY_PROFILES_SAMPLE_RATE = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE") or "0.1")
SENTRY_RELEASE = os.getenv("SENTRY_RELEASE", "aedip@1.0.0")

OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
OTEL_SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "aedip-api")
OTEL_SERVICE_VERSION = os.getenv("OTEL_SERVICE_VERSION", "1.0.0")
OTEL_METRIC_EXPORT_INTERVAL = int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL") or "60000")

PROMETHEUS_ENABLED = os.getenv("PROMETHEUS_ENABLED", "true").lower() in ("true", "1", "yes")
MONITORING_ENABLED = os.getenv("MONITORING_ENABLED", "true").lower() in ("true", "1", "yes")

# Schedule (24-hour format)
PIPELINE_RUN_TIME = os.getenv("PIPELINE_RUN_TIME", "08:00")

# --- Security / JWT ---
_JWT_DEFAULT_SECRET = "change-this-to-a-strong-random-secret-min-32-chars"
_jwt_env = os.getenv("JWT_SECRET_KEY", "")
if _jwt_env:
    JWT_SECRET_KEY = _jwt_env
elif DB_TYPE == "mysql" or IS_PRODUCTION:
    # Production must set JWT_SECRET_KEY explicitly â€” do not provide a fallback
    JWT_SECRET_KEY = ""
else:
    # Dev/test only: generate a random ephemeral secret so no known default is used
    import secrets as _secrets

    JWT_SECRET_KEY = _secrets.token_urlsafe(48)
    del _secrets
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES") or "30")
JWT_REFRESH_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS") or "7")

# --- Encryption Key (separate from JWT for Fernet encryption of API keys, etc.) ---
# Derives from JWT_SECRET_KEY only as a fallback for dev. Production must set ENCRYPTION_KEY explicitly.
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

# --- MFA Configuration (future-ready) ---
MFA_ENABLED = os.getenv("MFA_ENABLED", "false").lower() in ("true", "1", "yes")
MFA_ISSUER = os.getenv("MFA_ISSUER", "DataFlow")
MFA_TOTP_ISSUER = os.getenv("MFA_TOTP_ISSUER", MFA_ISSUER)

# --- SSO Configuration (future-ready) ---
SSO_ENABLED = os.getenv("SSO_ENABLED", "false").lower() in ("true", "1", "yes")
SSO_GOOGLE_CLIENT_ID = os.getenv("SSO_GOOGLE_CLIENT_ID", "")
SSO_GOOGLE_CLIENT_SECRET = os.getenv("SSO_GOOGLE_CLIENT_SECRET", "")
SSO_MICROSOFT_CLIENT_ID = os.getenv("SSO_MICROSOFT_CLIENT_ID", "")
SSO_MICROSOFT_CLIENT_SECRET = os.getenv("SSO_MICROSOFT_CLIENT_SECRET", "")
SSO_SAML_ENTITY_ID = os.getenv("SSO_SAML_ENTITY_ID", "")
SSO_SAML_ACS_URL = os.getenv("SSO_SAML_ACS_URL", "")

# --- Password Policy ---
PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH") or "8")
PASSWORD_REQUIRE_UPPERCASE = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"
PASSWORD_REQUIRE_LOWERCASE = os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true"
PASSWORD_REQUIRE_DIGIT = os.getenv("PASSWORD_REQUIRE_DIGIT", "true").lower() == "true"
PASSWORD_REQUIRE_SPECIAL = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"
PASSWORD_HISTORY_COUNT = int(os.getenv("PASSWORD_HISTORY_COUNT") or "5")

# --- Account Lockout ---
ACCOUNT_LOCKOUT_THRESHOLD = int(os.getenv("ACCOUNT_LOCKOUT_THRESHOLD") or "5")
ACCOUNT_LOCKOUT_DURATION_MINUTES = int(os.getenv("ACCOUNT_LOCKOUT_DURATION_MINUTES") or "30")

# --- CORS ---
# Development defaults to localhost origins. In production set CORS_ORIGINS
# explicitly (comma-separated) to your actual frontend domain(s).
_cors_env = os.getenv("CORS_ORIGINS", "")
if _cors_env:
    CORS_ORIGINS = _cors_env
elif DB_TYPE == "mysql" or IS_PRODUCTION:
    # Production without explicit CORS_ORIGINS is likely a
    # misconfiguration â€” default to empty so no cross-origin requests are
    # allowed until the deployer configures it deliberately.
    import warnings as _w

    _w.warn(
        "CORS_ORIGINS is not set in a production environment. "
        "Cross-origin requests will be rejected. Set CORS_ORIGINS to your "
        "frontend domain(s), e.g. 'https://app.example.com'.",
        stacklevel=1,
    )
    CORS_ORIGINS = ""
else:
    CORS_ORIGINS = "http://localhost:8501,http://localhost:3000"

# --- AI Platform (Phase 6) ---
AI_DEFAULT_PROVIDER = os.getenv("AI_DEFAULT_PROVIDER", "openai")
AI_DEFAULT_MODEL = os.getenv("AI_DEFAULT_MODEL", "gpt-4o-mini")
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS") or "4096")
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE") or "0.7")
AI_REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT") or "60")

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
AI_MEMORY_MAX_MESSAGES = int(os.getenv("AI_MEMORY_MAX_MESSAGES") or "20")
AI_CACHE_ENABLED = os.getenv("AI_CACHE_ENABLED", "true").lower() == "true"
AI_CACHE_TTL_SECONDS = int(os.getenv("AI_CACHE_TTL_SECONDS") or "3600")

# AI Security
AI_ENFORCE_PERMISSIONS = os.getenv("AI_ENFORCE_PERMISSIONS", "true").lower() == "true"
AI_MAX_INPUT_LENGTH = int(os.getenv("AI_MAX_INPUT_LENGTH") or "10000")
AI_DATA_RETENTION_DAYS = int(os.getenv("AI_DATA_RETENTION_DAYS") or "90")

# AI Usage Limits
AI_DAILY_TOKEN_LIMIT = int(os.getenv("AI_DAILY_TOKEN_LIMIT") or "1000000")
AI_MONTHLY_COST_LIMIT_USD = float(os.getenv("AI_MONTHLY_COST_LIMIT_USD") or "100.0")

# AI Document Chat
AI_DOC_MAX_SIZE_MB = int(os.getenv("AI_DOC_MAX_SIZE_MB") or "20")
AI_DOC_ALLOWED_TYPES = os.getenv("AI_DOC_ALLOWED_TYPES", "pdf,docx,xlsx,csv,pptx,txt").split(",")

# AI Forecasting
AI_FORECAST_CONFIDENCE_LEVEL = float(os.getenv("AI_FORECAST_CONFIDENCE_LEVEL") or "0.95")
AI_FORECAST_MAX_HORIZON = int(os.getenv("AI_FORECAST_MAX_HORIZON") or "365")

# AI Anomaly Detection
AI_ANOMALY_SENSITIVITY = float(os.getenv("AI_ANOMALY_SENSITIVITY") or "2.0")
AI_ANOMALY_MIN_DATA_POINTS = int(os.getenv("AI_ANOMALY_MIN_DATA_POINTS") or "10")


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

    if DB_TYPE == "mysql" and not DATABASE_URL:
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
        if DB_TYPE == "mysql" or IS_PRODUCTION:
            raise ValueError("JWT_SECRET_KEY must be set to a strong secret for production.")
        import warnings

        warnings.warn(
            "JWT_SECRET_KEY is using the default value. Set a strong secret for production.",
            stacklevel=2,
        )

    if (DB_TYPE == "mysql" or IS_PRODUCTION) and len(JWT_SECRET_KEY) < 32:
        raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production.")

    # ENCRYPTION_KEY should be separate from JWT_SECRET_KEY in production
    if (DB_TYPE == "mysql" or IS_PRODUCTION) and not ENCRYPTION_KEY:
        import warnings

        warnings.warn(
            "ENCRYPTION_KEY is not set. Falling back to JWT_SECRET_KEY derivation. "
            "Set a separate ENCRYPTION_KEY for production.",
            stacklevel=2,
        )

    if CORS_ORIGINS == "*":
        raise ValueError("CORS_ORIGINS cannot be '*'. Set allowed origins explicitly.")

    # Production-specific hardening
    if IS_PRODUCTION:
        if DB_TYPE == "sqlite":
            raise ValueError(
                "SQLite is not permitted in production. Set DB_TYPE=mysql for production deployments."
            )
        if not ENCRYPTION_KEY:
            raise ValueError(
                "ENCRYPTION_KEY must be set explicitly for production (separate from JWT_SECRET_KEY)."
            )
        if STORAGE_BACKEND == "local" and os.getenv(
            "ALLOW_LOCAL_STORAGE_IN_PRODUCTION", ""
        ).lower() not in ("1", "true", "yes"):
            raise ValueError(
                "STORAGE_BACKEND=local is not permitted in production. "
                "Set STORAGE_BACKEND to 'r2', 's3', or 'supabase' and configure the "
                "corresponding credentials. Set ALLOW_LOCAL_STORAGE_IN_PRODUCTION=1 "
                "only if you have a documented reason for local storage."
            )

        if BACKUP_ENABLED and not os.path.isabs(os.getenv("BACKUP_STORAGE_PATH", "")):
            import warnings

            warnings.warn(
                "BACKUP_STORAGE_PATH should be an absolute path in production.",
                stacklevel=2,
            )


# Workflow execution settings
ALLOW_WORKFLOW_CODE_EXEC = os.getenv("ALLOW_WORKFLOW_CODE_EXEC", "").lower() in (
    "1",
    "true",
    "yes",
)
