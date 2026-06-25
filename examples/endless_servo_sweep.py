from megawrapper import Board, Servo, delay

Board("/dev/ttyUSB0")

servo = Servo()
servo.attach(6)

while True:
    # Slow sweep
    for angle in range(0, 181):
        servo.write(angle)
        delay(15)

    # Fast return
    for angle in range(180, -1, -5):
        servo.write(angle)
        delay(5)
