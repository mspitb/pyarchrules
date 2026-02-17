"""Unit tests for PyArchError exception class."""

import pytest

from pyarchrules.core.errors import PyArchError


@pytest.mark.unit
def test_pyarcherror_with_message():
    """Should store and display the error message."""
    error = PyArchError("Test error message")

    assert error.message == "Test error message"
    assert str(error) == "Test error message"


@pytest.mark.unit
def test_pyarcherror_without_message():
    """Should handle empty message."""
    error = PyArchError()

    assert error.message == ""
    assert str(error) == ""


@pytest.mark.unit
def test_pyarcherror_is_exception():
    """Should be a subclass of Exception."""
    error = PyArchError("test")

    assert isinstance(error, Exception)


@pytest.mark.unit
def test_pyarcherror_can_be_raised():
    """Should be raisable and catchable."""
    with pytest.raises(PyArchError) as exc:
        raise PyArchError("Custom error")

    assert exc.value.message == "Custom error"
