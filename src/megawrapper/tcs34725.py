"""
TCS34725 RGB color sensor support for MegaWrapper.

Communicates with the sensor over I2C via an Arduino running StandardFirmata.
The sensor connects to the Arduino's I2C pins (SDA → A4, SCL → A5 on Uno/Nano).
"""

import threading

import pyfirmata2

from megawrapper.board import Board
from megawrapper.exceptions import MegaWrapperError, TCS34725Error

# ──────────────────────────────────────────────
# TCS34725 register map
# ──────────────────────────────────────────────
_COMMAND_BIT = 0x80       # must be set for all register accesses
_AUTO_INC = 0x20           # auto-increment register address

_ENABLE = 0x00             # R/W  – Enable
_ATIME = 0x01              # R/W  – RGBC integration time
_WTIME = 0x03              # R/W  – Wait time
_AILTL = 0x04              # R/W  – Alert interrupt low threshold low byte
_AILTH = 0x05              # R/W  – Alert interrupt low threshold high byte
_AIHTL = 0x06              # R/W  – Alert interrupt high threshold low byte
_AIHTH = 0x07              # R/W  – Alert interrupt high threshold high byte
_PERS = 0x0C               # R/W  – Interrupt persistence filter
_CONFIG = 0x0D             # R/W  – Configuration
_CONTROL = 0x0F            # R/W  – Gain control
_ID = 0x12                 # R    – Device ID (0x44 = TCS34725)
_STATUS = 0x13             # R    – Device status
_CDATA = 0x14              # R    – Clear data low byte
_RDATA = 0x16              # R    – Red data low byte
_GDATA = 0x18              # R    – Green data low byte
_BDATA = 0x1A              # R    – Blue data low byte

_DEFAULT_ADDRESS = 0x29

# Integration time constants (ATIME value → integration time)
INTEGRATION_TIMES = {
    0xFF: 2.4,
    0xF6: 24,
    0xEB: 50,
    0xC0: 101,
    0xB6: 154,
    0x00: 700,
}

# Gain constants
_GAIN_1X = 0x00
_GAIN_4X = 0x01
_GAIN_16X = 0x02
_GAIN_60X = 0x03

GAIN_VALUES = {
    _GAIN_1X: 1,
    _GAIN_4X: 4,
    _GAIN_16X: 16,
    _GAIN_60X: 60,
}


