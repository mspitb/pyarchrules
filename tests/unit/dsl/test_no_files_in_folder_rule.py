"""Unit tests for NoFilesInFolderRule."""

import pytest

from pyarchrules.core.rules.dsl.no_files_in_folder_rule import NoFilesInFolderRule
from pyarchrules.model.spec import ServiceSpec


class TestNoFilesInFolderRule:

    @pytest.fixture
    def service_dir(self, tmp_path):
        svc = tmp_path / "svc"
        svc.mkdir()
        return tmp_path

    def _make_spec(self, root):
        return ServiceSpec(name="svc", path="svc", project_root=root)

    # ------------------------------------------------------------------

    def test_only_subdirs_passes(self, service_dir):
        domain = service_dir / "svc" / "domain"
        domain.mkdir()
        (domain / "models").mkdir()
        (domain / "services").mkdir()
        rule = NoFilesInFolderRule(self._make_spec(service_dir), folder="domain")
        assert rule.validate() == []

    def test_file_directly_in_folder_returns_error(self, service_dir):
        domain = service_dir / "svc" / "domain"
        domain.mkdir()
        (domain / "stray.py").write_text("")
        rule = NoFilesInFolderRule(self._make_spec(service_dir), folder="domain")
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].rule_name == "no_files_in_folder"
        assert "stray.py" in violations[0].details["files"]

    def test_multiple_files_reported_together(self, service_dir):
        domain = service_dir / "svc" / "domain"
        domain.mkdir()
        (domain / "a.py").write_text("")
        (domain / "b.py").write_text("")
        rule = NoFilesInFolderRule(self._make_spec(service_dir), folder="domain")
        violations = rule.validate()
        assert len(violations) == 1
        assert set(violations[0].details["files"]) == {"a.py", "b.py"}

    def test_hidden_files_ignored(self, service_dir):
        domain = service_dir / "svc" / "domain"
        domain.mkdir()
        (domain / ".gitkeep").write_text("")
        rule = NoFilesInFolderRule(self._make_spec(service_dir), folder="domain")
        assert rule.validate() == []

    def test_nonexistent_folder_returns_error(self, service_dir):
        rule = NoFilesInFolderRule(self._make_spec(service_dir), folder="missing")
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].severity == "error"

    def test_rule_name(self, service_dir):
        (service_dir / "svc" / "domain").mkdir()
        rule = NoFilesInFolderRule(self._make_spec(service_dir), folder="domain")
        assert rule.rule_name == "no_files_in_folder"
