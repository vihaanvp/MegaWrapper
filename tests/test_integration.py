"""Basic integration tests: Board + Motor + Servo working together."""

import pytest

from megawrapper import Board, Motor, Servo, delay, millis
from megawrapper.exceptions import MegaWrapperError, InvalidSpeedError


class TestMotorServoIntegration:
    def test_motor_and_servo_on_same_board(self, mock_pyfirmata2):
        """Verify a single board can drive both a motor and a servo."""
        board = Board("/dev/ttyUSB0")

        # Motor
        motor = board.attach_motor(2, 4, 11, name="drive")
        motor.forward(80)
        assert motor.speed == 80
        assert motor.direction == "forward"

        # Servo
        servo = Servo()
        servo.attach(9)
        servo.write(90)
        assert servo.read() == 90

        board.close()

    def test_context_manager_with_motor_and_servo(self, mock_pyfirmata2):
        """Context manager should clean up even with mixed usage."""
        with Board("/dev/ttyUSB0") as board:
            motor = board.attach_motor(2, 4, 11)
            motor.forward(100)

            servo = Servo()
            servo.attach(9)
            servo.write(45)

        board._board.exit.assert_called_once()

    def test_utility_functions_available(self, mock_pyfirmata2):
        """Ensure delay and millis are importable and work."""
        assert callable(delay)
        assert callable(millis)
        ms = millis()
        assert isinstance(ms, int)
        assert ms > 0

    def test_exception_hierarchy(self, mock_pyfirmata2):
        """All custom exceptions inherit from MegaWrapperError."""
        assert issubclass(InvalidSpeedError, MegaWrapperError)

        try:
            raise InvalidSpeedError("test")
        except MegaWrapperError:
            pass  # expected
        else:
            pytest.fail("InvalidSpeedError should be catchable as MegaWrapperError")

    def test_stop_all_stops_motors_but_not_servo(self, mock_pyfirmata2):
        """stop_all should only affect motors, not servos."""
        board = Board("/dev/ttyUSB0")

        motor = board.attach_motor(2, 4, 11)
        motor.forward(100)

        servo = Servo()
        servo.attach(9)
        servo.write(90)

        board.stop_all()

        assert motor.speed == 0
        assert motor.direction == "stopped"
        # Servo should be unaffected
        assert servo.read() == 90
