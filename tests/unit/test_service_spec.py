"""Tests for ServiceSpec validation shared by the TOML loader and the DSL."""

import pytest

from pyarchrules.core.errors import ConfigError
from pyarchrules.model.spec import ServiceSpec


def _spec(tmp_path, **kwargs):
    return ServiceSpec(name="svc", path=".", project_root=tmp_path, **kwargs)


def test_tree_mode_string_is_coerced(tmp_path):
    assert _spec(tmp_path, tree_mode="strict").tree_mode.value == "strict"


def test_invalid_tree_mode(tmp_path):
    with pytest.raises(ConfigError, match="invalid tree_mode"):
        _spec(tmp_path, tree_mode="nope")


def test_duplicate_tree_entries(tmp_path):
    with pytest.raises(ConfigError, match="duplicate entries in 'tree'"):
        _spec(tmp_path, tree=["api", "api"])


@pytest.mark.parametrize("key", ["tree", "tree_ignore", "dependencies"])
def test_non_list_values_are_rejected(tmp_path, key):
    with pytest.raises(ConfigError, match=f"'{key}' must be a list"):
        _spec(tmp_path, **{key: "api"})


def test_dependency_syntax_is_validated_eagerly(tmp_path):
    with pytest.raises(ConfigError, match="invalid dependency rule 'api domain'"):
        _spec(tmp_path, dependencies=["api domain"])


def test_dependency_rules_are_normalised(tmp_path):
    rule = _spec(tmp_path, dependencies=["api\\v1/ -> domain"]).dependency_rules[0]
    assert (rule.source, rule.target) == ("api/v1", "domain")
