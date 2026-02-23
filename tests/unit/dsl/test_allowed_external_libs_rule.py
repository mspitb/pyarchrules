"""Unit tests for AllowedExternalLibsRule."""

import pytest

from pyarchrules.core.rules.dsl.allowed_external_libs_rule import AllowedExternalLibsRule
from pyarchrules.model.spec import ServiceSpec


class TestAllowedExternalLibsRule:

    @pytest.fixture
    def service_dir(self, tmp_path):
        svc = tmp_path / "svc"
        svc.mkdir()
        return tmp_path

    def _make_spec(self, root):
        return ServiceSpec(name="svc", path="svc", project_root=root)

    def _write(self, base, rel, content):
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    # ------------------------------------------------------------------

    def test_allowed_external_lib_passes(self, service_dir):
        self._write(service_dir / "svc", "domain/models.py", "from pydantic import BaseModel\n")
        rule = AllowedExternalLibsRule(
            self._make_spec(service_dir), folder="domain", libs=["pydantic"]
        )
        assert rule.validate() == []

    def test_stdlib_always_allowed(self, service_dir):
        self._write(
            service_dir / "svc",
            "domain/models.py",
            "import os\nimport sys\nfrom pathlib import Path\n",
        )
        rule = AllowedExternalLibsRule(self._make_spec(service_dir), folder="domain", libs=[])
        assert rule.validate() == []

    def test_relative_imports_always_allowed(self, service_dir):
        self._write(service_dir / "svc", "domain/service.py", "from .repo import UserRepo\n")
        rule = AllowedExternalLibsRule(self._make_spec(service_dir), folder="domain", libs=[])
        assert rule.validate() == []

    def test_forbidden_external_lib_returns_error(self, service_dir):
        self._write(service_dir / "svc", "domain/models.py", "import django\n")
        rule = AllowedExternalLibsRule(
            self._make_spec(service_dir), folder="domain", libs=["pydantic"]
        )
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].rule_name == "allowed_external_libs"
        assert "django" in violations[0].message
        assert "pydantic" in violations[0].details["allowed"]

    def test_multiple_violations_reported(self, service_dir):
        self._write(service_dir / "svc", "domain/models.py", "import django\nimport flask\n")
        rule = AllowedExternalLibsRule(
            self._make_spec(service_dir), folder="domain", libs=["pydantic"]
        )
        assert len(rule.validate()) == 2

    def test_nonexistent_folder_returns_error(self, service_dir):
        rule = AllowedExternalLibsRule(
            self._make_spec(service_dir), folder="missing", libs=["pydantic"]
        )
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].severity == "error"

    def test_rule_name(self, service_dir):
        (service_dir / "svc" / "domain").mkdir()
        rule = AllowedExternalLibsRule(self._make_spec(service_dir), folder="domain", libs=[])
        assert rule.rule_name == "allowed_external_libs"
