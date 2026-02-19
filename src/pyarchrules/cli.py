from pathlib import Path

import typer

from pyarchrules.config import PyArchConfig
from pyarchrules.core.errors import PyArchError
from pyarchrules.pyarchrules import PyArchRules

app = typer.Typer(help="PyArchRules - Architecture testing for Python projects")

# Color scheme matching the logo
BLUE = typer.colors.BLUE
CYAN = typer.colors.CYAN
GREEN = typer.colors.GREEN
YELLOW = typer.colors.YELLOW
RED = typer.colors.RED
BRIGHT_BLUE = typer.colors.BRIGHT_BLUE
BRIGHT_CYAN = typer.colors.BRIGHT_CYAN
MAGENTA = typer.colors.MAGENTA
BRIGHT_MAGENTA = typer.colors.BRIGHT_MAGENTA


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    """PyArchRules CLI."""
    if ctx.invoked_subcommand is None:
        typer.secho(ctx.get_help(), fg=BRIGHT_BLUE)
        raise typer.Exit(0)


@app.command("init-project")
def init_project(
    project_root: str = typer.Argument(".", help="Path to the project root"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force reinitialization without confirmation"
    ),
):
    """Create pyarchrules configuration in pyproject.toml."""
    root_path = Path(project_root).resolve()

    try:
        config = PyArchConfig.load(root_path)
    except PyArchError:
        typer.echo(typer.style("❌ pyproject.toml not found, please create one first", fg=RED))
        raise typer.Exit(code=1)

    already_initialized = config.is_initialized()

    if already_initialized and not force:
        typer.secho("⚠️  [tool.pyarchrules] is already initialized", fg=YELLOW)
        typer.secho("   This will replace the existing configuration.", fg=BRIGHT_BLUE)
        confirm = typer.confirm(
            typer.style("   Do you want to reinitialize?", fg=BRIGHT_CYAN), default=False
        )
        if not confirm:
            typer.secho("⏹️  Cancelled", fg=CYAN)
            raise typer.Exit(code=0)

    config.initialize(project_name=root_path.name)
    config.save()

    action = "reinitialized" if already_initialized else "initialized"
    typer.secho(f"✨ Successfully {action}!", fg=GREEN, bold=True)
    typer.secho(f"📝 {root_path / 'pyproject.toml'}", fg=BRIGHT_CYAN)
    typer.secho("")
    typer.secho("Configuration:", fg=MAGENTA, bold=True)
    typer.secho("  • root = '.'", fg=BRIGHT_BLUE)
    typer.secho("  • strict = true", fg=BRIGHT_BLUE)
    typer.secho("  • validate_paths = true", fg=BRIGHT_BLUE)
    typer.secho("  • fail_on_warning = false", fg=BRIGHT_BLUE)


@app.command("add-service")
def add_service(
    name: str = typer.Argument(None, help="Service name"),
    path: str = typer.Argument(None, help="Relative path to the service directory"),
):
    """Add a service to pyproject.toml."""
    root_path = Path.cwd()

    try:
        config = PyArchConfig.load(root_path)
    except PyArchError:
        typer.echo(typer.style("❌ pyproject.toml not found", fg=RED))
        raise typer.Exit(code=1)

    if name is None:
        name = typer.prompt(typer.style("📦 Service name", fg=BRIGHT_CYAN))

    if path is None:
        path = typer.prompt(typer.style("📁 Service path", fg=BRIGHT_CYAN), default=".")

    if not name.isidentifier():
        typer.secho(f"❌ Invalid service name '{name}'", fg=RED)
        typer.secho(
            "   Must be a valid Python identifier (alphanumeric + underscore, no spaces)",
            fg=BRIGHT_BLUE,
        )
        raise typer.Exit(code=1)

    try:
        existing_services = config.get_services()
        is_replacing = name in existing_services

        config.add_service(name, path)
        config.save()

        action = "✏️  Updated" if is_replacing else "➕ Added"
        typer.secho(f"{action} service '{name}'", fg=GREEN, bold=True)
        typer.secho(f"   Path: {path}", fg=BRIGHT_CYAN)
    except PyArchError as e:
        typer.echo(typer.style(f"❌ {str(e)}", fg=RED))
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
        typer.echo(typer.style("❌ pyproject.toml not found", fg=RED))
        raise typer.Exit(code=1)

    if name is None:
        services = config.get_services()
        if not services:
            typer.secho("❌ No services configured", fg=RED)
            raise typer.Exit(code=1)

        typer.secho("📦 Available services:", fg=MAGENTA, bold=True)
        for svc_name in services.keys():
            typer.secho(f"  • {svc_name}", fg=BRIGHT_BLUE)

        name = typer.prompt(typer.style("\n🗑️  Service name to remove", fg=BRIGHT_CYAN))

    if not force:
        confirm = typer.confirm(
            typer.style(f"⚠️  Remove service '{name}'?", fg=YELLOW), default=False
        )
        if not confirm:
            typer.secho("⏹️  Cancelled", fg=CYAN)
            raise typer.Exit(code=0)

    try:
        config.remove_service(name)
        config.save()
        typer.secho(f"🗑️  Service '{name}' removed", fg=GREEN)
    except PyArchError as e:
        typer.echo(typer.style(f"❌ {str(e)}", fg=RED))
        raise typer.Exit(code=1)


