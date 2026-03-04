"""Tests for TreeRule (tree_mode: exists / strict / full)."""

import pytest

from pyarchrules.core.rules.linter.tree_rule import TreeRule
from pyarchrules.model.spec.service_spec import TreeMode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_dirs(base, *paths):
    for p in paths:
        (base / p).mkdir(parents=True, exist_ok=True)

def make_files(base, *paths):
    for p in paths:
        f = base / p
        f.parent.mkdir(parents=True, exist_ok=True)
        f.touch()


# ---------------------------------------------------------------------------
# Common (all modes)
# ---------------------------------------------------------------------------

class TestTreeCommon:
    def test_no_tree_passes(self, make_service_spec):
        assert TreeRule(make_service_spec()).validate() == []

    def test_empty_tree_passes(self, make_service_spec):
        assert TreeRule(make_service_spec(tree=[])).validate() == []

    def test_service_dir_missing_returns_error(self, make_service_spec):
        spec = make_service_spec(path="nonexistent", tree=["api"])
        v = TreeRule(spec).validate()
        assert len(v) == 1 and v[0].severity == "error" and "does not exist" in v[0].message

    def test_rule_name(self, make_service_spec):
        assert TreeRule(make_service_spec()).rule_name == "tree_structure"

    @pytest.mark.parametrize("mode", [TreeMode.EXISTS, TreeMode.STRICT, TreeMode.EXACT])
    def test_all_declared_paths_present_passes(
        self, make_service_spec, tmp_test_dir, monkeypatch, mode
    ):
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "api/v1", "domain")
        spec = make_service_spec(tree=["api", "api/v1", "domain"], tree_mode=mode)
        assert TreeRule(spec).validate() == []

    @pytest.mark.parametrize("mode", [TreeMode.EXISTS, TreeMode.STRICT, TreeMode.EXACT])
    def test_missing_declared_path_returns_error(
        self, make_service_spec, tmp_test_dir, monkeypatch, mode
    ):
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api")
        spec = make_service_spec(tree=["api", "domain"], tree_mode=mode)
        v = TreeRule(spec).validate()
        errors = [x for x in v if x.severity == "error"]
        assert len(errors) == 1
        assert "domain" in errors[0].details["missing_paths"]


# ---------------------------------------------------------------------------
# mode = "exists"
# ---------------------------------------------------------------------------

class TestTreeModeExists:
    """Extra directories anywhere are silently ignored."""

    def test_extra_at_root_ignored(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "domain", "unexpected")
        spec = make_service_spec(tree=["api", "domain"], tree_mode=TreeMode.EXISTS)
        assert TreeRule(spec).validate() == []

    def test_extra_inside_declared_dir_ignored(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "api/internal")
        spec = make_service_spec(tree=["api"], tree_mode=TreeMode.EXISTS)
        assert TreeRule(spec).validate() == []

    def test_is_default_mode(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "extra")
        spec = make_service_spec(tree=["api"])  # no tree_mode → EXISTS
        assert TreeRule(spec).validate() == []


# ---------------------------------------------------------------------------
# mode = "strict"
# ---------------------------------------------------------------------------

