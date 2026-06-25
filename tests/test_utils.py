"""Tests for utility functions (delay, millis)."""

import time

from megawrapper.utils import delay, millis


class TestDelay:
    def test_delay_positive(self):
        start = time.time()
        delay(100)  # 100 ms
        elapsed = time.time() - start
        assert 0.08 <= elapsed <= 0.2  # allow some tolerance

    def test_delay_zero(self):
        start = time.time()
        delay(0)
        elapsed = time.time() - start
        assert elapsed < 0.1


class TestMillis:
    def test_millis_returns_int(self):
        assert isinstance(millis(), int)

    def test_millis_increases(self):
        t1 = millis()
        time.sleep(0.01)
        t2 = millis()
        assert t2 >= t1
