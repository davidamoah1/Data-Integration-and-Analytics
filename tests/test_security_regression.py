"""Security regression tests for Bandit fixes.

Tests that the security fixes are effective and cannot be bypassed.
"""

from __future__ import annotations

import os
import pickle
import tempfile

import pandas as pd
import pytest

# --- B314: XML security ------------------------------------------------------


class TestXmlSecurity:
    """Verify defusedxml prevents XML attacks."""

    def test_safe_xml_parsed(self, tmp_path):
        from etl.file_security import FileValidator

        xml_file = tmp_path / "test.xml"
        xml_file.write_text("<root><item>hello</item></root>")
        validator = FileValidator()
        result = validator.validate(str(xml_file), expected_type="xml")
        assert result["valid"]

    def test_billion_laughs_rejected(self, tmp_path):
        from etl.file_security import FileValidator

        xml_file = tmp_path / "evil.xml"
        xml_file.write_text(
            """<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;">
]>
<lolz>&lol3;</lolz>"""
        )
        validator = FileValidator()
        result = validator.validate(str(xml_file), expected_type="xml")
        assert not result["valid"]
        assert any("structure validation failed" in e for e in result["errors"])

    def test_xxe_rejected(self, tmp_path):
        from etl.file_security import FileValidator

        xml_file = tmp_path / "xxe.xml"
        xml_file.write_text(
            """<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<foo>&xxe;</foo>"""
        )
        validator = FileValidator()
        result = validator.validate(str(xml_file), expected_type="xml")
        assert not result["valid"]


# --- B301: Pickle security ---------------------------------------------------


class TestPickleSecurity:
    """Verify restricted unpickler and path boundary enforcement."""

    def test_path_traversal_rejected(self):
        from ml.automl import AutoMLEngine

        with pytest.raises(ValueError, match="artifact directory"):
            AutoMLEngine.load_artifact("/etc/passwd")

    def test_path_traversal_with_dotdot_rejected(self):
        from ml.automl import AutoMLEngine

        artifact_dir = tempfile.gettempdir()
        evil_path = os.path.join(artifact_dir, "..", "..", "etc", "passwd")
        with pytest.raises(ValueError, match="artifact directory"):
            AutoMLEngine.load_artifact(evil_path)

    def test_malicious_pickle_rejected(self):
        """A pickle that tries to import os.system should be blocked."""
        from ml.automl import AutoMLEngine

        artifact_dir = tempfile.gettempdir()
        evil_path = os.path.join(artifact_dir, "evil_model.pkl")

        class Exploit:
            def __reduce__(self):
                import os

                return (os.system, ("echo hacked",))

        with open(evil_path, "wb") as f:
            pickle.dump({"model": Exploit()}, f)

        with pytest.raises((pickle.UnpicklingError, ValueError)):
            AutoMLEngine.load_artifact(evil_path)

        os.unlink(evil_path)

    def test_valid_artifact_loads(self):
        """A legitimate artifact with sklearn model should load."""
        from sklearn.linear_model import LogisticRegression

        from ml.automl import AutoMLEngine

        artifact_dir = tempfile.gettempdir()
        os.environ["ARTIFACT_DIR"] = artifact_dir
        path = os.path.join(artifact_dir, "test_safe_model.pkl")
        model = LogisticRegression()
        model.fit([[0, 0], [1, 1]], [0, 1])
        with open(path, "wb") as f:
            pickle.dump({"model": model, "label_encoder": None}, f)

        data = AutoMLEngine.load_artifact(path)
        assert "model" in data
        os.unlink(path)
        del os.environ["ARTIFACT_DIR"]


# --- B102: exec security -----------------------------------------------------