class TestTreeModeStrict:
    """No extra dirs at covered levels; leaf internals are not inspected."""

    def test_regression_extra_at_root_caught(self, make_service_spec, tmp_test_dir, monkeypatch):
        """tree=[a,b], dirs a/b/c on disk → strict must flag c at root."""
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "a", "b", "c")
        spec = make_service_spec(tree=["a", "b"], tree_mode=TreeMode.STRICT)
        v = TreeRule(spec).validate()
        warnings = [x for x in v if x.severity == "warning"]
        assert len(warnings) == 1
        assert warnings[0].details["path"] == "."
        assert "c" in warnings[0].details["extra_items"]
        assert "a" not in warnings[0].details["extra_items"]

    def test_extra_sibling_inside_non_leaf_caught(
        self, make_service_spec, tmp_test_dir, monkeypatch
    ):
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "api/v1", "api/v2")  # v2 not in tree
        spec = make_service_spec(tree=["api", "api/v1"], tree_mode=TreeMode.STRICT)
        v = TreeRule(spec).validate()
        warnings = [x for x in v if x.severity == "warning"]
        assert len(warnings) == 1
        assert warnings[0].details["path"] == "api"
        assert "v2" in warnings[0].details["extra_items"]

    def test_leaf_internals_not_inspected(self, make_service_spec, tmp_test_dir, monkeypatch):
        """Strict does NOT look inside leaf dirs — that is full mode's job."""
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "api/hidden")  # api is a leaf
        spec = make_service_spec(tree=["api"], tree_mode=TreeMode.STRICT)
        assert TreeRule(spec).validate() == []

    def test_exact_match_passes(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "api/v1", "domain")
        spec = make_service_spec(tree=["api", "api/v1", "domain"], tree_mode=TreeMode.STRICT)
        assert TreeRule(spec).validate() == []

    def test_allow_files_true_tolerates_loose_files(
        self, make_service_spec, tmp_test_dir, monkeypatch
    ):
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "api/v1")
        make_files(tmp_test_dir, "api/router.py", "api/readme.md")
        spec = make_service_spec(
            tree=["api", "api/v1"], tree_mode=TreeMode.STRICT, tree_allow_files=True
        )
        assert [x for x in TreeRule(spec).validate() if x.severity == "warning"] == []

    def test_allow_files_false_catches_loose_files(
        self, make_service_spec, tmp_test_dir, monkeypatch
    ):
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "api/v1")
        make_files(tmp_test_dir, "api/loose.py")
        spec = make_service_spec(
            tree=["api", "api/v1"], tree_mode=TreeMode.STRICT, tree_allow_files=False
        )
        v = TreeRule(spec).validate()
        warnings = [x for x in v if x.severity == "warning"]
        assert any("loose.py" in w.details["extra_items"] for w in warnings)

    def test_multiple_covered_levels_each_violation_separate(
        self, make_service_spec, tmp_test_dir, monkeypatch
    ):
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "api/v1", "domain", "infra", "api/v2")
        # infra → extra at root; v2 → extra inside api
        spec = make_service_spec(
            tree=["api", "api/v1", "domain"], tree_mode=TreeMode.STRICT
        )
        v = TreeRule(spec).validate()
        warnings = [x for x in v if x.severity == "warning"]
        paths = {w.details["path"] for w in warnings}
        assert "." in paths      # infra caught at root
        assert "api" in paths    # v2 caught inside api


# ---------------------------------------------------------------------------
# mode = "full"
# ---------------------------------------------------------------------------

