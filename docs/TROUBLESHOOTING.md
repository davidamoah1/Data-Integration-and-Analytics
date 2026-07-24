# AEDIP Troubleshooting Guide

## Common Issues and Solutions

### 1. Dashboard Won't Load

**Symptom**: Dashboard page is blank or shows "Connection error"

**Solutions**:
- Verify the API is running: `curl http://localhost:8000/health`
- Check that `CORS_ORIGINS` in `.env` includes the dashboard URL
- Ensure the API and dashboard are on the same network (Docker Compose handles this)
- Check browser console for CORS errors
- Verify `API_BASE_URL` in the dashboard configuration points to the correct API host

### 2. Login Failed

**Symptom**: "Invalid credentials" or "Account locked"

**Solutions**:
- Verify email and password (demo credentials are in the Quick Start Guide)
- Check if the account is locked (5 failed attempts locks for 30 minutes)
- Ensure the user is active (`is_active = 1` in the database)
- Verify `JWT_SECRET_KEY` is set and consistent between API restarts
- Check that the database is accessible

### 3. Database Connection Error

**Symptom**: API returns 500 or health check shows "unhealthy"

**Solutions**:
- Verify `DB_TYPE` is set to `sqlite` or `mysql` in `.env`
- For MySQL: check `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`
- For SQLite: ensure the directory exists and is writable
- Test connection: `python -c "from shared.database import get_engine; print(get_engine())"`
- If using Docker, ensure the database container is healthy: `docker-compose ps`

### 4. Data Upload Fails

**Symptom**: "Error processing file" or file not accepted

**Solutions**:
- Check file format: only CSV, XLSX, and XLS are supported
- Verify file size is within your plan's upload limit (50MB for trial)
- Ensure the file has headers in the first row
- Check for encoding issues (UTF-8 recommended)
- Try saving as CSV and re-uploading
- Check API logs for detailed error messages

### 5. Charts Not Displaying

**Symptom**: KPI cards show but charts are blank

**Solutions**:
- Ensure your data has the required columns (sales, profit, date, region, category)
- Check that numeric columns don't contain text values
- Verify the selected industry pack matches your data columns
- Try switching to "Upload File" and uploading a sample dataset
- Check browser console for JavaScript errors

### 6. AI Copilot Not Responding

**Symptom**: AI Copilot returns errors or no response

**Solutions**:
- Verify `AI_DEFAULT_PROVIDER` and API keys are set in `.env`
- Check that the AI provider service is accessible from the server
- Verify your subscription includes AI Copilot feature
- Check API logs for AI-related errors
- Ensure you haven't exceeded your monthly AI query limit
- If using OpenAI, verify your API key is valid and has credits

### 7. ETL Pipeline Fails

**Symptom**: Pipeline status shows "failed"

**Solutions**:
- Check the pipeline logs in `logs/pipeline.log`
- Verify the data source is accessible (file path, database connection, API endpoint)
- Ensure the data format matches the pipeline's expected schema
- Check for insufficient disk space
- Verify file permissions for output paths
- Review transformation rules for errors

### 8. Trial Expired

**Symptom**: Features are locked, "Trial expired" message

**Solutions**:
- Upgrade to a paid plan via Administration → Organization → Subscription
- Or use the API: `POST /platform/subscription/upgrade?plan=starter`
- Contact your admin to upgrade
- Trial lasts 14 days from organization creation

### 9. Docker Compose Issues

**Symptom**: Services won't start or are unhealthy

**Solutions**:
- Check logs: `docker-compose logs api` or `docker-compose logs dashboard`
- Rebuild images: `docker-compose up -d --build`
- Clear volumes: `docker-compose down -v` (WARNING: deletes data)
- Ensure ports 8000 and 8501 are not in use
- Verify Docker has enough memory allocated (minimum 2GB)

### 10. Performance Issues

**Symptom**: Dashboard is slow, API responses are delayed

**Solutions**:
- Check system resources via Support → Diagnostics
- Ensure the database has proper indexes (run `alembic upgrade head`)
- Reduce the data size by applying filters
- Check for long-running ETL pipelines
- Verify rate limiting isn't too aggressive (`RATE_LIMIT_RPM`)
- Consider upgrading to a higher subscription plan for increased limits

## Diagnostic Commands

```bash
# Check API health
curl http://localhost:8000/health

# Check API readiness
curl http://localhost:8000/ready

# View API logs (Docker)
docker-compose logs -f api

# View dashboard logs (Docker)
docker-compose logs -f dashboard

# Run health check script
python monitoring/health_check.py

# Check database connection
python -c "from shared.database import get_engine; e = get_engine(); print(e.url)"

# Run tests
DB_TYPE=sqlite PYTEST_RUNNING=1 JWT_SECRET_KEY=test-secret python -m pytest tests/ -q
```

## Log Locations

| Log | Location | Description |
|-----|----------|-------------|
| API logs | Docker stdout | `docker-compose logs api` |
| Dashboard logs | Docker stdout | `docker-compose logs dashboard` |
| Pipeline logs | `logs/pipeline.log` | ETL pipeline execution |
| Application logs | `logs/` | General application logs |

## Getting Help

1. **Support Page**: Use the in-app Support page to submit tickets
2. **Documentation**: Check the `docs/` folder for detailed guides
3. **API Docs**: Visit `http://localhost:8000/docs` for interactive Swagger docs
4. **System Diagnostics**: Navigate to Support → Diagnostics for real-time system health
5. **Observability**: Admin users can view system metrics at the Observability page
