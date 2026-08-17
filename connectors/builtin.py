"""Built-in connector implementations.

Connectors for:
  - Databases: PostgreSQL, MySQL, SQL Server, Oracle, MongoDB
  - Files: CSV, Excel, JSON, XML, Parquet
  - Cloud Storage: Amazon S3, Google Drive, OneDrive, Dropbox
  - APIs: REST API, GraphQL API, Webhooks
  - Africa-first: Mobile Money, Bank API, Government Open Data
"""

from __future__ import annotations

import io
import json
import logging
from typing import Any, ClassVar

import pandas as pd

from connectors.base import BaseConnector, ConnectorRegistry

logger = logging.getLogger("etl_project.connectors")


# ═══════════════════════════════════════════════════════════════
# Database Connectors
# ═══════════════════════════════════════════════════════════════


@ConnectorRegistry.register
class PostgreSQLConnector(BaseConnector):
    type_code: ClassVar[str] = "postgresql"
    display_name: ClassVar[str] = "PostgreSQL"
    category: ClassVar[str] = "database"
    description: ClassVar[str] = "Connect to PostgreSQL databases"
    icon: ClassVar[str] = "database"
    config_schema: ClassVar[dict] = {
        "fields": [
            {"name": "host", "type": "string", "required": True},
            {"name": "port", "type": "integer", "required": True, "default": 5432},
            {"name": "database", "type": "string", "required": True},
            {"name": "schema", "type": "string", "required": False, "default": "public"},
        ]
    }
    auth_schema: ClassVar[dict] = {
        "fields": [
            {"name": "username", "type": "string", "required": True},
            {"name": "password", "type": "password", "required": True},
        ]
    }

    def test_connection(self) -> dict[str, Any]:
        try:
            import sqlalchemy as sa

            host = self.configuration.get("host", "localhost")
            port = self.configuration.get("port", 5432)
            db = self.configuration.get("database", "")
            user = self.auth_config.get("username", "")
            pwd = self.auth_config.get("password", "")
            url = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"
            engine = sa.create_engine(url)
            with engine.connect() as conn:
                conn.execute(sa.text("SELECT 1"))
            return {"success": True, "message": "Connection successful"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        import sqlalchemy as sa

        host = self.configuration.get("host", "localhost")
        port = self.configuration.get("port", 5432)
        db = self.configuration.get("database", "")
        user = self.auth_config.get("username", "")
        pwd = self.auth_config.get("password", "")
        url = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"
        engine = sa.create_engine(url)
        sql = (query or {}).get("sql", "SELECT * FROM information_schema.tables LIMIT 10")
        return pd.read_sql(sql, engine)


@ConnectorRegistry.register
class MySQLConnector(BaseConnector):
    type_code: ClassVar[str] = "mysql"
    display_name: ClassVar[str] = "MySQL"
    category: ClassVar[str] = "database"
    description: ClassVar[str] = "Connect to MySQL databases"
    icon: ClassVar[str] = "database"
    config_schema: ClassVar[dict] = {
        "fields": [
            {"name": "host", "type": "string", "required": True},
            {"name": "port", "type": "integer", "required": True, "default": 3306},
            {"name": "database", "type": "string", "required": True},
        ]
    }
    auth_schema: ClassVar[dict] = {
        "fields": [
            {"name": "username", "type": "string", "required": True},
            {"name": "password", "type": "password", "required": True},
        ]
    }

    def test_connection(self) -> dict[str, Any]:
        try:
            import sqlalchemy as sa

            host = self.configuration.get("host", "localhost")
            port = self.configuration.get("port", 3306)
            db = self.configuration.get("database", "")
            user = self.auth_config.get("username", "")
            pwd = self.auth_config.get("password", "")
            url = f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}"
            engine = sa.create_engine(url)
            with engine.connect() as conn:
                conn.execute(sa.text("SELECT 1"))
            return {"success": True, "message": "Connection successful"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        import sqlalchemy as sa

        host = self.configuration.get("host", "localhost")
        port = self.configuration.get("port", 3306)
        db = self.configuration.get("database", "")
        user = self.auth_config.get("username", "")
        pwd = self.auth_config.get("password", "")
        url = f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}"
        engine = sa.create_engine(url)
        sql = (query or {}).get("sql", "SELECT * FROM information_schema.tables LIMIT 10")
        return pd.read_sql(sql, engine)


