"""
CTkFocusRing — Keyboard focus indicator mixin for CustomTkinter widgets.

Adds a subtle animated glow ring around any widget when it receives keyboard
focus (Tab navigation). The ring fades in on focus and fades out on blur.

Usage (inside any CTkBaseClass widget's __init__):

    from .utility.ctk_focus_ring import FocusRingMixin
    FocusRingMixin.attach(self)

Or as a standalone wrapper:

    from customtkinter import CTkFocusRing
    CTkFocusRing.attach(my_button)
"""

import tkinter
from tkinter import TclError
from typing import Optional, Union, Tuple


# Default ring appearance
_DEFAULT_RING_WIDTH = 2
_DEFAULT_RING_PAD = 2
_DEFAULT_RING_COLOR_LIGHT = "#3B8ED0"
_DEFAULT_RING_COLOR_DARK = "#1F6AA5"
_FADE_STEPS = 6
_FADE_INTERVAL = 25  # ms per step


class FocusRingOverlay:
    """
    Draws a rounded-rectangle focus ring around a target widget using a
    transparent-background Toplevel (on Windows) or a canvas overlay.

    Since tkinter can't draw outside a widget's bounds, we use a canvas
    placed in the widget's parent, positioned around the target.
    """

    __slots__ = (
        "_target", "_parent", "_canvas", "_ring_id",
        "_ring_width", "_ring_pad", "_ring_color", "_corner_radius",
        "_visible", "_fade_step", "_fade_after_id",
    )

    def __init__(
        self,
        target,
        ring_color: Union[str, Tuple[str, str]] = None,
        ring_width: int = _DEFAULT_RING_WIDTH,
        ring_pad: int = _DEFAULT_RING_PAD,
        corner_radius: Optional[int] = None,
    ):
        self._target = target
        self._parent = target.winfo_parent()
        # Resolve parent widget object
        if isinstance(self._parent, str):
            self._parent = target.nametowidget(self._parent)

        self._ring_width = ring_width
        self._ring_pad = ring_pad
        self._visible = False
        self._fade_step = 0
        self._fade_after_id = None
        self._canvas: Optional[tkinter.Canvas] = None
        self._ring_id = None

        # Determine corner radius from target if available
        if corner_radius is not None:
            self._corner_radius = corner_radius
        elif hasattr(target, "_corner_radius"):
            self._corner_radius = target._corner_radius + ring_pad
        else:
            self._corner_radius = 6 + ring_pad

        # Determine ring color
        if ring_color is not None:
            self._ring_color = ring_color
        else:
            self._ring_color = (_DEFAULT_RING_COLOR_LIGHT, _DEFAULT_RING_COLOR_DARK)

    def _resolve_color(self) -> str:
        """Pick light or dark ring color based on target's appearance mode."""
        color = self._ring_color
        if isinstance(color, (list, tuple)) and len(color) == 2:
            if hasattr(self._target, "_appearance_mode"):
                return color[self._target._appearance_mode]
            return color[0]
        return color

    def _ensure_canvas(self) -> None:
        """Create the overlay canvas on first use."""
        if self._canvas is not None:
            return

        self._canvas = tkinter.Canvas(
            self._parent,
            highlightthickness=0,
            bd=0,
        )
        # Don't let the canvas affect parent layout
        self._canvas.place(x=0, y=0, width=0, height=0)
        # Keep it below the target widget but visible
        self._canvas.lower(self._target)

    def show(self) -> None:
        """Show the focus ring with a fade-in animation."""
        if self._visible:
            return
        self._visible = True
        self._cancel_fade()
        self._fade_step = 0
        self._fade_in_tick()

    def hide(self) -> None:
        """Hide the focus ring with a fade-out animation."""
        if not self._visible:
            return
        self._visible = False
        self._cancel_fade()
        self._fade_step = _FADE_STEPS
        self._fade_out_tick()

    def _cancel_fade(self) -> None:
        if self._fade_after_id is not None:
            try:
                self._target.after_cancel(self._fade_after_id)
            except (TclError, ValueError):
                pass
            self._fade_after_id = None

    def _fade_in_tick(self) -> None:
        self._fade_step += 1
        alpha = min(self._fade_step / _FADE_STEPS, 1.0)
        self._draw_ring(alpha)
        if self._fade_step < _FADE_STEPS:
            self._fade_after_id = self._target.after(_FADE_INTERVAL, self._fade_in_tick)
        else:
            self._fade_after_id = None

    def _fade_out_tick(self) -> None:
        self._fade_step -= 1
        if self._fade_step <= 0:
            self._remove_ring()
            self._fade_after_id = None
            return
        alpha = self._fade_step / _FADE_STEPS
        self._draw_ring(alpha)
        self._fade_after_id = self._target.after(_FADE_INTERVAL, self._fade_out_tick)

    def _draw_ring(self, alpha: float) -> None:
        """Draw or update the focus ring at the given alpha (0-1)."""
        self._ensure_canvas()

        try:
            # Get target position relative to parent
            x = self._target.winfo_x()
            y = self._target.winfo_y()
            w = self._target.winfo_width()
            h = self._target.winfo_height()
        except TclError:
            return

        pad = self._ring_pad + self._ring_width
        cx = x - pad
        cy = y - pad
        cw = w + 2 * pad
        ch = h + 2 * pad

        # Position the canvas
        self._canvas.place(x=cx, y=cy, width=cw, height=ch)
        self._canvas.lift(self._target)
        # Actually we want it behind the target
        self._canvas.lower(self._target)

        # Compute ring color with simulated alpha (blend with parent bg)
        ring_color = self._resolve_color()
        parent_bg = self._get_parent_bg()
        blended = self._blend(parent_bg, ring_color, alpha)

        # Configure canvas background to match parent
        self._canvas.configure(bg=parent_bg)

        rw = self._ring_width
        r = self._corner_radius
        # Draw rounded rectangle outline
        if self._ring_id is None:
            self._ring_id = self._draw_rounded_rect(
                rw, rw, cw - rw, ch - rw, r, blended, rw
            )
        else:
            # Update existing
            self._canvas.delete("focus_ring")
            self._ring_id = self._draw_rounded_rect(
                rw, rw, cw - rw, ch - rw, r, blended, rw
            )

    def _draw_rounded_rect(self, x1, y1, x2, y2, r, color, width) -> int:
        """Draw a rounded rectangle outline on the canvas."""
        r = min(r, (x2 - x1) // 2, (y2 - y1) // 2)
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
            x1 + r, y1,
        ]
        return self._canvas.create_line(
            *points, fill=color, width=width,
            smooth=True, splinesteps=20,
            tags="focus_ring",
        )

    def _remove_ring(self) -> None:
        """Remove the ring canvas."""
        if self._canvas is not None:
            self._canvas.place_forget()
            self._canvas.delete("focus_ring")
            self._ring_id = None

    def _get_parent_bg(self) -> str:
        """Get the parent widget's background color."""
        try:
            if hasattr(self._parent, "cget"):
                bg = self._parent.cget("bg")
                if bg and not bg.startswith("."):
                    return bg
        except TclError:
            pass

        # Fallback
        if hasattr(self._target, "_appearance_mode") and self._target._appearance_mode == 1:
            return "#2b2b2b"
        return "#ebebeb"

    @staticmethod
    def _blend(bg_hex: str, fg_hex: str, alpha: float) -> str:
        """Blend fg onto bg at alpha."""
        try:
            bg = bg_hex.lstrip("#")
            fg = fg_hex.lstrip("#")
            if len(bg) < 6 or len(fg) < 6:
                return fg_hex
            rb, gb, bb = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
            rf, gf, bf = int(fg[0:2], 16), int(fg[2:4], 16), int(fg[4:6], 16)
            r = int(rb + (rf - rb) * alpha)
            g = int(gb + (gf - gb) * alpha)
            b = int(bb + (bf - bb) * alpha)
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return fg_hex

    def destroy(self) -> None:
        """Clean up the focus ring."""
        self._cancel_fade()
        if self._canvas is not None:
            try:
                self._canvas.delete("focus_ring")
                self._canvas.destroy()
            except TclError:
                pass
            self._canvas = None
            self._ring_id = None


