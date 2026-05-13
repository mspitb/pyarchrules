"""Tests for tree dedup validation and tree_ignore patterns."""

from __future__ import annotations

import pytest

from pyarchrules.core.errors import ConfigError
from pyarchrules.core.rules.linter.tree_rule import TreeRule
from pyarchrules.model.spec.service_spec import TreeMode
from pyarchrules.pyarchrules import PyArchRules


# ---------------------------------------------------------------------------
# Duplicate tree entries
# ---------------------------------------------------------------------------


class TestTreeDuplicateRejection:
    def test_toml_loader_rejects_duplicates(self, make_project):
        project = make_project(
            services={"api": "src/api"},
            extra_config={
                "services": {"api": {"path": "src/api", "tree": ["api", "api", "domain"]}}
            },
        )
        with pytest.raises(ConfigError, match="duplicate entries in 'tree'"):
            PyArchRules(project.root)

    def test_dsl_rejects_duplicates(self, make_project):
        project = make_project(services={"api": "src/api"})
        rules = PyArchRules(project.root)
        with pytest.raises(ConfigError, match="duplicate entries in 'tree'"):
            rules.for_service("api").tree_structure(["api", "api", "domain"])

    def test_dsl_accepts_unique_tree(self, make_project):
        project = make_project(services={"api": "src/api"})
        project.mkdir("src/api/api")
        project.mkdir("src/api/domain")
        rules = PyArchRules(project.root)
        # Should NOT raise.
        rules.for_service("api").tree_structure(["api", "domain"])


# ---------------------------------------------------------------------------
# tree_ignore patterns
# ---------------------------------------------------------------------------


class TestTreeIgnore:
    def test_ignored_dir_does_not_trigger_strict(self, make_service_spec, tmp_test_dir):
        (tmp_test_dir / "api").mkdir()
        (tmp_test_dir / "domain").mkdir()
        (tmp_test_dir / "__snapshots__").mkdir()  # would be "extra" without ignore

        spec = make_service_spec(
            tree=["api", "domain"],
            tree_mode=TreeMode.STRICT,
            tree_ignore=["__snapshots__"],
        )
        violations = TreeRule(spec).validate()
        assert violations == []

    def test_glob_pattern_works(self, make_service_spec, tmp_test_dir):
        (tmp_test_dir / "api").mkdir()
        (tmp_test_dir / "migrations_001").mkdir()
        (tmp_test_dir / "migrations_002").mkdir()

        spec = make_service_spec(
            tree=["api"],
            tree_mode=TreeMode.STRICT,
            tree_ignore=["migrations_*"],
        )
        violations = TreeRule(spec).validate()
        assert violations == []

    def test_non_ignored_extra_still_reported(self, make_service_spec, tmp_test_dir):
        (tmp_test_dir / "api").mkdir()
        (tmp_test_dir / "__snapshots__").mkdir()  # ignored
        (tmp_test_dir / "junk").mkdir()           # NOT ignored

        spec = make_service_spec(
            tree=["api"],
            tree_mode=TreeMode.STRICT,
            tree_ignore=["__snapshots__"],
        )
        violations = TreeRule(spec).validate()
        warnings = [v for v in violations if v.severity == "warning"]
        assert any("junk" in v.message for v in warnings)
        assert not any("__snapshots__" in v.message for v in warnings)

    def test_exact_mode_skips_ignored_leaf_children(self, make_service_spec, tmp_test_dir):
        (tmp_test_dir / "domain").mkdir()
        (tmp_test_dir / "domain" / "__snapshots__").mkdir()
        (tmp_test_dir / "domain" / "rogue").mkdir()

        spec = make_service_spec(
            tree=["domain"],
            tree_mode=TreeMode.EXACT,
            tree_ignore=["__snapshots__"],
        )
        violations = TreeRule(spec).validate()
        warnings = [v for v in violations if v.severity == "warning"]
        assert any("rogue" in v.message for v in warnings)
        assert not any("__snapshots__" in v.message for v in warnings)

    def test_dsl_passes_ignore(self, make_project):
        project = make_project(services={"api": "src/api"})
        project.mkdir("src/api/domain")
        project.mkdir("src/api/__snapshots__")

        rules = PyArchRules(project.root)
        rules.for_service("api").tree_structure(
            ["domain"], mode="strict", ignore=["__snapshots__"]
        )
        result = rules.validate(raise_on_violation=False, verbose=False)
        assert result.is_valid

    def test_toml_loader_rejects_bad_tree_ignore_type(self, make_project):
        project = make_project(
            services={"api": "src/api"},
            extra_config={
                "services": {
                    "api": {"path": "src/api", "tree_ignore": "not a list"}
                }
            },
        )
        with pytest.raises(ConfigError, match="tree_ignore.*must be a list"):
            PyArchRules(project.root)

