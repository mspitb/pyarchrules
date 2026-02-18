"""Unit tests for PyArchError exception class."""

import pytest

from pyarchrules.core.errors import PyArchError


class TestPyArchError:
    """Tests for PyArchError exception class."""

    def test_stores_message(self):
        """Stores and displays the error message."""
        error = PyArchError("Test error message")

        assert str(error) == "Test error message"

    def test_handles_empty_message(self):
        """Handles empty message."""
        error = PyArchError()

        assert str(error) == ""

    def test_is_exception_subclass(self):
        """Is a subclass of Exception."""
        error = PyArchError("test")

        assert isinstance(error, Exception)

    def test_can_be_raised_and_caught(self):
        """Can be raised and caught."""
        with pytest.raises(PyArchError) as exc:
            raise PyArchError("Custom error")

        assert str(exc.value) == "Custom error"
