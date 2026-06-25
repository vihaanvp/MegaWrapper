import time

from megawrapper import Board

board = Board("/dev/ttyUSB0")

left = board.attach_motor(
    2,
    4,
    11,
    "left"
)

right = board.attach_motor(
    5,
    3,
    10,
    "right"
)

left.forward(50)
right.forward(100)

time.sleep(3)

board.stop_all()

board.close()
