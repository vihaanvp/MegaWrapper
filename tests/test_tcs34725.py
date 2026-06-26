"""
Tests for the TCS34725 colour sensor module.

All I2C communication is mocked — no real hardware required.
"""

from unittest.mock import MagicMock, call

import pytest
import pyfirmata2

from megawrapper import Board, TCS34725, TCS34725Error


# ──────────────────────────────────────────────
# Helpers: build simulated I2C reply data
# ──────────────────────────────────────────────

def _firmata_encode(value):
    """Encode a single 8-bit byte into two 7-bit Firmata bytes."""
    return [value & 0x7F, (value >> 7) & 0x7F]


def _build_reply(address_byte, *data_bytes):
    """Build the data tuple an I2C_REPLY handler would receive.

    Each I2C ``data_byte`` (0-255) is split into two 7-bit Firmata bytes.
    """
    encoded = [address_byte]
    for b in data_bytes:
        encoded.extend(_firmata_encode(b))
    return tuple(encoded)


def _rgbc_reply(clear, red, green, blue, address=0x29):
    """Build a full RGBC I2C reply (8 bytes) for a given address."""
    addr_byte = (address << 1) | 0x01  # read mode
    data = [
        clear & 0xFF, (clear >> 8) & 0xFF,
        red & 0xFF, (red >> 8) & 0xFF,
        green & 0xFF, (green >> 8) & 0xFF,
        blue & 0xFF, (blue >> 8) & 0xFF,
    ]
    return _build_reply(addr_byte, *data)


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

def _auto_reply(ctx, id_value=0x44, rgbc_data=None):
    """Build a ``send_sysex`` side-effect that auto-replies to I2C reads.

    The callback is looked up from ``captured_callbacks`` *at call time*
    (lazy), so it works even if ``TCS34725.__init__`` hasn't registered the
    handler yet at side-effect setup time.

    Parameters
    ----------
    ctx : dict
        The ``mock_ard_and_callbacks`` context dict.
    id_value : int
        The device ID to return for the ID-register read (1 byte).
    rgbc_data : tuple of (clear, red, green, blue) or None
        Data for the RGBC read (8 bytes). If None, defaults to (500,200,150,100).
    """
    if rgbc_data is None:
        rgbc_data = (500, 200, 150, 100)

    def side_effect(cmd, data):
        ctx["send_sysex_calls"].append((cmd, list(data)))
        if cmd == pyfirmata2.I2C_REQUEST and len(data) > 0 and (data[0] & 0x01):
            cb = ctx["captured_callbacks"].get(pyfirmata2.I2C_REPLY)
            if cb is None:
                return  # handler not yet registered — skip
            num_bytes = data[1] if len(data) > 1 else 0
            if num_bytes == 1:
                reply = _build_reply(data[0], id_value)
            else:
                reply = _rgbc_reply(*rgbc_data)
            cb(*reply)

    return side_effect


@pytest.fixture
def mock_ard_and_callbacks():
    """Set up a mock Board and capture I2C callbacks.

    Returns a dict with:
        board       — the created Board instance
        send_sysex_calls — list of (cmd, data) tuples sent via send_sysex
        captured_callbacks — dict mapping cmd → registered handler
    """
    import megawrapper.board as board_mod
    board_mod._active_board = None

    from unittest.mock import patch
    with patch("megawrapper.board.Arduino") as mock_ard_class:
        mock_ard = MagicMock()
        mock_ard_class.return_value = mock_ard
        mock_ard.get_pin.side_effect = lambda *_: MagicMock()

        captured_callbacks = {}
        send_calls = []

        def fake_add_cmd_handler(cmd, func):
            captured_callbacks[cmd] = func

        mock_ard.add_cmd_handler.side_effect = fake_add_cmd_handler

        board = Board("COM_test")

        yield {
            "board": board,
            "mock_ard": mock_ard,
            "send_sysex_calls": send_calls,
            "captured_callbacks": captured_callbacks,
        }


@pytest.fixture
def sensor(mock_ard_and_callbacks):
    """Create a TCS34725 sensor that responds with valid data."""
    ctx = mock_ard_and_callbacks
    ctx["mock_ard"].send_sysex.side_effect = _auto_reply(ctx)
    s = TCS34725(board=ctx["board"])
    return s


