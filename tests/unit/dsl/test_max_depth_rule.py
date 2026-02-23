"""Unit tests for MaxDepthRule."""

import pytest

from pyarchrules.core.rules.dsl.max_depth_rule import MaxDepthRule
from pyarchrules.model.spec import ServiceSpec


class TestMaxDepthRule:

    @pytest.fixture
    def service_dir(self, tmp_path):
        svc = tmp_path / "svc"
        svc.mkdir()
        return tmp_path

    def _make_spec(self, root):
        return ServiceSpec(name="svc", path="svc", project_root=root)

    # ------------------------------------------------------------------

    def test_flat_structure_within_limit_passes(self, service_dir):
        (service_dir / "svc" / "api").mkdir()
        (service_dir / "svc" / "domain").mkdir()
        rule = MaxDepthRule(self._make_spec(service_dir), max_depth=1)
        assert rule.validate() == []

    def test_depth_exactly_at_limit_passes(self, service_dir):
        (service_dir / "svc" / "a" / "b").mkdir(parents=True)
        rule = MaxDepthRule(self._make_spec(service_dir), max_depth=2)
        assert rule.validate() == []

    def test_depth_exceeding_limit_returns_error(self, service_dir):
        (service_dir / "svc" / "a" / "b" / "c").mkdir(parents=True)
        rule = MaxDepthRule(self._make_spec(service_dir), max_depth=2)
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].rule_name == "max_depth"
        assert violations[0].details["actual_depth"] == 3
        assert violations[0].details["max_depth"] == 2

    def test_empty_service_dir_passes(self, service_dir):
        rule = MaxDepthRule(self._make_spec(service_dir), max_depth=0)
        assert rule.validate() == []

    def test_folder_scoped_check(self, service_dir):
        # api is shallow, domain is deep — scoped to domain only
        (service_dir / "svc" / "api").mkdir()
        (service_dir / "svc" / "domain" / "a" / "b" / "c").mkdir(parents=True)
        rule = MaxDepthRule(self._make_spec(service_dir), max_depth=2, folder="domain")
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].details["actual_depth"] == 3

    def test_nonexistent_folder_returns_error(self, service_dir):
        rule = MaxDepthRule(self._make_spec(service_dir), max_depth=2, folder="missing")
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].severity == "error"

    def test_rule_name(self, service_dir):
        rule = MaxDepthRule(self._make_spec(service_dir), max_depth=3)
        assert rule.rule_name == "max_depth"
