from megawrapper import Board, Servo, delay

Board("/dev/ttyUSB0")

servo = Servo()
servo.attach(9)

servo.write(90)
delay(1000)

while True:
    servo.sweep(
        start=0,
        end=180,
        step=1,
        delay_ms=15
    )

    servo.sweep(
        start=180,
        end=0,
        step=5,
        delay_ms=5
    )
