"""Tests for the Motor class."""

from unittest.mock import MagicMock

import pytest

from megawrapper.motor import Motor
from megawrapper.exceptions import InvalidSpeedError


@pytest.fixture
def mock_board():
    """Return a mock pyfirmata2 board with independent pin mocks."""
    board = MagicMock()
    board.get_pin.side_effect = lambda *_: MagicMock()
    return board


class TestMotorInit:
    def test_default_state(self, mock_board):
        motor = Motor(mock_board, 2, 4, 11)
        assert motor.speed == 0
        assert motor.direction == "stopped"
        assert motor.name is None

    def test_with_name(self, mock_board):
        motor = Motor(mock_board, 2, 4, 11, name="left")
        assert motor.name == "left"

    def test_repr(self, mock_board):
        motor = Motor(mock_board, 2, 4, 11)
        assert "Motor(" in repr(motor)
        assert "stopped" in repr(motor)


class TestMotorForward:
    def test_forward_sets_pins_and_speed(self, mock_board):
        motor = Motor(mock_board, 2, 4, 11)
        motor.forward(75)
        motor._direction1.write.assert_called_with(1)
        motor._direction2.write.assert_called_with(0)
        motor._pwm.write.assert_called_with(0.75)
        assert motor.speed == 75
        assert motor.direction == "forward"

    def test_forward_default_speed(self, mock_board):
        motor = Motor(mock_board, 2, 4, 11)
        motor.forward()
        motor._pwm.write.assert_called_with(1.0)
        assert motor.speed == 100


class TestMotorBackward:
    def test_backward_sets_pins_and_speed(self, mock_board):
        motor = Motor(mock_board, 2, 4, 11)
        motor.backward(50)
        motor._direction1.write.assert_called_with(0)
        motor._direction2.write.assert_called_with(1)
        motor._pwm.write.assert_called_with(0.5)
        assert motor.speed == 50
        assert motor.direction == "backward"


class TestMotorStop:
    def test_stop_coasts(self, mock_board):
        motor = Motor(mock_board, 2, 4, 11)
        motor.forward(80)
        motor.stop()
        motor._direction1.write.assert_called_with(0)
        motor._direction2.write.assert_called_with(0)
        motor._pwm.write.assert_called_with(0.0)
        assert motor.speed == 0
        assert motor.direction == "stopped"


class TestMotorBrake:
    def test_brake_shorts_terminals(self, mock_board):
        motor = Motor(mock_board, 2, 4, 11)
        motor.brake()
        motor._direction1.write.assert_called_with(1)
        motor._direction2.write.assert_called_with(1)
        motor._pwm.write.assert_called_with(0.0)
        assert motor.direction == "braked"


class TestMotorSetSpeed:
    def test_set_speed_changes_speed_only(self, mock_board):
        motor = Motor(mock_board, 2, 4, 11)
        motor.forward(100)
        motor.set_speed(30)
        assert motor.speed == 30
        assert motor.direction == "forward"  # direction unchanged


class TestMotorSpeedProperty:
    def test_speed_setter(self, mock_board):
        motor = Motor(mock_board, 2, 4, 11)
        motor.speed = 60
        assert motor.speed == 60


class TestMotorSpeedValidation:
    @pytest.mark.parametrize("bad", [-1, 101, "abc", None])
    def test_invalid_speed_raises(self, mock_board, bad):
        motor = Motor(mock_board, 2, 4, 11)
        with pytest.raises(InvalidSpeedError):
            motor.forward(bad)

    @pytest.mark.parametrize("good", [0, 1, 50, 100])
    def test_valid_speeds(self, mock_board, good):
        motor = Motor(mock_board, 2, 4, 11)
        motor.forward(good)
        assert motor.speed == good
