"""Tests for DSLRegistry and LinterRegistry."""

import pytest

from pyarchrules.core.registries import DSLRegistry, LinterRegistry
from pyarchrules.core.rules.must_contain_folders_rule import MustContainFoldersRule
from pyarchrules.core.rules.rule_set import ServiceRuleSet
from pyarchrules.model.spec import ServiceSpec


@pytest.fixture
def service_spec(tmp_path):
    """Create a test service spec."""
    return ServiceSpec(
        name="test_service",
        path=".",
        project_root=tmp_path,
    )


class TestDSLRegistry:
    """Tests for DSLRegistry."""

    def test_register_and_get(self, service_spec):
        """Test registering and getting a RuleSet."""
        registry = DSLRegistry()
        rule_set = ServiceRuleSet(service_spec)

        registry.register("test_service", rule_set)

        assert registry.get("test_service") is rule_set

    def test_get_nonexistent_returns_none(self):
        """Test getting a nonexistent service returns None."""
        registry = DSLRegistry()

        assert registry.get("nonexistent") is None

    def test_has_returns_true_when_registered(self, service_spec):
        """Test has() returns True for registered services."""
        registry = DSLRegistry()
        rule_set = ServiceRuleSet(service_spec)
        registry.register("test_service", rule_set)

        assert registry.has("test_service") is True

    def test_has_returns_false_when_not_registered(self):
        """Test has() returns False for unregistered services."""
        registry = DSLRegistry()

        assert registry.has("nonexistent") is False

    def test_get_all_returns_all_registered(self, service_spec):
        """Test get_all() returns all registered RuleSets."""
        registry = DSLRegistry()
        rule_set1 = ServiceRuleSet(service_spec)
        rule_set2 = ServiceRuleSet(service_spec)

        registry.register("service1", rule_set1)
        registry.register("service2", rule_set2)

        all_rules = registry.get_all()

        assert len(all_rules) == 2
        assert all_rules["service1"] is rule_set1
        assert all_rules["service2"] is rule_set2

    def test_clear_removes_all(self, service_spec):
        """Test clear() removes all registered RuleSets."""
        registry = DSLRegistry()
        registry.register("service", ServiceRuleSet(service_spec))

        registry.clear()

        assert registry.get("service") is None
        assert len(registry.get_all()) == 0


class TestLinterRegistry:
    """Tests for LinterRegistry."""

    def test_register_and_get(self, service_spec):
        """Test registering and getting rules."""
        registry = LinterRegistry()
        rule = MustContainFoldersRule(service_spec, ["api"])

        registry.register("test_service", rule)

        rules = registry.get("test_service")
        assert len(rules) == 1
        assert rules[0] is rule

    def test_register_multiple_rules(self, service_spec):
        """Test registering multiple rules for same service."""
        registry = LinterRegistry()
        rule1 = MustContainFoldersRule(service_spec, ["api"])
        rule2 = MustContainFoldersRule(service_spec, ["domain"])

        registry.register("test_service", rule1)
        registry.register("test_service", rule2)

        rules = registry.get("test_service")
        assert len(rules) == 2

    def test_register_many(self, service_spec):
        """Test register_many adds multiple rules at once."""
        registry = LinterRegistry()
        rules = [
            MustContainFoldersRule(service_spec, ["api"]),
            MustContainFoldersRule(service_spec, ["domain"]),
        ]

        registry.register_many("test_service", rules)

        assert len(registry.get("test_service")) == 2

    def test_get_nonexistent_returns_empty_list(self):
        """Test getting rules for nonexistent service returns empty list."""
        registry = LinterRegistry()

        assert registry.get("nonexistent") == []

    def test_has_returns_true_when_registered(self, service_spec):
        """Test has() returns True for registered services."""
        registry = LinterRegistry()
        registry.register("test_service", MustContainFoldersRule(service_spec, ["api"]))

        assert registry.has("test_service") is True

    def test_get_all_services(self, service_spec):
        """Test get_all_services returns list of service names."""
        registry = LinterRegistry()
        registry.register("service1", MustContainFoldersRule(service_spec, ["api"]))
        registry.register("service2", MustContainFoldersRule(service_spec, ["api"]))

        services = registry.get_all_services()

        assert "service1" in services
        assert "service2" in services

    def test_clear_removes_all(self, service_spec):
        """Test clear() removes all registered rules."""
        registry = LinterRegistry()
        registry.register("service", MustContainFoldersRule(service_spec, ["api"]))

        registry.clear()

        assert registry.get("service") == []
        assert len(registry.get_all()) == 0