class TestExecSecurity:
    """Verify sandboxed Python execution prevents attacks."""

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

    def test_normal_code_executes(self, sample_df):
        from workflows.nodes import _run_python_sandboxed

        code = "result = df.copy()\nresult['c'] = result['a'] + result['b']"
        out = _run_python_sandboxed(code, sample_df, timeout=10)
        assert "c" in out.columns
        assert out["c"].tolist() == [5, 7, 9]

    def test_filesystem_access_blocked(self, sample_df):
        from workflows.nodes import _run_python_sandboxed

        code = (
            "import os\n"
            "result = df.copy()\n"
            "result['secret'] = open('/etc/passwd').read()[:10]"
        )
        with pytest.raises(Exception):
            _run_python_sandboxed(code, sample_df, timeout=10)

    def test_env_var_access_blocked(self, sample_df):
        from workflows.nodes import _run_python_sandboxed

        # Set a secret env var in the parent process
        os.environ["TEST_SECRET_KEY"] = "super-secret-value"
        try:
            code = (
                "import os\n"
                "result = df.copy()\n"
                "result['secret'] = os.environ.get('TEST_SECRET_KEY', 'none')"
            )
            # The sandbox blocks imports, so this should fail
            with pytest.raises(Exception):
                _run_python_sandboxed(code, sample_df, timeout=10)
        finally:
            del os.environ["TEST_SECRET_KEY"]

    def test_subprocess_execution_blocked(self, sample_df):
        from workflows.nodes import _run_python_sandboxed

        code = (
            "import subprocess\n" "subprocess.run(['whoami'], capture_output=True)\n" "result = df"
        )
        with pytest.raises(Exception):
            _run_python_sandboxed(code, sample_df, timeout=10)

    def test_timeout_enforced(self, sample_df):
        from workflows.nodes import _run_python_sandboxed

        # Pure Python busy loop — no imports needed
        code = "while True:\n    pass\n"
        with pytest.raises(RuntimeError, match="timed out"):
            _run_python_sandboxed(code, sample_df, timeout=2)


# --- B108: Temp storage ------------------------------------------------------


class TestTempStorage:
    """Verify no hardcoded /tmp paths."""

    def test_config_uses_tempfile(self):
        import config

        # On Vercel, paths should use tempfile.gettempdir(), not "/tmp"
        if os.getenv("VERCEL", "").lower() in ("1", "true", "yes"):
            assert (
                "/tmp"
                not in config.CAPTURE_STORAGE_DIR  # nosec B108 - string literal in assertion, not a temp path
                or tempfile.gettempdir() in config.CAPTURE_STORAGE_DIR
            )

    def test_no_hardcoded_tmp_in_source(self):
        """No Python source file should hardcode /tmp paths."""
        import ast

        for root, _dirs, files in os.walk("."):
            if "__pycache__" in root or ".git" in root or "node_modules" in root or "tests" in root:
                continue
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                with open(fpath, encoding="utf-8", errors="ignore") as f:
                    tree = ast.parse(f.read(), filename=fpath)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        if node.value.startswith(
                            "/tmp/"
                        ):  # nosec B108 — string literal in assertion, not a temp path
                            pytest.fail(f"{fpath} contains hardcoded /tmp path: {node.value}")


# --- B104: Server binding ----------------------------------------------------


class TestServerBinding:
    """Verify server binding defaults are secure."""

    def test_run_local_uses_localhost(self):
        with open("run_local.py") as f:
            content = f.read()
        assert 'host="127.0.0.1"' in content
        assert 'host="0.0.0.0"' not in content

    def test_url_validation_blocks_localhost(self):
        from shared.url_validation import UrlValidationError, validate_url

        with pytest.raises(UrlValidationError):
            validate_url("http://0.0.0.0/test")
        with pytest.raises(UrlValidationError):
            validate_url("http://localhost/test")
        with pytest.raises(UrlValidationError):
            validate_url("http://[::]/test")

    def test_url_validation_allows_localhost_when_flagged(self):
        from shared.url_validation import validate_url

        # allow_localhost=True should not raise for localhost string
        # (but may still fail DNS resolution in CI, so we just check it doesn't
        # raise the "Requests to localhost are not allowed" message)
        try:
            validate_url("http://localhost/test", allow_localhost=True)
        except Exception as e:
            assert "not allowed" not in str(e)
