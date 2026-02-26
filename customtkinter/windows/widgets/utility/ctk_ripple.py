"""
CTkRipple — Material-style ripple press effect for CustomTkinter widgets.

Draws an expanding semi-transparent circle from the click point, then fades
out. Works on any widget that has a canvas (CTkButton, CTkFrame, etc.).

Usage:
    from customtkinter import CTkRipple
    CTkRipple.attach(my_button)
    CTkRipple.attach(my_button, color="#ffffff", duration=400)
"""

import math
import time
from tkinter import TclError
from typing import Optional, Union, Tuple


_DEFAULT_DURATION = 350  # ms
_DEFAULT_COLOR_LIGHT = "#000000"
_DEFAULT_COLOR_DARK = "#ffffff"
_DEFAULT_OPACITY = 0.12
_FRAME_INTERVAL = 16  # ~60 fps


class _RippleAnimation:
    """Manages a single ripple expanding circle on a canvas."""

    __slots__ = (
        "_canvas", "_cx", "_cy", "_max_radius",
        "_duration", "_color", "_opacity", "_bg_color",
        "_start_time", "_after_id", "_oval_id", "_running",
    )

    def __init__(self, canvas, cx: int, cy: int, max_radius: float,
                 duration: int, color: str, opacity: float, bg_color: str):
        self._canvas = canvas
        self._cx = cx
        self._cy = cy
        self._max_radius = max_radius
        self._duration = max(1, duration)
        self._color = color
        self._opacity = opacity
        self._bg_color = bg_color
        self._start_time = 0.0
        self._after_id = None
        self._oval_id = None
        self._running = False

    def start(self) -> None:
        self._start_time = time.perf_counter()
        self._running = True
        # Create initial oval at click point (radius 0)
        self._oval_id = self._canvas.create_oval(
            self._cx, self._cy, self._cx, self._cy,
            outline="", fill=self._blend(self._opacity),
            tags="ctk_ripple",
        )
        self._canvas.tag_raise("ctk_ripple")
        self._tick()

    def cancel(self) -> None:
        if self._after_id is not None:
            try:
                self._canvas.after_cancel(self._after_id)
            except (TclError, ValueError):
                pass
            self._after_id = None
        self._cleanup()

    def _tick(self) -> None:
        if not self._running:
            return

        elapsed = (time.perf_counter() - self._start_time) * 1000
        t = min(elapsed / self._duration, 1.0)

        # Ease-out for expansion, ease-in for fade
        expand_t = 1.0 - (1.0 - t) ** 2  # ease-out-quad
        fade_t = t * t  # ease-in-quad (opacity decreases)

        radius = self._max_radius * expand_t
        current_opacity = self._opacity * (1.0 - fade_t)

        if self._oval_id is not None:
            try:
                self._canvas.coords(
                    self._oval_id,
                    self._cx - radius, self._cy - radius,
                    self._cx + radius, self._cy + radius,
                )
                fill = self._blend(current_opacity)
                self._canvas.itemconfigure(self._oval_id, fill=fill)
            except TclError:
                self._cleanup()
                return

        if t >= 1.0:
            self._cleanup()
        else:
            self._after_id = self._canvas.after(_FRAME_INTERVAL, self._tick)

    def _cleanup(self) -> None:
        self._running = False
        if self._oval_id is not None:
            try:
                self._canvas.delete(self._oval_id)
            except TclError:
                pass
            self._oval_id = None

    def _blend(self, alpha: float) -> str:
        """Blend ripple color onto background at given alpha."""
        try:
            bg = self._bg_color.lstrip("#")
            fg = self._color.lstrip("#")
            if len(bg) < 6 or len(fg) < 6:
                return self._color
            rb, gb, bb = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
            rf, gf, bf = int(fg[0:2], 16), int(fg[2:4], 16), int(fg[4:6], 16)
            r = int(rb + (rf - rb) * alpha)
            g = int(gb + (gf - gb) * alpha)
            b = int(bb + (bf - bb) * alpha)
            return f"#{max(0,min(255,r)):02x}{max(0,min(255,g)):02x}{max(0,min(255,b)):02x}"
        except Exception:
            return self._color


