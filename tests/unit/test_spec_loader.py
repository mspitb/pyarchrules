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
    # Global options
    # -------------------------------------------------------------------------

    def test_default_strict_is_true(self, make_project):
        """Default strict is True when not specified."""
        project = make_project(with_pyproject=True, services={"svc": "services/svc"})

        spec = SpecLoader(project.root).load()

        assert spec.strict is True

    def test_parses_strict_false(self, make_project):
        """strict = false is correctly parsed."""
        project = make_project(
            with_pyproject=True,
            services={"svc": "services/svc"},
            extra_config={"strict": False},
        )

        spec = SpecLoader(project.root).load()

        assert spec.strict is False

    def test_default_validate_paths_is_true(self, make_project):
        """Default validate_paths is True when not specified."""
        project = make_project(with_pyproject=True, services={"svc": "services/svc"})

        spec = SpecLoader(project.root).load()

        assert spec.validate_paths is True

    def test_parses_validate_paths_false(self, make_project):
        """validate_paths = false is correctly parsed."""
        project = make_project(
            with_pyproject=True,
            services={"svc": "services/svc"},
            extra_config={"validate_paths": False},
            create_service_dirs=True,
        )

        spec = SpecLoader(project.root).load()

        assert spec.validate_paths is False

    # -------------------------------------------------------------------------
    # Service options
    # -------------------------------------------------------------------------

    def test_parses_allowed_service_dependencies(self, tmp_test_dir):
        """allowed_service_dependencies is parsed correctly."""
        root = tmp_test_dir / "deps_test"
        root.mkdir(parents=True, exist_ok=True)
        (root / "services/api").mkdir(parents=True)
        (root / "services/auth").mkdir(parents=True)

        toml_content = """
[project]
name = "test"

[tool.pyarchrules.services.api]
path = "services/api"
allowed_service_dependencies = ["auth"]

[tool.pyarchrules.services.auth]
path = "services/auth"
"""
        (root / "pyproject.toml").write_text(toml_content, encoding="utf-8")

        spec = SpecLoader(root).load()

        assert spec.services["api"].allowed_service_dependencies == ["auth"]
        assert spec.services["auth"].allowed_service_dependencies == []

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
        tree_strict = true
        tree_allow_files = false
        """
        (root / "pyproject.toml").write_text(toml_content, encoding="utf-8")

        spec = SpecLoader(root).load()

        assert spec.services["svc"].tree == ["api", "domain", "infra", "api/v1"]
        assert spec.services["svc"].tree_strict is True
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
        tree_strict = true
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
        """Raises error when path doesn't exist and validate_paths=True."""
        project = make_project(
            with_pyproject=True,
            services={"svc": "nonexistent"},
            create_service_dirs=False,
        )

        with pytest.raises(PyArchError, match="doesn't exist"):
            SpecLoader(project.root).load()

    def test_nonexistent_path_allowed_when_validation_disabled(self, tmp_test_dir):
        """Allows nonexistent path when validate_paths=False."""
        root = tmp_test_dir / "no_validate"
        root.mkdir(parents=True, exist_ok=True)

        toml_content = """
[project]
name = "test"

[tool.pyarchrules]
validate_paths = false

[tool.pyarchrules.services.svc]
path = "nonexistent"
"""
        (root / "pyproject.toml").write_text(toml_content, encoding="utf-8")

        spec = SpecLoader(root).load()

        assert spec.services["svc"].path == "nonexistent"
