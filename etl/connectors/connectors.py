"""CSV connector — read CSV files with encoding detection and delimiter support."""

import os
from typing import Optional
import pandas as pd
import chardet

from etl.connectors.base import BaseConnector


class CSVConnector(BaseConnector):
    """Connector for CSV file sources."""

    def connect(self):
        path = self.config.get("file_path", "")
        if not os.path.exists(path):
            raise FileNotFoundError(f"CSV file not found: {path}")
        self._connected = True

    def _detect_encoding(self, path: str) -> str:
        with open(path, "rb") as f:
            raw = f.read(102400)
        result = chardet.detect(raw)
        return result.get("encoding", "utf-8")

    def extract(self, **kwargs) -> pd.DataFrame:
        path = self.config["file_path"]
        encoding = self.config.get("encoding") or self._detect_encoding(path)
        delimiter = self.config.get("delimiter", ",")
        skip_rows = self.config.get("skip_rows", 0)
        nrows = kwargs.get("nrows")

        df = pd.read_csv(
            path,
            encoding=encoding,
            delimiter=delimiter,
            skiprows=skip_rows,
            nrows=nrows,
            low_memory=False,
        )
        return df

    def get_schema(self) -> list[dict]:
        df = self.extract(nrows=100)
        schema = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            schema.append({
                "name": col,
                "type": dtype,
                "nullable": df[col].isnull().any(),
            })
        return schema


class ExcelConnector(BaseConnector):
    """Connector for Excel (.xlsx/.xls) files."""

    def connect(self):
        path = self.config.get("file_path", "")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Excel file not found: {path}")
        self._connected = True

    def extract(self, **kwargs) -> pd.DataFrame:
        path = self.config["file_path"]
        sheet = self.config.get("sheet_name", 0)
        header = self.config.get("header_row", 0)
        nrows = kwargs.get("nrows")

        df = pd.read_excel(
            path,
            sheet_name=sheet,
            header=header,
            nrows=nrows,
            engine="openpyxl",
        )
        return df

    def get_schema(self) -> list[dict]:
        df = self.extract(nrows=100)
        schema = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            schema.append({
                "name": col,
                "type": dtype,
                "nullable": df[col].isnull().any(),
            })
        return schema

    def list_sheets(self) -> list[str]:
        path = self.config["file_path"]
        xls = pd.ExcelFile(path, engine="openpyxl")
        return xls.sheet_names


class JSONConnector(BaseConnector):
    """Connector for JSON files."""

    def connect(self):
        path = self.config.get("file_path", "")
        if not os.path.exists(path):
            raise FileNotFoundError(f"JSON file not found: {path}")
        self._connected = True

    def extract(self, **kwargs) -> pd.DataFrame:
        path = self.config["file_path"]
        record_path = self.config.get("record_path", None)
        nrows = kwargs.get("nrows")

        df = pd.read_json(path, orient=self.config.get("orient", "records"))
        if record_path and isinstance(df.iloc[0].to_dict().get(record_path, None), list):
            df = pd.json_normalize(pd.read_json(path)[record_path])
        if nrows:
            df = df.head(nrows)
        return df

    def get_schema(self) -> list[dict]:
        df = self.extract(nrows=100)
        schema = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            schema.append({
                "name": col,
                "type": dtype,
                "nullable": df[col].isnull().any(),
            })
        return schema


class XMLConnector(BaseConnector):
    """Connector for XML files using xmltodict."""

    def connect(self):
        path = self.config.get("file_path", "")
        if not os.path.exists(path):
            raise FileNotFoundError(f"XML file not found: {path}")
        self._connected = True

    def extract(self, **kwargs) -> pd.DataFrame:
        import xmltodict

        path = self.config["file_path"]
        record_tag = self.config.get("record_tag", "record")
        encoding = self.config.get("encoding", "utf-8")

        with open(path, "r", encoding=encoding) as f:
            data = xmltodict.parse(f.read())

        # Navigate to the record list
        root = data
        for key in self.config.get("root_path", "").split("."):
            if key and key in root:
                root = root[key]

        records = root.get(record_tag, [])
        if isinstance(records, dict):
            records = [records]

        df = pd.DataFrame(records)
        return df

    def get_schema(self) -> list[dict]:
        df = self.extract()
        schema = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            schema.append({
                "name": col,
                "type": dtype,
                "nullable": df[col].isnull().any(),
            })
        return schema


