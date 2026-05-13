"""Tests for LinterRegistry."""

import pytest

from pyarchrules.core.registries import LinterRegistry
from pyarchrules.core.rules.linter import TreeRule
from pyarchrules.model.spec import ServiceSpec


@pytest.fixture
def service_spec(tmp_path):
    """Create a test service spec."""
    return ServiceSpec(name="test_service", path=".", project_root=tmp_path)


class TestLinterRegistry:
    """Tests for LinterRegistry."""

    def test_register_and_get(self, service_spec):
        """Register a rule and fetch it back."""
        registry = LinterRegistry()
        rule = TreeRule(service_spec)

        registry.register("test_service", rule)

        rules = registry.get("test_service")
        assert len(rules) == 1
        assert rules[0] is rule

    def test_register_multiple_rules(self, service_spec):
        """Multiple rules accumulate per service."""
        registry = LinterRegistry()
        rule1 = TreeRule(service_spec)
        rule2 = TreeRule(service_spec)

        registry.register("test_service", rule1)
        registry.register("test_service", rule2)

        rules = registry.get("test_service")
        assert len(rules) == 2

    def test_get_nonexistent_returns_none_by_default(self):
        """Unknown service returns ``None`` per the LSP-correct ``get`` contract."""
        registry = LinterRegistry()
        assert registry.get("nonexistent") is None

    def test_get_nonexistent_returns_default(self):
        """Callers that want a list pass ``default=[]`` explicitly."""
        registry = LinterRegistry()
        assert registry.get("nonexistent", []) == []

    def test_get_all_returns_all_registered(self, service_spec):
        registry = LinterRegistry()
        registry.register("service1", TreeRule(service_spec))
        registry.register("service2", TreeRule(service_spec))
        assert len(registry.get_all()) == 2

