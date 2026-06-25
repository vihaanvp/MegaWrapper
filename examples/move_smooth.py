from megawrapper import Board, Servo, delay

Board("/dev/ttyUSB0")

servo = Servo()
servo.attach(6)

servo.move_smooth(180)
delay(1000)

servo.move_smooth(0)
