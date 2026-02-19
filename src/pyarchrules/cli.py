from pathlib import Path

import typer

from pyarchrules.config import PyArchConfig
from pyarchrules.core.errors import PyArchError
from pyarchrules.core.rules.linter import (
    AllowedServiceDependenciesRule,
    DependenciesRule,
    PathExistenceRule,
    TreeRule,
)
from pyarchrules.core.spec_loader import SpecLoader

app = typer.Typer(help="PyArchRules - Architecture testing for Python projects")


@app.callback(invoke_without_command=False)
def callback():
    """PyArchRules CLI."""
    pass


@app.command("init-project")
def init_project(
    project_root: str = typer.Argument(".", help="Path to the project root"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force reinitialization without confirmation"
    ),
):
    """
    Create pyarchrules configuration in pyproject.toml with default properties.
    """
    root_path = Path(project_root).resolve()

    try:
        config = PyArchConfig.load(root_path)
    except PyArchError:
        typer.echo("pyproject.toml not found, please create one first")
        raise typer.Exit(code=1)

    already_initialized = config.is_initialized()

    if already_initialized and not force:
        typer.echo("⚠️  [tool.pyarchrules] is already initialized in pyproject.toml")
        typer.echo("   This will replace the existing configuration.")
        confirm = typer.confirm("   Do you want to reinitialize?", default=False)
        if not confirm:
            typer.echo("Cancelled.")
            raise typer.Exit(code=0)

    config.initialize(project_name=root_path.name)
    config.save()

    action = "reinitialized" if already_initialized else "initialized"
    typer.echo(f"✓ [tool.pyarchrules] section {action} in {root_path / 'pyproject.toml'}")
    typer.echo("  Configuration:")
    typer.echo("    root = '.'")
    typer.echo("    strict = true")
    typer.echo("    validate_paths = true")
    typer.echo("    fail_on_warning = false")


@app.command("add-service")
def add_service(
    name: str = typer.Argument(None, help="Service name"),
    path: str = typer.Argument(None, help="Relative path to the service directory"),
):
    """Add a service to pyproject.toml. Prompts for missing arguments."""
    root_path = Path.cwd()

    try:
        config = PyArchConfig.load(root_path)
    except PyArchError:
        typer.echo("❌ pyproject.toml not found")
        raise typer.Exit(code=1)

    if name is None:
        name = typer.prompt("Service name")

    if path is None:
        path = typer.prompt("Service path", default=".")

    if not name.isidentifier():
        typer.echo(
            f"❌ Invalid service name '{name}'. "
            f"Must be a valid Python identifier (alphanumeric + underscore, no spaces)."
        )
        raise typer.Exit(code=1)

    try:
        existing_services = config.get_services()
        is_replacing = name in existing_services

        config.add_service(name, path)
        config.save()

        action = "updated" if is_replacing else "added"
        typer.echo(f"✓ Service '{name}' {action} with path '{path}'")
    except PyArchError as e:
        typer.echo(f"❌ {str(e)}")
        raise typer.Exit(code=1)


@app.command("remove-service")
def remove_service(
    name: str = typer.Argument(None, help="Service name to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Remove a service from pyproject.toml."""
    root_path = Path.cwd()

    try:
        config = PyArchConfig.load(root_path)
    except PyArchError:
        typer.echo("❌ pyproject.toml not found")
        raise typer.Exit(code=1)

    if name is None:
        services = config.get_services()
        if not services:
            typer.echo("❌ No services configured")
            raise typer.Exit(code=1)

        typer.echo("Available services:")
        for svc_name in services.keys():
            typer.echo(f"  • {svc_name}")

        name = typer.prompt("\nService name to remove")

    if not force:
        confirm = typer.confirm(f"Remove service '{name}'?", default=False)
        if not confirm:
            typer.echo("Cancelled.")
            raise typer.Exit(code=0)

    try:
        config.remove_service(name)
        config.save()
        typer.echo(f"✓ Service '{name}' removed")
    except PyArchError as e:
        typer.echo(f"❌ {str(e)}")
        raise typer.Exit(code=1)


@app.command("list-services")
def list_services():
    """List all configured services."""
    root_path = Path.cwd()

    try:
        config = PyArchConfig.load(root_path)
    except PyArchError:
        typer.echo("❌ pyproject.toml not found")
        raise typer.Exit(code=1)

    if not config.is_initialized():
        typer.echo("❌ [tool.pyarchrules] not initialized. Run 'pyarchrules init-project' first.")
        raise typer.Exit(code=1)

    services = config.get_services()

    if not services:
        typer.echo("No services configured.")
        return

    typer.echo(f"Configured services ({len(services)}):")
    for name, path in services.items():
        typer.echo(f"  • {name}: {path}")


@app.command("check")
def check(
    project_root: str = typer.Argument(".", help="Path to the project root"),
    strict: bool = typer.Option(None, "--strict/--no-strict", help="Override strict mode"),
    verbose: bool = typer.Option(True, "--verbose/--quiet", help="Show detailed output"),
):
    """
    Validate project architecture against configured rules.

    Checks:
    - Path existence (validate_paths)
    - Tree structure (tree)
    - Allowed service dependencies (allowed_service_dependencies)
    - Internal dependencies (dependencies)
    """
    root_path = Path(project_root).resolve()

    try:
        # Load project specification
        spec_loader = SpecLoader(root_path)
        project_spec = spec_loader.load()
    except PyArchError as e:
        typer.echo(f"❌ Failed to load project configuration: {e}")
        raise typer.Exit(code=1)

    if not project_spec.services:
        typer.echo("⚠️  No services configured")
        raise typer.Exit(code=0)

    # Override strict mode if provided
    if strict is not None:
        project_spec.strict = strict

    typer.echo(f"🔍 Checking {len(project_spec.services)} service(s)...")
    typer.echo("")

    all_violations = []
    total_rules_checked = 0

    for service_name, service_spec in project_spec.services.items():
        if verbose:
            typer.echo(f"📦 Service: {service_name} (path: {service_spec.path})")

        rules = [
            PathExistenceRule(service_spec),
            TreeRule(service_spec),
            AllowedServiceDependenciesRule(service_spec),
            DependenciesRule(service_spec),
        ]

        for rule in rules:
            total_rules_checked += 1
            violations = rule.validate()
            all_violations.extend(violations)

        if verbose:
            typer.echo("")

    # Report results
    error_count = sum(1 for v in all_violations if v.severity == "error")
    warning_count = sum(1 for v in all_violations if v.severity == "warning")

    if all_violations:
        typer.echo("❌ Validation failed!")
        typer.echo("")
        typer.echo(f"Found {error_count} error(s) and {warning_count} warning(s):")
        typer.echo("")

        for violation in all_violations:
            severity_icon = "❌" if violation.severity == "error" else "⚠️ "
            typer.echo(f"{severity_icon} [{violation.service_name}] {violation.rule_name}")
            typer.echo(f"   {violation.message}")
            if violation.details:
                typer.echo(f"   Details: {violation.details}")
            typer.echo("")

        # Exit with error code based on strict mode
        if project_spec.strict and error_count > 0:
            raise typer.Exit(code=1)
        elif project_spec.fail_on_warning and (error_count > 0 or warning_count > 0):
            raise typer.Exit(code=1)
        else:
            raise typer.Exit(code=0)
    else:
        typer.echo("✅ All checks passed!")
        typer.echo(f"   Checked {total_rules_checked} rule(s) across {len(project_spec.services)} service(s)")
        raise typer.Exit(code=0)


def main():
    app()