@ConnectorRegistry.register
class SQLServerConnector(BaseConnector):
    type_code: ClassVar[str] = "sqlserver"
    display_name: ClassVar[str] = "SQL Server"
    category: ClassVar[str] = "database"
    description: ClassVar[str] = "Connect to Microsoft SQL Server databases"
    icon: ClassVar[str] = "database"
    config_schema: ClassVar[dict] = {
        "fields": [
            {"name": "host", "type": "string", "required": True},
            {"name": "port", "type": "integer", "required": True, "default": 1433},
            {"name": "database", "type": "string", "required": True},
        ]
    }
    auth_schema: ClassVar[dict] = {
        "fields": [
            {"name": "username", "type": "string", "required": True},
            {"name": "password", "type": "password", "required": True},
        ]
    }

    def test_connection(self) -> dict[str, Any]:
        try:
            import sqlalchemy as sa

            host = self.configuration.get("host", "localhost")
            port = self.configuration.get("port", 1433)
            db = self.configuration.get("database", "")
            user = self.auth_config.get("username", "")
            pwd = self.auth_config.get("password", "")
            url = f"mssql+pyodbc://{user}:{pwd}@{host}:{port}/{db}?driver=ODBC+Driver+17+for+SQL+Server"
            engine = sa.create_engine(url)
            with engine.connect() as conn:
                conn.execute(sa.text("SELECT 1"))
            return {"success": True, "message": "Connection successful"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        import sqlalchemy as sa

        host = self.configuration.get("host", "localhost")
        port = self.configuration.get("port", 1433)
        db = self.configuration.get("database", "")
        user = self.auth_config.get("username", "")
        pwd = self.auth_config.get("password", "")
        url = f"mssql+pyodbc://{user}:{pwd}@{host}:{port}/{db}?driver=ODBC+Driver+17+for+SQL+Server"
        engine = sa.create_engine(url)
        sql = (query or {}).get("sql", "SELECT TOP 10 * FROM sys.tables")
        return pd.read_sql(sql, engine)


@ConnectorRegistry.register
class OracleConnector(BaseConnector):
    type_code: ClassVar[str] = "oracle"
    display_name: ClassVar[str] = "Oracle"
    category: ClassVar[str] = "database"
    description: ClassVar[str] = "Connect to Oracle databases"
    icon: ClassVar[str] = "database"

    def test_connection(self) -> dict[str, Any]:
        return {"success": False, "message": "Oracle connector requires oracledb package"}

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        return pd.DataFrame()


@ConnectorRegistry.register
class MongoDBConnector(BaseConnector):
    type_code: ClassVar[str] = "mongodb"
    display_name: ClassVar[str] = "MongoDB"
    category: ClassVar[str] = "database"
    description: ClassVar[str] = "Connect to MongoDB document databases"
    icon: ClassVar[str] = "database"
    config_schema: ClassVar[dict] = {
        "fields": [
            {"name": "host", "type": "string", "required": True},
            {"name": "port", "type": "integer", "required": True, "default": 27017},
            {"name": "database", "type": "string", "required": True},
            {"name": "collection", "type": "string", "required": True},
        ]
    }

    def test_connection(self) -> dict[str, Any]:
        try:
            from pymongo import MongoClient

            host = self.configuration.get("host", "localhost")
            port = self.configuration.get("port", 27017)
            client = MongoClient(host, port, serverSelectionTimeoutMS=5000)
            client.admin.command("ping")
            return {"success": True, "message": "Connection successful"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        from pymongo import MongoClient

        host = self.configuration.get("host", "localhost")
        port = self.configuration.get("port", 27017)
        db_name = self.configuration.get("database", "")
        coll_name = self.configuration.get("collection", "")
        client = MongoClient(host, port)
        db = client[db_name]
        coll = db[coll_name]
        filter_query = (query or {}).get("filter", {})
        docs = list(coll.find(filter_query).limit(1000))
        return pd.DataFrame(docs) if docs else pd.DataFrame()


# ═══════════════════════════════════════════════════════════════
# File Connectors
# ═══════════════════════════════════════════════════════════════


@ConnectorRegistry.register
class CSVConnector(BaseConnector):
    type_code: ClassVar[str] = "csv"
    display_name: ClassVar[str] = "CSV File"
    category: ClassVar[str] = "file"
    description: ClassVar[str] = "Read CSV files"
    icon: ClassVar[str] = "file"
    config_schema: ClassVar[dict] = {
        "fields": [
            {"name": "file_path", "type": "string", "required": True},
            {"name": "delimiter", "type": "string", "required": False, "default": ","},
            {"name": "encoding", "type": "string", "required": False, "default": "utf-8"},
        ]
    }

    def test_connection(self) -> dict[str, Any]:
        import os

        path = self.configuration.get("file_path", "")
        if os.path.exists(path):
            return {"success": True, "message": "File exists and is readable"}
        return {"success": False, "message": f"File not found: {path}"}

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        path = self.configuration.get("file_path", "")
        delimiter = self.configuration.get("delimiter", ",")
        encoding = self.configuration.get("encoding", "utf-8")
        return pd.read_csv(path, delimiter=delimiter, encoding=encoding)


@ConnectorRegistry.register
class ExcelConnector(BaseConnector):
    type_code: ClassVar[str] = "excel"
    display_name: ClassVar[str] = "Excel File"
    category: ClassVar[str] = "file"
    description: ClassVar[str] = "Read Excel (.xlsx, .xls) files"
    icon: ClassVar[str] = "file"
    config_schema: ClassVar[dict] = {
        "fields": [
            {"name": "file_path", "type": "string", "required": True},
            {"name": "sheet_name", "type": "string", "required": False},
        ]
    }

    def test_connection(self) -> dict[str, Any]:
        import os

        path = self.configuration.get("file_path", "")
        if os.path.exists(path):
            return {"success": True, "message": "File exists and is readable"}
        return {"success": False, "message": f"File not found: {path}"}

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        path = self.configuration.get("file_path", "")
        sheet = self.configuration.get("sheet_name", 0)
        return pd.read_excel(path, sheet_name=sheet)


@ConnectorRegistry.register
class JSONConnector(BaseConnector):
    type_code: ClassVar[str] = "json"
    display_name: ClassVar[str] = "JSON File"
    category: ClassVar[str] = "file"
    description: ClassVar[str] = "Read JSON files"
    icon: ClassVar[str] = "file"

    def test_connection(self) -> dict[str, Any]:
        import os

        path = self.configuration.get("file_path", "")
        if os.path.exists(path):
            return {"success": True, "message": "File exists"}
        return {"success": False, "message": f"File not found: {path}"}

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        path = self.configuration.get("file_path", "")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame([data])


@ConnectorRegistry.register
class XMLConnector(BaseConnector):
    type_code: ClassVar[str] = "xml"
    display_name: ClassVar[str] = "XML File"
    category: ClassVar[str] = "file"
    description: ClassVar[str] = "Read XML files"
    icon: ClassVar[str] = "file"

    def test_connection(self) -> dict[str, Any]:
        import os

        path = self.configuration.get("file_path", "")
        if os.path.exists(path):
            return {"success": True, "message": "File exists"}
        return {"success": False, "message": f"File not found: {path}"}

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        path = self.configuration.get("file_path", "")
        return pd.read_xml(path)


@ConnectorRegistry.register
class ParquetConnector(BaseConnector):
    type_code: ClassVar[str] = "parquet"
    display_name: ClassVar[str] = "Parquet File"
    category: ClassVar[str] = "file"
    description: ClassVar[str] = "Read Parquet columnar files"
    icon: ClassVar[str] = "file"

    def test_connection(self) -> dict[str, Any]:
        import os

        path = self.configuration.get("file_path", "")
        if os.path.exists(path):
            return {"success": True, "message": "File exists"}
        return {"success": False, "message": f"File not found: {path}"}

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        path = self.configuration.get("file_path", "")
        return pd.read_parquet(path)


# ═══════════════════════════════════════════════════════════════
# Cloud Storage Connectors
# ═══════════════════════════════════════════════════════════════


@ConnectorRegistry.register
class S3Connector(BaseConnector):
    type_code: ClassVar[str] = "s3"
    display_name: ClassVar[str] = "Amazon S3"
    category: ClassVar[str] = "cloud_storage"
    description: ClassVar[str] = "Connect to Amazon S3 buckets"
    icon: ClassVar[str] = "cloud"
    config_schema: ClassVar[dict] = {
        "fields": [
            {"name": "bucket", "type": "string", "required": True},
            {"name": "region", "type": "string", "required": False, "default": "us-east-1"},
            {"name": "key", "type": "string", "required": False},
        ]
    }
    auth_schema: ClassVar[dict] = {
        "fields": [
            {"name": "access_key_id", "type": "string", "required": True},
            {"name": "secret_access_key", "type": "password", "required": True},
        ]
    }

    def test_connection(self) -> dict[str, Any]:
        try:
            import boto3

            session = boto3.Session(
                aws_access_key_id=self.auth_config.get("access_key_id"),
                aws_secret_access_key=self.auth_config.get("secret_access_key"),
                region_name=self.configuration.get("region", "us-east-1"),
            )
            s3 = session.client("s3")
            s3.head_bucket(Bucket=self.configuration.get("bucket", ""))
            return {"success": True, "message": "S3 bucket accessible"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        import boto3

        session = boto3.Session(
            aws_access_key_id=self.auth_config.get("access_key_id"),
            aws_secret_access_key=self.auth_config.get("secret_access_key"),
            region_name=self.configuration.get("region", "us-east-1"),
        )
        s3 = session.client("s3")
        key = (query or {}).get("key", self.configuration.get("key", ""))
        obj = s3.get_object(Bucket=self.configuration.get("bucket", ""), Key=key)
        return pd.read_csv(io.BytesIO(obj["Body"].read()))


@ConnectorRegistry.register
class GoogleDriveConnector(BaseConnector):
    type_code: ClassVar[str] = "google_drive"
    display_name: ClassVar[str] = "Google Drive"
    category: ClassVar[str] = "cloud_storage"
    description: ClassVar[str] = "Connect to Google Drive files"
    icon: ClassVar[str] = "cloud"

    def test_connection(self) -> dict[str, Any]:
        return {
            "success": False,
            "message": "Google Drive connector requires google-api-python-client package and OAuth setup",
        }

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        return pd.DataFrame()


@ConnectorRegistry.register
class OneDriveConnector(BaseConnector):
    type_code: ClassVar[str] = "onedrive"
    display_name: ClassVar[str] = "Microsoft OneDrive"
    category: ClassVar[str] = "cloud_storage"
    description: ClassVar[str] = "Connect to OneDrive files"
    icon: ClassVar[str] = "cloud"

    def test_connection(self) -> dict[str, Any]:
        return {
            "success": False,
            "message": "OneDrive connector requires Microsoft Graph API setup",
        }

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        return pd.DataFrame()


@ConnectorRegistry.register
class DropboxConnector(BaseConnector):
    type_code: ClassVar[str] = "dropbox"
    display_name: ClassVar[str] = "Dropbox"
    category: ClassVar[str] = "cloud_storage"
    description: ClassVar[str] = "Connect to Dropbox files"
    icon: ClassVar[str] = "cloud"

    def test_connection(self) -> dict[str, Any]:
        return {
            "success": False,
            "message": "Dropbox connector requires dropbox package and access token",
        }

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        return pd.DataFrame()


# ═══════════════════════════════════════════════════════════════
# API Connectors
# ═══════════════════════════════════════════════════════════════


@ConnectorRegistry.register
class RESTAPIConnector(BaseConnector):
    type_code: ClassVar[str] = "rest_api"
    display_name: ClassVar[str] = "REST API"
    category: ClassVar[str] = "api"
    description: ClassVar[str] = "Connect to any REST API endpoint"
    icon: ClassVar[str] = "api"
    config_schema: ClassVar[dict] = {
        "fields": [
            {"name": "base_url", "type": "string", "required": True},
            {"name": "endpoint", "type": "string", "required": True},
            {"name": "method", "type": "string", "required": False, "default": "GET"},
            {"name": "headers", "type": "json", "required": False},
            {"name": "params", "type": "json", "required": False},
        ]
    }
    auth_schema: ClassVar[dict] = {
        "fields": [
            {
                "name": "type",
                "type": "select",
                "options": ["none", "bearer", "api_key", "basic"],
                "default": "none",
            },
            {"name": "token", "type": "password", "required": False},
            {"name": "api_key_header", "type": "string", "required": False, "default": "X-API-Key"},
        ]
    }

    def test_connection(self) -> dict[str, Any]:
        try:
            import requests

            from shared.url_validation import validate_url, UrlValidationError

            url = self.configuration.get("base_url", "")
            if not url:
                return {"success": False, "message": "base_url is required"}
            try:
                validate_url(url)
            except UrlValidationError as e:
                return {"success": False, "message": str(e)}
            headers = self._build_headers()
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code < 400:
                return {"success": True, "message": f"API reachable (status {resp.status_code})"}
            return {"success": False, "message": f"API returned status {resp.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        import requests

        from shared.url_validation import validate_url, UrlValidationError

        base_url = self.configuration.get("base_url", "")
        endpoint = (query or {}).get("endpoint", self.configuration.get("endpoint", ""))
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            validate_url(url)
        except UrlValidationError:
            raise ValueError(f"URL validation failed for {url}") from None
        headers = self._build_headers()
        params = (query or {}).get("params", self.configuration.get("params", {}))
        method = (query or {}).get("method", self.configuration.get("method", "GET"))
        resp = requests.request(method, url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return pd.DataFrame(data)
        if isinstance(data, dict):
            for key in ("data", "results", "items", "records"):
                if key in data and isinstance(data[key], list):
                    return pd.DataFrame(data[key])
            return pd.DataFrame([data])
        return pd.DataFrame()

    def _build_headers(self) -> dict[str, str]:
        headers = dict(self.configuration.get("headers", {}))
        auth_type = self.auth_config.get("type", "none")
        token = self.auth_config.get("token", "")
        if auth_type == "bearer" and token:
            headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "api_key" and token:
            header_name = self.auth_config.get("api_key_header", "X-API-Key")
            headers[header_name] = token
        elif auth_type == "basic" and token:
            headers["Authorization"] = f"Basic {token}"
        return headers


@ConnectorRegistry.register
class GraphQLAPIConnector(BaseConnector):
    type_code: ClassVar[str] = "graphql_api"
    display_name: ClassVar[str] = "GraphQL API"
    category: ClassVar[str] = "api"
    description: ClassVar[str] = "Connect to GraphQL APIs"
    icon: ClassVar[str] = "api"
    config_schema: ClassVar[dict] = {
        "fields": [
            {"name": "endpoint_url", "type": "string", "required": True},
        ]
    }

    def test_connection(self) -> dict[str, Any]:
        try:
            import requests

            url = self.configuration.get("endpoint_url", "")
            if not url:
                return {"success": False, "message": "endpoint_url is required"}
            headers = self._build_headers()
            resp = requests.post(url, json={"query": "{ __typename }"}, headers=headers, timeout=10)
            if resp.status_code < 400:
                return {"success": True, "message": "GraphQL endpoint reachable"}
            return {"success": False, "message": f"Endpoint returned status {resp.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        import requests

        url = self.configuration.get("endpoint_url", "")
        graphql_query = (query or {}).get("query", "")
        headers = self._build_headers()
        resp = requests.post(url, json={"query": graphql_query}, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        if isinstance(data, dict):
            for key in data:
                if isinstance(data[key], list):
                    return pd.DataFrame(data[key])
        return pd.DataFrame([data]) if data else pd.DataFrame()

    def _build_headers(self) -> dict[str, str]:
        headers = {}
        auth_type = self.auth_config.get("type", "none")
        token = self.auth_config.get("token", "")
        if auth_type == "bearer" and token:
            headers["Authorization"] = f"Bearer {token}"
        return headers


@ConnectorRegistry.register
class WebhookConnector(BaseConnector):
    type_code: ClassVar[str] = "webhook"
    display_name: ClassVar[str] = "Webhook"
    category: ClassVar[str] = "api"
    description: ClassVar[str] = "Receive data via webhook callbacks"
    icon: ClassVar[str] = "api"

    def test_connection(self) -> dict[str, Any]:
        return {
            "success": True,
            "message": "Webhook connector is passive — data arrives via POST callbacks",
        }

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        payload = (query or {}).get("payload", [])
        if isinstance(payload, list):
            return pd.DataFrame(payload)
        return pd.DataFrame([payload]) if payload else pd.DataFrame()


# ═══════════════════════════════════════════════════════════════
# Africa-First Connectors
# ═══════════════════════════════════════════════════════════════


@ConnectorRegistry.register
class MobileMoneyConnector(BaseConnector):
    type_code: ClassVar[str] = "mobile_money"
    display_name: ClassVar[str] = "Mobile Money (Africa)"
    category: ClassVar[str] = "api"
    description: ClassVar[str] = "Connect to mobile money platforms (MTN MoMo, Airtel Money, etc.)"
    icon: ClassVar[str] = "wallet"
    is_africa_first: ClassVar[bool] = True
    region: ClassVar[str] = "africa"
    config_schema: ClassVar[dict] = {
        "fields": [
            {
                "name": "provider",
                "type": "select",
                "options": ["mtn_momo", "airtel_money", "mpesa", "orange_money", "vodafone_cash"],
                "required": True,
            },
            {"name": "base_url", "type": "string", "required": True},
            {
                "name": "environment",
                "type": "select",
                "options": ["sandbox", "production"],
                "default": "sandbox",
            },
        ]
    }
    auth_schema: ClassVar[dict] = {
        "fields": [
            {"name": "api_key", "type": "password", "required": True},
            {"name": "api_user_id", "type": "string", "required": True},
            {"name": "subscription_key", "type": "password", "required": True},
        ]
    }

    def test_connection(self) -> dict[str, Any]:
        provider = self.configuration.get("provider", "")
        base_url = self.configuration.get("base_url", "")
        if not base_url:
            return {"success": False, "message": "base_url is required"}
        return {
            "success": True,
            "message": f"Mobile money connector configured for {provider}. Test with a live API call.",
        }

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        import requests

        base_url = self.configuration.get("base_url", "")
        endpoint = (query or {}).get("endpoint", "transactions")
        headers = {
            "Ocp-Apim-Subscription-Key": self.auth_config.get("subscription_key", ""),
            "Authorization": f"Bearer {self.auth_config.get('api_key', '')}",
        }
        resp = requests.get(f"{base_url}/{endpoint}", headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame([data])


@ConnectorRegistry.register
class BankAPIConnector(BaseConnector):
    type_code: ClassVar[str] = "bank_api"
    display_name: ClassVar[str] = "Banking API (Africa)"
    category: ClassVar[str] = "api"
    description: ClassVar[str] = "Connect to African banking APIs for transaction data"
    icon: ClassVar[str] = "bank"
    is_africa_first: ClassVar[bool] = True
    region: ClassVar[str] = "africa"
    config_schema: ClassVar[dict] = {
        "fields": [
            {"name": "bank_name", "type": "string", "required": True},
            {"name": "base_url", "type": "string", "required": True},
        ]
    }
    auth_schema: ClassVar[dict] = {
        "fields": [
            {"name": "client_id", "type": "string", "required": True},
            {"name": "client_secret", "type": "password", "required": True},
        ]
    }

    def test_connection(self) -> dict[str, Any]:
        bank = self.configuration.get("bank_name", "")
        return {
            "success": True,
            "message": f"Bank API connector configured for {bank}. Test with live credentials.",
        }

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        return pd.DataFrame()


@ConnectorRegistry.register
class GovernmentOpenDataConnector(BaseConnector):
    type_code: ClassVar[str] = "gov_open_data"
    display_name: ClassVar[str] = "Government Open Data (Africa)"
    category: ClassVar[str] = "api"
    description: ClassVar[str] = "Connect to African government open data portals"
    icon: ClassVar[str] = "government"
    is_africa_first: ClassVar[bool] = True
    region: ClassVar[str] = "africa"
    config_schema: ClassVar[dict] = {
        "fields": [
            {"name": "country", "type": "string", "required": True},
            {"name": "portal_url", "type": "string", "required": True},
            {"name": "dataset_id", "type": "string", "required": False},
        ]
    }

    def test_connection(self) -> dict[str, Any]:
        url = self.configuration.get("portal_url", "")
        if not url:
            return {"success": False, "message": "portal_url is required"}
        try:
            import requests

            from shared.url_validation import validate_url, UrlValidationError

            try:
                validate_url(url)
            except UrlValidationError as e:
                return {"success": False, "message": str(e)}
            resp = requests.get(url, timeout=10)
            if resp.status_code < 400:
                return {"success": True, "message": "Open data portal reachable"}
            return {"success": False, "message": f"Portal returned status {resp.status_code}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        import requests

        from shared.url_validation import validate_url, UrlValidationError

        portal = self.configuration.get("portal_url", "")
        dataset_id = (query or {}).get("dataset_id", self.configuration.get("dataset_id", ""))
        full_url = f"{portal}/api/3/action/datastore_search"
        try:
            validate_url(full_url)
        except UrlValidationError:
            raise ValueError(f"URL validation failed for portal URL") from None
        resp = requests.get(
            full_url,
            params={"resource_id": dataset_id},
            timeout=30,
        )
        resp.raise_for_status()
        records = resp.json().get("result", {}).get("records", [])
        return pd.DataFrame(records) if records else pd.DataFrame()


@ConnectorRegistry.register
class HospitalSystemConnector(BaseConnector):
    type_code: ClassVar[str] = "hospital_system"
    display_name: ClassVar[str] = "Hospital Information System"
    category: ClassVar[str] = "api"
    description: ClassVar[str] = "Connect to hospital information systems (HIS) for patient data"
    icon: ClassVar[str] = "healthcare"
    is_africa_first: ClassVar[bool] = True
    region: ClassVar[str] = "africa"
    config_schema: ClassVar[dict] = {
        "fields": [
            {"name": "system_name", "type": "string", "required": True},
            {"name": "base_url", "type": "string", "required": True},
        ]
    }

    def test_connection(self) -> dict[str, Any]:
        return {"success": True, "message": "HIS connector configured. Test with live credentials."}

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        return pd.DataFrame()


@ConnectorRegistry.register
class StudentInfoSystemConnector(BaseConnector):
    type_code: ClassVar[str] = "student_info_system"
    display_name: ClassVar[str] = "Student Information System"
    category: ClassVar[str] = "api"
    description: ClassVar[str] = "Connect to student information systems (SIS) for education data"
    icon: ClassVar[str] = "education"
    is_africa_first: ClassVar[bool] = True
    region: ClassVar[str] = "africa"
    config_schema: ClassVar[dict] = {
        "fields": [
            {"name": "system_name", "type": "string", "required": True},
            {"name": "base_url", "type": "string", "required": True},
        ]
    }

    def test_connection(self) -> dict[str, Any]:
        return {"success": True, "message": "SIS connector configured. Test with live credentials."}

    def extract_data(self, query: dict[str, Any] | None = None) -> pd.DataFrame:
        return pd.DataFrame()
