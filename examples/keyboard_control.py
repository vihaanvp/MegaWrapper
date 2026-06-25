from megawrapper import Board

board = Board("/dev/ttyUSB0")

motor = board.attach_motor(
    2,
    4,
    11
)

while True:
    command = input(
        "f=forward b=backward s=stop q=quit > "
    ).lower()

    if command == "f":
        motor.forward(100)

    elif command == "b":
        motor.backward(100)

    elif command == "s":
        motor.stop()

    elif command == "q":
        break

board.close()
