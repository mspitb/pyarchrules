"""Unit tests for MustContainFoldersRule."""

import pytest

from pyarchrules.core.rules.dsl.must_contain_folders_rule import MustContainFoldersRule
from pyarchrules.model.spec import ServiceSpec


class TestMustContainFoldersRule:
    """Unit tests for MustContainFoldersRule validation logic."""

    @pytest.fixture
    def service_dir(self, tmp_path):
        """Create a service directory with api, models, utils folders."""
        service = tmp_path / "my_service"
        service.mkdir()
        (service / "api").mkdir()
        (service / "models").mkdir()
        (service / "utils").mkdir()
        return tmp_path

    def _make_spec(self, project_root, name="my_service", path="my_service"):
        return ServiceSpec(name=name, path=path, project_root=project_root)

    # -------------------------------------------------------------------------
    # Validation: required folders
    # -------------------------------------------------------------------------

    def test_all_required_folders_present_passes(self, service_dir):
        """Passes when all required folders exist."""
        rule = MustContainFoldersRule(
            service_spec=self._make_spec(service_dir),
            required_folders=["api", "models"],
            allow_extra=True,
        )

        violations = rule.validate()

        assert len(violations) == 0

    def test_missing_folders_returns_error(self, service_dir):
        """Returns error when required folders are missing."""
        rule = MustContainFoldersRule(
            service_spec=self._make_spec(service_dir),
            required_folders=["api", "models", "controllers", "tests"],
            allow_extra=True,
        )

        violations = rule.validate()

        assert len(violations) == 1
        assert violations[0].severity == "error"
        assert violations[0].rule_name == "must_contain_folders"
        assert "Missing required folders" in violations[0].message
        assert set(violations[0].details["missing"]) == {"controllers", "tests"}

    def test_exact_match_passes(self, service_dir):
        """Passes when folders exactly match required list."""
        rule = MustContainFoldersRule(
            service_spec=self._make_spec(service_dir),
            required_folders=["api", "models", "utils"],
            allow_extra=False,
        )

        violations = rule.validate()

        assert len(violations) == 0

    # -------------------------------------------------------------------------
    # Validation: extra folders
    # -------------------------------------------------------------------------

    def test_extra_folders_allowed_passes(self, service_dir):
        """Passes with extra folders when allow_extra=True."""
        rule = MustContainFoldersRule(
            service_spec=self._make_spec(service_dir),
            required_folders=["api"],
            allow_extra=True,
        )

        violations = rule.validate()

        assert len(violations) == 0

    def test_extra_folders_not_allowed_returns_warning(self, service_dir):
        """Returns warning when extra folders exist and allow_extra=False."""
        rule = MustContainFoldersRule(
            service_spec=self._make_spec(service_dir),
            required_folders=["api", "models"],
            allow_extra=False,
        )

        violations = rule.validate()

        assert len(violations) == 1
        assert violations[0].severity == "warning"
        assert "Extra folders not allowed" in violations[0].message
        assert "utils" in violations[0].details["extra"]

    def test_missing_and_extra_returns_both_violations(self, service_dir):
        """Returns both missing and extra violations."""
        rule = MustContainFoldersRule(
            service_spec=self._make_spec(service_dir),
            required_folders=["api", "controllers"],
            allow_extra=False,
        )

        violations = rule.validate()

        assert len(violations) == 2
        messages = [v.message for v in violations]
        assert any("Missing required folders" in m for m in messages)
        assert any("Extra folders not allowed" in m for m in messages)

    # -------------------------------------------------------------------------
    # Edge cases
    # -------------------------------------------------------------------------

    def test_service_directory_not_exists_returns_error(self, tmp_path):
        """Returns error when service directory doesn't exist."""
        rule = MustContainFoldersRule(
            service_spec=self._make_spec(tmp_path, path="nonexistent"),
            required_folders=["api"],
            allow_extra=True,
        )

        violations = rule.validate()

        assert len(violations) == 1
        assert violations[0].severity == "error"
        assert "does not exist" in violations[0].message

    def test_hidden_folders_ignored(self, service_dir):
        """Hidden folders (starting with .) are ignored."""
        (service_dir / "my_service" / ".hidden").mkdir()

        rule = MustContainFoldersRule(
            service_spec=self._make_spec(service_dir),
            required_folders=["api", "models", "utils"],
            allow_extra=False,
        )

        violations = rule.validate()

        assert len(violations) == 0

    def test_rule_name_property(self, service_dir):
        """Rule has correct name."""
        rule = MustContainFoldersRule(
            service_spec=self._make_spec(service_dir),
            required_folders=["api"],
        )

        assert rule.rule_name == "must_contain_folders"
