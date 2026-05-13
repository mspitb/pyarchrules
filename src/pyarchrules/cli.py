import sys
from pathlib import Path

import typer

from pyarchrules.core.config import PyArchConfig
from pyarchrules.core.errors import PyArchError
from pyarchrules.core.reporting import ConsoleViolationReporter
from pyarchrules.pyarchrules import PyArchRules

app = typer.Typer(
    help="PyArchRules - Architecture testing for Python projects",
    no_args_is_help=True,
)

# Exit codes (documented public contract):
#   0  — success or only warnings (without ``-W``)
#   1  — at least one error-severity violation, or ``-W`` upgrade tripped
#   2  — configuration / loading error (PyArchError before validation runs)
EXIT_OK = 0
EXIT_VIOLATIONS = 1
EXIT_CONFIG = 2

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

    config.initialize()
    config.save()

    action = "reinitialized" if already_initialized else "initialized"
    typer.secho(f"✨ Successfully {action}!", fg=GREEN, bold=True)
    typer.secho(f"📝 {root_path / 'pyproject.toml'}", fg=BRIGHT_CYAN)
    typer.secho("")
    typer.secho(
        "Add a service with: pyarchrules add-service <name> <path>",
        fg=BRIGHT_BLUE,
    )


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


@app.command("show-config")
def show_config(
    project_root: str = typer.Argument(".", help="Path to the project root"),
):
    """Print the resolved pyarchrules configuration as JSON.

    Useful for debugging which services and rules will run before invoking
    ``check``. Output goes to stdout; loading errors exit with code 2.
    """
    import json
    from dataclasses import asdict

    root_path = Path(project_root).resolve()
    try:
        pyarchrules = PyArchRules(root_path)
    except PyArchError as e:
        typer.secho(f"❌ Failed to load configuration: {e}", fg=RED, err=True)
        raise typer.Exit(code=EXIT_CONFIG)

    payload = {
        "project_root": str(pyarchrules.project_root),
        "services": {
            name: {
                **{k: (str(v) if isinstance(v, Path) else v) for k, v in asdict(spec).items()},
                "rules": [r.rule_name for r in pyarchrules.linter_rules_for(name)],
            }
            for name, spec in pyarchrules.project_spec.services.items()
        },
    }
    typer.echo(json.dumps(payload, indent=2, sort_keys=True, default=str))


