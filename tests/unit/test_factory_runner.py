"""Tests for RuleFactory and RuleRunner."""

import pytest

from pyarchrules.core.errors import ValidationError
from pyarchrules.core.rules.dependencies_rule import DependenciesRule
from pyarchrules.core.rules.dsl import DslRule
from pyarchrules.core.rules.factory import RULE_TYPES, RuleFactory
from pyarchrules.core.rules.isolation_rule import ServiceIsolationRule
from pyarchrules.core.rules.linter import LinterRule
from pyarchrules.core.rules.no_circular_imports_rule import NoCircularImportsRule
from pyarchrules.core.rules.rule_set import ServiceRuleSet
from pyarchrules.core.rules.tree_rule import TreeRule
from pyarchrules.core.runner import RuleRunner
from pyarchrules.model.spec import ProjectSpec, ServiceSpec


def test_dsl_rules_have_a_service_rule_set_method():
    for rule_type in (TreeRule, DependenciesRule, NoCircularImportsRule):
        assert issubclass(rule_type, DslRule)
        assert callable(getattr(ServiceRuleSet, rule_type.dsl_method))


def test_every_registered_rule_is_a_linter_rule():
    assert all(issubclass(rule_type, LinterRule) for rule_type in RULE_TYPES)
    assert not issubclass(ServiceIsolationRule, DslRule)


@pytest.fixture
def make_spec(tmp_path):
    def _make(name="svc", **kwargs):
        (tmp_path / name).mkdir(exist_ok=True)
        return ServiceSpec(name=name, path=name, project_root=tmp_path, **kwargs)

    return _make


class TestRuleFactory:
    def test_unconfigured_service_gets_no_rules(self, make_spec):
        spec = make_spec()
        assert RuleFactory.create(spec, ProjectSpec(services={"svc": spec})) == []

    def test_configured_keys_enable_their_rules(self, make_spec):
        spec = make_spec(tree=["api"], dependencies=["api -> domain"], no_circular_imports=True)
        rules = RuleFactory.create(spec, ProjectSpec(services={"svc": spec}))
        assert [type(r) for r in rules] == [TreeRule, DependenciesRule, NoCircularImportsRule]

    def test_isolation_skips_shared_services(self, make_spec):
        a, shared = make_spec("a"), make_spec("shared", shared=True)
        project = ProjectSpec(services={"a": a, "shared": shared}, isolate_services=True)
        created = RuleFactory.create_all(project)
        assert [type(r) for r in created["a"]] == [ServiceIsolationRule]
        assert created["shared"] == []


class TestRuleRunner:
    def test_passes_without_rules(self):
        assert RuleRunner([]).run(raise_on_violation=True, verbose=False).is_valid

    def test_returns_violations_without_raising(self, make_spec):
        rule = TreeRule(make_spec(tree=["missing"]))
        result = RuleRunner([rule]).run(raise_on_violation=False, verbose=False)
        assert result.error_count == 1

    def test_raises_on_violation(self, make_spec):
        rule = TreeRule(make_spec(tree=["missing"]))
        with pytest.raises(ValidationError, match="1 error"):
            RuleRunner([rule]).run(raise_on_violation=True, verbose=False)

    def test_custom_reporter_receives_failing_result(self, make_spec):
        class Spy:
            result = None

            def report(self, result):
                self.result = result

        spy = Spy()
        rule = TreeRule(make_spec(tree=["missing"]))
        RuleRunner([rule]).run(raise_on_violation=False, verbose=True, reporter=spy)
        assert spy.result.error_count == 1
