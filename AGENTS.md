# AGENTS.md — MegaWrapper

A combined DC-motor + servo control library. Wraps `pyfirmata2` for
Arduino-style control over Firmata.

## Package layout

```
src/megawrapper/
├── __init__.py     # exports Board, Motor, Servo, delay, millis, exceptions
├── board.py        # Board class (motor management + servo singleton)
├── motor.py        # Motor class (forward, backward, stop, brake)
├── servo.py        # Servo class (write, read, move_smooth, sweep)
├── utils.py        # delay(), millis()
├── exceptions.py   # MegaWrapperError hierarchy
└── version.py      # __version__ = "1.0.0"
```

Package name: **`megawrapper`** — import as `from megawrapper import Board`.

Not on PyPI. Install locally: `pip install -e /path/to/MegaWrapper`.

## Commands

```bash
pip install -e .              # editable install (deps: pyfirmata2, pyserial)
python -m pytest tests/ -v   # run all 72 tests
```

No lint, typecheck, or CI workflows configured. No `pyproject.toml` tool config
beyond setuptools. No pre-commit hooks.

## Architecture — Board duality

The **Board** class serves two patterns simultaneously:

1. **Motor pattern** — `board = Board(port)` → `board.attach_motor(2,4,11)`
   → `motor.forward(100)`. Supports context manager, `stop_all()`, optional
   STBY pin.
2. **Servo pattern** — `Board(port)` → `Servo()` → `servo.attach(9)`.
   `Servo.attach()` calls `Board.get_active_board()` to find the most recently
   created Board. The active board is stored in a module-level `_active_board`
   variable inside `board.py`.

**Key consequence:** you must create a `Board` *before* calling `Servo.attach()`.
Failing to do so raises `RuntimeError("No board initialised")`.

## Motor class

Created exclusively via `board.attach_motor(d1, d2, pwm, name=None)`.

Speed is always **0–100** (int or float). Internally divided by 100 for
pyfirmata2's 0.0–1.0 PWM range. Invalid values raise `InvalidSpeedError`.

Four direction states: `"forward"`, `"backward"`, `"stopped"`, `"braked"`.

## Servo class

Angles are **silently clamped** to [0, 180]. Passing `200` writes `180`.
Passing `-10` writes `0`.

`read()` requires `write()` to have been called first — otherwise raises
`RuntimeError`. The library tracks commanded angle only (servos don't
report position).

## Testing

All tests mock `pyfirmata2.Arduino` via `tests/conftest.py`. No real
Arduino needed.

```python
@pytest.fixture(autouse=True)
def mock_pyfirmata2():
    # Resets _active_board before each test
    # Each board.get_pin() call returns a fresh MagicMock
```

**Critical detail for writing tests:** `get_pin` uses
`side_effect = lambda *_: MagicMock()`, so every call returns a
*different* mock. This means `_direction1`, `_direction2`, and `_pwm`
are independent — use `assert_called_with()` on the specific pin mock,
not `assert_called_once()` on a shared mock.

72 tests across 6 files. Fast (~0.5 s).

## Exceptions

```
MegaWrapperError
├── InvalidSpeedError          # speed not a number or outside 0–100
├── BoardConnectionError       # Arduino unreachable
└── StandbyNotConfiguredError  # wake()/sleep() without STBY pin
```

`RuntimeError` is also raised directly for servo state errors (not attached,
angle unknown).

## History

This repo is the merge of two prior libraries: `motor-like-arduino` (v0.1.0)
and `servo-like-arduino` (v0.2.0). Both are now archived in favour of
MegaWrapper.
