"""DSL rule: layer_must_not_import — hard-forbid any import from source layer into target layer."""

from __future__ import annotations

from pathlib import Path

from pyarchrules.core.rules.base.import_rule import ImportBaseRule
from pyarchrules.core.rules.checks.imports import ImportInfo
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class LayerMustNotImportRule(ImportBaseRule):
    """Forbid any module in *source* from importing anything inside *target*.

    More explicit than ``dependencies`` (which is an allowlist): this is a direct
    hard ban on a specific direction.

    DSL usage::

        rules.for_service("backend").layer_must_not_import("domain", "infra")
        # domain must not import anything from infra
    """

    def __init__(self, service_spec: ServiceSpec, source: str, target: str):
        super().__init__(service_spec, folder=source)
        self._source = source
        self._target = target

    @property
    def rule_name(self) -> str:
        return "layer_must_not_import"

    def _check_file(
        self,
        file: Path,
        rel_path: Path,
        imports: list[ImportInfo],
    ) -> list[RuleViolation]:
        service_root = self._service_spec.absolute_path
        target_abs = service_root / self._target

        violations = []
        for imp in imports:
            # Resolve relative imports to absolute path within service
            if imp.is_relative:
                dots = len(imp.module) - len(imp.module.lstrip("."))
                rest = imp.module.lstrip(".")
                base = file.parent
                for _ in range(dots - 1):
                    base = base.parent
                candidate = (base / rest.replace(".", "/")) if rest else base
            else:
                # Absolute: check if first segment matches target folder name
                candidate = service_root / imp.module.split(".")[0]

            try:
                candidate.resolve().relative_to(target_abs.resolve())
                violations.append(
                    self._make_violation(
                        rel_path=rel_path,
                        message=f"Layer '{self._source}' must not import from '{self._target}': "
                        f"'{imp.module}' (line {imp.lineno})",
                        details={
                            "source": self._source,
                            "target": self._target,
                            "module": imp.module,
                            "lineno": imp.lineno,
                        },
                    )
                )
            except ValueError:
                pass  # not under target — fine

        return violations
