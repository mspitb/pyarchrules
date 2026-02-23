"""Unit tests for NoPrivateImportsRule."""

import pytest

from pyarchrules.core.rules.dsl.no_private_imports_rule import NoPrivateImportsRule
from pyarchrules.model.spec import ServiceSpec


class TestNoPrivateImportsRule:

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

    def test_clean_public_import_passes(self, service_dir):
        self._write(service_dir / "svc", "api/views.py", "from domain.models import User\n")
        rule = NoPrivateImportsRule(self._make_spec(service_dir))
        assert rule.validate() == []

    def test_import_private_name_returns_error(self, service_dir):
        self._write(
            service_dir / "svc", "api/views.py", "from domain.models import _internal_helper\n"
        )
        rule = NoPrivateImportsRule(self._make_spec(service_dir))
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].rule_name == "no_private_imports"
        assert "_internal_helper" in violations[0].details["names"]

    def test_import_private_module_returns_error(self, service_dir):
        self._write(service_dir / "svc", "api/views.py", "import _secrets\n")
        rule = NoPrivateImportsRule(self._make_spec(service_dir))
        violations = rule.validate()
        assert len(violations) == 1
        assert "_secrets" in violations[0].message

    def test_relative_import_of_private_is_allowed(self, service_dir):
        # Relative imports (own package) must not be flagged
        self._write(service_dir / "svc", "domain/service.py", "from ._helpers import _build\n")
        rule = NoPrivateImportsRule(self._make_spec(service_dir))
        assert rule.validate() == []

    def test_dunder_import_is_allowed(self, service_dir):
        self._write(service_dir / "svc", "domain/models.py", "from domain import __version__\n")
        rule = NoPrivateImportsRule(self._make_spec(service_dir))
        assert rule.validate() == []

    def test_folder_scoped_ignores_other_folder(self, service_dir):
        self._write(service_dir / "svc", "api/views.py", "from x import _secret\n")
        self._write(service_dir / "svc", "domain/models.py", "from x import Foo\n")
        rule = NoPrivateImportsRule(self._make_spec(service_dir), folder="domain")
        assert rule.validate() == []

    def test_rule_name(self, service_dir):
        rule = NoPrivateImportsRule(self._make_spec(service_dir))
        assert rule.rule_name == "no_private_imports"
