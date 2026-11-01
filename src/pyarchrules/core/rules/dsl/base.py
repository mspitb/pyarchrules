"""Interface for rules that can be attached from Python code."""

from __future__ import annotations

from typing import ClassVar

from pyarchrules.core.rules.rule import Rule


class DslRule(Rule):
    """A rule exposed as a fluent method of ``ServiceRuleSet``.

    Subclasses name that method in :attr:`dsl_method`; a test checks that it
    exists, so the rule cannot be declared DSL-capable without a DSL method.
    """

    #: Name of the ``ServiceRuleSet`` method that attaches this rule.
    dsl_method: ClassVar[str]
