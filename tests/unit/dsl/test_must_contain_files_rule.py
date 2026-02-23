"""Unit tests for MustContainFilesRule."""

import pytest

from pyarchrules.core.rules.dsl.must_contain_files_rule import MustContainFilesRule
from pyarchrules.model.spec import ServiceSpec


class TestMustContainFilesRule:

    @pytest.fixture
    def service_dir(self, tmp_path):
        svc = tmp_path / "svc"
        svc.mkdir()
        (svc / "README.md").write_text("# readme")
        (svc / "pyproject.toml").write_text("")
        return tmp_path

    def _make_spec(self, root):
        return ServiceSpec(name="svc", path="svc", project_root=root)

    # ------------------------------------------------------------------

    def test_all_required_files_present_passes(self, service_dir):
        rule = MustContainFilesRule(
            self._make_spec(service_dir), files=["README.md", "pyproject.toml"]
        )
        assert rule.validate() == []

    def test_single_missing_file_returns_error(self, service_dir):
        rule = MustContainFilesRule(
            self._make_spec(service_dir), files=["README.md", "MISSING.txt"]
        )
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].severity == "error"
        assert violations[0].rule_name == "must_contain_files"
        assert "MISSING.txt" in violations[0].message
        assert "MISSING.txt" in violations[0].details["missing"]

    def test_all_files_missing_returns_error(self, service_dir):
        rule = MustContainFilesRule(self._make_spec(service_dir), files=["a.txt", "b.txt"])
        violations = rule.validate()
        assert len(violations) == 1
        assert set(violations[0].details["missing"]) == {"a.txt", "b.txt"}

    def test_empty_required_list_passes(self, service_dir):
        rule = MustContainFilesRule(self._make_spec(service_dir), files=[])
        assert rule.validate() == []

    def test_nonexistent_service_dir_returns_error(self, tmp_path):
        spec = ServiceSpec(name="ghost", path="ghost", project_root=tmp_path)
        rule = MustContainFilesRule(spec, files=["README.md"])
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].severity == "error"

    def test_rule_name(self, service_dir):
        rule = MustContainFilesRule(self._make_spec(service_dir), files=[])
        assert rule.rule_name == "must_contain_files"
