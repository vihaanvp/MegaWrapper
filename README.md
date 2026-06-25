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
# Required dependencies
pip install pyfirmata2 pyserial

# Install MegaWrapper (local / editable)
pip install -e .
```

MegaWrapper is not published on PyPI — install directly from the source directory.

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

## Full Documentation

Complete API reference, examples, edge cases, and exception details are available on the **[GitHub Wiki](https://github.com/vihaanvp/MegaWrapper/wiki)**:

| Page | Description |
|------|-------------|
| [Board API](https://github.com/vihaanvp/MegaWrapper/wiki/Board-API) | Board class, connection, motor management, standby pin |
| [Motor API](https://github.com/vihaanvp/MegaWrapper/wiki/Motor-API) | DC motor control — forward, backward, stop, brake |
| [Servo API](https://github.com/vihaanvp/MegaWrapper/wiki/Servo-API) | Servo control — write, read, smooth movement, sweep |
| [Utilities](https://github.com/vihaanvp/MegaWrapper/wiki/Utilities) | `delay()`, `millis()` helpers |
| [Exceptions](https://github.com/vihaanvp/MegaWrapper/wiki/Exceptions) | Exception hierarchy and catch-all patterns |
| [Examples](https://github.com/vihaanvp/MegaWrapper/wiki/Examples) | 10 complete runnable examples |
| [Edge Cases & Notes](https://github.com/vihaanvp/MegaWrapper/wiki/Edge-Cases) | Behavioural details and gotchas |

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