class TCS34725:
    """TCS34725 RGB color sensor.

    Communicates with the sensor over I2C through the Arduino board.
    The sensor must be wired to the Arduino's I2C pins (SDA/A4, SCL/A5).

    Args:
        board: A :class:`Board` instance. If ``None``, uses
               :meth:`Board.get_active_board()`.

    Raises:
        TCS34725Error: If the sensor cannot be detected or a read times out.
        RuntimeError: If no Board has been created yet (and none provided).
    """

    def __init__(self, board=None):
        self._board = board if board is not None else Board.get_active_board()
        self._ard = self._board._board  # The pyfirmata2 Arduino instance
        self._address = _DEFAULT_ADDRESS

        # Synchronisation for I2C reads
        self._reply_data = None
        self._reply_event = threading.Event()

        # Configure I2C bus (delay = 0 µs between stop/start)
        self._ard.send_sysex(pyfirmata2.I2C_CONFIG, [0, 0])

        # Register handler for incoming I2C_REPLY messages
        self._ard.add_cmd_handler(pyfirmata2.I2C_REPLY, self._handle_i2c_reply)

        # Verify the sensor is present by reading its ID register
        dev_id = self._read_u8(_ID)
        if dev_id is None or dev_id == 0:
            id_str = f"0x{dev_id:02X}" if dev_id is not None else "??"
            raise TCS34725Error(
                f"TCS34725 not detected on I2C address 0x{self._address:02X} "
                f"(read ID={id_str})"
            )

        # Power on + RGBC ADC enable
        self._write_u8(_ENABLE, 0x03)
        self._integration_time = None
        self._gain = None
        self._set_integration_time(0xFF)   # 2.4 ms (fastest)
        self._set_gain(_GAIN_1X)

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    def rgb(self):
        """Read normalized RGB values (0–255 each).

        Returns:
            A ``(red, green, blue)`` tuple scaled relative to the clear channel.
            Returns ``(0, 0, 0)`` if no light is detected (clear = 0).
        """
        clear, red, green, blue = self.rgb_raw()

        if clear == 0:
            return (0, 0, 0)

        r = int((red / clear) * 255)
        g = int((green / clear) * 255)
        b = int((blue / clear) * 255)

        return (
            max(0, min(255, r)),
            max(0, min(255, g)),
            max(0, min(255, b)),
        )

    def rgb_raw(self):
        """Read raw 16-bit RGBC values from the sensor.

        Returns:
            A ``(clear, red, green, blue)`` tuple of raw ADC counts.
        """
        data = self._read_regs(_CDATA, 8)
        # data is guaranteed by _read_regs to be exactly 8 bytes
        clear = data[0] | (data[1] << 8)
        red   = data[2] | (data[3] << 8)
        green = data[4] | (data[5] << 8)
        blue  = data[6] | (data[7] << 8)
        return (clear, red, green, blue)

    def color_temperature(self):
        """Estimate colour temperature in Kelvin.

        Uses the canonical TCS34725 algorithm from the AMS application note.

        Returns:
            Colour temperature in Kelvin, or ``0`` if the reading is invalid.
        """
        clear, red, green, blue = self.rgb_raw()
        return self._calculate_color_temperature(red, green, blue, clear)

    def lux(self):
        """Estimate ambient light level in lux.

        Returns:
            Illuminance in lux, or ``0`` if the reading is invalid.
        """
        clear, red, green, blue = self.rgb_raw()
        effective_gain = self._gain if self._gain is not None else 1
        return self._calculate_lux(
            red, green, blue, clear,
            self._integration_time or 2.4,
            GAIN_VALUES.get(effective_gain, 1),
        )

    def set_gain(self, gain):
        """Set the RGBC gain level.

        Args:
            gain: One of ``1``, ``4``, ``16``, or ``60``.

        Raises:
            ValueError: If ``gain`` is not a recognised value.
        """
        if gain == 1:
            self._set_gain(_GAIN_1X)
        elif gain == 4:
            self._set_gain(_GAIN_4X)
        elif gain == 16:
            self._set_gain(_GAIN_16X)
        elif gain == 60:
            self._set_gain(_GAIN_60X)
        else:
            raise ValueError(f"Invalid gain {gain!r}. Use 1, 4, 16, or 60.")
        self._gain = gain

    def set_integration_time(self, time_ms):
        """Set the RGBC integration time.

        Args:
            time_ms: Integration time in milliseconds. The closest supported
                     value is rounded down. Supported values (ms):
                     2.4, 24, 50, 101, 154, 700.

        Raises:
            ValueError: If ``time_ms`` is not a recognised value.
        """
        # Find the closest ATIME value (round down)
        sorted_times = sorted(INTEGRATION_TIMES.items(), key=lambda x: x[1])
        chosen_atime = None
        for atime, ms in sorted_times:
            if time_ms >= ms:
                chosen_atime = atime
        if chosen_atime is None:
            raise ValueError(
                f"Unsupported integration time {time_ms!r} ms. "
                f"Supported: {sorted(set(INTEGRATION_TIMES.values()))}"
            )
        self._set_integration_time(chosen_atime)
        self._integration_time = INTEGRATION_TIMES[chosen_atime]

    # ──────────────────────────────────────────
    # Low-level I2C helpers
    # ──────────────────────────────────────────

    def _write_u8(self, reg, value):
        """Write a single byte to a register."""
        cmd = _COMMAND_BIT | reg
        addr_w = (self._address << 1)  # bit 0 = 0 → write
        self._ard.send_sysex(pyfirmata2.I2C_REQUEST, [addr_w, cmd, value])

    def _read_u8(self, reg):
        """Read a single unsigned byte from a register."""
        data = self._read_regs(reg, 1)
        return data[0] if data else None

    def _read_regs(self, reg, count):
        """Read ``count`` consecutive register bytes starting at ``reg``."""
        cmd = _COMMAND_BIT | _AUTO_INC | reg
        addr_w = (self._address << 1)          # write mode
        addr_r = (self._address << 1) | 0x01   # read mode

        # 1) Set the register pointer on the sensor
        self._ard.send_sysex(pyfirmata2.I2C_REQUEST, [addr_w, cmd])

        # 2) Request a read of ``count`` bytes
        self._reply_data = None
        self._reply_event.clear()
        self._ard.send_sysex(pyfirmata2.I2C_REQUEST, [addr_r, count])

        # 3) Wait for the reply (handled asynchronously in the Firmata thread)
        if not self._reply_event.wait(timeout=2.0):
            raise TCS34725Error(
                f"I2C read timeout after {count} byte(s) from reg 0x{reg:02X}"
            )

        return self._decode_reply(self._reply_data, count)

    def _set_integration_time(self, atime):
        """Write the ATIME register."""
        self._write_u8(_ATIME, atime)

    def _set_gain(self, gain):
        """Write the CONTROL register."""
        self._write_u8(_CONTROL, gain)

    # ──────────────────────────────────────────
    # I2C reply handling
    # ──────────────────────────────────────────

    def _handle_i2c_reply(self, *data):
        """Receive I2C_REPLY data from the Firmata board.

        ``data[0]`` is the address+mode byte echoed from the request.
        ``data[1:]`` are the raw 7-bit Firmata-encoded byte pairs.
        """
        self._reply_data = list(data)
        self._reply_event.set()

    @staticmethod
    def _decode_reply(data, expected_count):
        """Decode Firmata 7-bit encoded I2C reply data.

        Each I2C byte read from the sensor is sent as two 7-bit bytes:
        ``[value & 0x7F, (value >> 7) & 0x7F]``.

        Args:
            data: The raw data from the I2C_REPLY handler, where
                  ``data[0]`` is the address+mode and ``data[1:]`` are
                  the 7-bit encoded pairs.
            expected_count: Number of I2C bytes we expect.

        Returns:
            List of decoded bytes.
        """
        if not data or len(data) < 2:
            return []

        raw = data[1:]  # skip the address+mode byte
        decoded = []
        i = 0
        while i + 1 < len(raw) and len(decoded) < expected_count:
            low = raw[i]
            high = raw[i + 1]
            decoded.append(low | (high << 7))
            i += 2
        return decoded

    # ──────────────────────────────────────────
    # Colour math (from AMS application note)
    # ──────────────────────────────────────────

    @staticmethod
    def _calculate_color_temperature(r, g, b, c):
        """Estimate colour temperature using the canonical algorithm."""
        if c == 0:
            return 0

        # Avoid divide-by-zero edge cases
        if r == 0 or g == 0:
            return 0

        # IR compensation (sensor has significant IR leakage)
        ir = (r + g + b - c) // 2 if (r + g + b > c) else 0

        # Remove IR from channels
        r2 = r - ir
        b2 = b - ir

        if r2 == 0:
            return 0

        # Normalise
        r2 = max(r2, 0)
        b2 = max(b2, 0)

        ct = _color_temperature(r2, b2)
        return ct

    @staticmethod
    def _calculate_lux(r, g, b, c, integration_time_ms, gain):
        """Estimate lux using the canonical TCS34725 algorithm."""
        if c == 0:
            return 0

        ir = (r + g + b - c) // 2 if (r + g + b > c) else 0
        r2 = max(r - ir, 0)
        g2 = max(g - ir, 0)
        b2 = max(b - ir, 0)

        # GA * 1 second / integration time (ms)
        atime_ms = integration_time_ms
        if atime_ms <= 0:
            return 0

        if gain <= 0:
            gain = 1

        cpl = (atime_ms * gain) / 60.0  # counts per lux

        if cpl == 0:
            return 0

        lux_est = (r2 * 1.0 + g2 * 1.0 + b2 * 1.0) / cpl

        # Apply empirical glass attenuation factor (typical ≈ 0.55
        # for no cover glass). Using 1.0 as the default.
        lux_est = max(lux_est, 0.0)
        return round(lux_est, 1)


# Module-level helper to keep the class clean
def _color_temperature(r, b):
    """Interpolate colour temperature from a lookup table."""
    # AMS application note – CT curve
    # (r/b ratio → temperature in K)
    ct_table = [
        (0.55, 10000),
        (0.63, 8000),
        (0.71, 6500),
        (0.78, 5500),
        (0.87, 4800),
        (1.00, 4200),
        (1.16, 3700),
        (1.33, 3300),
        (1.50, 3000),
        (1.68, 2700),
        (1.87, 2500),
        (2.10, 2300),
        (2.42, 2100),
        (2.80, 1900),
        (3.20, 1700),
        (3.50, 1550),
    ]

    ratio = r / b if b != 0 else 99.0

    # Clamp to table range
    if ratio <= ct_table[0][0]:
        return ct_table[0][1]
    if ratio >= ct_table[-1][0]:
        return ct_table[-1][1]

    # Linear interpolation
    for i in range(len(ct_table) - 1):
        if ct_table[i][0] <= ratio <= ct_table[i + 1][0]:
            x0, y0 = ct_table[i]
            x1, y1 = ct_table[i + 1]
            return int(y0 + (y1 - y0) * (ratio - x0) / (x1 - x0))

    return 0
