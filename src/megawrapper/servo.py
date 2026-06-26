from .board import Board
from .utils import delay


class Servo:
    """Represents a servo motor attached to an Arduino pin.

    Usage
    -----
    >>> board = Board("/dev/ttyUSB0")
    >>> servo = Servo()
    >>> servo.attach(9)
    >>> servo.write(90)
    """

    def __init__(self):
        self._servo = None
        self.pin = None
        self.current_angle = None

    # ------------------------------------------------------------------
    # Attach / detach
    # ------------------------------------------------------------------

    def attach(self, pin):
        """Bind the servo to a PWM-capable digital pin."""
        board = Board.get_active_board()
        self.pin = pin
        self._servo = board._board.get_pin(f"d:{pin}:s")

    def detach(self):
        """Release the servo pin."""
        if self._servo is not None and self.pin is not None:
            try:
                board = Board.get_active_board()
                # Release the pin in pyfirmata2's internal tracking
                board._board.taken['digital'][self.pin] = False
                # Reset the pin mode from SERVO back to OUTPUT on the Arduino
                board._board.digital[self.pin].mode = 1  # 1 = OUTPUT
            except (RuntimeError, KeyError, IndexError, AttributeError):
                pass  # Already detached or board gone — nothing to do
        self._servo = None
        self.pin = None
        self.current_angle = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_attached(self):
        if self._servo is None:
            raise RuntimeError("Servo not attached. Call attach(pin) first.")

    @staticmethod
    def _validate_and_clamp_angle(angle):
        try:
            angle = int(angle)
        except (TypeError, ValueError) as exc:
            raise ValueError("angle must be a number between 0 and 180") from exc
        return max(0, min(180, angle))

    # ------------------------------------------------------------------
    # Movement commands
    # ------------------------------------------------------------------

    def write(self, angle):
        """Immediately move the servo to *angle* (0-180)."""
        self._ensure_attached()
        angle = self._validate_and_clamp_angle(angle)
        self._servo.write(angle)
        self.current_angle = angle

    def read(self):
        """Return the last written angle.

        Raises RuntimeError if ``write()`` has never been called.
        """
        self._ensure_attached()
        if self.current_angle is None:
            raise RuntimeError(
                "Servo angle is unknown. Call write() first."
            )
        return self.current_angle

    def move_smooth(self, target_angle, delay_ms=15):
        """Move the servo to *target_angle* one degree at a time.

        *delay_ms* controls the pause between each degree step.
        """
        self._ensure_attached()
        target_angle = self._validate_and_clamp_angle(target_angle)

        if self.current_angle is None:
            self.write(target_angle)
            return

        if target_angle == self.current_angle:
            return

        step = 1 if target_angle > self.current_angle else -1
        for angle in range(self.current_angle + step, target_angle + step, step):
            self.write(angle)
            delay(delay_ms)

    def sweep(self, start=0, end=180, step=1, delay_ms=15):
        """Continuously sweep the servo between *start* and *end* angles."""
        self._ensure_attached()
        if step <= 0:
            raise ValueError("step must be greater than 0")

        start = self._validate_and_clamp_angle(start)
        end = self._validate_and_clamp_angle(end)

        if start < end:
            angles = range(start, end + 1, step)
        else:
            angles = range(start, end - 1, -step)

        for angle in angles:
            self.write(angle)
            delay(delay_ms)
