import time


def delay(ms):
    """Pause execution for *ms* milliseconds.

    Analogous to Arduino's ``delay()``.
    """
    time.sleep(ms / 1000)


def millis():
    """Return the number of milliseconds since the epoch.

    Analogous to Arduino's ``millis()``.
    """
    return int(time.time() * 1000)
