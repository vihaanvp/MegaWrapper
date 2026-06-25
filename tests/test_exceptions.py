"""Tests for custom exception classes."""

import pytest

from megawrapper.exceptions import (
    MegaWrapperError,
    InvalidSpeedError,
    BoardConnectionError,
    StandbyNotConfiguredError,
)


class TestMegaWrapperError:
    def test_is_exception(self):
        assert issubclass(MegaWrapperError, Exception)

    def test_can_be_raised(self):
        with pytest.raises(MegaWrapperError):
            raise MegaWrapperError("something went wrong")


class TestInvalidSpeedError:
    def test_inheritance(self):
        assert issubclass(InvalidSpeedError, MegaWrapperError)

    def test_message(self):
        with pytest.raises(InvalidSpeedError, match="Speed must be between"):
            raise InvalidSpeedError("Speed must be between 0 and 100.")


class TestBoardConnectionError:
    def test_inheritance(self):
        assert issubclass(BoardConnectionError, MegaWrapperError)


class TestStandbyNotConfiguredError:
    def test_inheritance(self):
        assert issubclass(StandbyNotConfiguredError, MegaWrapperError)

    def test_message(self):
        err = StandbyNotConfiguredError("No STBY pin configured.")
        assert "STBY" in str(err)
