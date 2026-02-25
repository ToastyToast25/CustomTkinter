import tkinter
from typing import Union, Tuple, Optional, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkStatusBadge(CTkBaseClass):
    """
    Status badge / pill component with dot indicator and colored background.
    Shows a small status indicator with optional dot icon and text.

    Usage:
        badge = CTkStatusBadge(parent, text="Online", style="success")
        badge.set_status("Offline", "error")
    """

    _STYLE_COLORS = {
        "success": {
            "fg":   ("#dcfce7", "#14532d"),
            "text": ("#166534", "#86efac"),
            "dot":  ("#22c55e", "#4ade80"),
        },
        "warning": {
            "fg":   ("#fef3c7", "#451a03"),
            "text": ("#92400e", "#fcd34d"),
            "dot":  ("#f59e0b", "#fbbf24"),
        },
        "error": {
            "fg":   ("#fecaca", "#450a0a"),
            "text": ("#991b1b", "#fca5a5"),
            "dot":  ("#ef4444", "#f87171"),
        },
        "info": {
            "fg":   ("#dbeafe", "#172554"),
            "text": ("#1e40af", "#93c5fd"),
            "dot":  ("#3b82f6", "#60a5fa"),
        },
        "muted": {
            "fg":   ("#f3f4f6", "#1f2937"),
            "text": ("#6b7280", "#9ca3af"),
            "dot":  ("#9ca3af", "#6b7280"),
        },
    }

    def __init__(self,
                 master: Any,
                 text: str = "Status",
                 style: str = "muted",
                 show_dot: bool = True,
                 width: int = 0,
                 height: int = 26,
                 corner_radius: Optional[int] = None,

                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 dot_color: Optional[Union[str, Tuple[str, str]]] = None,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 **kwargs):

        super().__init__(master=master, width=width, height=height,
                         bg_color="transparent", **kwargs)

        self._text = text
        self._style = style
        self._show_dot = show_dot
        self._corner_radius = 12 if corner_radius is None else corner_radius

        # resolve style colors (user overrides take priority)
        style_cfg = self._STYLE_COLORS.get(style, self._STYLE_COLORS["muted"])
        self._fg_color = fg_color or style_cfg["fg"]
        self._text_color = text_color or style_cfg["text"]
        self._dot_color = dot_color or style_cfg["dot"]

        # font
        self._font = font or CTkFont(size=12)

        # grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # canvas for rounded background
        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, sticky="nswe")
        self._draw_engine = DrawEngine(self._canvas)

        # inner layout frame
        self._inner = tkinter.Frame(self, bg=self._apply_appearance_mode(self._fg_color))
        self._inner.grid(row=0, column=0, sticky="nswe")

        # dot indicator
        self._dot_label = tkinter.Label(
            self._inner,
            text="\u25CF",
            font=("Segoe UI", 8),
            fg=self._apply_appearance_mode(self._dot_color),
            bg=self._apply_appearance_mode(self._fg_color),
        )
        if self._show_dot:
            self._dot_label.pack(side="left", padx=(10, 2), pady=2)

        # text label
        self._text_label = tkinter.Label(
            self._inner,
            text=self._text,
            font=self._font if isinstance(self._font, tuple) else (
                self._font.cget("family"), self._font.cget("size"),
                self._font.cget("weight")),
            fg=self._apply_appearance_mode(self._text_color),
            bg=self._apply_appearance_mode(self._fg_color),
        )
        pad_left = 10 if not self._show_dot else 0
        self._text_label.pack(side="left", padx=(pad_left, 10), pady=2)

        self._draw()

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(
            self._apply_widget_scaling(self._current_width),
            self._apply_widget_scaling(self._current_height),
            self._apply_widget_scaling(self._corner_radius),
            0)

        if no_color_updates is False or requires_recoloring:
            fg = self._apply_appearance_mode(self._fg_color)
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._canvas.itemconfig("inner_parts", fill=fg, outline=fg)
            self._inner.configure(bg=fg)
            self._text_label.configure(bg=fg,
                                       fg=self._apply_appearance_mode(self._text_color))
            self._dot_label.configure(bg=fg,
                                      fg=self._apply_appearance_mode(self._dot_color))

    def set_status(self, text: str, style: Optional[str] = None):
        """Update the badge text and optionally change its style."""
        self._text = text
        self._text_label.configure(text=text)

        if style is not None and style != self._style:
            self._style = style
            style_cfg = self._STYLE_COLORS.get(style, self._STYLE_COLORS["muted"])
            self._fg_color = style_cfg["fg"]
            self._text_color = style_cfg["text"]
            self._dot_color = style_cfg["dot"]
            self._draw()

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    def configure(self, **kwargs):
        require_redraw = False
        if "text" in kwargs:
            self._text = kwargs.pop("text")
            self._text_label.configure(text=self._text)
        if "style" in kwargs:
            self.set_status(self._text, kwargs.pop("style"))
        if "show_dot" in kwargs:
            self._show_dot = kwargs.pop("show_dot")
            if self._show_dot:
                self._dot_label.pack(side="left", padx=(10, 2), pady=2, before=self._text_label)
            else:
                self._dot_label.pack_forget()
        if "fg_color" in kwargs:
            self._fg_color = kwargs.pop("fg_color")
            require_redraw = True
        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            require_redraw = True
        if "dot_color" in kwargs:
            self._dot_color = kwargs.pop("dot_color")
            require_redraw = True
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "text":
            return self._text
        elif attribute_name == "style":
            return self._style
        elif attribute_name == "show_dot":
            return self._show_dot
        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "dot_color":
            return self._dot_color
        else:
            return super().cget(attribute_name)