class TestTreeModeExact:
    """Strict + recursive walk inside leaf directories."""

    def test_extra_at_root_caught(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "domain", "infra")  # infra not in tree
        spec = make_service_spec(tree=["api", "domain"], tree_mode=TreeMode.EXACT)
        v = TreeRule(spec).validate()
        warnings = [x for x in v if "extra_items" in x.details]
        assert any("infra" in w.details["extra_items"] for w in warnings)

    def test_undeclared_inside_leaf_caught(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "api/internal")  # api is a leaf
        spec = make_service_spec(tree=["api"], tree_mode=TreeMode.EXACT)
        v = TreeRule(spec).validate()
        recursive = [x for x in v if "undeclared_paths" in x.details]
        assert len(recursive) == 1
        assert "api/internal" in recursive[0].details["undeclared_paths"]

    def test_undeclared_deep_inside_leaf_caught(
        self, make_service_spec, tmp_test_dir, monkeypatch
    ):
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "api/v1", "api/v1/handlers")  # api is a leaf
        spec = make_service_spec(tree=["api"], tree_mode=TreeMode.EXACT)
        v = TreeRule(spec).validate()
        recursive = [x for x in v if "undeclared_paths" in x.details]
        assert len(recursive) == 1
        undeclared = recursive[0].details["undeclared_paths"]
        assert "api/v1" in undeclared
        assert "api/v1/handlers" in undeclared

    def test_non_leaf_extra_caught_by_strict_not_recursive(
        self, make_service_spec, tmp_test_dir, monkeypatch
    ):
        """v2 is inside non-leaf api → strict catches it; recursive doesn't."""
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "api/v1", "api/v2")  # api is non-leaf
        spec = make_service_spec(tree=["api", "api/v1"], tree_mode=TreeMode.EXACT)
        v = TreeRule(spec).validate()
        strict_v = [x for x in v if "extra_items" in x.details]
        recursive_v = [x for x in v if "undeclared_paths" in x.details]
        assert any("v2" in x.details["extra_items"] for x in strict_v)
        assert len(recursive_v) == 0

    def test_leaf_extra_caught_by_recursive_not_strict(
        self, make_service_spec, tmp_test_dir, monkeypatch
    ):
        """api/internal is inside leaf api → recursive catches it; strict doesn't."""
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "api/internal")  # api is a leaf
        spec = make_service_spec(tree=["api"], tree_mode=TreeMode.EXACT)
        v = TreeRule(spec).validate()
        strict_v = [x for x in v if "extra_items" in x.details]
        recursive_v = [x for x in v if "undeclared_paths" in x.details]
        assert len(strict_v) == 0
        assert any("api/internal" in x.details["undeclared_paths"] for x in recursive_v)

    def test_exact_match_passes(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "api/v1", "domain")
        spec = make_service_spec(tree=["api", "api/v1", "domain"], tree_mode=TreeMode.EXACT)
        assert TreeRule(spec).validate() == []

    def test_files_not_flagged_by_recursive(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api")
        make_files(tmp_test_dir, "api/router.py")
        spec = make_service_spec(tree=["api"], tree_mode=TreeMode.EXACT, tree_allow_files=True)
        recursive_v = [x for x in TreeRule(spec).validate() if "undeclared_paths" in x.details]
        assert len(recursive_v) == 0

    def test_hidden_and_dunder_dirs_ignored(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(tmp_test_dir, "api", "api/.git", "api/__pycache__")
        spec = make_service_spec(tree=["api"], tree_mode=TreeMode.EXACT)
        assert TreeRule(spec).validate() == []

    def test_multiple_leaves_violations_in_one_report(
        self, make_service_spec, tmp_test_dir, monkeypatch
    ):
        """All undeclared dirs from all leaves are collected into one violation."""
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(
            tmp_test_dir,
            "api", "api/internal",          # api is a leaf
            "domain", "domain/core",         # domain is a leaf
        )
        spec = make_service_spec(tree=["api", "domain"], tree_mode=TreeMode.EXACT)
        v = TreeRule(spec).validate()
        recursive_v = [x for x in v if "undeclared_paths" in x.details]
        assert len(recursive_v) == 1
        undeclared = recursive_v[0].details["undeclared_paths"]
        assert "api/internal" in undeclared
        assert "domain/core" in undeclared

    def test_strict_and_leaf_violations_coexist(
        self, make_service_spec, tmp_test_dir, monkeypatch
    ):
        """infra at root (strict) + internal inside leaf domain (recursive) — no overlap."""
        monkeypatch.chdir(tmp_test_dir)
        make_dirs(
            tmp_test_dir,
            "api", "api/v1",    # api non-leaf, v1 is leaf
            "domain",           # leaf
            "domain/core",      # undeclared inside leaf → recursive
            "infra",            # undeclared at root → strict
        )
        spec = make_service_spec(
            tree=["api", "api/v1", "domain"], tree_mode=TreeMode.EXACT
        )
        v = TreeRule(spec).validate()
        strict_v = [x for x in v if "extra_items" in x.details]
        recursive_v = [x for x in v if "undeclared_paths" in x.details]

        assert any("infra" in x.details["extra_items"] for x in strict_v)
        assert any("domain/core" in x.details["undeclared_paths"] for x in recursive_v)
        # no overlap: domain/core not in strict, infra not in recursive
        assert not any("domain/core" in x.details.get("extra_items", []) for x in strict_v)
        assert not any("infra" in x.details.get("undeclared_paths", []) for x in recursive_v)


# ---------------------------------------------------------------------------
# SpecLoader integration
# ---------------------------------------------------------------------------

class TestTreeModeSpecLoader:
    def test_default_mode_is_exists(self, make_project, tmp_test_dir):
        project = make_project(
            with_pyproject=True,
            services={"svc": "svc"},
            create_service_dirs=True,
        )
        from pyarchrules.core.spec_loader import SpecLoader
        spec = SpecLoader(project.root).load()
        assert spec.services["svc"].tree_mode == TreeMode.EXISTS

    def test_strict_mode_parsed(self, make_project):
        project = make_project(with_pyproject=False)
        project.write_pyproject({
            "project": {"name": "test"},
            "tool": {"pyarchrules": {
                "validate_paths": False,
                "services": {"svc": {"path": ".", "tree_mode": "strict"}},
            }},
        })
        from pyarchrules.core.spec_loader import SpecLoader
        spec = SpecLoader(project.root).load()
        assert spec.services["svc"].tree_mode == TreeMode.STRICT

    def test_exact_mode_parsed(self, make_project):
        project = make_project(with_pyproject=False)
        project.write_pyproject({
            "project": {"name": "test"},
            "tool": {"pyarchrules": {
                "validate_paths": False,
                "services": {"svc": {"path": ".", "tree_mode": "exact"}},
            }},
        })
        from pyarchrules.core.spec_loader import SpecLoader
        spec = SpecLoader(project.root).load()
        assert spec.services["svc"].tree_mode == TreeMode.EXACT

    def test_invalid_mode_raises_error(self, make_project):
        from pyarchrules.core.errors import PyArchError
        from pyarchrules.core.spec_loader import SpecLoader
        project = make_project(with_pyproject=False)
        project.write_pyproject({
            "project": {"name": "test"},
            "tool": {"pyarchrules": {
                "validate_paths": False,
                "services": {"svc": {"path": ".", "tree_mode": "turbo"}},
            }},
        })
        with pytest.raises(PyArchError, match="invalid tree_mode"):
            SpecLoader(project.root).load()