class CTkFocusRing:
    """
    Static utility class to attach focus ring behavior to any widget.

    Usage:
        CTkFocusRing.attach(my_button)
        CTkFocusRing.attach(my_entry, ring_color="#ff0000")
    """

    @staticmethod
    def attach(
        widget,
        ring_color: Union[str, Tuple[str, str]] = None,
        ring_width: int = _DEFAULT_RING_WIDTH,
        ring_pad: int = _DEFAULT_RING_PAD,
        corner_radius: Optional[int] = None,
    ) -> FocusRingOverlay:
        """
        Attach a focus ring to the given widget. The ring appears on
        keyboard focus (<FocusIn>) and disappears on blur (<FocusOut>).

        Returns the FocusRingOverlay instance for manual control.
        """
        overlay = FocusRingOverlay(
            target=widget,
            ring_color=ring_color,
            ring_width=ring_width,
            ring_pad=ring_pad,
            corner_radius=corner_radius,
        )

        def on_focus_in(event):
            # Only show for keyboard focus, not mouse click
            overlay.show()

        def on_focus_out(event):
            overlay.hide()

        # Bind to the widget's underlying tkinter widget if it has one
        bind_target = widget
        if hasattr(widget, "_canvas"):
            bind_target = widget._canvas
        elif hasattr(widget, "_entry"):
            bind_target = widget._entry
        elif hasattr(widget, "_textbox"):
            bind_target = widget._textbox

        bind_target.bind("<FocusIn>", on_focus_in, add="+")
        bind_target.bind("<FocusOut>", on_focus_out, add="+")

        # Store reference to prevent GC
        if not hasattr(widget, "_focus_ring_overlays"):
            widget._focus_ring_overlays = []
        widget._focus_ring_overlays.append(overlay)

        # Hook into destroy — only wrap once to prevent stacking
        if not hasattr(widget, "_focus_ring_original_destroy"):
            widget._focus_ring_original_destroy = widget.destroy

            def destroy_with_cleanup():
                for ov in getattr(widget, "_focus_ring_overlays", []):
                    ov.destroy()
                widget._focus_ring_original_destroy()

            widget.destroy = destroy_with_cleanup

        return overlay
