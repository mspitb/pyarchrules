"""Unit tests for ForbiddenExternalLibsRule."""

import pytest

from pyarchrules.core.rules.dsl.forbidden_external_libs_rule import ForbiddenExternalLibsRule
from pyarchrules.model.spec import ServiceSpec


class TestForbiddenExternalLibsRule:

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

    def test_non_forbidden_import_passes(self, service_dir):
        self._write(service_dir / "svc", "domain/models.py", "from pydantic import BaseModel\n")
        rule = ForbiddenExternalLibsRule(
            self._make_spec(service_dir), folder="domain", libs=["django", "flask"]
        )
        assert rule.validate() == []

    def test_forbidden_import_returns_error(self, service_dir):
        self._write(service_dir / "svc", "domain/models.py", "import django\n")
        rule = ForbiddenExternalLibsRule(
            self._make_spec(service_dir), folder="domain", libs=["django", "flask"]
        )
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].rule_name == "forbidden_external_libs"
        assert "django" in violations[0].message
        assert "django" in violations[0].details["forbidden"]

    def test_multiple_forbidden_imports_return_multiple_errors(self, service_dir):
        self._write(service_dir / "svc", "domain/models.py", "import django\nimport flask\n")
        rule = ForbiddenExternalLibsRule(
            self._make_spec(service_dir), folder="domain", libs=["django", "flask"]
        )
        assert len(rule.validate()) == 2

    def test_relative_imports_not_flagged(self, service_dir):
        self._write(service_dir / "svc", "domain/service.py", "from .repo import Repo\n")
        rule = ForbiddenExternalLibsRule(
            self._make_spec(service_dir), folder="domain", libs=["django"]
        )
        assert rule.validate() == []

    def test_nonexistent_folder_returns_error(self, service_dir):
        rule = ForbiddenExternalLibsRule(
            self._make_spec(service_dir), folder="missing", libs=["django"]
        )
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].severity == "error"

    def test_rule_name(self, service_dir):
        (service_dir / "svc" / "domain").mkdir()
        rule = ForbiddenExternalLibsRule(self._make_spec(service_dir), folder="domain", libs=[])
        assert rule.rule_name == "forbidden_external_libs"
