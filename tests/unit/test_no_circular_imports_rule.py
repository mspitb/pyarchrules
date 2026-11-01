"""Unit tests for NoCircularImportsRule."""

import pytest

from pyarchrules.core.rules.checks.imports import detect_cycles
from pyarchrules.core.rules.no_circular_imports_rule import NoCircularImportsRule
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
        # a â†’ b, no cycle
        self._write(service_dir / "svc", "domain/__init__.py", "")
        self._write(service_dir / "svc", "domain/a.py", "from . import b\n")
        self._write(service_dir / "svc", "domain/b.py", "x = 1\n")
        rule = NoCircularImportsRule(self._make_spec(service_dir))
        assert rule.validate() == []

    def test_direct_cycle_returns_error(self, service_dir):
        # a â†’ b â†’ a  (relative imports within the domain package)
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

    def test_absolute_import_cycle_is_detected(self, service_dir):
        self._write(service_dir / "svc", "domain/a.py", "from domain import b\n")
        self._write(service_dir / "svc", "domain/b.py", "import domain.a\n")
        violations = NoCircularImportsRule(self._make_spec(service_dir)).validate()
        assert len(violations) == 1
        assert violations[0].details["cycle"] == ["domain/a", "domain/b", "domain/a"]

    def test_service_name_prefixed_absolute_import_cycle(self, service_dir):
        self._write(service_dir / "svc", "a.py", "from svc.b import x\n")
        self._write(service_dir / "svc", "b.py", "from svc.a import y\n")
        assert len(NoCircularImportsRule(self._make_spec(service_dir)).validate()) == 1

    def test_type_checking_import_does_not_form_cycle(self, service_dir):
        self._write(
            service_dir / "svc",
            "a.py",
            "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from b import X\n",
        )
        self._write(service_dir / "svc", "b.py", "from a import y\n")
        assert NoCircularImportsRule(self._make_spec(service_dir)).validate() == []

    def test_each_cycle_is_reported_once(self, service_dir):
        self._write(service_dir / "svc", "a.py", "import b\nimport c\n")
        self._write(service_dir / "svc", "b.py", "import c\n")
        self._write(service_dir / "svc", "c.py", "import a\n")
        assert len(NoCircularImportsRule(self._make_spec(service_dir)).validate()) == 1

    def test_detect_cycles_handles_deep_graph(self):
        graph = {f"m{i}": {f"m{i + 1}"} for i in range(5000)}
        graph["m5000"] = {"m0"}
        assert len(detect_cycles(graph)) == 1
