from .exceptions import InvalidSpeedError


class Motor:
    """Represents a DC motor connected to an H-bridge driver.

    Parameters
    ----------
    board : pyfirmata2.Arduino
        The pyfirmata2 board instance used for pin I/O.
    direction1 : int
        First direction-control digital pin.
    direction2 : int
        Second direction-control digital pin.
    pwm : int
        PWM-capable pin for speed control.
    name : str, optional
        Optional human-readable label for the motor.
    """

    def __init__(self, board, direction1, direction2, pwm, name=None):
        self._direction1 = board.get_pin(f"d:{direction1}:o")
        self._direction2 = board.get_pin(f"d:{direction2}:o")
        self._pwm = board.get_pin(f"d:{pwm}:p")
        self.name = name
        self._speed = 0
        self._direction = "stopped"

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def __repr__(self):
        return (
            f"Motor(direction='{self._direction}', speed={self._speed})"
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_speed(self, speed):
        if not isinstance(speed, (int, float)):
            raise InvalidSpeedError("Speed must be a number.")
        if not 0 <= speed <= 100:
            raise InvalidSpeedError("Speed must be between 0 and 100.")

    def _apply_speed(self, speed):
        # pyfirmata2 expects a float in [0.0, 1.0]
        self._pwm.write(speed / 100)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def speed(self):
        """Current motor speed (0-100)."""
        return self._speed

    @speed.setter
    def speed(self, speed):
        self.set_speed(speed)

    @property
    def direction(self):
        """Current motor direction (forward / backward / stopped / braked)."""
        return self._direction

    # ------------------------------------------------------------------
    # Movement commands
    # ------------------------------------------------------------------

    def forward(self, speed=100):
        """Rotate the motor forward at *speed* (0-100)."""
        self._validate_speed(speed)
        self._direction1.write(1)
        self._direction2.write(0)
        self._apply_speed(speed)
        self._speed = speed
        self._direction = "forward"

    def backward(self, speed=100):
        """Rotate the motor backward at *speed* (0-100)."""
        self._validate_speed(speed)
        self._direction1.write(0)
        self._direction2.write(1)
        self._apply_speed(speed)
        self._speed = speed
        self._direction = "backward"

    def stop(self):
        """Stop the motor (coast)."""
        self._direction1.write(0)
        self._direction2.write(0)
        self._apply_speed(0)
        self._speed = 0
        self._direction = "stopped"

    def brake(self):
        """Stop the motor by shorting the terminals (brake)."""
        self._direction1.write(1)
        self._direction2.write(1)
        self._apply_speed(0)
        self._speed = 0
        self._direction = "braked"

    def set_speed(self, speed):
        """Change the motor speed without altering direction."""
        self._validate_speed(speed)
        self._apply_speed(speed)
        self._speed = speed
