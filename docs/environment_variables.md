# Environment Variables Reference

This document lists every environment variable used by the DataFlow backend and frontend, whether it is required, its default value, and its purpose.

## Frontend

| Variable | Required | Default | Used By | Purpose |
|----------|----------|---------|---------|---------|
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | `frontend/services/api/client.ts` | Base URL for backend API calls. On Vercel this should be `/api` so requests are routed to the Python function. |
| `NEXT_PUBLIC_APP_NAME` | No | `DataFlow` | `frontend/next.config.js` | Display name used in UI metadata. |

## Core / Database

| Variable | Required | Default | Used By | Purpose |
|----------|----------|---------|---------|---------|
| `DB_TYPE` | **Production: Yes** | `sqlite` | `config.py`, `shared/database.py` | Database driver: `mysql` or `sqlite`. Defaults to SQLite for dev/serverless cold starts. |
| `MYSQL_HOST` | If `DB_TYPE=mysql` | `localhost` | `config.py`, `shared/database.py` | MySQL host. |
| `MYSQL_PORT` | If `DB_TYPE=mysql` | `3306` | `config.py` | MySQL port. |
| `MYSQL_DATABASE` | If `DB_TYPE=mysql` | *(empty)* | `config.py` | MySQL database name. |
| `MYSQL_USER` | If `DB_TYPE=mysql` | *(empty)* | `config.py` | MySQL username. |
| `MYSQL_PASSWORD` | If `DB_TYPE=mysql` | *(empty)* | `config.py` | MySQL password. |
| `SQLITE_DB_PATH` | No | `database/etl_database.db` | `config.py` | SQLite database file path. |
| `POOL_SIZE` | No | `10` | `shared/database.py` | SQLAlchemy connection pool size. |
| `POOL_TIMEOUT` | No | `30` | `shared/database.py` | Pool checkout timeout. |
| `POOL_RECYCLE` | No | `3600` | `shared/database.py` | Connection recycle time. |
| `MAX_OVERFLOW` | No | `20` | `shared/database.py` | Max overflow connections. |

## Security / Auth

| Variable | Required | Default | Used By | Purpose |
|----------|----------|---------|---------|---------|
| `JWT_SECRET_KEY` | **Production: Yes** | `change-this-to-a-strong-random-secret-min-32-chars` | `shared/security.py`, `config.py` | Signing key for JWT tokens. Must be >= 32 chars in production. |
| `JWT_ALGORITHM` | No | `HS256` | `shared/security.py` | JWT algorithm. |
| `JWT_ACCESS_EXPIRE_MINUTES` | No | `30` | `shared/security.py` | Access token TTL. |
| `JWT_REFRESH_EXPIRE_DAYS` | No | `7` | `shared/security.py` | Refresh token TTL. |
| `SUPER_ADMIN_EMAIL` | No | `admin@dataflow.io` | `authentication/services.py` | Default admin email created at startup. |
| `SUPER_ADMIN_PASSWORD` | No | *(empty)* | `authentication/services.py` | Default admin password. If empty, no default admin is created. |
| `PASSWORD_MIN_LENGTH` | No | `8` | `shared/security.py` | Minimum password length. |
| `PASSWORD_REQUIRE_UPPERCASE` | No | `true` | `shared/security.py` | Enforce uppercase letters. |
| `PASSWORD_REQUIRE_LOWERCASE` | No | `true` | `shared/security.py` | Enforce lowercase letters. |
| `PASSWORD_REQUIRE_DIGIT` | No | `true` | `shared/security.py` | Enforce digits. |
| `PASSWORD_REQUIRE_SPECIAL` | No | `true` | `shared/security.py` | Enforce special characters. |
| `PASSWORD_HISTORY_COUNT` | No | `5` | `shared/security.py` | Number of previous passwords to remember. |
| `ACCOUNT_LOCKOUT_THRESHOLD` | No | `5` | `shared/security.py` | Failed login attempts before lockout. |
| `ACCOUNT_LOCKOUT_DURATION_MINUTES` | No | `30` | `shared/security.py` | Lockout duration. |
| `CORS_ORIGINS` | No | `http://localhost:8501,http://localhost:3000` | `api/main.py` | Allowed CORS origins. Cannot be `*`. |
| `RATE_LIMIT_RPM` | No | `120` | `shared/middleware.py` | Requests per minute per IP. |

## Deployment / Runtime

