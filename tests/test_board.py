"""Tests for the Board class (combined motor + servo board)."""

from unittest.mock import MagicMock

import pytest

from megawrapper import Board
from megawrapper.exceptions import BoardConnectionError, StandbyNotConfiguredError
from megawrapper.motor import Motor


class TestBoardInitialisation:
    def test_creates_arduino_connection(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        mock_pyfirmata2.assert_called_once_with("/dev/ttyUSB0")
        assert board._board is not None

    def test_no_stby_by_default(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        assert board._stby is None

    def test_stby_pin_configured(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0", stby=6)
        assert board._stby is not None
        board._stby.write.assert_called_with(1)  # wake by default

    def test_connection_error(self, mock_pyfirmata2):
        mock_pyfirmata2.side_effect = Exception("port not found")
        with pytest.raises(BoardConnectionError, match="port not found"):
            Board("/dev/ttyUSB0")

    def test_active_board_singleton(self, mock_pyfirmata2):
        board1 = Board("/dev/ttyUSB0")
        assert Board.get_active_board() is board1

        board2 = Board("COM3")
        assert Board.get_active_board() is board2  # last one wins

    def test_get_active_board_before_any_created(self, mock_pyfirmata2):
        # Manually reset by clearing the global (happens between tests via fixture)
        with pytest.raises(RuntimeError, match="No board initialised"):
            Board.get_active_board()


class TestBoardMotorAttachment:
    def test_attach_motor_returns_motor(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        motor = board.attach_motor(2, 4, 11, name="left")
        assert isinstance(motor, Motor)
        assert motor.name == "left"

    def test_attach_motor_registers(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        m1 = board.attach_motor(2, 4, 11)
        m2 = board.attach_motor(5, 3, 10)
        assert board.motors == [m1, m2]

    def test_attach_motor_uses_correct_pins(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        board.attach_motor(2, 4, 11)
        board._board.get_pin.assert_any_call("d:2:o")
        board._board.get_pin.assert_any_call("d:4:o")
        board._board.get_pin.assert_any_call("d:11:p")


class TestBoardMotorControl:
    def test_stop_all_stops_every_motor(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        m1 = board.attach_motor(2, 4, 11)
        m2 = board.attach_motor(5, 3, 10)

        m1.forward(100)
        m2.forward(50)
        board.stop_all()

        assert m1.direction == "stopped"
        assert m1.speed == 0
        assert m2.direction == "stopped"
        assert m2.speed == 0


class TestBoardStandby:
    def test_wake_raises_without_stby(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        with pytest.raises(StandbyNotConfiguredError):
            board.wake()

    def test_sleep_raises_without_stby(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        with pytest.raises(StandbyNotConfiguredError):
            board.sleep()

    def test_wake_and_sleep(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0", stby=6)
        board.sleep()
        board._stby.write.assert_called_with(0)
        board.wake()
        board._stby.write.assert_called_with(1)


class TestBoardCleanup:
    def test_close_stops_motors_and_exits(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0")
        m = board.attach_motor(2, 4, 11)
        m.forward(100)
        board.close()
        assert m.speed == 0
        board._board.exit.assert_called_once()

    def test_close_with_stby(self, mock_pyfirmata2):
        board = Board("/dev/ttyUSB0", stby=6)
        board.close()
        board._stby.write.assert_called_with(0)

    def test_context_manager(self, mock_pyfirmata2):
        with Board("/dev/ttyUSB0") as board:
            m = board.attach_motor(2, 4, 11)
            m.forward(80)
        # Board should be closed on exit
        board._board.exit.assert_called_once()
