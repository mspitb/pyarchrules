"""Unit tests for TreeStructureRule."""

import pytest

from pyarchrules.core.rules.tree_structure_rule import TreeStructureRule
from pyarchrules.model.spec import ServiceSpec, TreeNodeSpec


class TestTreeStructureRule:
    """Tests for TreeStructureRule validation logic."""

    @pytest.fixture
    def service_dir(self, tmp_path):
        """Create a service directory with api, domain, infra folders."""
        service = tmp_path / "my_service"
        service.mkdir()
        (service / "api").mkdir()
        (service / "domain").mkdir()
        (service / "infra").mkdir()
        return tmp_path

    def _make_spec(self, project_root, tree=None, name="my_service", path="my_service"):
        return ServiceSpec(
            name=name,
            path=path,
            project_root=project_root,
            tree=tree or {},
        )

    # -------------------------------------------------------------------------
    # Validation: required subdirs
    # -------------------------------------------------------------------------

    def test_no_tree_spec_passes(self, service_dir):
        """Passes when no tree spec is defined."""
        rule = TreeStructureRule(self._make_spec(service_dir))

        violations = rule.validate()

        assert len(violations) == 0

    def test_all_subdirs_present_passes(self, service_dir):
        """Passes when all required subdirs are present."""
        tree = {".": TreeNodeSpec(subdirs=["api", "domain"], allow_extra=True)}
        rule = TreeStructureRule(self._make_spec(service_dir, tree=tree))

        violations = rule.validate()

        assert len(violations) == 0

    def test_missing_subdirs_returns_error(self, service_dir):
        """Returns error when required subdirs are missing."""
        tree = {".": TreeNodeSpec(subdirs=["api", "domain", "tests"], allow_extra=True)}
        rule = TreeStructureRule(self._make_spec(service_dir, tree=tree))

        violations = rule.validate()

        assert len(violations) == 1
        assert violations[0].severity == "error"
        assert "tests" in violations[0].details["missing"]

    # -------------------------------------------------------------------------
    # Validation: extra dirs
    # -------------------------------------------------------------------------

    def test_extra_dirs_allowed_passes(self, service_dir):
        """Passes with extra dirs when allow_extra=True."""
        tree = {".": TreeNodeSpec(subdirs=["api"], allow_extra=True)}
        rule = TreeStructureRule(self._make_spec(service_dir, tree=tree))

        violations = rule.validate()

        assert len(violations) == 0

    def test_extra_dirs_not_allowed_returns_warning(self, service_dir):
        """Returns warning when extra dirs exist and allow_extra=False."""
        tree = {".": TreeNodeSpec(subdirs=["api"], allow_extra=False)}
        rule = TreeStructureRule(self._make_spec(service_dir, tree=tree))

        violations = rule.validate()

        assert len(violations) == 1
        assert violations[0].severity == "warning"
        assert (
            "domain" in violations[0].details["extra"] or "infra" in violations[0].details["extra"]
        )

    def test_missing_and_extra_returns_both_violations(self, service_dir):
        """Returns both missing and extra violations."""
        tree = {".": TreeNodeSpec(subdirs=["api", "tests"], allow_extra=False)}
        rule = TreeStructureRule(self._make_spec(service_dir, tree=tree))

        violations = rule.validate()

        assert len(violations) == 2
        messages = [v.message for v in violations]
        assert any("Missing" in m for m in messages)
        assert any("Extra" in m for m in messages)

    # -------------------------------------------------------------------------
    # Edge cases
    # -------------------------------------------------------------------------

    def test_service_directory_not_exists_returns_error(self, tmp_path):
        """Returns error when service directory doesn't exist."""
        tree = {".": TreeNodeSpec(subdirs=["api"], allow_extra=True)}
        rule = TreeStructureRule(self._make_spec(tmp_path, tree=tree, path="nonexistent"))

        violations = rule.validate()

        assert len(violations) == 1
        assert violations[0].severity == "error"
        assert "does not exist" in violations[0].message

    def test_validates_nested_paths(self, service_dir):
        """Validates nested directory paths correctly."""
        api_dir = service_dir / "my_service" / "api"
        (api_dir / "v1").mkdir()
        (api_dir / "v2").mkdir()

        tree = {"api": TreeNodeSpec(subdirs=["v1", "v2"], allow_extra=False)}
        rule = TreeStructureRule(self._make_spec(service_dir, tree=tree))

        violations = rule.validate()

        assert len(violations) == 0

    def test_rule_name_property(self, service_dir):
        """Rule has correct name."""
        rule = TreeStructureRule(self._make_spec(service_dir))

        assert rule.rule_name == "tree_structure"