@app.command("list-services")
def list_services():
    """List all configured services."""
    root_path = Path.cwd()

    try:
        config = PyArchConfig.load(root_path)
    except PyArchError:
        typer.echo(typer.style("❌ pyproject.toml not found", fg=RED))
        raise typer.Exit(code=1)

    if not config.is_initialized():
        typer.secho("❌ [tool.pyarchrules] not initialized", fg=RED)
        typer.secho("   Run 'pyarchrules init-project' first", fg=BRIGHT_BLUE)
        raise typer.Exit(code=1)

    services = config.get_services()

    if not services:
        typer.secho("📦 No services configured", fg=YELLOW)
        return

    typer.secho(f"📦 Configured services ({len(services)}):", fg=MAGENTA, bold=True)
    typer.secho("")
    for name, path in services.items():
        typer.secho(f"  • {name}", fg=BRIGHT_CYAN, bold=True)
        typer.secho(f"    {path}", fg=BRIGHT_BLUE)


@app.command("check")
def check(
    project_root: str = typer.Argument(".", help="Path to the project root"),
    strict: bool = typer.Option(None, "--strict/--no-strict", help="Override strict mode"),
    verbose: bool = typer.Option(True, "--verbose/--quiet", help="Show detailed output"),
):
    """Validate project architecture against configured rules."""
    root_path = Path(project_root).resolve()

    try:
        pyarchrules = PyArchRules(root_path)
    except PyArchError as e:
        typer.echo(typer.style(f"❌ Failed to load configuration: {e}", fg=RED))
        raise typer.Exit(code=1)

    if not pyarchrules.services:
        typer.echo(typer.style("⚠️  No services configured", fg=YELLOW))
        raise typer.Exit(code=0)

    if strict is not None:
        pyarchrules.project_spec.strict = strict

    typer.secho(f"🔍 Checking {len(pyarchrules.services)} service(s)...", fg=MAGENTA, bold=True)
    typer.secho("")

    if verbose:
        for service_name, service_spec in pyarchrules.project_spec.services.items():
            typer.secho(f"📦 {service_name}", fg=BRIGHT_CYAN, bold=True)
            typer.secho(f"   Path: {service_spec.path}", fg=BRIGHT_BLUE)

            service_rules = pyarchrules.linter_registry.get(service_name)
            if service_rules:
                rules_list = ", ".join(rule.rule_name for rule in service_rules)
                typer.secho(f"   Rules: {rules_list}", fg=BLUE)
            else:
                typer.secho("   Rules: none", fg=YELLOW)
        typer.secho("")

    try:
        result = pyarchrules.validate(
            raise_on_violation=False,
            verbose=False,
            run_dsl=False,
            run_linter=True,
        )

        error_count = result.error_count
        warning_count = result.warning_count

        if not result.is_valid:
            typer.secho("❌  Validation failed!", fg=RED, bold=True)
            typer.secho("")
            typer.secho(f"Found {error_count} error(s) and {warning_count} warning(s):", fg=YELLOW)
            typer.secho("")

            for violation in result.violations:
                severity_icon = "❌" if violation.severity == "error" else "⚠️ "
                severity_color = RED if violation.severity == "error" else YELLOW

                typer.secho(
                    f"{severity_icon} [{violation.service_name}] {violation.rule_name}",
                    fg=severity_color,
                    bold=True,
                )
                typer.secho(f"   {violation.message}", fg=BRIGHT_BLUE)
                if violation.details:
                    typer.secho(f"   Details: {violation.details}", fg=BLUE)
                typer.secho("")

            if pyarchrules.project_spec.strict and error_count > 0:
                raise typer.Exit(code=1)
            elif pyarchrules.project_spec.fail_on_warning and (
                error_count > 0 or warning_count > 0
            ):
                raise typer.Exit(code=1)
            else:
                raise typer.Exit(code=0)
        else:
            typer.secho("✨ All checks passed!", fg=GREEN, bold=True)
            total_rules = sum(
                len(rules) for rules in pyarchrules.linter_registry.get_all().values()
            )
            typer.secho(
                f"   Checked {total_rules} rule(s) across {len(pyarchrules.services)} service(s)",
                fg=BRIGHT_CYAN,
            )
            raise typer.Exit(code=0)

    except PyArchError as e:
        typer.echo(typer.style(f"❌ Validation error: {e}", fg=RED))
        raise typer.Exit(code=1)


def main():
    app()
