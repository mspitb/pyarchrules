"""Unit tests for ClassesMustMatchPatternRule."""

import pytest

from pyarchrules.core.rules.dsl.classes_must_match_pattern_rule import ClassesMustMatchPatternRule
from pyarchrules.model.spec import ServiceSpec


class TestClassesMustMatchPatternRule:

    @pytest.fixture
    def service_dir(self, tmp_path):
        svc = tmp_path / "svc"
        svc.mkdir()
        return tmp_path

    def _make_spec(self, root):
        return ServiceSpec(name="svc", path="svc", project_root=root)

    def _write(self, base, rel, content):
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    # ------------------------------------------------------------------

    def test_matching_class_passes(self, service_dir):
        self._write(
            service_dir / "svc", "domain/services/user_service.py", "class UserService:\n    pass\n"
        )
        rule = ClassesMustMatchPatternRule(
            self._make_spec(service_dir), folder="domain/services", pattern=r".*Service$"
        )
        assert rule.validate() == []

    def test_non_matching_class_returns_error(self, service_dir):
        self._write(
            service_dir / "svc", "domain/services/user_service.py", "class UserManager:\n    pass\n"
        )
        rule = ClassesMustMatchPatternRule(
            self._make_spec(service_dir), folder="domain/services", pattern=r".*Service$"
        )
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].rule_name == "classes_must_match_pattern"
        assert "UserManager" in violations[0].message
        assert violations[0].details["pattern"] == r".*Service$"

    def test_multiple_classes_all_must_match(self, service_dir):
        self._write(
            service_dir / "svc",
            "domain/services/mixed.py",
            "class UserService:\n    pass\nclass UserHelper:\n    pass\n",
        )
        rule = ClassesMustMatchPatternRule(
            self._make_spec(service_dir), folder="domain/services", pattern=r".*Service$"
        )
        violations = rule.validate()
        assert len(violations) == 1
        assert "UserHelper" in violations[0].details["class"]

    def test_no_classes_passes(self, service_dir):
        self._write(service_dir / "svc", "domain/services/helpers.py", "def helper():\n    pass\n")
        rule = ClassesMustMatchPatternRule(
            self._make_spec(service_dir), folder="domain/services", pattern=r".*Service$"
        )
        assert rule.validate() == []

    def test_repository_pattern(self, service_dir):
        self._write(
            service_dir / "svc", "domain/repos/user_repo.py", "class UserRepository:\n    pass\n"
        )
        rule = ClassesMustMatchPatternRule(
            self._make_spec(service_dir), folder="domain/repos", pattern=r".*Repository$"
        )
        assert rule.validate() == []

    def test_nonexistent_folder_returns_error(self, service_dir):
        rule = ClassesMustMatchPatternRule(
            self._make_spec(service_dir), folder="missing", pattern=r".*Service$"
        )
        violations = rule.validate()
        assert len(violations) == 1
        assert violations[0].severity == "error"

    def test_rule_name(self, service_dir):
        (service_dir / "svc" / "domain").mkdir()
        rule = ClassesMustMatchPatternRule(
            self._make_spec(service_dir), folder="domain", pattern=r".*"
        )
        assert rule.rule_name == "classes_must_match_pattern"
