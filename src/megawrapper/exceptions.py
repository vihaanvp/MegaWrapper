class MegaWrapperError(Exception):
    """Base exception for MegaWrapper."""
    pass


class InvalidSpeedError(MegaWrapperError):
    """Raised when speed is outside 0-100."""
    pass


class BoardConnectionError(MegaWrapperError):
    """Raised when the board cannot be reached."""
    pass


class StandbyNotConfiguredError(MegaWrapperError):
    """Raised when wake() or sleep() is called without an STBY pin."""
    pass
