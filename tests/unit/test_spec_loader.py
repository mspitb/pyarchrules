"""Unit tests for SpecLoader."""

import pytest

from pyarchrules.core.errors import PyArchError
from pyarchrules.core.spec_loader import SpecLoader
from pyarchrules.model.spec import ProjectSpec, ServiceSpec


class TestSpecLoader:
    """Tests for SpecLoader configuration loading."""

    # -------------------------------------------------------------------------
    # Basic loading
    # -------------------------------------------------------------------------

    def test_returns_project_spec(self, make_project):
        """Returns ProjectSpec instance."""
        project = make_project(with_pyproject=True, services={"svc": "services/svc"})

        spec = SpecLoader(project.root).load()

        assert isinstance(spec, ProjectSpec)

    def test_returns_services_as_service_spec(self, make_project):
        """Services are returned as ServiceSpec instances."""
        project = make_project(with_pyproject=True, services={"svc": "services/svc"})

        spec = SpecLoader(project.root).load()

        assert "svc" in spec.services
        assert isinstance(spec.services["svc"], ServiceSpec)
        assert spec.services["svc"].name == "svc"
        assert spec.services["svc"].path == "services/svc"

    def test_fallback_to_root_service(self, make_project):
        """Falls back to root service when no services defined."""
        project = make_project(with_pyproject=True, services=None)

        spec = SpecLoader(project.root).load()

        assert "root" in spec.services
        assert spec.services["root"].path == "."


    # -------------------------------------------------------------------------
    # Service options
    # -------------------------------------------------------------------------


    def test_parses_internal_dependencies(self, tmp_test_dir):
        """dependencies (internal layer rules) is parsed correctly."""
        root = tmp_test_dir / "internal_deps"
        root.mkdir(parents=True, exist_ok=True)
        (root / "services/svc").mkdir(parents=True)

        toml_content = """
[project]
name = "test"

[tool.pyarchrules.services.svc]
path = "services/svc"
dependencies = ["api -> domain", "domain -> infra"]
"""
        (root / "pyproject.toml").write_text(toml_content, encoding="utf-8")

        spec = SpecLoader(root).load()

        assert spec.services["svc"].dependencies == ["api -> domain", "domain -> infra"]

    def test_parses_tree_structure(self, tmp_test_dir):
        """tree structure specification is parsed correctly as list of strings."""
        root = tmp_test_dir / "tree_test"
        root.mkdir(parents=True, exist_ok=True)
        (root / "services/svc").mkdir(parents=True)

        toml_content = """
        [project]
        name = "test"
        [tool.pyarchrules.services.svc]
        path = "services/svc"
        tree = ["api", "domain", "infra", "api/v1"]
        tree_mode = "strict"
        tree_allow_files = false
        """
        (root / "pyproject.toml").write_text(toml_content, encoding="utf-8")

        from pyarchrules.model.spec.service_spec import TreeMode
        spec = SpecLoader(root).load()

        assert spec.services["svc"].tree == ["api", "domain", "infra", "api/v1"]
        assert spec.services["svc"].tree_mode == TreeMode.STRICT
        assert spec.services["svc"].tree_allow_files is False

    def test_parses_tree_allow_files_default(self, tmp_test_dir):
        """tree_allow_files defaults to True when not specified."""
        root = tmp_test_dir / "tree_default"
        root.mkdir(parents=True, exist_ok=True)
        (root / "services/svc").mkdir(parents=True)

        toml_content = """
        [project]
        name = "test"
        [tool.pyarchrules.services.svc]
        path = "services/svc"
        tree = ["api"]
        tree_mode = "exact"
        """
        (root / "pyproject.toml").write_text(toml_content, encoding="utf-8")

        spec = SpecLoader(root).load()

        assert spec.services["svc"].tree_allow_files is True  # default

    # -------------------------------------------------------------------------
    # Path validation
    # -------------------------------------------------------------------------

    def test_path_outside_project_raises_error(self, make_project):
        """Raises error when path is outside project root."""
        project = make_project(with_pyproject=True, services={"svc": "../outside"})

        with pytest.raises(PyArchError, match="outside project root"):
            SpecLoader(project.root).load()

    def test_nonexistent_path_raises_error(self, make_project):
        """Raises error when path doesn't exist."""
        project = make_project(
            with_pyproject=True,
            services={"svc": "nonexistent"},
            create_service_dirs=False,
        )

        with pytest.raises(PyArchError, match="doesn't exist"):
            SpecLoader(project.root).load()

    def test_string_shorthand_is_rejected(self, tmp_test_dir):
        """Service value must be a table — string shorthand is no longer accepted."""
        root = tmp_test_dir / "string_shorthand"
        root.mkdir(parents=True, exist_ok=True)
        (root / "svc").mkdir(parents=True)

        toml_content = """
[project]
name = "test"

[tool.pyarchrules.services]
svc = "svc"
"""
        (root / "pyproject.toml").write_text(toml_content, encoding="utf-8")

        with pytest.raises(PyArchError, match="must be a table"):
            SpecLoader(root).load()

    def test_unknown_project_key_rejected(self, make_project):
        """Removed project keys (root, validate_paths) are no longer accepted."""
        project = make_project(
            with_pyproject=True,
            services={"svc": "services/svc"},
            extra_config={"validate_paths": True},
        )

        with pytest.raises(PyArchError, match="Unknown key"):
            SpecLoader(project.root).load()

    def test_parses_no_circular_imports(self, make_project):
        """no_circular_imports = true is parsed onto ServiceSpec."""
        project = make_project(
            with_pyproject=False,
            services={"svc": "svc"},
        )
        project.write_pyproject({
            "project": {"name": "test"},
            "tool": {"pyarchrules": {
                "services": {"svc": {"path": "svc", "no_circular_imports": True}},
            }},
        })
        project.mkdir("svc")

        spec = SpecLoader(project.root).load()

        assert spec.services["svc"].no_circular_imports is True
