import tkinter
from typing import Union, Tuple, Optional, Any

from .theme import ThemeManager
from .font import CTkFont
from .appearance_mode import AppearanceModeTracker


class CTkToolTip:
    """
    Tooltip that appears when hovering over a widget.
    Supports delay, fade animation, auto-positioning, wrapping,
    escape-to-dismiss, and disable/enable control.

    Usage:
        button = ctk.CTkButton(root, text="Hover me")
        CTkToolTip(button, message="This is a tooltip")

        # Disable temporarily
        tip.disable()
        tip.enable()
    """

    def __init__(self,
                 widget: Any,
                 message: str = "",
                 delay: int = 400,
                 duration: int = 0,
                 x_offset: int = 16,
                 y_offset: int = 12,
                 max_width: int = 300,

                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_width: int = 1,
                 corner_radius: int = 6,
                 padding: int = 8,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 alpha: float = 0.95,
                 fade_in: bool = True,
                 fade_duration: int = 150,
                 follow_cursor: bool = False,
                 enabled: bool = True,
                 **kwargs):

        self._widget = widget
        self._message = message
        self._delay = max(0, delay)
        self._duration = max(0, duration)
        self._x_offset = x_offset
        self._y_offset = y_offset
        self._max_width = max_width
        self._alpha = alpha
        self._padding = padding
        self._corner_radius = corner_radius
        self._border_width = border_width
        self._fade_in = fade_in
        self._fade_duration = max(50, fade_duration)
        self._follow_cursor = follow_cursor
        self._enabled = enabled

        # colors
        self._fg_color = ("#f0f0f0", "#333333") if fg_color is None else fg_color
        self._text_color = ("#1a1a1a", "#e0e0e0") if text_color is None else text_color
        self._border_color = ("#c0c0c0", "#555555") if border_color is None else border_color

        # font
        self._font = font

        # internal state
        self._toplevel: Optional[tkinter.Toplevel] = None
        self._after_enter_id = None
        self._after_duration_id = None
        self._fade_after_id = None
        self._follow_after_id = None
        self._visible = False
        self._current_alpha = 0.0

        # callbacks
        self._on_show_callback = None
        self._on_hide_callback = None

        # bind events
        self._enter_bind_id = self._widget.bind("<Enter>", self._on_enter, add="+")
        self._leave_bind_id = self._widget.bind("<Leave>", self._on_leave, add="+")
        self._click_bind_id = self._widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, event=None):
        """Schedule tooltip display after delay."""
        if not self._enabled:
            return
        self._cancel_scheduled()
        self._after_enter_id = self._widget.after(self._delay, self._show)

    def _on_leave(self, event=None):
        """Cancel scheduled tooltip or hide with fade."""
        self._cancel_scheduled()
        if self._visible and self._fade_in:
            self._fade_out()
        else:
            self._hide()

    def _cancel_scheduled(self):
        """Cancel any pending after() calls."""
        for attr in ("_after_enter_id", "_after_duration_id",
                     "_fade_after_id", "_follow_after_id"):
            aid = getattr(self, attr, None)
            if aid is not None:
                try:
                    self._widget.after_cancel(aid)
                except Exception:
                    pass
                setattr(self, attr, None)

    def _get_cursor_pos(self):
        """Get absolute cursor position."""
        try:
            return self._widget.winfo_pointerx(), self._widget.winfo_pointery()
        except Exception:
            return (self._widget.winfo_rootx() + self._x_offset,
                    self._widget.winfo_rooty() + self._widget.winfo_height())

    def _calculate_position(self, tip_width, tip_height):
        """Calculate tooltip position with screen bounds clamping."""
        cx, cy = self._get_cursor_pos()
        x = cx + self._x_offset
        y = cy + self._y_offset

        try:
            screen_w = self._widget.winfo_screenwidth()
            screen_h = self._widget.winfo_screenheight()

            if x + tip_width > screen_w - 10:
                x = max(10, cx - tip_width - self._x_offset)
            if y + tip_height > screen_h - 10:
                y = max(10, cy - tip_height - self._y_offset)
        except Exception:
            pass

        return int(x), int(y)

    def _show(self):
        """Create and show the tooltip window."""
        if self._visible or not self._message or not self._enabled:
            return

        self._toplevel = tkinter.Toplevel(self._widget)
        self._toplevel.withdraw()
        self._toplevel.overrideredirect(True)

        try:
            self._toplevel.attributes("-topmost", True)
        except Exception:
            pass

        # start invisible for fade-in
        self._current_alpha = 0.0 if self._fade_in else self._alpha
        try:
            self._toplevel.attributes("-alpha", self._current_alpha)
        except Exception:
            pass

        # get colors for current appearance mode
        fg = self._resolve_color(self._fg_color)
        text = self._resolve_color(self._text_color)
        border = self._resolve_color(self._border_color)

        # border frame
        border_frame = tkinter.Frame(self._toplevel, bg=border)
        border_frame.pack(fill="both", expand=True)

        # inner frame
        inner_frame = tkinter.Frame(border_frame, bg=fg)
        inner_frame.pack(fill="both", expand=True,
                         padx=self._border_width, pady=self._border_width)

        # label with wrapping
        font = self._font
        if font is None:
            font = ("Segoe UI", 12)

        label = tkinter.Label(inner_frame,
                              text=self._message,
                              justify="left",
                              wraplength=self._max_width,
                              bg=fg,
                              fg=text,
                              font=font,
                              padx=self._padding,
                              pady=self._padding)
        label.pack()

        # position
        self._toplevel.update_idletasks()
        tip_w = self._toplevel.winfo_reqwidth()
        tip_h = self._toplevel.winfo_reqheight()
        x, y = self._calculate_position(tip_w, tip_h)

        self._toplevel.geometry(f"+{x}+{y}")
        self._toplevel.deiconify()
        self._visible = True

        # bind escape to dismiss
        try:
            self._toplevel.bind("<Escape>", lambda e: self._on_leave())
        except Exception:
            pass

        # fade in
        if self._fade_in:
            self._fade_in_step()
        else:
            try:
                self._toplevel.attributes("-alpha", self._alpha)
            except Exception:
                pass

        # follow cursor
        if self._follow_cursor:
            self._follow_tick()

        # auto-hide after duration
        if self._duration > 0:
            self._after_duration_id = self._widget.after(self._duration, self._on_leave)

        if self._on_show_callback:
            self._on_show_callback()

    def _fade_in_step(self):
        """Animate fade-in by incrementing alpha."""
        if not self._visible or self._toplevel is None:
            return
        interval = 16
        step = self._alpha / (self._fade_duration / interval)
        self._current_alpha = min(self._alpha, self._current_alpha + step)
        try:
            self._toplevel.attributes("-alpha", self._current_alpha)
        except Exception:
            return
        if self._current_alpha < self._alpha:
            self._fade_after_id = self._widget.after(interval, self._fade_in_step)

    def _fade_out(self):
        """Animate fade-out by decrementing alpha, then destroy."""
        if self._toplevel is None:
            self._visible = False
            return
        interval = 16
        step = self._alpha / (self._fade_duration / interval)
        self._current_alpha = max(0.0, self._current_alpha - step)
        try:
            self._toplevel.attributes("-alpha", self._current_alpha)
        except Exception:
            self._hide()
            return
        if self._current_alpha > 0.01:
            self._fade_after_id = self._widget.after(interval, self._fade_out)
        else:
            self._hide()

    def _follow_tick(self):
        """Update tooltip position to follow cursor."""
        if not self._visible or self._toplevel is None:
            return
        try:
            tip_w = self._toplevel.winfo_width()
            tip_h = self._toplevel.winfo_height()
            x, y = self._calculate_position(tip_w, tip_h)
            self._toplevel.geometry(f"+{x}+{y}")
        except Exception:
            pass
        self._follow_after_id = self._widget.after(50, self._follow_tick)

    def _hide(self):
        """Destroy the tooltip window."""
        self._cancel_scheduled()
        if self._toplevel is not None:
            try:
                self._toplevel.destroy()
            except Exception:
                pass
            self._toplevel = None
        if self._visible and self._on_hide_callback:
            self._on_hide_callback()
        self._visible = False
        self._current_alpha = 0.0

    def enable(self):
        """Enable the tooltip."""
        self._enabled = True

    def disable(self):
        """Disable the tooltip and hide if visible."""
        self._enabled = False
        self._hide()

    def show(self):
        """Programmatically show the tooltip."""
        self._cancel_scheduled()
        self._show()

    def hide(self):
        """Programmatically hide the tooltip."""
        self._on_leave()

    def configure(self, **kwargs):
        """Configure tooltip properties."""
        if "message" in kwargs:
            self._message = kwargs.pop("message")
            if self._visible:
                self._hide()
                self._show()
        if "delay" in kwargs:
            self._delay = max(0, kwargs.pop("delay"))
        if "duration" in kwargs:
            self._duration = max(0, kwargs.pop("duration"))
        if "x_offset" in kwargs:
            self._x_offset = kwargs.pop("x_offset")
        if "y_offset" in kwargs:
            self._y_offset = kwargs.pop("y_offset")
        if "fg_color" in kwargs:
            self._fg_color = kwargs.pop("fg_color")
        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
        if "border_color" in kwargs:
            self._border_color = kwargs.pop("border_color")
        if "font" in kwargs:
            self._font = kwargs.pop("font")
        if "alpha" in kwargs:
            self._alpha = kwargs.pop("alpha")
        if "max_width" in kwargs:
            self._max_width = kwargs.pop("max_width")
        if "fade_in" in kwargs:
            self._fade_in = kwargs.pop("fade_in")
        if "follow_cursor" in kwargs:
            self._follow_cursor = kwargs.pop("follow_cursor")
        if "enabled" in kwargs:
            enabled = kwargs.pop("enabled")
            if enabled:
                self.enable()
            else:
                self.disable()
        if "on_show" in kwargs:
            self._on_show_callback = kwargs.pop("on_show")
        if "on_hide" in kwargs:
            self._on_hide_callback = kwargs.pop("on_hide")

    def cget(self, attribute_name: str):
        attrs = {
            "message": self._message, "delay": self._delay,
            "duration": self._duration, "x_offset": self._x_offset,
            "y_offset": self._y_offset, "fg_color": self._fg_color,
            "text_color": self._text_color, "border_color": self._border_color,
            "font": self._font, "alpha": self._alpha, "max_width": self._max_width,
            "fade_in": self._fade_in, "follow_cursor": self._follow_cursor,
            "enabled": self._enabled, "fade_duration": self._fade_duration,
        }
        if attribute_name in attrs:
            return attrs[attribute_name]
        raise ValueError(f"'{attribute_name}' is not a valid attribute")

    @staticmethod
    def _resolve_color(color):
        """Resolve a (light, dark) color tuple to a single color string."""
        if isinstance(color, (list, tuple)) and len(color) >= 2:
            mode = AppearanceModeTracker.appearance_mode
            return color[mode] if mode < len(color) else color[0]
        return color

    def destroy(self):
        """Unbind events and clean up."""
        self._cancel_scheduled()
        self._hide()
        try:
            self._widget.unbind("<Enter>")
            self._widget.unbind("<Leave>")
            self._widget.unbind("<ButtonPress>")
        except Exception:
            pass

    def is_visible(self) -> bool:
        return self._visible

    def is_enabled(self) -> bool:
        return self._enabled