class CTkRipple:
    """
    Static utility class to attach ripple effect to any CTkBaseClass widget.

    The ripple is rendered on the widget's internal canvas and clipped
    within the widget bounds.

    Usage:
        CTkRipple.attach(button)
        CTkRipple.attach(button, color="#ffffff", opacity=0.15, duration=400)
    """

    @staticmethod
    def attach(
        widget,
        color: Union[str, Tuple[str, str]] = None,
        opacity: float = _DEFAULT_OPACITY,
        duration: int = _DEFAULT_DURATION,
    ) -> None:
        """
        Attach a ripple effect to the widget. Triggers on <Button-1>.

        Args:
            widget: A CustomTkinter widget (must have a _canvas attribute)
            color: Ripple color (single or (light, dark) tuple).
                   Defaults to black in light mode, white in dark mode.
            opacity: Ripple opacity at its peak (0.0 to 1.0, default 0.12)
            duration: Animation duration in ms (default 350)
        """
        if color is None:
            color = (_DEFAULT_COLOR_LIGHT, _DEFAULT_COLOR_DARK)

        # Find the canvas to draw on
        canvas = None
        if hasattr(widget, "_canvas"):
            canvas = widget._canvas
        elif hasattr(widget, "canvas"):
            canvas = widget.canvas

        if canvas is None:
            return  # Can't attach to widget without a canvas

        # Track active ripples for cleanup
        active_ripples = []

        def _resolve_color() -> str:
            if isinstance(color, (list, tuple)) and len(color) == 2:
                if hasattr(widget, "_appearance_mode"):
                    return color[widget._appearance_mode]
                return color[0]
            return color

        def _get_canvas_bg() -> str:
            """Get the canvas's current fill color (fg_color of the widget)."""
            try:
                if hasattr(widget, "_fg_color"):
                    fg = widget._fg_color
                    if isinstance(fg, (list, tuple)) and len(fg) == 2:
                        mode = getattr(widget, "_appearance_mode", 0)
                        return fg[mode]
                    if fg and fg != "transparent":
                        return fg
                # Try reading canvas bg
                bg = canvas.cget("bg")
                if bg and not bg.startswith("."):
                    return bg
            except Exception:
                pass
            # Fallback
            if hasattr(widget, "_appearance_mode") and widget._appearance_mode == 1:
                return "#2b2b2b"
            return "#dbdbdb"

        def on_click(event):
            # Clean up finished ripples
            for r in active_ripples[:]:
                if not r._running:
                    active_ripples.remove(r)

            # Calculate click position on the canvas
            cx = event.x
            cy = event.y
            w = canvas.winfo_width()
            h = canvas.winfo_height()

            # Max radius: distance from click to farthest corner
            corners = [(0, 0), (w, 0), (0, h), (w, h)]
            max_radius = max(
                math.sqrt((cx - fx) ** 2 + (cy - fy) ** 2)
                for fx, fy in corners
            )

            ripple = _RippleAnimation(
                canvas=canvas,
                cx=cx, cy=cy,
                max_radius=max_radius,
                duration=duration,
                color=_resolve_color(),
                opacity=opacity,
                bg_color=_get_canvas_bg(),
            )
            active_ripples.append(ripple)
            ripple.start()

        canvas.bind("<Button-1>", on_click, add="+")

        # Store reference to prevent GC and allow cleanup
        if not hasattr(widget, "_ripple_effects"):
            widget._ripple_effects = []
        widget._ripple_effects.append(active_ripples)

        # Hook destroy for cleanup — only wrap once to prevent stacking
        if not hasattr(widget, "_original_destroy_ripple"):
            widget._original_destroy_ripple = widget.destroy

            def destroy_with_cleanup():
                for ripple_list in getattr(widget, "_ripple_effects", []):
                    for r in ripple_list:
                        r.cancel()
                    ripple_list.clear()
                widget._original_destroy_ripple()

            widget.destroy = destroy_with_cleanup
