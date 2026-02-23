"""Unit tests for FilesMustMatchPatternRule."""

import pytest

from pyarchrules.core.rules.dsl.files_must_match_pattern_rule import FilesMustMatchPatternRule
from pyarchrules.model.spec import ServiceSpec


class TestFilesMustMatchPatternRule:

    @pytest.fixture
    def service_dir(self, tmp_path):
        svc = tmp_path / "svc"
        svc.mkdir()
        return tmp_path

    def _make_spec(self, root):
        return ServiceSpec(name="svc", path="svc", project_root=root)

    # ------------------------------------------------------------------

    def test_all_files_match_pattern_passes(self, service_dir):
        tests = service_dir / "svc" / "tests"
        tests.mkdir()
        (tests / "test_foo.py").write_text("")
        (tests / "test_bar.py").write_text("")
        rule = FilesMustMatchPatternRule(
            self._make_spec(service_dir), folder="tests", pattern="test_*.py"
        )
        assert rule.validate() == []

    def test_non_matching_file_returns_error(self, service_dir):
        tests = service_dir / "svc" / "tests"
        tests.mkdir()
        (tests / "test_foo.py").write_text("")
        (tests / "helper.py").write_text("")
        rule = FilesMustMatchPatternRule(
            self._make_spec(service_dir), folder="tests", pattern="test_*.py"
        )
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].rule_name == "files_must_match_pattern"
        assert "helper.py" in violations[0].message
        assert violations[0].details["pattern"] == "test_*.py"

    def test_multiple_non_matching_files_returns_multiple_errors(self, service_dir):
        tests = service_dir / "svc" / "tests"
        tests.mkdir()
        (tests / "helper.py").write_text("")
        (tests / "utils.py").write_text("")
        rule = FilesMustMatchPatternRule(
            self._make_spec(service_dir), folder="tests", pattern="test_*.py"
        )
        assert len(rule.validate()) == 2

    def test_empty_folder_passes(self, service_dir):
        (service_dir / "svc" / "tests").mkdir()
        rule = FilesMustMatchPatternRule(
            self._make_spec(service_dir), folder="tests", pattern="test_*.py"
        )
        assert rule.validate() == []

    def test_nonexistent_folder_returns_error(self, service_dir):
        rule = FilesMustMatchPatternRule(
            self._make_spec(service_dir), folder="missing", pattern="*.py"
        )
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].severity == "error"

    def test_rule_name(self, service_dir):
        (service_dir / "svc" / "tests").mkdir()
        rule = FilesMustMatchPatternRule(
            self._make_spec(service_dir), folder="tests", pattern="*.py"
        )
        assert rule.rule_name == "files_must_match_pattern"
