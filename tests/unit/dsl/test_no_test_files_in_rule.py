"""Unit tests for NoTestFilesInRule."""

import pytest

from pyarchrules.core.rules.dsl.no_test_files_in_rule import NoTestFilesInRule
from pyarchrules.model.spec import ServiceSpec


class TestNoTestFilesInRule:

    @pytest.fixture
    def service_dir(self, tmp_path):
        svc = tmp_path / "svc"
        svc.mkdir()
        return tmp_path

    def _make_spec(self, root):
        return ServiceSpec(name="svc", path="svc", project_root=root)

    def _write(self, base, rel):
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("")

    # ------------------------------------------------------------------

    def test_production_file_passes(self, service_dir):
        self._write(service_dir / "svc", "domain/user_service.py")
        rule = NoTestFilesInRule(self._make_spec(service_dir), folder="domain")
        assert rule.validate() == []

    def test_test_prefix_file_returns_error(self, service_dir):
        self._write(service_dir / "svc", "domain/test_user_service.py")
        rule = NoTestFilesInRule(self._make_spec(service_dir), folder="domain")
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].rule_name == "no_test_files_in"
        assert "test_user_service.py" in violations[0].message

    def test_test_suffix_file_returns_error(self, service_dir):
        self._write(service_dir / "svc", "domain/user_service_test.py")
        rule = NoTestFilesInRule(self._make_spec(service_dir), folder="domain")
        violations = rule.validate()
        assert len(violations) == 1
        assert "user_service_test.py" in violations[0].message

    def test_nested_test_file_returns_error(self, service_dir):
        self._write(service_dir / "svc", "domain/sub/test_repo.py")
        rule = NoTestFilesInRule(self._make_spec(service_dir), folder="domain")
        violations = rule.validate()
        assert len(violations) == 1

    def test_multiple_test_files_return_multiple_errors(self, service_dir):
        self._write(service_dir / "svc", "domain/test_a.py")
        self._write(service_dir / "svc", "domain/test_b.py")
        rule = NoTestFilesInRule(self._make_spec(service_dir), folder="domain")
        assert len(rule.validate()) == 2

    def test_nonexistent_folder_returns_error(self, service_dir):
        rule = NoTestFilesInRule(self._make_spec(service_dir), folder="missing")
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].severity == "error"

    def test_rule_name(self, service_dir):
        (service_dir / "svc" / "domain").mkdir()
        rule = NoTestFilesInRule(self._make_spec(service_dir), folder="domain")
        assert rule.rule_name == "no_test_files_in"
