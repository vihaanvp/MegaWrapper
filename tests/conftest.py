"""
pytest configuration and shared fixtures for MegaWrapper tests.

We mock ``pyfirmata2.Arduino`` so all tests run without real hardware.
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_pyfirmata2():
    """Replace pyfirmata2.Arduino with a MagicMock before every test."""
    # Reset the board singleton so tests start clean
    import megawrapper.board as board_mod
    board_mod._active_board = None

    with patch("megawrapper.board.Arduino") as mock_ard:
        # Configure the mock board instance
        mock_board = MagicMock()
        mock_ard.return_value = mock_board

        # Each call to get_pin returns a *fresh* MagicMock so that
        # direction and PWM pins are independent mocks.
        mock_board.get_pin.side_effect = lambda *_: MagicMock()

        yield mock_ard
