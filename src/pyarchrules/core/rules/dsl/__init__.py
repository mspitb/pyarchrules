"""DSL rules — used via the Python fluent API (ServiceRuleSet)."""

from pyarchrules.core.rules.dsl.allowed_external_libs_rule import AllowedExternalLibsRule
from pyarchrules.core.rules.dsl.classes_must_match_pattern_rule import ClassesMustMatchPatternRule
from pyarchrules.core.rules.dsl.files_must_be_snake_case_rule import FilesMustBeSnakeCaseRule
from pyarchrules.core.rules.dsl.files_must_match_pattern_rule import FilesMustMatchPatternRule
from pyarchrules.core.rules.dsl.forbidden_external_libs_rule import ForbiddenExternalLibsRule
from pyarchrules.core.rules.dsl.layer_must_not_import_rule import LayerMustNotImportRule
from pyarchrules.core.rules.dsl.max_depth_rule import MaxDepthRule
from pyarchrules.core.rules.dsl.must_contain_files_rule import MustContainFilesRule
from pyarchrules.core.rules.dsl.must_contain_folders_rule import MustContainFoldersRule
from pyarchrules.core.rules.dsl.no_circular_imports_rule import NoCircularImportsRule
from pyarchrules.core.rules.dsl.no_files_in_folder_rule import NoFilesInFolderRule
from pyarchrules.core.rules.dsl.no_private_imports_rule import NoPrivateImportsRule
from pyarchrules.core.rules.dsl.no_relative_imports_rule import NoRelativeImportsRule
from pyarchrules.core.rules.dsl.no_test_files_in_rule import NoTestFilesInRule
from pyarchrules.core.rules.dsl.no_wildcard_imports_rule import NoWildcardImportsRule
from pyarchrules.core.rules.dsl.tree_structure_rule import TreeStructureRule

__all__ = [
    # File-system rules
    "MustContainFoldersRule",
    "MustContainFilesRule",
    "FilesMustMatchPatternRule",
    "NoFilesInFolderRule",
    "MaxDepthRule",
    "TreeStructureRule",
    # Import / dependency rules
    "NoCircularImportsRule",
    "NoWildcardImportsRule",
    "NoPrivateImportsRule",
    "NoRelativeImportsRule",
    "AllowedExternalLibsRule",
    "ForbiddenExternalLibsRule",
    "LayerMustNotImportRule",
    # Naming rules
    "FilesMustBeSnakeCaseRule",
    "ClassesMustMatchPatternRule",
    "NoTestFilesInRule",
]
