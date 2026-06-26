# MegaWrapper — Usage Guide

A unified Python library for controlling DC motors, servo motors, and I2C
sensors (TCS34725 colour sensor) over Firmata via an Arduino running
StandardFirmata.

---

## Installation

```bash
pip install -e /path/to/MegaWrapper
```

This auto-installs `pyfirmata2` and `pyserial`.

---

## Table of Contents

1. [Common — Board & Utilities](#1-common--board--utilities)
2. [DC Motors](#2-dc-motors)
3. [Servo Motors](#3-servo-motors)
4. [TCS34725 Colour Sensor](#4-tcs34725-colour-sensor)

---

## 1. Common — Board & Utilities

### Board

Every session starts by creating a `Board` — it opens the serial connection
to the Arduino.

```python
from megawrapper import Board

board = Board("COM3")           # Windows
board = Board("/dev/ttyUSB0")   # Linux / macOS
```

#### Optional standby pin (TB6612FNG motor driver)

```python
board = Board("COM3", stby=8)   # STBY on digital pin 8
```

#### Singleton access (used by Servo and TCS34725)

```python
board = Board("COM3")
same_board = Board.get_active_board()   # returns the Board above
```

**Raises** `RuntimeError` if no Board has been created yet.

#### Motor management

```python
motor = board.attach_motor(2, 4, 11, name="left")
board.motors        # list of all attached Motors
board.stop_all()    # stop every motor at once
```

#### Sleep / wake (needs STBY pin)

```python
board.sleep()       # disable motor driver
board.wake()        # re-enable motor driver
```

Raises `StandbyNotConfiguredError` if no STBY pin was given in the
constructor.

#### Cleanup

```python
board.close()       # stops motors, sleeps driver, closes serial port
```

Or use the context manager:

```python
with Board("COM3") as board:
    motor = board.attach_motor(2, 4, 11)
    motor.forward(100)
# board.close() called automatically
```

### Utilities

```python
from megawrapper import delay, millis

delay(500)          # pause 500 ms
now = millis()      # int timestamp in ms
```

---

## 2. DC Motors

### Attach

Motors are created via the Board, never directly.

```python
board = Board("COM3")
motor = board.attach_motor(direction1=2, direction2=4, pwm=11, name="left")
```

| Parameter    | Description                                         |
|-------------|-----------------------------------------------------|
| `direction1` | Digital pin for H-bridge input 1                    |
| `direction2` | Digital pin for H-bridge input 2                    |
| `pwm`        | PWM-capable pin for speed control                   |
| `name`       | Optional label (e.g. `"left"`, `"right"`, `"arm"`) |

### Movement

```python
motor.forward(75)          # forward at 75%
motor.backward(50)         # backward at 50%
motor.stop()               # coast to stop
motor.brake()              # abrupt stop (short terminals)
```

Speed is **0–100** (int or float). Invalid values raise `InvalidSpeedError`.

### Properties

```python
motor.speed                # current speed (0–100)
motor.direction            # "forward" | "backward" | "stopped" | "braked"
motor.name                 # user-assigned label or None
```

### Change speed without affecting direction

```python
motor.set_speed(80)        # keep current direction, new speed
# or via property:
motor.speed = 80
```

### Full example

```python
from megawrapper import Board, delay

with Board("COM3", stby=8) as board:
    left = board.attach_motor(2, 4, 11, "left")
    right = board.attach_motor(7, 8, 10, "right")

    left.forward(100)
    right.forward(100)
    delay(2000)

    left.backward(80)
    right.backward(80)
    delay(2000)

    board.stop_all()
```

---

## 3. Servo Motors

### Attach

Servos use a singleton-style pattern. A Board must already exist.

```python
from megawrapper import Board, Servo

board = Board("COM3")
servo = Servo()
servo.attach(9)             # PWM-capable digital pin
```

`attach()` calls `Board.get_active_board()` internally.

```python
servo.detach()              # release the pin
```

### Write

```python
servo.write(90)             # move to 90°
servo.write(200)            # clamped to 180
servo.write(-10)            # clamped to 0
```

Angles are **silently clamped** to [0, 180].

### Read

```python
angle = servo.read()        # last commanded angle
```

**Raises** `RuntimeError` if `write()` was never called.

### Smooth movement

```python
servo.move_smooth(180)              # step 1° at a time (15 ms delay)
servo.move_smooth(0, delay_ms=50)   # slower stepping
```

If no previous angle is known, calls `write()` directly.

### Sweep

```python
servo.sweep(0, 180, step=1, delay_ms=15)   # sweep forward
servo.sweep(180, 0, step=2, delay_ms=10)   # sweep backward
```

`step` must be > 0. Angles are clamped to [0, 180].

### Full example

```python
from megawrapper import Board, Servo, delay

board = Board("COM3")
servo = Servo()
servo.attach(9)

servo.write(0)
delay(1000)

servo.move_smooth(180, delay_ms=20)
delay(500)

servo.sweep(180, 0, step=2, delay_ms=10)
```

---

## 4. TCS34725 Colour Sensor

### Wiring

| TCS34725 | Arduino          |
|----------|------------------|
| VIN      | 3.3 V or 5 V    |
| GND      | GND              |
| SDA      | A4 (Uno/Nano)   |
| SCL      | A5 (Uno/Nano)   |
| LED      | GND (or via resistor to VIN for active照明) |

The Arduino must be running **StandardFirmata** (comes with the Arduino IDE).

### Initialise

```python
from megawrapper import Board, TCS34725

board = Board("COM3")
sensor = TCS34725(board)        # explicit board
# or rely on the active board singleton:
sensor = TCS34725()             # uses Board.get_active_board()
```

On construction the sensor is automatically configured at 2.4 ms integration
time (fastest) and 1× gain. The ID register (0x44) is verified — raises
`TCS34725Error` if the sensor is absent.

### Read colour

```python
# Raw 16-bit ADC counts (clear, red, green, blue)
c, r, g, b = sensor.rgb_raw()

# Normalised 0–255 per channel (scaled relative to clear)
r, g, b = sensor.rgb()
```

`rgb()` returns `(0, 0, 0)` when clear = 0 (no light).

### Read colour temperature and lux

```python
kelvin = sensor.color_temperature()     # 1550–10000 K (approx.)
lux_val = sensor.lux()                  # illuminance in lux
```

Both return `0` if the reading is invalid (clear = 0).

### Gain control

```python
sensor.set_gain(1)      # 1×  (low gain, bright conditions)
sensor.set_gain(4)      # 4×
sensor.set_gain(16)     # 16×
sensor.set_gain(60)     # 60× (high gain, dim conditions)
```

Raises `ValueError` for unrecognised values.

### Integration time

```python
sensor.set_integration_time(2.4)    # fastest — 2.4 ms
sensor.set_integration_time(24)     # 24 ms
sensor.set_integration_time(50)     # 50 ms
sensor.set_integration_time(101)    # 101 ms
sensor.set_integration_time(154)    # 154 ms
sensor.set_integration_time(700)    # slowest — 700 ms
```

Longer times give better precision but run less frequently. Raises
`ValueError` for unsupported values.

### Full example

```python
from megawrapper import Board, TCS34725, delay

with Board("COM3") as board:
    sensor = TCS34725(board)

    # Configure for moderate light
    sensor.set_gain(4)
    sensor.set_integration_time(24)

    while True:
        r, g, b = sensor.rgb()
        ct = sensor.color_temperature()
        lux_val = sensor.lux()

        print(f"RGB: ({r:3d}, {g:3d}, {b:3d})  "
              f"CT: {ct:5d} K  Lux: {lux_val:6.1f}")

        delay(500)      # 2 Hz
```

---

## Exception Hierarchy

```
MegaWrapperError                 (base exception)
├── InvalidSpeedError            speed not a number or outside 0–100
├── BoardConnectionError         Arduino unreachable
├── StandbyNotConfiguredError    wake()/sleep() without STBY pin
└── TCS34725Error                TCS34725 sensor I/O error
```

`RuntimeError` is raised directly for:

- `Board.get_active_board()` when no Board exists
- `Servo.read()` when `write()` was never called
- `Servo.attach()` before creating a Board
- `TCS34725()` when no Board exists and none is provided

---

## Wiring Reference

| Component       | Arduino Pin               |
|----------------|---------------------------|
| H-bridge IN1   | Any digital               |
| H-bridge IN2   | Any digital               |
| H-bridge PWM   | PWM-capable (3,5,6,9,10,11) |
| H-bridge STBY  | Any digital (optional)    |
| Servo signal   | PWM-capable               |
| TCS34725 SDA   | A4                        |
| TCS34725 SCL   | A5                        |
