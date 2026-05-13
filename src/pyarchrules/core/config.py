"""Configuration management for PyArchRules."""

from __future__ import annotations

import tomllib
from pathlib import Path

import tomlkit

from pyarchrules.core.errors import PyArchError

# Directories that are never scanned when looking for nested pyproject.toml
# files. Keeps the conflict-detection walk fast and avoids false positives
# from vendored / packaged dependencies.
_NESTED_SCAN_IGNORED_DIRS: frozenset[str] = frozenset(
    {
        "node_modules",
        "site-packages",
        "__pycache__",
        "build",
        "dist",
    }
)


class PyArchConfig:
    """Manages pyproject.toml configuration for PyArchRules."""

    def __init__(self, doc: tomlkit.TOMLDocument, path: Path):
        self._doc = doc
        self._path = path

    @classmethod
    def load(cls, project_root: Path) -> PyArchConfig:
        """Load configuration from pyproject.toml."""
        pyproject = project_root / "pyproject.toml"

        if not pyproject.exists():
            raise PyArchError("pyproject.toml not found")

        with open(pyproject, encoding="utf-8") as f:
            doc = tomlkit.parse(f.read())

        return cls(doc, pyproject)

    def save(self) -> None:
        """Write configuration to pyproject.toml."""
        with open(self._path, "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(self._doc))

    def _get_pyarchrules(self) -> dict:
        """Get [tool.pyarchrules] section."""
        return self._doc.get("tool", {}).get("pyarchrules", {})

    def is_initialized(self) -> bool:
        """Check if [tool.pyarchrules] section exists."""
        return "pyarchrules" in self._doc.get("tool", {})

    def initialize(self) -> None:
        """Initialize ``[tool.pyarchrules]`` with a commented v1 template.

        Writes an empty table (so the loader treats the project as
        initialized) plus a complete commented example covering every v1
        key. The user uncomments and edits what they need.

        Service definitions live under ``[tool.pyarchrules.services.<name>]``
        and can also be added programmatically via :meth:`add_service`.
        To lint the whole project as a single unit, declare a
        ``services.root`` entry with ``path = "."``.
        """
        tool = self._doc.setdefault("tool", tomlkit.table())

        pyarch = tomlkit.table()

        for line in (
            "Add a service with: pyarchrules add-service <name> <path>",
            "Or define one inline below. The whole project can also be a",
            'single "root" service with path = ".".',
            "",
            "Enforce cross-service boundaries (services may not import each",
            "other's internals; services marked `shared = true` are exempt).",
            "isolate_services = true",
            "",
            "Example service (uncomment & adjust):",
            "",
            "[tool.pyarchrules.services.backend]",
            'path = "src/backend"',
            "",
            "Required directory layout under the service.",
            'tree_mode: "exists" (default) | "strict" | "exact"',
            'tree             = ["api", "domain", "infra"]',
            'tree_mode        = "strict"',
            "tree_allow_files = true",
            "Glob patterns of dirs to ignore in strict/exact mode.",
            'tree_ignore      = ["__snapshots__", "migrations_*"]',
            "",
            'Allowed import directions ("source -> target").',
            "Layers not listed as a source are unrestricted.",
            "dependencies = [",
            '  "api    -> domain",',
            '  "domain -> infra",',
            "]",
            "",
            "Detect circular module imports inside the service.",
            "no_circular_imports = true",
            "",
            "Mark this service as shared (other services may import from it",
            "even with isolate_services = true). Typical for services/shared.",
            "shared = false",
        ):
            pyarch.add(tomlkit.comment(line) if line else tomlkit.comment(""))

        pyarch.add(tomlkit.nl())

        tool["pyarchrules"] = pyarch

    def get_services(self) -> dict[str, str]:
        """Get all configured services as a dict mapping name to path."""
        services = self._get_pyarchrules().get("services", {})

        if not isinstance(services, dict):
            return {}

        result = {}
        for name, service_data in services.items():
            if isinstance(service_data, dict):
                path = service_data.get("path")
                if path:
                    result[name] = str(path)
            else:
                result[name] = str(service_data)

        return result

    def add_service(self, name: str, path: str) -> None:
        """Add or update a service in the configuration."""
        if not self.is_initialized():
            raise PyArchError(
                "[tool.pyarchrules] not initialized. Run 'pyarchrules init-project' first."
            )

        if not name.isidentifier():
            raise PyArchError(f"Invalid service name '{name}'. Must be a valid Python identifier.")

        tool = self._doc.setdefault("tool", tomlkit.table())
        pyarch = tool.setdefault("pyarchrules", tomlkit.table())
        services = pyarch.setdefault("services", tomlkit.table())

        if name in services:
            del services[name]

        service_table = tomlkit.table()
        service_table["path"] = path
        service_table.add(tomlkit.nl())
        services[name] = service_table

    def remove_service(self, name: str) -> None:
        """Remove a service from the configuration."""
        if not self.is_initialized():
            raise PyArchError("[tool.pyarchrules] not initialized")

        services = self._get_pyarchrules().get("services", {})

        if name not in services:
            raise PyArchError(f"Service '{name}' not found")

        del services[name]

    # ------------------------------------------------------------------
    # Nested config detection
    # ------------------------------------------------------------------

    @staticmethod
    def find_nested_pyarch_configs(
        project_root: Path,
        exclude: Path,
    ) -> list[tuple[Path, dict]]:
        """Find ``pyproject.toml`` files under *project_root* with a
        ``[tool.pyarchrules]`` section, excluding *exclude* itself.

        Skips hidden directories (``.git``, ``.venv``, ``.tox``, ...) and a
        small allow-list of common heavy/vendored folders so the walk is
        fast even on large monorepos.

        Parameters
        ----------
        project_root : Path
            Directory to walk recursively.
        exclude : Path
            Path to the *root* ``pyproject.toml`` that is being checked
            (so it is not reported as a nested config of itself).

        Returns
        -------
        list[tuple[Path, dict]]
            Pairs of (absolute pyproject path, parsed ``[tool.pyarchrules]``
            table). Files that fail to parse are silently skipped.
        """
        project_root = project_root.resolve()
        exclude_resolved = exclude.resolve()
        found: list[tuple[Path, dict]] = []

        def walk(directory: Path) -> None:
            try:
                entries = list(directory.iterdir())
            except OSError:
                return
            for entry in entries:
                if entry.is_dir():
                    if entry.name.startswith(".") or entry.name in _NESTED_SCAN_IGNORED_DIRS:
                        continue
                    walk(entry)
                elif entry.name == "pyproject.toml":
                    resolved = entry.resolve()
                    if resolved == exclude_resolved:
                        continue
                    try:
                        with open(resolved, "rb") as f:
                            data = tomllib.load(f)
                    except (OSError, tomllib.TOMLDecodeError):
                        continue
                    section = data.get("tool", {}).get("pyarchrules")
                    if section is not None:
                        found.append((resolved, section))

        walk(project_root)
        return found

    @staticmethod
    def detect_service_conflicts(
        root_pyproject: Path,
        root_services: dict[str, Path],
        nested_configs: list[tuple[Path, dict]],
    ) -> list[str]:
        """Return human-readable conflict messages for nested configs.

        A conflict is one of:

        - **Same service name** declared in both root and nested config.
        - **Same effective absolute path** targeted by services in both.

        Parameters
        ----------
        root_pyproject : Path
            The root ``pyproject.toml`` (used to render relative paths).
        root_services : dict[str, Path]
            Mapping of service name → absolute service directory, as
            resolved by the root config.
        nested_configs : list[tuple[Path, dict]]
            Output of :meth:`find_nested_pyarch_configs`.

        Returns
        -------
        list[str]
            One bullet line per conflict, suitable for stderr printing.
            Empty list when no conflicts are detected.
        """
        messages: list[str] = []
        root_dir = root_pyproject.parent.resolve()
        root_path_to_name = {abs_path.resolve(): name for name, abs_path in root_services.items()}

        for sub_pyproject, sub_section in nested_configs:
            sub_services = sub_section.get("services", {})
            if not isinstance(sub_services, dict):
                continue

            try:
                sub_pretty = sub_pyproject.relative_to(root_dir).as_posix()
            except ValueError:
                sub_pretty = str(sub_pyproject)

            sub_dir = sub_pyproject.parent
            for name, sdata in sub_services.items():
                if not isinstance(sdata, dict):
                    continue
                spath_rel = sdata.get("path")
                if not isinstance(spath_rel, str) or not spath_rel:
                    continue
                sabs = (sub_dir / spath_rel).resolve()

                if name in root_services:
                    messages.append(
                        f"{sub_pretty}: redefines service '{name}' "
                        f"(root targets '{root_services[name]}', "
                        f"nested targets '{sabs}')"
                    )
                elif sabs in root_path_to_name:
                    messages.append(
                        f"{sub_pretty}: service '{name}' targets the same "
                        f"path as root service '{root_path_to_name[sabs]}' "
                        f"({sabs})"
                    )

        return messages
