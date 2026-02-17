from pathlib import Path

import typer

from pyarchrules.config import PyArchConfig
from pyarchrules.core.errors import PyArchError

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
    typer.echo("  Root path set to: '.'")


@app.command("add-service")
def add_service(
    name: str = typer.Argument(None, help="Service name"),
    path: str = typer.Argument(None, help="Relative path to the service directory"),
):
    """Add a service to pyproject.toml. Prompts for missing arguments."""
    root_path = Path(".").resolve()

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

        if is_replacing:
            typer.echo(f"✓ Service '{name}' updated with path '{path}'")
        else:
            typer.echo(f"✓ Service '{name}' added with path '{path}'")
    except PyArchError as e:
        typer.echo(f"❌ {e.message}")
        raise typer.Exit(code=1)


@app.command("remove-service")
def remove_service(
    name: str = typer.Argument(None, help="Service name to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Remove a service from pyproject.toml. Prompts for missing arguments."""
    root_path = Path(".").resolve()

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
        typer.echo(f"❌ {e.message}")
        raise typer.Exit(code=1)


@app.command("list-services")
def list_services():
    """List all configured services."""
    root_path = Path(".").resolve()

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


def main():
    app()
