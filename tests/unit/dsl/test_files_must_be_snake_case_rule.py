"""Unit tests for FilesMustBeSnakeCaseRule."""

import pytest

from pyarchrules.core.rules.dsl.files_must_be_snake_case_rule import FilesMustBeSnakeCaseRule
from pyarchrules.model.spec import ServiceSpec


class TestFilesMustBeSnakeCaseRule:

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

    def test_snake_case_files_pass(self, service_dir):
        self._write(service_dir / "svc", "domain/user_service.py")
        self._write(service_dir / "svc", "domain/order_repo.py")
        rule = FilesMustBeSnakeCaseRule(self._make_spec(service_dir))
        assert rule.validate() == []

    def test_camel_case_file_returns_error(self, service_dir):
        self._write(service_dir / "svc", "domain/UserService.py")
        rule = FilesMustBeSnakeCaseRule(self._make_spec(service_dir))
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].rule_name == "files_must_be_snake_case"
        assert "UserService.py" in violations[0].message

    def test_dunder_files_are_skipped(self, service_dir):
        self._write(service_dir / "svc", "domain/__init__.py")
        self._write(service_dir / "svc", "domain/__version__.py")
        rule = FilesMustBeSnakeCaseRule(self._make_spec(service_dir))
        assert rule.validate() == []

    def test_private_files_are_skipped(self, service_dir):
        self._write(service_dir / "svc", "domain/_internal.py")
        rule = FilesMustBeSnakeCaseRule(self._make_spec(service_dir))
        assert rule.validate() == []

    def test_folder_scoped_ignores_other_folders(self, service_dir):
        self._write(service_dir / "svc", "api/BadName.py")
        self._write(service_dir / "svc", "domain/good_name.py")
        rule = FilesMustBeSnakeCaseRule(self._make_spec(service_dir), folder="domain")
        assert rule.validate() == []

    def test_recursive_check(self, service_dir):
        self._write(service_dir / "svc", "domain/sub/BadName.py")
        rule = FilesMustBeSnakeCaseRule(self._make_spec(service_dir))
        violations = rule.validate()
        assert len(violations) == 1

    def test_nonexistent_folder_returns_error(self, service_dir):
        rule = FilesMustBeSnakeCaseRule(self._make_spec(service_dir), folder="missing")
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].severity == "error"

    def test_rule_name(self, service_dir):
        rule = FilesMustBeSnakeCaseRule(self._make_spec(service_dir))
        assert rule.rule_name == "files_must_be_snake_case"