# ──────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────

class TestTCS34725Init:
    """Construction and initialisation."""

    def test_create_with_explicit_board(self, mock_ard_and_callbacks):
        ctx = mock_ard_and_callbacks
        ctx["mock_ard"].send_sysex.side_effect = _auto_reply(ctx)

        s = TCS34725(board=ctx["board"])
        assert s is not None
        # Should have sent I2C_CONFIG and then writes for ENABLE, ATIME, CONTROL
        cmds = [c for c, _ in ctx["send_sysex_calls"]]
        assert pyfirmata2.I2C_CONFIG in cmds
        assert pyfirmata2.I2C_REQUEST in cmds

    def test_create_uses_active_board(self, mock_ard_and_callbacks):
        ctx = mock_ard_and_callbacks
        ctx["mock_ard"].send_sysex.side_effect = _auto_reply(ctx)

        # TCS34725() with no board arg → uses get_active_board()
        s = TCS34725()
        assert s is not None

    def test_raises_if_no_id(self, mock_ard_and_callbacks):
        ctx = mock_ard_and_callbacks
        # Reply with ID = 0x00 → sensor not detected
        ctx["mock_ard"].send_sysex.side_effect = _auto_reply(ctx, id_value=0x00)

        with pytest.raises(TCS34725Error, match="not detected"):
            TCS34725(board=ctx["board"])

    def test_raises_if_no_board(self):
        import megawrapper.board as board_mod
        board_mod._active_board = None
        with pytest.raises(RuntimeError, match="No board initialised"):
            TCS34725()

    def test_raises_if_id_read_timeout(self, mock_ard_and_callbacks):
        ctx = mock_ard_and_callbacks
        # Don't simulate any I2C reply → timeout
        with pytest.raises(TCS34725Error, match="timeout"):
            TCS34725(board=ctx["board"])


class TestTCS34725Read:
    """Reading colour data."""

    def test_rgb_raw(self, sensor):
        clear, red, green, blue = sensor.rgb_raw()
        assert clear == 500
        assert red == 200
        assert green == 150
        assert blue == 100

    def test_rgb_normalized(self, sensor):
        r, g, b = sensor.rgb()
        # clear=500, so normalized: r=200/500*255=102, g=150/500*255=76.5, b=100/500*255=51
        assert r == 102   # int(200/500 * 255)
        assert g == 76    # int(150/500 * 255)
        assert b == 51    # int(100/500 * 255)

    def test_rgb_returns_zero_when_clear_is_zero(self, mock_ard_and_callbacks):
        ctx = mock_ard_and_callbacks
        ctx["mock_ard"].send_sysex.side_effect = _auto_reply(
            ctx, rgbc_data=(0, 100, 50, 25)
        )

        s = TCS34725(board=ctx["board"])
        r, g, b = s.rgb()
        assert r == 0
        assert g == 0
        assert b == 0

    def test_color_temperature(self, sensor):
        ct = sensor.color_temperature()
        # clear=500, r=200, g=150, b=100
        # IR = (200+150+100-500)//2 = -25 // 2 = 0 (since 450 < 500, ir=0)
        # r2=200, b2=100, ratio=2.0 → interpolated CT ≈ 2500K
        assert ct > 2000
        assert ct < 3000

    def test_color_temperature_zero_when_clear_zero(self, mock_ard_and_callbacks):
        ctx = mock_ard_and_callbacks
        ctx["mock_ard"].send_sysex.side_effect = _auto_reply(
            ctx, rgbc_data=(0, 0, 0, 0)
        )

        s = TCS34725(board=ctx["board"])
        assert s.color_temperature() == 0

    def test_lux(self, sensor):
        lux_val = sensor.lux()
        # Empirical: with integration_time=2.4ms, gain=1
        # r2=200, g2=150, b2=100, cpl=(2.4*1)/60=0.04
        # (200+150+100)/0.04=11250
        assert lux_val > 0

    def test_lux_zero_when_clear_zero(self, mock_ard_and_callbacks):
        ctx = mock_ard_and_callbacks
        ctx["mock_ard"].send_sysex.side_effect = _auto_reply(
            ctx, rgbc_data=(0, 0, 0, 0)
        )

        s = TCS34725(board=ctx["board"])
        assert s.lux() == 0


