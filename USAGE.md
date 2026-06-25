# MegaWrapper — Complete Usage Reference

> **Version:** 1.0.0  
> **Author:** Vihaan Parlikar  
> **License:** MIT  

A unified Python library for Arduino-style **DC motor** and **servo** control over
Firmata. Wraps `pyfirmata2` to give you a simple, Arduino-inspired API.

---

## Table of Contents

1. [Installation](#installation)
2. [Arduino Setup](#arduino-setup)
3. [Port Identification](#port-identification)
4. [Package Overview](#package-overview)
5. [Board API](#board-api)
6. [Motor API](#motor-api)
7. [Servo API](#servo-api)
8. [Utility Functions](#utility-functions)
9. [Exception Hierarchy](#exception-hierarchy)
10. [Complete Examples](#complete-examples)
11. [Edge Cases & Notes](#edge-cases--notes)

---

## Installation

```bash
# Required dependencies
pip install pyfirmata2 pyserial

# Install MegaWrapper (local / editable)
pip install -e /path/to/MegaWrapper

# Or just point pip at the directory
pip install -e .
```

---

## Arduino Setup

1. Open the Arduino IDE.
2. Go to **File → Examples → Firmata → StandardFirmata**.
3. Upload the sketch to your Arduino board.
4. Leave the USB cable connected — that's the serial link the library uses.

---

## Port Identification

| OS      | Typical port                                  |
|---------|-----------------------------------------------|
| Linux   | `/dev/ttyUSB0`, `/dev/ttyACM0`               |
| macOS   | `/dev/tty.usbserial-*`, `/dev/tty.usbmodem*` |
| Windows | `COM3`, `COM4`, etc.                          |

To find the right port on Windows, open **Device Manager** and look under
**Ports (COM & LPT)**. On Linux/macOS, run `ls /dev/tty*` before and after
plugging in the Arduino and see what appears.

---

## Package Overview

```
from megawrapper import (
    Board,                     # Arduino connection
    Motor,                     # DC motor (H-bridge)
    Servo,                     # Servo motor
    delay,                     # Pause (ms)
    millis,                    # Epoch time (ms)

    MegaWrapperError,          # Base exception
    InvalidSpeedError,         # Speed out of 0-100
    BoardConnectionError,      # Can't reach Arduino
    StandbyNotConfiguredError, # STBY pin not set

    __version__,               # "1.0.0"
)
```

All public symbols are importable directly from `megawrapper`:

```python
from megawrapper import Board, Motor, Servo
```

---

## Board API

The `Board` class manages a serial connection to an Arduino running
StandardFirmata. It serves double duty:

1. **Motor users** — create a Board, then attach motors to it.
2. **Servo users** — create a Board (the last one created becomes the
   "active" board), then Servo will find it automatically.

### Constructor

```python
Board(port: str, stby: int | None = None)
```

| Parameter | Type   | Required | Default | Description                                      |
|-----------|--------|----------|---------|--------------------------------------------------|
| `port`    | `str`  | Yes      | —       | Serial port of the Arduino.                      |
| `stby`    | `int`  | No       | `None`  | Digital pin for TB6612FNG standby (optional).    |

**Raises:** `BoardConnectionError` if the Arduino cannot be reached.

**Example:**

```python
# Minimal
board = Board("/dev/ttyUSB0")

# With standby pin for TB6612FNG motor driver
board = Board("/dev/ttyUSB0", stby=6)
```

When a `stby` pin is provided, the driver is **woken automatically**
(pin set HIGH) during construction.

---

### `Board.get_active_board()`

```python
@staticmethod
Board.get_active_board() -> Board
```

Returns the most recently created `Board` instance. This is how `Servo`
finds the board.

**Raises:** `RuntimeError` if no Board has been created yet.

```python
board = Board("/dev/ttyUSB0")
assert Board.get_active_board() is board  # True
```

---

### `Board.attach_motor()`

```python
Board.attach_motor(
    direction1: int,
    direction2: int,
    pwm: int,
    name: str | None = None,
) -> Motor
```

Creates a `Motor` and registers it in `board.motors`.

| Parameter    | Type     | Required | Default | Description                           |
|--------------|----------|----------|---------|---------------------------------------|
| `direction1` | `int`    | Yes      | —       | First direction-control digital pin.  |
| `direction2` | `int`    | Yes      | —       | Second direction-control digital pin. |
| `pwm`        | `int`    | Yes      | —       | PWM-capable pin for speed.            |
| `name`       | `str`    | No       | `None`  | Optional label (e.g. `"left"`).       |

**Returns:** The newly created `Motor` instance.

```python
motor = board.attach_motor(2, 4, 11, name="drive")
```

---

### `Board.stop_all()`

```python
Board.stop_all() -> None
```

Calls `motor.stop()` on every motor in `board.motors`.

```python
board.stop_all()  # every motor coasts to a stop
```

---

### `Board.wake()` / `Board.sleep()`

```python
Board.wake()  -> None    # enable motor driver (STBY → HIGH)
Board.sleep() -> None    # disable motor driver (STBY → LOW)
```

Only available when `stby` was provided to the constructor.

**Raises:** `StandbyNotConfiguredError` if no STBY pin was set.

```python
board = Board("/dev/ttyUSB0", stby=6)
board.sleep()   # motors can't move
board.wake()    # motors can move again
```

---

### `Board.close()`

```python
Board.close() -> None
```

1. Stops all motors.
2. Asserts STBY LOW (if configured).
3. Calls `exit()` on the underlying pyfirmata2 connection.

Always call this when done, or use the context manager.

---

### Context Manager

```python
with Board("/dev/ttyUSB0") as board:
    motor = board.attach_motor(2, 4, 11)
    motor.forward(100)
# board.close() called automatically on exit
```

---

### `board.motors`

A `list[Motor]` of every motor created via `attach_motor()` on this board.
Updated automatically.

```python
board = Board("/dev/ttyUSB0")
m1 = board.attach_motor(2, 4, 11)
m2 = board.attach_motor(5, 3, 10)
print(board.motors)  # [m1, m2]
```

---

## Motor API

The `Motor` class controls a DC motor connected through an H-bridge driver
that uses **2 direction pins** + **1 PWM pin** (e.g. L298N, TB6612FNG,
L293D, MX1508).

**You never create a Motor directly** — use `board.attach_motor()`.

---

### `Motor.forward()`

```python
Motor.forward(speed: int | float = 100) -> None
```

Rotate the motor forward at the given speed.

| Parameter | Type         | Default | Description                    |
|-----------|--------------|---------|--------------------------------|
| `speed`   | `int/float`  | `100`   | Speed percentage (0 = stop, 100 = full). |

**Raises:** `InvalidSpeedError` if speed is not a number or outside 0–100.

```python
motor.forward()     # full speed
motor.forward(75)   # 75% speed
```

---

### `Motor.backward()`

```python
Motor.backward(speed: int | float = 100) -> None
```

Rotate the motor backward. Same parameters and validation as `forward()`.

```python
motor.backward(50)  # 50% speed backward
```

---

### `Motor.stop()`

```python
Motor.stop() -> None
```

Coast to a stop (both direction pins LOW, PWM = 0).

```python
motor.stop()
```

---

### `Motor.brake()`

```python
Motor.brake() -> None
```

Brake by shorting the motor terminals (both direction pins HIGH, PWM = 0).
Stops more abruptly than `stop()`.

```python
motor.brake()
```

---

### `Motor.set_speed()`

```python
Motor.set_speed(speed: int | float) -> None
```

Change speed without altering direction.

| Parameter | Type         | Description                              |
|-----------|--------------|------------------------------------------|
| `speed`   | `int/float`  | New speed (0–100).                       |

```python
motor.forward(100)
motor.set_speed(30)   # now going forward at 30%
```

---

### `Motor.speed` property

```python
Motor.speed -> int
```

Current speed (0–100). Readable and writable (setter calls `set_speed()`).

```python
print(motor.speed)   # e.g. 75
motor.speed = 50     # same as motor.set_speed(50)
```

---

### `Motor.direction` property

```python
Motor.direction -> str
```

One of: `"forward"`, `"backward"`, `"stopped"`, `"braked"`.

```python
print(motor.direction)  # e.g. "forward"
```

---

### `Motor.name`

```python
Motor.name -> str | None
```

The optional name given at creation time.

```python
motor = board.attach_motor(2, 4, 11, name="left")
print(motor.name)  # "left"
```

---

### `Motor.__repr__()`

```python
repr(motor)  # e.g. "Motor(direction='forward', speed=75)"
```

---

## Servo API

The `Servo` class controls a standard servo motor (0–180°) attached to a
PWM-capable Arduino pin.

---

### `Servo()`

```python
servo = Servo()
```

Creates an un-attached servo. You must call `attach(pin)` before any
movement commands.

---

### `Servo.attach()`

```python
Servo.attach(pin: int) -> None
```

Bind the servo to a PWM-capable digital pin.

| Parameter | Type  | Description                |
|-----------|-------|----------------------------|
| `pin`     | `int` | Digital pin number (e.g. 9). |

**Requires:** A `Board` must have been created beforehand (it uses
`Board.get_active_board()`).

**Raises:** `RuntimeError` if no Board exists.

```python
Board("/dev/ttyUSB0")
servo = Servo()
servo.attach(9)
```

---

### `Servo.detach()`

```python
Servo.detach() -> None
```

Release the pin. Clears `pin`, `current_angle`, and the internal servo
reference. Call `attach()` again before further movement.

```python
servo.detach()
```

---

### `Servo.write()`

```python
Servo.write(angle: int | float) -> None
```

Immediately move the servo to the given angle.

| Parameter | Type         | Description                            |
|-----------|--------------|----------------------------------------|
| `angle`   | `int/float`  | Target angle. Clamped to 0–180 internally. |

**Raises:**
- `RuntimeError` if not attached.
- `ValueError` if angle is not a number.

```python
servo.write(90)    # centre
servo.write(0)     # minimum
servo.write(180)   # maximum
servo.write(200)   # silently clamped to 180
```

---

### `Servo.read()`

```python
Servo.read() -> int
```

Return the last angle written via `write()`, `move_smooth()`, or `sweep()`.

**Raises:**
- `RuntimeError` if not attached.
- `RuntimeError` if `write()` has never been called (angle is unknown).

```python
servo.write(90)
print(servo.read())  # 90
```

---

### `Servo.move_smooth()`

```python
Servo.move_smooth(
    target_angle: int | float,
    delay_ms: int = 15,
) -> None
```

Move to `target_angle` one degree at a time with a pause between steps.
Produces a smooth, visible rotation.

| Parameter     | Type         | Default | Description                              |
|---------------|--------------|---------|------------------------------------------|
| `target_angle`| `int/float`  | —       | Destination angle (clamped 0–180).       |
| `delay_ms`    | `int`        | `15`    | Milliseconds between each 1° step.       |

**Behaviour when `current_angle` is `None`:** jumps directly to target
(same as `write()`).

**Behaviour when `target_angle == current_angle`:** does nothing.

```python
servo.attach(9)
servo.write(0)
servo.move_smooth(180, delay_ms=10)  # smooth 0→180
```

---

### `Servo.sweep()`

```python
Servo.sweep(
    start: int | float = 0,
    end: int | float = 180,
    step: int = 1,
    delay_ms: int = 15,
) -> None
```

Sweep the servo from `start` to `end`, stepping by `step` degrees each
`delay_ms` milliseconds.

| Parameter | Type         | Default | Description                             |
|-----------|--------------|---------|-----------------------------------------|
| `start`   | `int/float`  | `0`     | Starting angle (clamped 0–180).         |
| `end`     | `int/float`  | `180`   | Ending angle (clamped 0–180).           |
| `step`    | `int`        | `1`     | Degrees per step (must be > 0).         |
| `delay_ms`| `int`        | `15`    | Milliseconds between each step.         |

**Raises:** `ValueError` if `step <= 0`.

Works in both directions: `start < end` sweeps up, `start > end` sweeps down.

```python
servo.sweep(0, 180, 1, 15)     # slow sweep up
servo.sweep(180, 0, 5, 5)      # fast sweep down
```

---

### `Servo.pin`

```python
Servo.pin -> int | None
```

The pin the servo is attached to, or `None` if detached.

---

### `Servo.current_angle`

```python
Servo.current_angle -> int | None
```

The last commanded angle, or `None` if `write()` has never been called.
Updated by `write()`, `move_smooth()`, and `sweep()`.

---

## Utility Functions

### `delay(ms)`

```python
delay(ms: int | float) -> None
```

Pause execution for `ms` milliseconds. Analogous to Arduino's `delay()`.

```python
from megawrapper import delay
delay(1000)  # wait 1 second
```

### `millis()`

```python
millis() -> int
```

Return the number of milliseconds since the epoch (Unix time × 1000).
Analogous to Arduino's `millis()`.

```python
from megawrapper import millis
start = millis()
# ... do something ...
elapsed = millis() - start
```

---

## Exception Hierarchy

```
Exception
└── MegaWrapperError                   # Base for all library errors
    ├── InvalidSpeedError              # Speed not a number or outside 0-100
    ├── BoardConnectionError           # Cannot connect to Arduino
    └── StandbyNotConfiguredError      # wake()/sleep() called without STBY pin
```

Additionally, the library may raise standard Python exceptions:

| Exception      | Raised by             | Condition                                   |
|----------------|-----------------------|---------------------------------------------|
| `RuntimeError` | `Servo.attach()`      | No Board has been created yet.              |
| `RuntimeError` | `Servo.write/read/...`| Servo not attached via `attach()`.          |
| `RuntimeError` | `Servo.read()`        | `write()` never called — angle unknown.     |
| `ValueError`   | `Servo.sweep()`       | `step <= 0`.                                |
| `ValueError`   | `Servo.write()`       | Angle is not a number.                      |

**Catch-all pattern:**

```python
from megawrapper import MegaWrapperError

try:
    board = Board("COM3")
    motor = board.attach_motor(2, 4, 11)
    motor.forward(999)        # raises InvalidSpeedError
except MegaWrapperError as e:
    print(f"MegaWrapper error: {e}")
```

---

## Complete Examples

### Example 1 — Single DC Motor

```python
import time
from megawrapper import Board

board = Board("/dev/ttyUSB0")

motor = board.attach_motor(
    2,   # Direction pin 1
    4,   # Direction pin 2
    11,  # PWM pin
)

motor.forward(100)          # full speed forward
time.sleep(2)
motor.backward(50)          # half speed backward
time.sleep(2)
motor.stop()                # coast to stop

board.close()
```

### Example 2 — Dual DC Motors (Tank Drive)

```python
import time
from megawrapper import Board

board = Board("/dev/ttyUSB0")

left  = board.attach_motor(2, 4, 11, name="left")
right = board.attach_motor(5, 3, 10, name="right")

# Go straight
left.forward(100)
right.forward(100)
time.sleep(2)

# Turn right
left.forward(100)
right.forward(50)
time.sleep(2)

# Stop
board.stop_all()
board.close()
```

### Example 3 — TB6612FNG Standby Pin

```python
import time
from megawrapper import Board

board = Board("/dev/ttyUSB0", stby=6)

motor = board.attach_motor(2, 4, 11)

motor.forward(100)
time.sleep(2)

board.sleep()           # driver disabled
time.sleep(1)

board.wake()            # driver re-enabled
motor.backward(100)
time.sleep(2)

board.close()
```

### Example 4 — Context Manager

```python
from megawrapper import Board

with Board("/dev/ttyUSB0") as board:
    motor = board.attach_motor(2, 4, 11)
    motor.forward(100)
    input("Press Enter to stop...")
# board.close() called automatically
```

### Example 5 — Single Servo

```python
from megawrapper import Board, Servo, delay

Board("/dev/ttyUSB0")

servo = Servo()
servo.attach(9)

servo.write(90)            # centre
delay(1000)

servo.write(0)             # minimum
delay(1000)

servo.write(180)           # maximum
```

### Example 6 — Smooth Servo Movement

```python
from megawrapper import Board, Servo

Board("/dev/ttyUSB0")
servo = Servo()
servo.attach(9)

servo.move_smooth(180)     # smooth 1°/step, 15 ms between steps
```

### Example 7 — Continuous Servo Sweep

```python
from megawrapper import Board, Servo, delay

Board("/dev/ttyUSB0")
servo = Servo()
servo.attach(6)

while True:
    # Slow sweep up
    for angle in range(0, 181):
        servo.write(angle)
        delay(15)

    # Fast return
    for angle in range(180, -1, -5):
        servo.write(angle)
        delay(5)
```

### Example 8 — Servo + Motor on One Board

```python
import time
from megawrapper import Board, Servo, delay

board = Board("/dev/ttyUSB0")

# Motor
motor = board.attach_motor(2, 4, 11)
motor.forward(100)

# Servo (uses the same board automatically)
servo = Servo()
servo.attach(9)
servo.write(90)

time.sleep(2)

board.close()   # stops motor, cleans up everything
```

### Example 9 — Keyboard Interactive Motor Control

```python
from megawrapper import Board

board = Board("/dev/ttyUSB0")
motor = board.attach_motor(2, 4, 11)

while True:
    cmd = input("f=forward b=backward s=stop q=quit > ").lower()
    if cmd == "f":
        motor.forward(100)
    elif cmd == "b":
        motor.backward(100)
    elif cmd == "s":
        motor.stop()
    elif cmd == "q":
        break

board.close()
```

### Example 10 — Error Handling

```python
from megawrapper import (
    Board, MegaWrapperError,
    BoardConnectionError,
    InvalidSpeedError,
)

try:
    board = Board("COM99")    # wrong port
except BoardConnectionError as e:
    print(f"Connection failed: {e}")
    exit(1)

motor = board.attach_motor(2, 4, 11)

try:
    motor.forward(-5)         # invalid speed
except InvalidSpeedError as e:
    print(f"Speed error: {e}")
    motor.stop()

board.close()
```

---

## Edge Cases & Notes

### Board
- **Multiple Board instances:** Each creates its own serial connection.
  The *last* one created becomes the active board for `Servo`.
- **`get_active_board()` before any Board exists:** Raises `RuntimeError`.
- **`stby` pin:** If provided, automatically set HIGH (wake) on creation.
  Set LOW (sleep) on `close()`.
- **Context manager:** Always calls `close()` even if an exception occurs
  inside the `with` block.

### Motor
- **Speed range:** Integer or float. `0` = stopped, `100` = full.
  Converted internally to `0.0–1.0` for pyfirmata2 PWM.
- **`forward()` / `backward()` with no argument:** Defaults to `100`
  (full speed).
- **`set_speed()`** changes speed without affecting direction pins.
- **`stop()` vs `brake()`:** `stop()` lets the motor coast (inertia);
  `brake()` shorts the terminals for abrupt halting.
- **Reusing after stop:** Just call `forward()` or `backward()` again.

### Servo
- **Angle clamping:** All angles are clamped to `[0, 180]`. Passing `200`
  behaves the same as `180`. Passing `-10` behaves the same as `0`.
- **`attach()` requires a prior `Board`:** Uses
  `Board.get_active_board()` internally.
- **`read()` requires a prior `write()`:** The library tracks the last
  *commanded* angle, not the physical angle (servos don't report position).
- **`move_smooth()` when `current_angle` is `None`:** Jumps directly to
  target without stepping.
- **`move_smooth()` when already at target:** No-op (no writes sent).
- **`sweep()` direction:** Automatically determined by `start` vs `end`.
  `step` must be positive.
- **`detach()`:** Clears all state. Call `attach()` again to reuse.

### General
- **Port already in use:** pyfirmata2 will raise an exception, which
  MegaWrapper converts to `BoardConnectionError`.
- **Serial latency:** Some Arduino clones may need extra time to initialise
  after opening the serial port.
- **Power:** Always use an external power supply for motors and servos.
  Do not draw significant current from the Arduino's 5 V pin.
- **`delay()` vs `time.sleep()`:** `delay(ms)` is a thin wrapper around
  `time.sleep(ms / 1000)` — they are equivalent. Use whichever you prefer.
