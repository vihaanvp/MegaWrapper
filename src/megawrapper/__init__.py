from .board import Board
from .motor import Motor
from .servo import Servo
from .tcs34725 import TCS34725
from .utils import delay, millis

from .exceptions import (
    MegaWrapperError,
    InvalidSpeedError,
    BoardConnectionError,
    StandbyNotConfiguredError,
    TCS34725Error,
)

from .version import __version__

__all__ = [
    "Board",
    "Motor",
    "Servo",
    "TCS34725",
    "delay",
    "millis",
    "MegaWrapperError",
    "InvalidSpeedError",
    "BoardConnectionError",
    "StandbyNotConfiguredError",
    "TCS34725Error",
    "__version__",
]
