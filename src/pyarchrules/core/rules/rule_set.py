from pyarchrules.core.rules.dsl import (
    AllowedExternalLibsRule,
    ClassesMustMatchPatternRule,
    FilesMustBeSnakeCaseRule,
    FilesMustMatchPatternRule,
    ForbiddenExternalLibsRule,
    LayerMustNotImportRule,
    MaxDepthRule,
    MustContainFilesRule,
    MustContainFoldersRule,
    NoCircularImportsRule,
    NoFilesInFolderRule,
    NoPrivateImportsRule,
    NoRelativeImportsRule,
    NoTestFilesInRule,
    NoWildcardImportsRule,
)
from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.spec.service_spec import ServiceSpec


class ServiceRuleSet:
    """Fluent builder for attaching DSL rules to a service.

    Each method appends a rule and returns ``self`` so calls can be chained::

        rules.for_service("api")
            .must_contain_folders(["domain", "infra"])
            .no_wildcard_imports()

    Parameters
    ----------
    service_spec : ServiceSpec
        Specification of the service these rules apply to.
    """

    def __init__(self, service_spec: ServiceSpec):
        self._service_spec = service_spec
        self._rules: list[Rule] = []

    def must_contain_folders(
        self, folders: list[str], allow_extra: bool = True
    ) -> "ServiceRuleSet":
        """Assert the service root contains all *folders*.

        Parameters
        ----------
        folders : list[str]
            Folder names that must be present.
        allow_extra : bool, optional
            When ``False``, extra folders not in *folders* produce a warning.

        Returns
        -------
        ServiceRuleSet
        """
        self._rules.append(
            MustContainFoldersRule(
                service_spec=self._service_spec, required_folders=folders, allow_extra=allow_extra
            )
        )
        return self

    def must_contain_files(self, files: list[str]) -> "ServiceRuleSet":
        """Assert the service root contains all *files*.

        Parameters
        ----------
        files : list[str]
            File names that must be present.

        Returns
        -------
        ServiceRuleSet
        """
        self._rules.append(MustContainFilesRule(self._service_spec, files=files))
        return self

    def files_must_match_pattern(self, folder: str, pattern: str) -> "ServiceRuleSet":
        """Assert every file in *folder* matches the glob *pattern*.

        Parameters
        ----------
        folder : str
            Sub-path relative to the service root.
        pattern : str
            Glob pattern, e.g. ``"*_service.py"``.

        Returns
        -------
        ServiceRuleSet
        """
        self._rules.append(
            FilesMustMatchPatternRule(self._service_spec, folder=folder, pattern=pattern)
        )
        return self

    def no_files_in_folder(self, folder: str) -> "ServiceRuleSet":
        """Assert *folder* contains only subdirectories — no direct files.

        Parameters
        ----------
        folder : str

        Returns
        -------
        ServiceRuleSet
        """
        self._rules.append(NoFilesInFolderRule(self._service_spec, folder=folder))
        return self

    def max_depth(self, depth: int, folder: str | None = None) -> "ServiceRuleSet":
        """Assert the directory tree does not exceed *depth* nesting levels.

        Parameters
        ----------
        depth : int
            Maximum allowed nesting depth (root = 0).
        folder : str, optional
            Restrict the check to this sub-path; defaults to the service root.

        Returns
        -------
        ServiceRuleSet
        """
        self._rules.append(MaxDepthRule(self._service_spec, max_depth=depth, folder=folder))
        return self

    def no_circular_imports(self, folder: str | None = None) -> "ServiceRuleSet":
        """Detect circular import chains using AST + DFS.

        Parameters
        ----------
        folder : str, optional
            Restrict the scan to this sub-path; defaults to the service root.

        Returns
        -------
        ServiceRuleSet
        """
        self._rules.append(NoCircularImportsRule(self._service_spec, folder=folder))
        return self

    def no_wildcard_imports(self, folder: str | None = None) -> "ServiceRuleSet":
        """Forbid ``from x import *``.

        Parameters
        ----------
        folder : str, optional
            Restrict the scan to this sub-path; defaults to the service root.

        Returns
        -------
        ServiceRuleSet
        """
        self._rules.append(NoWildcardImportsRule(self._service_spec, folder=folder))
        return self

    def no_private_imports(self, folder: str | None = None) -> "ServiceRuleSet":
        """Forbid importing ``_private`` symbols from foreign modules.

        Parameters
        ----------
        folder : str, optional
            Restrict the scan to this sub-path; defaults to the service root.

        Returns
        -------
        ServiceRuleSet
        """
        self._rules.append(NoPrivateImportsRule(self._service_spec, folder=folder))
        return self

    def no_relative_imports_in(self, folder: str | None = None) -> "ServiceRuleSet":
        """Forbid relative imports (``from . import ...``) inside *folder* or the whole service.

        Parameters
        ----------
        folder : str, optional
            Restrict the scan to this sub-path; defaults to the service root.

        Returns
        -------
        ServiceRuleSet
        """
        self._rules.append(NoRelativeImportsRule(self._service_spec, folder=folder))
        return self

    def allowed_external_libs(
        self, folder: str | None = None, *, libs: list[str]
    ) -> "ServiceRuleSet":
        """Allow only the listed external libraries inside *folder* or the whole service.

        Parameters
        ----------
        folder : str, optional
            Restrict the scan to this sub-path; defaults to the service root.
        libs : list[str]
            Allowed third-party package names.

        Returns
        -------
        ServiceRuleSet
        """
        self._rules.append(AllowedExternalLibsRule(self._service_spec, libs=libs, folder=folder))
        return self

    def forbidden_external_libs(
        self, folder: str | None = None, *, libs: list[str]
    ) -> "ServiceRuleSet":
        """Forbid specific external libraries inside *folder* or the whole service.

        Parameters
        ----------
        folder : str, optional
            Restrict the scan to this sub-path; defaults to the service root.
        libs : list[str]
            Forbidden third-party package names.

        Returns
        -------
        ServiceRuleSet
        """
        self._rules.append(ForbiddenExternalLibsRule(self._service_spec, libs=libs, folder=folder))
        return self

    def layer_must_not_import(self, source: str, target: str) -> "ServiceRuleSet":
        """Hard-forbid any import from *source* layer into *target* layer.

        Parameters
        ----------
        source : str
            Folder that must not import from *target*.
        target : str
            Folder that must not be imported by *source*.

        Returns
        -------
        ServiceRuleSet
        """
        self._rules.append(LayerMustNotImportRule(self._service_spec, source=source, target=target))
        return self

    def files_must_be_snake_case(self, folder: str | None = None) -> "ServiceRuleSet":
        """Assert all ``.py`` files use ``snake_case`` naming.

        Parameters
        ----------
        folder : str, optional
            Restrict the scan to this sub-path; defaults to the service root.

        Returns
        -------
        ServiceRuleSet
        """
        self._rules.append(FilesMustBeSnakeCaseRule(self._service_spec, folder=folder))
        return self

    def classes_must_match_pattern(self, folder: str, pattern: str) -> "ServiceRuleSet":
        """Assert every class in *folder* matches the regexp *pattern*.

        Parameters
        ----------
        folder : str
        pattern : str
            Regular expression applied to class names, e.g. ``r".*Service$"``.

        Returns
        -------
        ServiceRuleSet
        """
        self._rules.append(
            ClassesMustMatchPatternRule(self._service_spec, folder=folder, pattern=pattern)
        )
        return self

    def no_test_files_in(self, folder: str) -> "ServiceRuleSet":
        """Assert no test files (``test_*.py`` / ``*_test.py``) exist in *folder*.

        Parameters
        ----------
        folder : str

        Returns
        -------
        ServiceRuleSet
        """
        self._rules.append(NoTestFilesInRule(self._service_spec, folder=folder))
        return self

    def _collect_violations(self) -> list:
        violations = []
        for rule in self._rules:
            violations.extend(rule.validate())
        return violations
