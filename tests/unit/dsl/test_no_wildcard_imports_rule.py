"""Unit tests for NoWildcardImportsRule."""

import pytest

from pyarchrules.core.rules.dsl.no_wildcard_imports_rule import NoWildcardImportsRule
from pyarchrules.model.spec import ServiceSpec


class TestNoWildcardImportsRule:

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
        return p

    # ------------------------------------------------------------------

    def test_clean_file_passes(self, service_dir):
        self._write(service_dir / "svc", "api/views.py", "from domain.models import User\n")
        rule = NoWildcardImportsRule(self._make_spec(service_dir))
        assert rule.validate() == []

    def test_wildcard_import_returns_error(self, service_dir):
        self._write(service_dir / "svc", "api/views.py", "from domain.models import *\n")
        rule = NoWildcardImportsRule(self._make_spec(service_dir))
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].rule_name == "no_wildcard_imports"
        assert violations[0].severity == "error"
        assert "domain.models" in violations[0].message

    def test_multiple_wildcards_returns_multiple_errors(self, service_dir):
        self._write(
            service_dir / "svc",
            "api/views.py",
            "from domain.models import *\nfrom domain.utils import *\n",
        )
        rule = NoWildcardImportsRule(self._make_spec(service_dir))
        assert len(rule.validate()) == 2

    def test_folder_scoped_ignores_other_folders(self, service_dir):
        # wildcard in api/ — but we only check domain/
        self._write(service_dir / "svc", "api/views.py", "from x import *\n")
        self._write(service_dir / "svc", "domain/models.py", "from x import Foo\n")
        rule = NoWildcardImportsRule(self._make_spec(service_dir), folder="domain")
        assert rule.validate() == []

    def test_folder_scoped_catches_violation_in_folder(self, service_dir):
        self._write(service_dir / "svc", "domain/models.py", "from x import *\n")
        rule = NoWildcardImportsRule(self._make_spec(service_dir), folder="domain")
        assert len(rule.validate()) == 1

    def test_nonexistent_folder_returns_error(self, service_dir):
        rule = NoWildcardImportsRule(self._make_spec(service_dir), folder="missing")
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].severity == "error"

    def test_rule_name(self, service_dir):
        rule = NoWildcardImportsRule(self._make_spec(service_dir))
        assert rule.rule_name == "no_wildcard_imports"
