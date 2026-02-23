"""Unit tests for NoRelativeImportsRule."""

import pytest

from pyarchrules.core.rules.dsl.no_relative_imports_rule import NoRelativeImportsRule
from pyarchrules.model.spec import ServiceSpec


class TestNoRelativeImportsRule:

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

    def test_absolute_imports_pass(self, service_dir):
        self._write(
            service_dir / "svc", "api/views.py", "from domain.models import User\nimport os\n"
        )
        rule = NoRelativeImportsRule(self._make_spec(service_dir), folder="api")
        assert rule.validate() == []

    def test_relative_import_returns_error(self, service_dir):
        self._write(service_dir / "svc", "api/views.py", "from . import schemas\n")
        rule = NoRelativeImportsRule(self._make_spec(service_dir), folder="api")
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].rule_name == "no_relative_imports"
        assert violations[0].severity == "error"

    def test_deep_relative_import_returns_error(self, service_dir):
        self._write(service_dir / "svc", "api/views.py", "from ..domain import models\n")
        rule = NoRelativeImportsRule(self._make_spec(service_dir), folder="api")
        assert len(rule.validate()) == 1

    def test_relative_import_in_other_folder_not_flagged(self, service_dir):
        # relative import lives in domain/, but rule only checks api/
        self._write(service_dir / "svc", "domain/service.py", "from . import repo\n")
        self._write(service_dir / "svc", "api/views.py", "from domain.models import User\n")
        rule = NoRelativeImportsRule(self._make_spec(service_dir), folder="api")
        assert rule.validate() == []

    def test_nonexistent_folder_returns_error(self, service_dir):
        rule = NoRelativeImportsRule(self._make_spec(service_dir), folder="missing")
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].severity == "error"

    def test_rule_name(self, service_dir):
        (service_dir / "svc" / "api").mkdir()
        rule = NoRelativeImportsRule(self._make_spec(service_dir), folder="api")
        assert rule.rule_name == "no_relative_imports"