@app.command("check")
def check(
    project_root: str = typer.Argument(".", help="Path to the project root"),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to a non-default pyproject.toml (file or its parent dir).",
    ),
    service_filter: list[str] = typer.Option(
        None,
        "--service",
        "-s",
        help="Limit checks to one or more services (repeat for multiple).",
    ),
    rule_filter: list[str] = typer.Option(
        None,
        "--rule",
        "-r",
        help="Limit checks to one or more rule names (repeat for multiple).",
    ),
    warnings_as_errors: bool = typer.Option(
        False,
        "--warnings-as-errors",
        "-W",
        help="Treat warning-severity violations as errors (exit 1).",
    ),
    output_format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help='Output format for violations: "text" (default) or "json".',
    ),
    verbose: bool = typer.Option(True, "--verbose/--quiet", help="Show detailed output"),
):
    """Validate project architecture against configured rules.

    Exit codes
    ----------
    0
        Validation passed (or only warnings, without ``-W``).
    1
        At least one error-severity violation (or warning when ``-W``).
    2
        Configuration / loading failure (no validation performed).
    """
    if output_format not in ("text", "json"):
        typer.secho(
            f"❌ Invalid --format '{output_format}'. Use 'text' or 'json'.",
            fg=RED,
            err=True,
        )
        raise typer.Exit(code=EXIT_CONFIG)

    # Resolve project root: prefer explicit --config, then positional argument.
    if config is not None:
        config_path = config.resolve()
        root_path = config_path.parent if config_path.is_file() else config_path
    else:
        root_path = Path(project_root).resolve()

    try:
        pyarchrules = PyArchRules(root_path)
    except PyArchError as e:
        typer.secho(f"❌ Failed to load configuration: {e}", fg=RED, err=True)
        raise typer.Exit(code=EXIT_CONFIG)

    if not pyarchrules.services:
        typer.secho("⚠️  No services configured", fg=YELLOW)
        raise typer.Exit(code=EXIT_OK)

    # Detect parallel pyarchrules configs in nested pyproject.toml files.
    # We do not load or merge them — just shout if they exist so the user
    # knows there is a second source of architectural truth in the tree.
    nested = PyArchConfig.find_nested_pyarch_configs(
        project_root=root_path,
        exclude=root_path / "pyproject.toml",
    )
    if nested and output_format == "text":
        root_services_abs = {
            name: svc.absolute_path for name, svc in pyarchrules.project_spec.services.items()
        }
        conflicts = PyArchConfig.detect_service_conflicts(
            root_pyproject=root_path / "pyproject.toml",
            root_services=root_services_abs,
            nested_configs=nested,
        )
        if conflicts:
            typer.secho(
                f"⚠️  Found {len(nested)} nested pyarchrules config(s) "
                f"with {len(conflicts)} conflict(s):",
                fg=YELLOW,
                err=True,
                bold=True,
            )
            for line in conflicts:
                typer.secho(f"   • {line}", fg=YELLOW, err=True)
            typer.secho(
                "   This run uses the root config only. To run a nested "
                "config explicitly, point check at its directory.",
                fg=BRIGHT_BLUE,
                err=True,
            )
            typer.secho("", err=True)
        else:
            typer.secho(
                f"ℹ️  Found {len(nested)} nested pyarchrules config(s) (no conflicts with root).",
                fg=BRIGHT_BLUE,
                err=True,
            )
            typer.secho("", err=True)

    if output_format == "text":
        typer.secho(f"🔍 Checking {len(pyarchrules.services)} service(s)...", fg=MAGENTA, bold=True)
        typer.secho("")

        if verbose:
            for service_name, service_spec in pyarchrules.project_spec.services.items():
                typer.secho(f"📦 {service_name}", fg=BRIGHT_CYAN, bold=True)
                typer.secho(f"   Path: {service_spec.path}", fg=BRIGHT_BLUE)

                service_rules = pyarchrules.linter_rules_for(service_name)
                if service_rules:
                    rules_list = ", ".join(rule.rule_name for rule in service_rules)
                    typer.secho(f"   Rules: {rules_list}", fg=BLUE)
                else:
                    typer.secho("   Rules: none", fg=YELLOW)
            typer.secho("")

    result = pyarchrules.check_linter(raise_on_violation=False, verbose=False)

    # Apply --service / --rule post-filters. Validate names early so a typo
    # surfaces immediately instead of silently returning zero violations.
    if service_filter:
        unknown = [s for s in service_filter if s not in pyarchrules.services]
        if unknown:
            typer.secho(
                f"❌ Unknown service(s): {', '.join(unknown)}. "
                f"Available: {', '.join(pyarchrules.services)}",
                fg=RED,
                err=True,
            )
            raise typer.Exit(code=EXIT_CONFIG)
    if service_filter or rule_filter:
        from pyarchrules.model.rules import RuleEvalResult

        kept = [
            v
            for v in result.violations
            if (not service_filter or v.service_name in service_filter)
            and (not rule_filter or v.rule_name in rule_filter)
        ]
        result = RuleEvalResult(violations=kept)

    error_count = result.error_count
    warning_count = result.warning_count

    if output_format == "json":
        # Single machine-readable document on stdout.

        ConsoleViolationReporter(stream=sys.stdout, format="json").report(result)
    else:
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
        else:
            typer.secho("✨ All checks passed!", fg=GREEN, bold=True)
            total_rules = pyarchrules.linter_rule_count
            typer.secho(
                f"   Checked {total_rules} rule(s) across {len(pyarchrules.services)} service(s)",
                fg=BRIGHT_CYAN,
            )

    # Exit code matrix:
    #   - any error → 1
    #   - warnings + -W → 1
    #   - otherwise → 0
    if error_count > 0 or (warnings_as_errors and warning_count > 0):
        raise typer.Exit(code=EXIT_VIOLATIONS)
    raise typer.Exit(code=EXIT_OK)


def main():
    app()
