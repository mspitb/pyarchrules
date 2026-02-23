"""Unit tests for NoCircularImportsRule."""

import pytest

from pyarchrules.core.rules.dsl.no_circular_imports_rule import NoCircularImportsRule
from pyarchrules.model.spec import ServiceSpec


class TestNoCircularImportsRule:

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

    def test_no_imports_passes(self, service_dir):
        self._write(service_dir / "svc", "domain/models.py", "x = 1\n")
        rule = NoCircularImportsRule(self._make_spec(service_dir))
        assert rule.validate() == []

    def test_linear_dependency_passes(self, service_dir):
        # a → b, no cycle
        self._write(service_dir / "svc", "domain/__init__.py", "")
        self._write(service_dir / "svc", "domain/a.py", "from . import b\n")
        self._write(service_dir / "svc", "domain/b.py", "x = 1\n")
        rule = NoCircularImportsRule(self._make_spec(service_dir))
        assert rule.validate() == []

    def test_direct_cycle_returns_error(self, service_dir):
        # a → b → a  (relative imports within the domain package)
        self._write(service_dir / "svc", "domain/__init__.py", "")
        self._write(service_dir / "svc", "domain/a.py", "from . import b\n")
        self._write(service_dir / "svc", "domain/b.py", "from . import a\n")
        rule = NoCircularImportsRule(self._make_spec(service_dir))
        violations = rule.validate()
        assert len(violations) >= 1
        assert violations[0].rule_name == "no_circular_imports"
        assert violations[0].severity == "error"
        assert "cycle" in violations[0].details

    def test_folder_scoped_ignores_cycle_outside_folder(self, service_dir):
        # cycle in api/, but rule only checks domain/
        self._write(service_dir / "svc", "api/a.py", "from . import b\n")
        self._write(service_dir / "svc", "api/b.py", "from . import a\n")
        self._write(service_dir / "svc", "domain/models.py", "x = 1\n")
        rule = NoCircularImportsRule(self._make_spec(service_dir), folder="domain")
        assert rule.validate() == []

    def test_nonexistent_folder_returns_error(self, service_dir):
        rule = NoCircularImportsRule(self._make_spec(service_dir), folder="missing")
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].severity == "error"

    def test_rule_name(self, service_dir):
        rule = NoCircularImportsRule(self._make_spec(service_dir))
        assert rule.rule_name == "no_circular_imports"
