"""PyArchError — project-level exception hierarchy."""


class PyArchError(Exception):
    """Base class for all PyArchRules errors.

    Catch this when you want to handle *any* pyarchrules failure
    uniformly. Catch one of the subclasses for fine-grained control.
    """


class ConfigError(PyArchError):
    """Raised for problems detected while loading or parsing configuration.

    Examples: malformed ``pyproject.toml``, unknown keys, invalid enum
    values, missing required fields, paths that resolve outside the
    project root.
    """


class ValidationError(PyArchError):
    """Raised when an architecture rule reports violations.

    Used by ``raise_on_violation=True`` callers; otherwise violations are
    returned in the ``RuleEvalResult`` instead of being thrown.
    """


class ServiceNotFoundError(PyArchError):
    """Raised when a service name is referenced but not declared in the spec.

    Typically thrown by :meth:`PyArchRules.for_service` when the DSL is
    pointed at a non-existent service.
    """
