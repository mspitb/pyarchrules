"""Unit tests for LayerMustNotImportRule."""

import pytest

from pyarchrules.core.rules.dsl.layer_must_not_import_rule import LayerMustNotImportRule
from pyarchrules.model.spec import ServiceSpec


class TestLayerMustNotImportRule:

    @pytest.fixture
    def service_dir(self, tmp_path):
        svc = tmp_path / "svc"
        (svc / "domain").mkdir(parents=True)
        (svc / "infra").mkdir(parents=True)
        return tmp_path

    def _make_spec(self, root):
        return ServiceSpec(name="svc", path="svc", project_root=root)

    def _write(self, base, rel, content):
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    # ------------------------------------------------------------------

    def test_no_forbidden_import_passes(self, service_dir):
        self._write(service_dir / "svc", "domain/service.py", "from pydantic import BaseModel\n")
        rule = LayerMustNotImportRule(self._make_spec(service_dir), source="domain", target="infra")
        assert rule.validate() == []

    def test_absolute_import_of_target_returns_error(self, service_dir):
        self._write(service_dir / "svc", "domain/service.py", "from infra.db import Session\n")
        rule = LayerMustNotImportRule(self._make_spec(service_dir), source="domain", target="infra")
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].rule_name == "layer_must_not_import"
        assert violations[0].details["source"] == "domain"
        assert violations[0].details["target"] == "infra"

    def test_unrelated_absolute_import_passes(self, service_dir):
        self._write(service_dir / "svc", "domain/service.py", "import pydantic\n")
        rule = LayerMustNotImportRule(self._make_spec(service_dir), source="domain", target="infra")
        assert rule.validate() == []

    def test_nonexistent_source_returns_error(self, service_dir):
        rule = LayerMustNotImportRule(
            self._make_spec(service_dir), source="missing", target="infra"
        )
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].severity == "error"

    def test_rule_name(self, service_dir):
        rule = LayerMustNotImportRule(self._make_spec(service_dir), source="domain", target="infra")
        assert rule.rule_name == "layer_must_not_import"
