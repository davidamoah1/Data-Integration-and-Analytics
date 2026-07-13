"""Tests for ETL connectors — CSV, Excel, JSON, XML connectors."""

import os
import tempfile
import pytest
import pandas as pd

from etl.connectors.connectors import (
    CSVConnector, ExcelConnector, JSONConnector, XMLConnector,
    get_connector, register_connector, CONNECTOR_REGISTRY,
)
from etl.connectors.base import BaseConnector


@pytest.fixture
def sample_csv(tmp_path):
    path = tmp_path / "test.csv"
    data = "name,age,city\nAlice,30,Lagos\nBob,25,Accra\nCarol,35,Cairo\n"
    path.write_text(data)
    return str(path)


@pytest.fixture
def sample_json(tmp_path):
    path = tmp_path / "test.json"
    path.write_text('[{"name":"Alice","age":30},{"name":"Bob","age":25}]')
    return str(path)


@pytest.fixture
def sample_xml(tmp_path):
    path = tmp_path / "test.xml"
    path.write_text(
        '<?xml version="1.0"?>\n<root><record><name>Alice</name><age>30</age></record>'
        '<record><name>Bob</name><age>25</age></record></root>'
    )
    return str(path)


class TestCSVConnector:
    def test_extract(self, sample_csv):
        conn = CSVConnector("csv", {"file_path": sample_csv})
        conn.connect()
        df = conn.extract()
        assert len(df) == 3
        assert list(df.columns) == ["name", "age", "city"]
        conn.close()

    def test_preview(self, sample_csv):
        conn = CSVConnector("csv", {"file_path": sample_csv})
        conn.connect()
        df = conn.preview(rows=2)
        assert len(df) == 2
        conn.close()

    def test_get_schema(self, sample_csv):
        conn = CSVConnector("csv", {"file_path": sample_csv})
        conn.connect()
        schema = conn.get_schema()
        assert len(schema) == 3
        assert schema[0]["name"] == "name"
        conn.close()

    def test_auto_encoding(self, sample_csv):
        conn = CSVConnector("csv", {"file_path": sample_csv})
        conn.connect()
        df = conn.extract()
        assert "name" in df.columns
        conn.close()

    def test_delimiter(self, tmp_path):
        path = tmp_path / "semi.csv"
        path.write_text("a;b;c\n1;2;3\n")
        conn = CSVConnector("csv", {"file_path": str(path), "delimiter": ";"})
        conn.connect()
        df = conn.extract()
        assert list(df.columns) == ["a", "b", "c"]
        conn.close()


class TestJSONConnector:
    def test_extract(self, sample_json):
        conn = JSONConnector("json", {"file_path": sample_json})
        conn.connect()
        df = conn.extract()
        assert len(df) == 2
        assert "name" in df.columns
        conn.close()

    def test_get_schema(self, sample_json):
        conn = JSONConnector("json", {"file_path": sample_json})
        conn.connect()
        schema = conn.get_schema()
        assert len(schema) == 2
        conn.close()


class TestXMLConnector:
    def test_extract(self, sample_xml):
        conn = XMLConnector("xml", {"file_path": sample_xml, "record_tag": "record", "root_path": "root"})
        conn.connect()
        df = conn.extract()
        assert len(df) == 2
        assert "name" in df.columns
        conn.close()


class TestConnectorRegistry:
    def test_get_connector_csv(self, sample_csv):
        conn = get_connector("csv", {"file_path": sample_csv})
        assert isinstance(conn, CSVConnector)

    def test_get_connector_json(self, sample_json):
        conn = get_connector("json", {"file_path": sample_json})
        assert isinstance(conn, JSONConnector)

    def test_get_connector_unknown(self):
        with pytest.raises(ValueError, match="Unknown connector type"):
            get_connector("invalid", {})

    def test_register_custom_connector(self):
        class DummyConnector(BaseConnector):
            def connect(self): self._connected = True
            def extract(self, **kw): return pd.DataFrame()
            def get_schema(self): return []

        register_connector("dummy", DummyConnector)
        assert "dummy" in CONNECTOR_REGISTRY
        conn = get_connector("dummy", {})
        assert isinstance(conn, DummyConnector)