class MySQLConnector(BaseConnector):
    """Connector for MySQL database queries."""

    def connect(self):
        from sqlalchemy import create_engine
        conn_str = self.config.get("connection_string", "")
        if not conn_str:
            host = self.config.get("host", "localhost")
            port = self.config.get("port", 3306)
            db = self.config.get("database", "")
            user = self.config.get("user", "")
            pwd = self.config.get("password", "")
            conn_str = f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}"
        self._engine = create_engine(conn_str, pool_pre_ping=True)
        self._connected = True

    def extract(self, **kwargs) -> pd.DataFrame:
        query = self.config.get("query")
        table = self.config.get("table")
        nrows = kwargs.get("nrows")

        if query:
            sql = query
            if nrows:
                sql = f"SELECT * FROM ({query}) AS sub LIMIT {nrows}"
        elif table:
            sql = f"SELECT * FROM `{table}`"
            if nrows:
                sql += f" LIMIT {nrows}"
        else:
            raise ValueError("MySQLConnector requires either 'query' or 'table' in config")

        return pd.read_sql(sql, self._engine)

    def get_schema(self) -> list[dict]:
        table = self.config.get("table")
        if not table:
            df = self.extract(nrows=100)
        else:
            df = pd.read_sql(f"SELECT * FROM `{table}` LIMIT 100", self._engine)
        schema = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            schema.append({
                "name": col,
                "type": dtype,
                "nullable": df[col].isnull().any(),
            })
        return schema

    def close(self):
        if hasattr(self, "_engine"):
            self._engine.dispose()
        super().close()


class RESTAPIConnector(BaseConnector):
    """Connector for REST API data sources."""

    def connect(self):
        self._connected = True

    def extract(self, **kwargs) -> pd.DataFrame:
        import requests

        url = self.config["url"]
        method = self.config.get("method", "GET").upper()
        headers = self.config.get("headers", {})
        params = self.config.get("params", {})
        body = self.config.get("body")
        auth = self.config.get("auth")
        data_path = self.config.get("data_path", None)  # dot-separated path to records
        nrows = kwargs.get("nrows")

        resp = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=body,
            auth=auth,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        if data_path:
            for key in data_path.split("."):
                if key and isinstance(data, dict):
                    data = data.get(key, [])

        if isinstance(data, dict):
            data = [data]

        df = pd.DataFrame(data)
        if nrows:
            df = df.head(nrows)
        return df

    def get_schema(self) -> list[dict]:
        df = self.extract(nrows=100)
        schema = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            schema.append({
                "name": col,
                "type": dtype,
                "nullable": df[col].isnull().any(),
            })
        return schema


# --- Connector registry ----------------------------------------------------

CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {
    "csv": CSVConnector,
    "excel": ExcelConnector,
    "json": JSONConnector,
    "xml": XMLConnector,
    "mysql": MySQLConnector,
    "api": RESTAPIConnector,
}


def get_connector(source_type: str, config: dict) -> BaseConnector:
    """Factory: return a connector instance for the given source type.

    Args:
        source_type: One of: csv, excel, json, xml, mysql, api.
        config: Connector-specific configuration dict.

    Returns:
        Connector instance (not yet connected).
    """
    source_type = source_type.lower()
    if source_type not in CONNECTOR_REGISTRY:
        raise ValueError(f"Unknown connector type: '{source_type}'. Available: {list(CONNECTOR_REGISTRY.keys())}")
    cls = CONNECTOR_REGISTRY[source_type]
    return cls(name=source_type, config=config)


def register_connector(source_type: str, connector_cls: type[BaseConnector]):
    """Register a custom connector at runtime.

    Allows plugging in new connectors without modifying the core engine.
    """
    CONNECTOR_REGISTRY[source_type.lower()] = connector_cls
