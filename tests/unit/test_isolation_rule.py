"""Tests for ServiceIsolationRule (project-level isolate_services)."""

from __future__ import annotations

from pyarchrules.pyarchrules import PyArchRules


def _scaffold(project, name: str, *, pkg: str):
    """Create services/<name>/<pkg>/{__init__.py, main.py}."""
    project.mkdir(f"services/{name}/{pkg}")
    project.touch(f"services/{name}/__init__.py")
    project.touch(f"services/{name}/{pkg}/__init__.py")


class TestServiceIsolation:
    def test_cross_service_import_is_reported(self, make_project):
        project = make_project(
            services={
                "catalog": "services/catalog",
                "orders": "services/orders",
            },
            extra_config={"isolate_services": True},
        )
        _scaffold(project, "catalog", pkg="api")
        _scaffold(project, "orders", pkg="api")
        project.touch(
            "services/orders/api/handler.py",
            "from catalog.api import something\n",
        )

        rules = PyArchRules(project.root)
        result = rules.check_linter()

        offending = [v for v in result.violations if v.rule_name == "service_isolation"]
        assert offending, "expected a cross-service isolation violation"
        assert offending[0].service_name == "orders"
        assert "catalog" in offending[0].message
        assert offending[0].details == {
            "from_service": "orders",
            "to_service": "catalog",
            "import_statement": "catalog.api",
        }

    def test_shared_service_is_importable(self, make_project):
        project = make_project(
            services={
                "shared": "services/shared",
                "orders": "services/orders",
            },
            extra_config={"isolate_services": True},
        )
        # Mark `shared` as shared via TOML
        config = project.read_pyproject()
        config["tool"]["pyarchrules"]["services"]["shared"]["shared"] = True
        project.write_pyproject(config)

        _scaffold(project, "shared", pkg="models")
        _scaffold(project, "orders", pkg="api")
        project.touch(
            "services/orders/api/handler.py",
            "from shared.models import User\n",
        )

        rules = PyArchRules(project.root)
        result = rules.check_linter()
        assert not [v for v in result.violations if v.rule_name == "service_isolation"]

    def test_shared_service_has_no_isolation_rule_attached(self, make_project):
        project = make_project(
            services={
                "shared": "services/shared",
                "orders": "services/orders",
            },
            extra_config={"isolate_services": True},
        )
        config = project.read_pyproject()
        config["tool"]["pyarchrules"]["services"]["shared"]["shared"] = True
        project.write_pyproject(config)

        rules = PyArchRules(project.root)
        # shared services get no isolation rule.
        shared_rules = [r.rule_name for r in rules.linter_rules_for("shared")]
        orders_rules = [r.rule_name for r in rules.linter_rules_for("orders")]
        assert "service_isolation" not in shared_rules
        assert "service_isolation" in orders_rules

    def test_isolation_disabled_by_default(self, make_project):
        project = make_project(
            services={
                "catalog": "services/catalog",
                "orders": "services/orders",
            },
        )
        _scaffold(project, "catalog", pkg="api")
        _scaffold(project, "orders", pkg="api")
        project.touch(
            "services/orders/api/handler.py",
            "from catalog.api import something\n",
        )

        rules = PyArchRules(project.root)
        result = rules.check_linter()
        # No isolation rule active without the project-level flag.
        assert not [v for v in result.violations if v.rule_name == "service_isolation"]

    def test_same_service_imports_are_fine(self, make_project):
        project = make_project(
            services={"orders": "services/orders"},
            extra_config={"isolate_services": True},
        )
        _scaffold(project, "orders", pkg="api")
        _scaffold(project, "orders", pkg="domain")
        project.touch(
            "services/orders/api/handler.py",
            "from orders.domain import User\nimport os\n",
        )

        rules = PyArchRules(project.root)
        result = rules.check_linter()
        assert not [v for v in result.violations if v.rule_name == "service_isolation"]

    def test_stdlib_imports_ignored(self, make_project):
        project = make_project(
            services={
                "catalog": "services/catalog",
                "orders": "services/orders",
            },
            extra_config={"isolate_services": True},
        )
        _scaffold(project, "catalog", pkg="api")
        _scaffold(project, "orders", pkg="api")
        project.touch(
            "services/orders/api/handler.py",
            "import os\nfrom pathlib import Path\nimport json\n",
        )

        rules = PyArchRules(project.root)
        result = rules.check_linter()
        assert not [v for v in result.violations if v.rule_name == "service_isolation"]

    def test_third_party_imports_ignored(self, make_project):
        project = make_project(
            services={
                "catalog": "services/catalog",
                "orders": "services/orders",
            },
            extra_config={"isolate_services": True},
        )
        _scaffold(project, "catalog", pkg="api")
        _scaffold(project, "orders", pkg="api")
        # ``requests`` does not match any service name → must be ignored.
        project.touch(
            "services/orders/api/handler.py",
            "import requests\nfrom flask import Flask\n",
        )

        rules = PyArchRules(project.root)
        result = rules.check_linter()
        assert not [v for v in result.violations if v.rule_name == "service_isolation"]

