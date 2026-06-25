# MegaWrapper

**Arduino-style motor and servo control for Python — one library to rule them all.**

MegaWrapper combines `motor-like-arduino` and `servo-like-arduino` into a single
convenience package. Control DC motors (via H-bridge drivers) and servos connected
to an Arduino running StandardFirmata using a simple, intuitive API inspired by the
Arduino ecosystem.

---

## Features

- **DC Motor control** — forward, backward, stop, brake with percentage-based speed (0–100)
- **Servo control** — write, read, smooth movement, sweep with Arduino-like syntax
- **Multiple motors** per board
- **Multiple drivers** — TB6612FNG, L293D, L298N, MX1508
- **Optional standby pin** support (TB6612FNG)
- **Context manager** support (`with Board(...) as board`)
- **Utility functions** — `delay()`, `millis()`
- **Custom exceptions** for clean error handling
- **Built on pyFirmata2**

---

## Installation

```bash
pip install pyfirmata2 pyserial
pip install megawrapper
```

Or install from source:

```bash
pip install -e .
```

---

## Quick Start — DC Motor

```python
from megawrapper import Board

board = Board("/dev/ttyUSB0")

motor = board.attach_motor(
    2,   # Direction Pin 1
    4,   # Direction Pin 2
    11   # PWM Pin
)

motor.forward(100)   # full speed forward
motor.backward(50)   # half speed backward
motor.stop()         # coast to a stop
motor.brake()        # brake

board.close()
```

---

## Quick Start — Servo

```python
from megawrapper import Board, Servo, delay

Board("/dev/ttyUSB0")

servo = Servo()
servo.attach(9)

servo.write(90)       # move to 90°
delay(1000)           # wait 1 second

servo.move_smooth(180)  # sweep smoothly to 180°

servo.sweep(
    start=0,
    end=180,
    step=1,
    delay_ms=15
)
```

---

## Dual Motor Example

```python
from megawrapper import Board
import time

board = Board("/dev/ttyUSB0")

left = board.attach_motor(2, 4, 11, name="left")
right = board.attach_motor(5, 3, 10, name="right")

left.forward(50)
right.forward(100)

time.sleep(3)

board.stop_all()
board.close()
```

---

## Context Manager

```python
from megawrapper import Board, Motor

with Board("/dev/ttyUSB0") as board:
    motor = board.attach_motor(2, 4, 11)
    motor.forward(100)
    # board is automatically closed on exit
```

---

## Optional TB6612FNG Standby Support

```python
board = Board("/dev/ttyUSB0", stby=6)
board.sleep()   # disable motor driver
board.wake()    # re-enable motor driver
```

---

## Examples

Ready-to-run examples are available in the `examples/` directory:

| File | Description |
|------|-------------|
| `single_motor.py` | Basic single motor control |
| `dual_motor.py` | Two motor control |
| `tank_drive.py` | Tank-style steering |
| `keyboard_control.py` | Interactive keyboard control |
| `servo_test.py` | Servo sweep demonstration |
| `move_smooth.py` | Smooth servo movement |
| `endless_servo_sweep.py` | Continuous servo sweep |

---

## Exceptions

| Exception | When raised |
|-----------|-------------|
| `MegaWrapperError` | Base exception for all library errors |
| `InvalidSpeedError` | Motor speed is outside 0–100 |
| `BoardConnectionError` | Cannot connect to Arduino |
| `StandbyNotConfiguredError` | `wake()` / `sleep()` called without a STBY pin |

---

## Requirements

- Python 3.8+
- Arduino running StandardFirmata (File → Examples → Firmata → StandardFirmata)
- pyFirmata2
- pyserial

---

## License

MIT — see [LICENSE](LICENSE).

## Author

Vihaan Parlikar
