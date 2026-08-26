"""Tests for Sprint 6 enterprise hardening â€” security, resilience, observability."""

import os
import sys
import time

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DB_TYPE"] = "sqlite"
os.environ["SQLITE_DB_PATH"] = "test_enterprise.db"
os.environ["PYTEST_RUNNING"] = "1"


class TestSecurityHeaders:
    """Test security headers middleware."""

    def test_security_headers_present(self, client):
        """Security headers should be present on all responses."""
        response = client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


class TestHealthAndReadiness:
    """Test health, readiness, and metrics endpoints."""

    def test_health_endpoint(self, client):
        """Health endpoint should return status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database_connected" in data

    def test_ready_endpoint(self, client):
        """Readiness endpoint should check subsystems."""
        response = client.get("/ready")
        assert response.status_code in (200, 503)
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]

    def test_metrics_endpoint(self, client):
        """Metrics endpoint should return Prometheus-format text."""
        response = client.get("/api/monitoring/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")
        body = response.text
        assert len(body) > 0


class TestResilience:
    """Test retry and circuit breaker utilities."""

    def test_retry_succeeds_on_first_attempt(self):
        from shared.resilience import retry

        call_count = 0

        @retry(max_attempts=3, base_delay=0.01)
        def succeeding_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = succeeding_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_succeeds_after_failure(self):
        from shared.resilience import retry

        call_count = 0

        @retry(max_attempts=3, base_delay=0.01)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "recovered"

        result = flaky_func()
        assert result == "recovered"
        assert call_count == 2

    def test_retry_exhausts_attempts(self):
        from shared.resilience import retry

        @retry(max_attempts=2, base_delay=0.01)
        def always_failing():
            raise RuntimeError("Permanent failure")

        with pytest.raises(RuntimeError, match="Permanent failure"):
            always_failing()

    def test_circuit_breaker_opens_after_threshold(self):
        from shared.resilience import CircuitBreaker

        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0)

        def failing_func():
            raise ValueError("Service down")

        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(failing_func)

        assert breaker.state == "open"
        with pytest.raises(RuntimeError, match="Circuit breaker is OPEN"):
            breaker.call(failing_func)

    def test_circuit_breaker_resets_on_success(self):
        from shared.resilience import CircuitBreaker

        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=0.1)

        def succeeding_func():
            return "ok"

        result = breaker.call(succeeding_func)
        assert result == "ok"
        assert breaker.state == "closed"

    def test_circuit_breaker_half_open_recovery(self):
        from shared.resilience import CircuitBreaker

        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        call_count = 0

        def recovering_func():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError("Still down")
            return "recovered"

        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(recovering_func)

        assert breaker.state == "open"

        time.sleep(0.15)
        assert breaker.state == "half_open"

        result = breaker.call(recovering_func)
        assert result == "recovered"
        assert breaker.state == "closed"


class TestAPIKeyHardening:
    """Test API key security improvements."""

    def test_dev_api_key_works_in_non_production(self, client):
        """Dev API key should work when DB_TYPE is not mysql."""
        response = client.get("/health?api_key=dev-api-key-change-in-production")
        assert response.status_code == 200


class TestCORSSecurity:
    """Test CORS configuration."""

    def test_cors_headers_restricted(self, client):
        """CORS should not allow wildcard methods."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "TRACE",
            },
        )
        # TRACE should not be in allowed methods
        allow_methods = response.headers.get("Access-Control-Allow-Methods", "")
        if allow_methods:
            assert "TRACE" not in allow_methods.upper()
