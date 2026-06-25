import time

from megawrapper import Board

board = Board("/dev/ttyUSB0")

left = board.attach_motor(2, 4, 11)
right = board.attach_motor(5, 3, 10)

left.forward(100)
right.forward(100)

time.sleep(2)

left.forward(50)
right.forward(100)

time.sleep(2)

left.stop()
right.stop()

board.close()
