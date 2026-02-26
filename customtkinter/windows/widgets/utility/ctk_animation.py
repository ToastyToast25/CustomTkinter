"""
CTkAnimation — Shared animation/easing framework for CustomTkinter.

Provides reusable easing functions and a lightweight property animator
that any widget can use via tkinter's `after()` scheduling.

Usage:
    from .utility.ctk_animation import CTkAnimation, Easing

    anim = CTkAnimation(
        widget=self,            # any tkinter widget (for .after())
        from_value=0.0,
        to_value=1.0,
        duration=300,           # ms
        easing=Easing.EASE_OUT_CUBIC,
        on_step=lambda v: self._draw_at(v),
        on_complete=lambda: print("done"),
    )
    anim.start()
    anim.cancel()               # safe to call even if not running
"""

import math
import time
from tkinter import TclError
from typing import Callable, Optional


# ---------------------------------------------------------------------------
# Easing functions:  f(t) -> t   where t in [0, 1]
# ---------------------------------------------------------------------------

def _linear(t: float) -> float:
    return t


def _ease_in_quad(t: float) -> float:
    return t * t


def _ease_out_quad(t: float) -> float:
    return 1.0 - (1.0 - t) * (1.0 - t)


def _ease_in_out_quad(t: float) -> float:
    if t < 0.5:
        return 2.0 * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 2 / 2.0


def _ease_in_cubic(t: float) -> float:
    return t * t * t


def _ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


def _ease_in_out_cubic(t: float) -> float:
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


def _ease_out_back(t: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2


def _ease_out_elastic(t: float) -> float:
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    c4 = (2.0 * math.pi) / 3.0
    return 2.0 ** (-10.0 * t) * math.sin((t * 10.0 - 0.75) * c4) + 1.0


def _ease_out_bounce(t: float) -> float:
    n1 = 7.5625
    d1 = 2.75
    if t < 1.0 / d1:
        return n1 * t * t
    elif t < 2.0 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


def _spring(t: float) -> float:
    """Slight overshoot then settle — good for UI elements snapping into place."""
    return 1.0 - math.cos(t * math.pi * 0.5) * math.exp(-6.0 * t) if t < 1.0 else 1.0


class Easing:
    """Named constants for easing functions."""
    LINEAR = _linear
    EASE_IN_QUAD = _ease_in_quad
    EASE_OUT_QUAD = _ease_out_quad
    EASE_IN_OUT_QUAD = _ease_in_out_quad
    EASE_IN_CUBIC = _ease_in_cubic
    EASE_OUT_CUBIC = _ease_out_cubic
    EASE_IN_OUT_CUBIC = _ease_in_out_cubic
    EASE_OUT_BACK = _ease_out_back
    EASE_OUT_ELASTIC = _ease_out_elastic
    EASE_OUT_BOUNCE = _ease_out_bounce
    SPRING = _spring


# ---------------------------------------------------------------------------
# Color interpolation helpers
# ---------------------------------------------------------------------------

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between two floats."""
    return a + (b - a) * t


def lerp_color(hex1: str, hex2: str, t: float) -> str:
    """Interpolate between two hex colors (#RRGGBB). Returns #RRGGBB string."""
    hex1 = hex1.lstrip("#")
    hex2 = hex2.lstrip("#")
    r1, g1, b1 = int(hex1[0:2], 16), int(hex1[2:4], 16), int(hex1[4:6], 16)
    r2, g2, b2 = int(hex2[0:2], 16), int(hex2[2:4], 16), int(hex2[4:6], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------------------------------------------------------------------------
# CTkAnimation — the main animator class
# ---------------------------------------------------------------------------

_FRAME_INTERVAL = 16  # ~60 fps


class CTkAnimation:
    """
    Animate a float value from `from_value` to `to_value` over `duration` ms
    using the given `easing` function.  Calls `on_step(current_value)` each
    frame and `on_complete()` when finished.

    Requires a tkinter widget to schedule `after()` calls on.
    """

    __slots__ = (
        "_widget", "_from", "_to", "_duration", "_easing",
        "_on_step", "_on_complete", "_after_id", "_start_time", "_running",
    )

    def __init__(
        self,
        widget,
        from_value: float = 0.0,
        to_value: float = 1.0,
        duration: int = 300,
        easing: Callable[[float], float] = _ease_out_cubic,
        on_step: Optional[Callable[[float], None]] = None,
        on_complete: Optional[Callable[[], None]] = None,
    ):
        self._widget = widget
        self._from = from_value
        self._to = to_value
        self._duration = max(1, duration)
        self._easing = easing
        self._on_step = on_step
        self._on_complete = on_complete
        self._after_id: Optional[str] = None
        self._start_time: float = 0.0
        self._running: bool = False

    # -- public API ---------------------------------------------------------

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> "CTkAnimation":
        """Start (or restart) the animation. Returns self for chaining."""
        self.cancel()
        self._start_time = time.perf_counter()
        self._running = True
        self._tick()
        return self

    def cancel(self) -> None:
        """Cancel the animation if running. Safe to call when not running."""
        if self._after_id is not None:
            try:
                self._widget.after_cancel(self._after_id)
            except (TclError, ValueError):
                pass
            self._after_id = None
        self._running = False

    def update_target(self, to_value: float) -> None:
        """Change the target mid-animation, keeping current progress."""
        if self._running:
            # compute current value so we can restart from there
            elapsed = (time.perf_counter() - self._start_time) * 1000
            t = min(elapsed / self._duration, 1.0)
            eased = self._easing(t)
            current = self._from + (self._to - self._from) * eased
            self._from = current
            self._to = to_value
            self._start_time = time.perf_counter()
        else:
            self._to = to_value
            self.start()

    # -- internal -----------------------------------------------------------

    def _tick(self) -> None:
        elapsed = (time.perf_counter() - self._start_time) * 1000
        t = min(elapsed / self._duration, 1.0)
        eased = self._easing(t)
        value = self._from + (self._to - self._from) * eased

        if self._on_step is not None:
            self._on_step(value)

        if t >= 1.0:
            self._running = False
            self._after_id = None
            if self._on_complete is not None:
                self._on_complete()
        else:
            self._after_id = self._widget.after(_FRAME_INTERVAL, self._tick)
