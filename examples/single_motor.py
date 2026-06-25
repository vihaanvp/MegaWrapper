import time

from megawrapper import Board

board = Board("/dev/ttyUSB0")

motor = board.attach_motor(
    2,
    4,
    11
)

motor.forward(100)

time.sleep(2)

motor.stop()

board.close()
