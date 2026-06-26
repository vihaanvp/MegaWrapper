# Changelog

## v0.1.0 (2026-06-25)

Initial release of MegaWrapper — a unified Python library for Arduino-style DC motor and servo control over Firmata.

### Added

- **`Board`** — manages a serial connection to an Arduino running StandardFirmata.
  - Constructor accepts `port` and optional `stby` (standby pin for TB6612FNG).
  - `get_active_board()` static method for servo singleton access.
  - `attach_motor()` to create and register motor instances.
  - `stop_all()` to halt all motors on the board.
  - `wake()` / `sleep()` for standby pin control.
  - `close()` for clean teardown.
  - Context manager support (`with Board(...) as board`).
  - `board.motors` list updated automatically.

- **`Motor`** — DC motor control via H-bridge (2 direction pins + 1 PWM pin).
  - `forward(speed)` / `backward(speed)` with percentage-based speed (0–100).
  - `stop()` (coast) and `brake()` (abrupt halt).
  - `set_speed()` to change speed without affecting direction.
  - `speed`, `direction`, `name` properties.
  - Informative `__repr__()`.

- **`Servo`** — standard servo control on PWM-capable pins.
  - `attach(pin)` / `detach()` for lifecycle management.
  - `write(angle)` with automatic clamping to 0–180.
  - `read()` returning the last commanded angle.
  - `move_smooth(target, delay_ms)` for stepped rotation.
  - `sweep(start, end, step, delay_ms)` for continuous sweeping.
  - `pin` and `current_angle` properties.

- **Utilities** — `delay(ms)` and `millis()` Arduino-style helpers.

- **Exceptions** — clean error hierarchy:
  - `MegaWrapperError` (base)
  - `InvalidSpeedError` (speed outside 0–100)
  - `BoardConnectionError` (Arduino unreachable)
  - `StandbyNotConfiguredError` (STBY pin not set)

- **Package infrastructure:**
  - `pyproject.toml` with setuptools build configuration.
  - All dependencies (`pyfirmata2`, `pyserial`) declared and auto-installed.
  - MIT license.
  - Editable install via `pip install -e .`

- **Documentation:**
  - `README.md` with quick-start examples and links to the wiki.
  - GitHub Wiki with 8 dedicated pages: Home, Board API, Motor API, Servo API, Utilities, Exceptions, Examples, Edge Cases & Notes.
  - `AGENTS.md` for LLM session guidance.
  - `CHANGELOG.md` (this file).

- **Testing:**
  - 72 unit tests across 6 files.
  - All tests mock `pyfirmata2.Arduino` — no hardware required.
  - `conftest.py` resets `_active_board` and provides fresh pin mocks per test.

## v0.2.0-beta (2026-06-26)

### Added

- **`TCS34725`** — RGB colour sensor support over Firmata I2C.
  - `rgb()` / `rgb_raw()` — read normalised and raw RGBC channels.
  - `color_temperature()` — estimate correlated colour temperature (K).
  - `lux()` — estimate illuminance (lux).
  - `set_gain(gain)` — configure sensor gain (1×, 4×, 16×, 60×).
  - `set_integration_time(ms)` — set integration time (2.4–700 ms).
  - Firmata I2C read/write via `send_sysex`/`add_cmd_handler`.
  - I2C reply decoded from 7-bit Firmata encoding.
  - `TCS34725Error` exception for sensor-specific failures.

- **Testing:**
  - 22 new unit tests for TCS34725 (94 total).
  - All tests mock Firmata I2C — no hardware required.
  - Lazy callback lookup pattern for async I2C reply simulation.

### Notes

- Released on the `beta` branch — not merged to `main`.
- Not published on PyPI — install from source.
- Requires Python 3.8+, Arduino running StandardFirmata.
- This release merges and supersedes `motor-like-arduino` (v0.1.0) and `servo-like-arduino` (v0.2.0).
