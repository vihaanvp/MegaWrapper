from pyfirmata2 import Arduino

from .motor import Motor
from .exceptions import BoardConnectionError, StandbyNotConfiguredError


# Module-level reference for the singleton-style servo access pattern.
# The most recently created Board is automatically registered here.
_active_board = None


class Board:
    """Represents a connection to an Arduino board running StandardFirmata.

    **Motor usage** (H-bridge drivers such as L298N, TB6612FNG, L293D)::

        board = Board("/dev/ttyUSB0")
        motor = board.attach_motor(2, 4, 11)
        motor.forward(100)

    **Servo usage** (singleton-style, mirrors the Arduino API)::

        board = Board("/dev/ttyUSB0")
        servo = Servo()
        servo.attach(9)
        servo.write(90)

    Parameters
    ----------
    port : str
        The serial port the Arduino is connected to (e.g. ``/dev/ttyUSB0``,
        ``COM3``).
    stby : int, optional
        Digital pin connected to the STBY line of a TB6612FNG (or similar)
        motor driver. When provided you can use :meth:`wake` and
        :meth:`sleep` to control driver power.
    """

    def __init__(self, port, stby=None):
        global _active_board

        try:
            self._board = Arduino(port)
        except Exception as e:
            raise BoardConnectionError(str(e))

        # Motor tracking ---------------------------------------------------
        self.motors = []

        # Optional standby pin (TB6612FNG etc.) ---------------------------
        if stby is not None:
            self._stby = self._board.get_pin(f"d:{stby}:o")
            self._stby.write(1)          # wake by default
        else:
            self._stby = None

        # Register as the active board for servo access --------------------
        _active_board = self

    # ------------------------------------------------------------------
    # Singleton access (used by Servo)
    # ------------------------------------------------------------------

    @staticmethod
    def get_active_board():
        """Return the most recently created Board instance.

        Raises ``RuntimeError`` if no Board has been created yet.
        """
        global _active_board
        if _active_board is None:
            raise RuntimeError(
                "No board initialised. Create a Board first."
            )
        return _active_board

    # ------------------------------------------------------------------
    # Motor attachment
    # ------------------------------------------------------------------

    def attach_motor(self, direction1, direction2, pwm, name=None):
        """Create and register a :class:`Motor` on this board.

        Parameters
        ----------
        direction1 : int
            First direction-control digital pin.
        direction2 : int
            Second direction-control digital pin.
        pwm : int
            PWM-capable pin.
        name : str, optional
            Optional label (e.g. ``"left"``, ``"right"``).

        Returns
        -------
        Motor
            The newly created Motor instance.
        """
        motor = Motor(self._board, direction1, direction2, pwm, name)
        self.motors.append(motor)
        return motor

    # ------------------------------------------------------------------
    # Bulk motor control
    # ------------------------------------------------------------------

    def stop_all(self):
        """Stop every motor attached to this board."""
        for motor in self.motors:
            motor.stop()

    # ------------------------------------------------------------------
    # Standby pin (TB6612FNG)
    # ------------------------------------------------------------------

    def wake(self):
        """Enable the motor driver by taking the STBY pin high."""
        if self._stby is None:
            raise StandbyNotConfiguredError("No STBY pin configured.")
        self._stby.write(1)

    def sleep(self):
        """Disable the motor driver by taking the STBY pin low."""
        if self._stby is None:
            raise StandbyNotConfiguredError("No STBY pin configured.")
        self._stby.write(0)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self):
        """Stop all motors, put the driver to sleep (if applicable),
        and close the serial connection to the Arduino."""
        self.stop_all()
        if self._stby is not None:
            self._stby.write(0)
        self._board.exit()

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
