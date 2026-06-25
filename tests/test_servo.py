"""Tests for the Servo class."""

from unittest.mock import MagicMock, patch

import pytest

from megawrapper import Board, Servo
from megawrapper.servo import delay as servo_delay  # noqa: used internally


@pytest.fixture(autouse=True)
def reset_active_board():
    """Ensure a fresh board singleton before each servo test."""
    import megawrapper.board as board_mod
    board_mod._active_board = None


class TestServoAttach:
    def test_attach_requires_active_board(self, mock_pyfirmata2):
        servo = Servo()
        with pytest.raises(RuntimeError, match="No board initialised"):
            servo.attach(9)

    def test_attach_sets_pin_and_servo(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        servo = Servo()
        servo.attach(9)
        assert servo.pin == 9
        assert servo._servo is not None
        board._board.get_pin.assert_called_with("d:9:s")

    def test_detach_clears_state(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        servo = Servo()
        servo.attach(9)
        servo.detach()
        assert servo._servo is None
        assert servo.pin is None
        assert servo.current_angle is None


class TestServoWrite:
    def test_write_sets_angle(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        servo = Servo()
        servo.attach(9)
        servo.write(90)
        servo._servo.write.assert_called_with(90)
        assert servo.current_angle == 90

    def test_write_clamps_low(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        servo = Servo()
        servo.attach(9)
        servo.write(-10)
        servo._servo.write.assert_called_with(0)

    def test_write_clamps_high(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        servo = Servo()
        servo.attach(9)
        servo.write(200)
        servo._servo.write.assert_called_with(180)

    @pytest.mark.parametrize("angle", [0, 45, 90, 135, 180])
    def test_valid_angles(self, mock_pyfirmata2, angle):
        board = Board("/dev/ttyUSB0")
        servo = Servo()
        servo.attach(9)
        servo.write(angle)
        servo._servo.write.assert_called_with(angle)

    def test_write_raises_if_not_attached(self, mock_pyfirmata2):
        Board("/dev/ttyUSB0")
        servo = Servo()
        with pytest.raises(RuntimeError, match="Servo not attached"):
            servo.write(90)

    def test_write_validates_type(self, mock_pyfirmata2):
        Board("/dev/ttyUSB0")
        servo = Servo()
        servo.attach(9)
        with pytest.raises(ValueError, match="angle must be a number"):
            servo.write("invalid")


class TestServoRead:
    def test_read_returns_current_angle(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        servo = Servo()
        servo.attach(9)
        servo.write(45)
        assert servo.read() == 45

    def test_read_raises_if_never_written(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        servo = Servo()
        servo.attach(9)
        with pytest.raises(RuntimeError, match="Servo angle is unknown"):
            servo.read()

    def test_read_raises_if_not_attached(self, mock_pyfirmata2):
        Board("/dev/ttyUSB0")
        servo = Servo()
        with pytest.raises(RuntimeError, match="Servo not attached"):
            servo.read()


class TestServoMoveSmooth:
    def test_move_smooth_no_current_writes_directly(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        servo = Servo()
        servo.attach(9)
        servo.move_smooth(120)
        # Without a current_angle it should jump directly
        servo._servo.write.assert_called_once_with(120)

    def test_move_smooth_same_angle_does_nothing(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        servo = Servo()
        servo.attach(9)
        servo.write(90)
        servo._servo.write.reset_mock()
        servo.move_smooth(90)
        servo._servo.write.assert_not_called()


class TestServoSweep:
    def test_sweep_forwards(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        servo = Servo()
        servo.attach(9)
        servo.sweep(start=90, end=92, step=1, delay_ms=1)
        calls = [call[0][0] for call in servo._servo.write.call_args_list]
        assert calls == [90, 91, 92]

    def test_sweep_backwards(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        servo = Servo()
        servo.attach(9)
        servo.sweep(start=92, end=90, step=1, delay_ms=1)
        calls = [call[0][0] for call in servo._servo.write.call_args_list]
        assert calls == [92, 91, 90]

    def test_sweep_negative_step_raises(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        servo = Servo()
        servo.attach(9)
        with pytest.raises(ValueError, match="step must be greater than 0"):
            servo.sweep(start=0, end=180, step=-1, delay_ms=1)

    def test_sweep_clamps_angles(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        servo = Servo()
        servo.attach(9)
        # Start below 0 and end above 180 should be clamped
        servo.sweep(start=-10, end=190, step=100, delay_ms=1)
        calls = [call[0][0] for call in servo._servo.write.call_args_list]
        assert calls == [0, 100]  # clamped to valid range