| Variable | Required | Default | Used By | Purpose |
|----------|----------|---------|---------|---------|
| `VERCEL` | No | *(empty)* | `api/main.py`, `api/index.py` | When `1`/`true`, enables serverless-safe mode (skips heavy startup). |
| `DISABLE_STARTUP_TASKS` | No | *(empty)* | `api/main.py` | When `1`/`true`, skips DB migrations/seeding/scheduler startup. |
| `DISABLE_CONFIG_VALIDATION` | No | *(empty)* | `config.py` | When `1`/`true`, skips strict config validation at startup. |
| `PYTEST_RUNNING` | No | *(empty)* | `api/main.py`, `scheduler/report_scheduler.py` | Disables rate limiting and scheduler when running tests. |
| `LOG_PATH` | No | `logs/pipeline.log` | `etl/logging_config.py` | Log file path. Leave empty for stdout-only logging. |
| `LOG_LEVEL` | No | `INFO` | `etl/logging_config.py` | Logging level. |
| `LOG_FORMAT` | No | `text` | `etl/logging_config.py` | `text` or `json` structured logs. |
| `PIPELINE_RUN_TIME` | No | `08:00` | Scheduler | Daily pipeline run time. |

## AI Platform

| Variable | Required | Default | Used By | Purpose |
|----------|----------|---------|---------|---------|
| `AI_DEFAULT_PROVIDER` | No | `openai` | `ai/gateway.py` | Default AI provider. |
| `AI_DEFAULT_MODEL` | No | `gpt-4o-mini` | `ai/gateway.py` | Default AI model. |
| `AI_MAX_TOKENS` | No | `4096` | `ai/gateway.py` | Max tokens per request. |
| `AI_TEMPERATURE` | No | `0.7` | `ai/gateway.py` | Default model temperature. |
| `AI_REQUEST_TIMEOUT` | No | `60` | `ai/gateway.py` | AI provider request timeout. |
| `OPENAI_API_KEY` | If using OpenAI | *(empty)* | `ai/providers/manager.py` | OpenAI API key. |
| `GEMINI_API_KEY` | If using Gemini | *(empty)* | `ai/providers/manager.py` | Google Gemini API key. |
| `DEEPSEEK_API_KEY` | If using DeepSeek | *(empty)* | `ai/providers/manager.py` | DeepSeek API key. |
| `GLM_API_KEY` | If using GLM | *(empty)* | `ai/providers/manager.py` | GLM API key. |
| `CLAUDE_API_KEY` | If using Claude | *(empty)* | `ai/providers/manager.py` | Anthropic Claude API key. |
| `LOCAL_LLM_BASE_URL` | No | `http://localhost:11434/v1` | `ai/providers/manager.py` | Local LLM endpoint (e.g., Ollama). |
| `AI_MEMORY_MAX_MESSAGES` | No | `20` | `ai/memory.py` | Max conversation history messages. |
| `AI_CACHE_ENABLED` | No | `true` | `ai/cache.py` | Enable AI response caching. |
| `AI_CACHE_TTL_SECONDS` | No | `3600` | `ai/cache.py` | AI cache TTL. |
| `AI_ENFORCE_PERMISSIONS` | No | `true` | `ai/security.py` | Enforce RBAC on AI endpoints. |
| `AI_MAX_INPUT_LENGTH` | No | `10000` | `ai/security.py` | Max user input length. |
| `AI_DATA_RETENTION_DAYS` | No | `90` | `ai/models.py` | AI data retention. |
| `AI_DAILY_TOKEN_LIMIT` | No | `1000000` | `ai/usage.py` | Daily token budget. |
| `AI_MONTHLY_COST_LIMIT_USD` | No | `100.0` | `ai/usage.py` | Monthly cost budget. |
| `AI_DOC_MAX_SIZE_MB` | No | `20` | `ai/engines/document_chat.py` | Max upload size for document chat. |
| `AI_DOC_ALLOWED_TYPES` | No | `pdf,docx,xlsx,csv,pptx,txt` | `ai/engines/document_chat.py` | Allowed document types. |
| `AI_FORECAST_CONFIDENCE_LEVEL` | No | `0.95` | `ai/engines/enterprise_forecast.py` | Forecast confidence interval. |
| `AI_FORECAST_MAX_HORIZON` | No | `365` | `ai/engines/enterprise_forecast.py` | Max forecast horizon. |
| `AI_ANOMALY_SENSITIVITY` | No | `2.0` | `ai/engines/enterprise_anomaly.py` | Anomaly detection z-score threshold. |
| `AI_ANOMALY_MIN_DATA_POINTS` | No | `10` | `ai/engines/enterprise_anomaly.py` | Minimum data points for anomaly detection. |

