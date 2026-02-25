import tkinter
from typing import Union, Tuple, Optional, Any

from .theme import ThemeManager
from .font import CTkFont
from .appearance_mode import AppearanceModeTracker


class CTkToolTip:
    """
    Tooltip that appears when hovering over a widget.
    Supports delay, auto-positioning, wrapping, and fade animation.

    Usage:
        button = ctk.CTkButton(root, text="Hover me")
        CTkToolTip(button, message="This is a tooltip")
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
                 **kwargs):

        self._widget = widget
        self._message = message
        self._delay = max(0, delay)
        self._duration = max(0, duration)  # 0 = stay until mouse leaves
        self._x_offset = x_offset
        self._y_offset = y_offset
        self._max_width = max_width
        self._alpha = alpha
        self._padding = padding
        self._corner_radius = corner_radius
        self._border_width = border_width

        # colors
        self._fg_color = ("#f0f0f0", "#333333") if fg_color is None else fg_color
        self._text_color = ("#1a1a1a", "#e0e0e0") if text_color is None else text_color
        self._border_color = ("#c0c0c0", "#555555") if border_color is None else border_color

        # font
        self._font = font

        # internal state
        self._toplevel: Optional[tkinter.Toplevel] = None
        self._after_enter_id = None
        self._after_leave_id = None
        self._after_duration_id = None
        self._visible = False

        # bind events
        self._widget.bind("<Enter>", self._on_enter, add="+")
        self._widget.bind("<Leave>", self._on_leave, add="+")
        self._widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, event=None):
        """Schedule tooltip display after delay."""
        self._cancel_scheduled()
        self._after_enter_id = self._widget.after(self._delay, self._show)

    def _on_leave(self, event=None):
        """Cancel scheduled tooltip or hide it."""
        self._cancel_scheduled()
        self._hide()

    def _cancel_scheduled(self):
        """Cancel any pending after() calls."""
        if self._after_enter_id is not None:
            self._widget.after_cancel(self._after_enter_id)
            self._after_enter_id = None
        if self._after_leave_id is not None:
            self._widget.after_cancel(self._after_leave_id)
            self._after_leave_id = None
        if self._after_duration_id is not None:
            self._widget.after_cancel(self._after_duration_id)
            self._after_duration_id = None

    def _show(self):
        """Create and show the tooltip window."""
        if self._visible or not self._message:
            return

        self._toplevel = tkinter.Toplevel(self._widget)
        self._toplevel.withdraw()
        self._toplevel.overrideredirect(True)

        # set transparency
        try:
            self._toplevel.attributes("-alpha", self._alpha)
        except Exception:
            pass

        # keep on top
        try:
            self._toplevel.attributes("-topmost", True)
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
            font = ("Segoe UI", 12) if hasattr(tkinter, "Tcl") else ("TkDefaultFont", 12)

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

        # calculate position
        self._toplevel.update_idletasks()
        tip_width = self._toplevel.winfo_reqwidth()
        tip_height = self._toplevel.winfo_reqheight()

        # get cursor position
        try:
            x = self._widget.winfo_rootx() + self._widget.winfo_pointerx() - self._widget.winfo_rootx() + self._x_offset
            y = self._widget.winfo_rooty() + self._widget.winfo_pointery() - self._widget.winfo_rooty() + self._y_offset
        except Exception:
            x = self._widget.winfo_rootx() + self._x_offset
            y = self._widget.winfo_rooty() + self._widget.winfo_height() + self._y_offset

        # screen bounds check
        try:
            screen_w = self._widget.winfo_screenwidth()
            screen_h = self._widget.winfo_screenheight()

            # flip horizontally if off-screen right
            if x + tip_width > screen_w - 10:
                x = max(10, x - tip_width - self._x_offset * 2)

            # flip vertically if off-screen bottom
            if y + tip_height > screen_h - 10:
                y = max(10, y - tip_height - self._y_offset * 2)
        except Exception:
            pass

        self._toplevel.geometry(f"+{int(x)}+{int(y)}")
        self._toplevel.deiconify()
        self._visible = True

        # auto-hide after duration
        if self._duration > 0:
            self._after_duration_id = self._widget.after(self._duration, self._hide)

    def _hide(self):
        """Destroy the tooltip window."""
        if self._toplevel is not None:
            try:
                self._toplevel.destroy()
            except Exception:
                pass
            self._toplevel = None
        self._visible = False

    def configure(self, **kwargs):
        """Configure tooltip properties."""
        if "message" in kwargs:
            self._message = kwargs.pop("message")
        if "delay" in kwargs:
            self._delay = max(0, kwargs.pop("delay"))
        if "duration" in kwargs:
            self._duration = max(0, kwargs.pop("duration"))
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

    def cget(self, attribute_name: str):
        if attribute_name == "message":
            return self._message
        elif attribute_name == "delay":
            return self._delay
        elif attribute_name == "duration":
            return self._duration
        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "alpha":
            return self._alpha
        elif attribute_name == "max_width":
            return self._max_width
        else:
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
