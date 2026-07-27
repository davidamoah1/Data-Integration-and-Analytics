"""Tests for production configuration validation."""

import os
from unittest import mock

import pytest

import config


class TestValidateConfig:
    """Validate fail-fast behavior for production-critical settings."""

    @pytest.fixture(autouse=True)
    def _reset_env(self, monkeypatch):
        """Ensure environment-dependent config values are stable for each test."""
        monkeypatch.setattr(config, "DB_TYPE", "sqlite")
        monkeypatch.setattr(config, "JWT_SECRET_KEY", "dummy-secret-for-tests")
        monkeypatch.setattr(config, "CORS_ORIGINS", "http://localhost:3000")

    def test_sqlite_config_is_allowed(self):
        config.validate_config()

    def test_invalid_db_type_raises(self, monkeypatch):
        monkeypatch.setattr(config, "DB_TYPE", "postgres")
        with pytest.raises(ValueError, match="DB_TYPE must be set to"):
            config.validate_config()

    def test_mysql_missing_variables_raises(self, monkeypatch):
        monkeypatch.setattr(config, "DB_TYPE", "mysql")
        with (
            mock.patch.dict(
                os.environ,
                {
                    "MYSQL_HOST": "",
                    "MYSQL_DATABASE": "",
                    "MYSQL_USER": "",
                    "MYSQL_PASSWORD": "",
                },
                clear=False,
            ),
            pytest.raises(ValueError, match="MySQL production configuration incomplete"),
        ):
            config.validate_config()

    def test_mysql_default_jwt_secret_raises(self, monkeypatch):
        monkeypatch.setattr(config, "DB_TYPE", "mysql")
        monkeypatch.setattr(config, "JWT_SECRET_KEY", config._JWT_DEFAULT_SECRET)
        with (
            mock.patch.dict(
                os.environ,
                {
                    "MYSQL_HOST": "localhost",
                    "MYSQL_DATABASE": "aedip",
                    "MYSQL_USER": "aedip_user",
                    "MYSQL_PASSWORD": "secret",
                },
                clear=False,
            ),
            pytest.raises(ValueError, match="JWT_SECRET_KEY must be set to a strong secret"),
        ):
            config.validate_config()

    def test_mysql_wildcard_cors_raises(self, monkeypatch):
        monkeypatch.setattr(config, "DB_TYPE", "mysql")
        monkeypatch.setattr(
            config, "JWT_SECRET_KEY", "a-very-strong-random-secret-min-32-characters-long"
        )
        monkeypatch.setattr(config, "CORS_ORIGINS", "*")
        with (
            mock.patch.dict(
                os.environ,
                {
                    "MYSQL_HOST": "localhost",
                    "MYSQL_DATABASE": "aedip",
                    "MYSQL_USER": "aedip_user",
                    "MYSQL_PASSWORD": "secret",
                },
                clear=False,
            ),
            pytest.raises(ValueError, match="CORS_ORIGINS cannot be"),
        ):
            config.validate_config()