## Cache / Workers

| Variable | Required | Default | Used By | Purpose |
|----------|----------|---------|---------|---------|
| `REDIS_URL` | No | *(empty)* | `performance/cache.py`, `performance/worker_entry.py` | Redis connection string. |
| `CACHE_ENABLED` | No | `true` | `performance/cache.py` | Enable caching. |
| `CACHE_DEFAULT_TTL` | No | `300` | `performance/cache.py` | Default cache TTL. |
| `CACHE_KEY_PREFIX` | No | `aedip` | `performance/cache.py` | Cache key prefix. |
| `WORKER_MIN_WORKERS` | No | `2` | `performance/worker_entry.py` | Min worker pool size. |
| `WORKER_MAX_WORKERS` | No | `20` | `performance/worker_entry.py` | Max worker pool size. |
| `WORKER_SCALE_UP_THRESHOLD` | No | `10` | `performance/worker_entry.py` | Scale-up threshold. |
| `WORKER_SCALE_DOWN_THRESHOLD` | No | `2` | `performance/worker_entry.py` | Scale-down threshold. |
| `WORKER_SCALE_CHECK_INTERVAL` | No | `30` | `performance/worker_entry.py` | Autoscale check interval. |
| `CHUNK_SIZE_DEFAULT` | No | `5000` | Database queries | Default query chunk size. |

## Notifications

| Variable | Required | Default | Used By | Purpose |
|----------|----------|---------|---------|---------|
| `SMTP_HOST` | No | *(empty)* | `notifications/service.py` | SMTP server host. |
| `SMTP_PORT` | No | `587` | `notifications/service.py` | SMTP server port. |
| `SMTP_USER` | No | *(empty)* | `notifications/service.py` | SMTP username. |
| `SMTP_PASSWORD` | No | *(empty)* | `notifications/service.py` | SMTP password. |
| `SMTP_FROM` | No | `noreply@dataflow.io` | `notifications/service.py` | Default sender address. |
| `SMS_PROVIDER` | No | *(empty)* | `monitoring/health_check.py` | SMS provider. |
| `TWILIO_SID` | No | *(empty)* | `monitoring/health_check.py` | Twilio SID. |
| `WHATSAPP_PROVIDER` | No | *(empty)* | `monitoring/health_check.py` | WhatsApp provider. |
| `WHATSAPP_BUSINESS_ID` | No | *(empty)* | `monitoring/health_check.py` | WhatsApp Business ID. |
| `PUSH_PROVIDER` | No | *(empty)* | `monitoring/health_check.py` | Push provider. |
| `FIREBASE_CREDENTIALS` | No | *(empty)* | `monitoring/health_check.py` | Firebase service account JSON. |
| `FIREBASE_CREDENTIALS_PATH` | No | *(empty)* | `monitoring/health_check.py` | Path to Firebase credentials file. |

## Data / Backups

| Variable | Required | Default | Used By | Purpose |
|----------|----------|---------|---------|---------|
| `RAW_DATA_PATH` | No | *(empty)* | `config.py` | Path to raw input data. |
| `PROCESSED_DATA_PATH` | No | `data/processed/cleaned_data.csv` | `config.py` | Path for processed data. |
| `DEMO_DATASETS_DIR` | No | `demo_datasets` | `config.py` | Demo datasets directory. |
| `SEED_DEMO_DATA` | No | `false` | `config.py`, `api/main.py` | Enable demo data seeding. |
| `BACKUP_PATH` | No | `backups` | `services/backup_service.py` | Backup directory. |

## Minimum Vercel Environment

For a successful Vercel deployment, set at minimum:

```env
DB_TYPE=mysql
MYSQL_HOST=<hostinger-host>
MYSQL_PORT=3306
MYSQL_DATABASE=<db-name>
MYSQL_USER=<db-user>
MYSQL_PASSWORD=<db-password>
JWT_SECRET_KEY=<64-char-random-string>
NEXT_PUBLIC_API_URL=/api
CORS_ORIGINS=https://<your-vercel-domain>,https://<your-custom-domain>
```

Optional but recommended:

```env
SUPER_ADMIN_EMAIL=admin@dataflow.io
SUPER_ADMIN_PASSWORD=<strong-password>
LOG_FORMAT=json
LOG_PATH=
DISABLE_STARTUP_TASKS=false
```