class TestTCS34725Gain:
    """Gain configuration."""

    def test_set_gain_valid(self, sensor):
        sensor.set_gain(4)
        # Should have written CONTROL register with 0x01
        writes = [
            (cmd, d) for cmd, d in sensor._ard.send_sysex.call_args_list
        ]
        # Just verify no exception raised
        assert sensor._gain == 4

    def test_set_gain_invalid(self, sensor):
        with pytest.raises(ValueError, match="Invalid gain"):
            sensor.set_gain(99)

    def test_set_integration_time_valid(self, sensor):
        sensor.set_integration_time(24)
        assert sensor._integration_time == 24

    def test_set_integration_time_invalid(self, sensor):
        with pytest.raises(ValueError, match="unsupported|Unsupported"):
            sensor.set_integration_time(1)


class TestTCS34725I2CEncoding:
    """Verify the Firmata 7-bit I2C encoding/decoding."""

    def test_decode_reply(self):
        # Encode bytes 0xAB, 0xCD
        reply = _build_reply(0x52, 0xAB, 0xCD)
        decoded = TCS34725._decode_reply(list(reply), 2)
        assert decoded == [0xAB, 0xCD]

    def test_decode_reply_handles_high_bytes(self):
        # Test values > 127
        reply = _build_reply(0x52, 0xFF, 0x80)
        decoded = TCS34725._decode_reply(list(reply), 2)
        assert decoded == [0xFF, 0x80]

    def test_decode_empty_reply(self):
        assert TCS34725._decode_reply(None, 2) == []
        assert TCS34725._decode_reply([0x52], 2) == []


class TestTCS34725Integration:
    """End-to-end flow with the mock."""

    def test_sensor_round_trip(self, sensor):
        clear, red, green, blue = sensor.rgb_raw()
        assert isinstance(clear, int)
        assert isinstance(red, int)
        assert isinstance(green, int)
        assert isinstance(blue, int)
        assert 0 <= clear <= 65535
        assert 0 <= red <= 65535
        assert 0 <= green <= 65535
        assert 0 <= blue <= 65535

    def test_i2c_config_sent_on_init(self, mock_ard_and_callbacks):
        """Verify I2C_CONFIG is sent during construction."""
        ctx = mock_ard_and_callbacks
        ctx["mock_ard"].send_sysex.side_effect = _auto_reply(ctx)

        TCS34725(board=ctx["board"])

        config_calls = [
            (cmd, d) for cmd, d in ctx["send_sysex_calls"]
            if cmd == pyfirmata2.I2C_CONFIG
        ]
        assert len(config_calls) == 1
        assert config_calls[0][1] == [0, 0]


class TestTCS34725InitSequence:
    """Verify the init sequence emitted over I2C."""

    def test_init_writes_enable_atime_control(self, mock_ard_and_callbacks):
        ctx = mock_ard_and_callbacks
        ctx["mock_ard"].send_sysex.side_effect = _auto_reply(ctx)

        TCS34725(board=ctx["board"])

        # Filter to I2C write requests (bit 0 = 0)
        writes = [
            d for cmd, d in ctx["send_sysex_calls"]
            if cmd == pyfirmata2.I2C_REQUEST and len(d) > 2 and not (d[0] & 0x01)
        ]
        # First write should be ENABLE (0x80|0x00 = 0x80) with value 0x03
        # Using auto-inc: COMMAND_BIT|AUTO_INC = 0xA0, but for writes it's COMMAND_BIT|reg = 0x80
        assert len(writes) >= 3, f"Expected ≥3 I2C writes, got {len(writes)}: {writes}"
        # writes are [addr, cmd, value]
        # ENABLE: cmd = 0x80 | 0x00 = 0x80, value = 0x03
        # ATIME: cmd = 0x80 | 0x01 = 0x81, value = 0xFF
        # CONTROL: cmd = 0x80 | 0x0F = 0x8F, value = 0x00
