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

    Size variants:
        badge = CTkStatusBadge(parent, text="OK", style="success", size="small")

    Count badge:
        badge = CTkStatusBadge(parent, count=5, style="error")
        badge.set_count(42)

    Pulse animation:
        badge = CTkStatusBadge(parent, text="Live", style="success", pulse=True)
        badge.stop_pulse()
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

    _SIZE_CONFIG = {
        "small":   {"font_size": 10, "height": 22},
        "default": {"font_size": 12, "height": 26},
        "large":   {"font_size": 14, "height": 32},
    }

    def __init__(self,
                 master: Any,
                 text: str = "Status",
                 style: str = "muted",
                 show_dot: bool = True,
                 width: int = 0,
                 height: Optional[int] = None,
                 corner_radius: Optional[int] = None,

                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 dot_color: Optional[Union[str, Tuple[str, str]]] = None,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 size: str = "default",
                 count: Optional[int] = None,
                 pulse: bool = False,
                 **kwargs):

        # resolve size variant
        self._size = size if size in self._SIZE_CONFIG else "default"
        size_cfg = self._SIZE_CONFIG[self._size]

        # height: explicit > size variant default
        if height is None:
            height = size_cfg["height"]

        super().__init__(master=master, width=width, height=height,
                         bg_color="transparent", **kwargs)

        self._text = text
        self._style = style
        self._show_dot = show_dot
        self._corner_radius = 12 if corner_radius is None else corner_radius

        # count badge mode
        self._count = count

        # pulse state
        self._pulse = pulse
        self._pulse_after_id: Optional[str] = None
        self._pulse_direction: int = 1  # 1 = fading out, -1 = fading in
        self._pulse_t: float = 0.0  # 0.0 = full color, 1.0 = faded

        # animated transition state
        self._transition_after_id: Optional[str] = None

        # resolve style colors (user overrides take priority)
        style_cfg = self._STYLE_COLORS.get(style, self._STYLE_COLORS["muted"])
        self._fg_color = fg_color or style_cfg["fg"]
        self._text_color = text_color or style_cfg["text"]
        self._dot_color = dot_color or style_cfg["dot"]

        # font: explicit > size variant default
        if font is not None:
            self._font = font
        else:
            self._font = CTkFont(size=size_cfg["font_size"])

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
        dot_font_size = max(6, size_cfg["font_size"] - 4)
        self._dot_label = tkinter.Label(
            self._inner,
            text="\u25CF",
            font=("Segoe UI", dot_font_size),
            fg=self._apply_appearance_mode(self._dot_color),
            bg=self._apply_appearance_mode(self._fg_color),
        )

        # text label
        self._text_label = tkinter.Label(
            self._inner,
            text=self._format_display_text(),
            font=self._font if isinstance(self._font, tuple) else (
                self._font.cget("family"), self._font.cget("size"),
                self._font.cget("weight")),
            fg=self._apply_appearance_mode(self._text_color),
            bg=self._apply_appearance_mode(self._fg_color),
        )

        # layout depending on count mode vs text mode
        self._layout_content()

        self._draw()

        # start pulse if requested
        if self._pulse:
            self.start_pulse()

    def _format_display_text(self) -> str:
        """Return the display string based on count or text mode."""
        if self._count is not None:
            if self._count > 99:
                return "99+"
            return str(self._count)
        return self._text

    def _layout_content(self):
        """Pack the dot and text labels according to the current mode."""
        self._dot_label.pack_forget()
        self._text_label.pack_forget()

        if self._count is not None:
            # count badge: compact, centered, no dot
            self._text_label.pack(side="left", padx=(8, 8), pady=2)
        else:
            # normal text mode
            if self._show_dot:
                pad_cfg = self._SIZE_CONFIG[self._size]
                dot_padx_left = 10 if self._size != "small" else 6
                self._dot_label.pack(side="left", padx=(dot_padx_left, 2), pady=2)
            pad_left = (10 if self._size != "small" else 6) if not self._show_dot else 0
            pad_right = 10 if self._size != "small" else 6
            self._text_label.pack(side="left", padx=(pad_left, pad_right), pady=2)

    # ── Color helpers ──────────────────────────────────────────────

    @staticmethod
    def _lerp_hex(c1: str, c2: str, t: float) -> str:
        """Linearly interpolate between two hex colors (#RRGGBB)."""
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        return f"#{int(r1+(r2-r1)*t):02x}{int(g1+(g2-g1)*t):02x}{int(b1+(b2-b1)*t):02x}"

    def _color_to_hex(self, color: str) -> str:
        """Resolve any tkinter color string to a #RRGGBB hex string."""
        if color.startswith("#") and len(color) == 7:
            return color
        try:
            r, g, b = self.winfo_rgb(color)
            return f"#{r >> 8:02x}{g >> 8:02x}{b >> 8:02x}"
        except Exception:
            return "#333333"

    @staticmethod
    def _ease_out_cubic(t: float) -> float:
        """Ease-out cubic easing function."""
        return 1.0 - (1.0 - t) ** 3

    # ── Animated color transition ──────────────────────────────────

    def _animate_transition(self, old_fg: str, new_fg: str,
                            old_text: str, new_text: str,
                            old_dot: str, new_dot: str,
                            start_ms: int, duration_ms: int = 200):
        """Animate the color transition from old colors to new colors."""
        import time
        elapsed = int((time.time() * 1000)) - start_ms
        if elapsed < 0:
            elapsed = 0

        if elapsed >= duration_ms:
            # final frame: apply exact target colors
            self._apply_colors_directly(new_fg, new_text, new_dot)
            self._transition_after_id = None
            return

        t = self._ease_out_cubic(elapsed / duration_ms)

        fg_now = self._lerp_hex(old_fg, new_fg, t)
        text_now = self._lerp_hex(old_text, new_text, t)
        dot_now = self._lerp_hex(old_dot, new_dot, t)

        self._apply_colors_directly(fg_now, text_now, dot_now)

        # schedule next frame at ~60fps (16ms)
        self._transition_after_id = self.after(
            16,
            self._animate_transition,
            old_fg, new_fg, old_text, new_text, old_dot, new_dot,
            start_ms, duration_ms,
        )

    def _cancel_transition(self):
        """Cancel any running color transition animation."""
        if self._transition_after_id is not None:
            self.after_cancel(self._transition_after_id)
            self._transition_after_id = None

    def _apply_colors_directly(self, fg_hex: str, text_hex: str, dot_hex: str):
        """Apply resolved hex colors directly to all widget parts."""
        self._canvas.itemconfig("inner_parts", fill=fg_hex, outline=fg_hex)
        self._inner.configure(bg=fg_hex)
        self._text_label.configure(bg=fg_hex, fg=text_hex)
        self._dot_label.configure(bg=fg_hex, fg=dot_hex)

    # ── Pulse animation ────────────────────────────────────────────

    def start_pulse(self):
        """Start the dot pulsing animation (fades dot color toward bg color and back)."""
        self._pulse = True
        self._pulse_t = 0.0
        self._pulse_direction = 1
        self._pulse_step()

    def stop_pulse(self):
        """Stop the dot pulsing animation and restore the dot to its full color."""
        self._pulse = False
        if self._pulse_after_id is not None:
            self.after_cancel(self._pulse_after_id)
            self._pulse_after_id = None
        # restore dot to its actual color
        self._dot_label.configure(fg=self._apply_appearance_mode(self._dot_color))

    def _pulse_step(self):
        """One step of the pulse animation. Called every 16ms for ~60fps."""
        if not self._pulse:
            return

        # advance t: full cycle is 1000ms (500ms each direction), step is 16ms
        dt = 16.0 / 500.0  # fraction of one half-cycle per frame
        self._pulse_t += dt * self._pulse_direction

        if self._pulse_t >= 1.0:
            self._pulse_t = 1.0
            self._pulse_direction = -1
        elif self._pulse_t <= 0.0:
            self._pulse_t = 0.0
            self._pulse_direction = 1

        # interpolate dot color toward fg color (simulating 50% opacity fade)
        dot_hex = self._color_to_hex(self._apply_appearance_mode(self._dot_color))
        fg_hex = self._color_to_hex(self._apply_appearance_mode(self._fg_color))

        eased = self._ease_out_cubic(self._pulse_t)
        # at t=1.0, fully faded (halfway to fg_color = 50% opacity effect)
        pulsed = self._lerp_hex(dot_hex, fg_hex, eased * 0.5)

        self._dot_label.configure(fg=pulsed)

        self._pulse_after_id = self.after(16, self._pulse_step)

    # ── Drawing ────────────────────────────────────────────────────

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

    # ── Public API ─────────────────────────────────────────────────

    def set_status(self, text: str, style: Optional[str] = None):
        """Update the badge text and optionally change its style with animated transition."""
        self._text = text
        self._text_label.configure(text=self._format_display_text())

        if style is not None and style != self._style:
            # capture old resolved colors before changing style
            old_fg_hex = self._color_to_hex(self._apply_appearance_mode(self._fg_color))
            old_text_hex = self._color_to_hex(self._apply_appearance_mode(self._text_color))
            old_dot_hex = self._color_to_hex(self._apply_appearance_mode(self._dot_color))

            # update style and color tuples
            self._style = style
            style_cfg = self._STYLE_COLORS.get(style, self._STYLE_COLORS["muted"])
            self._fg_color = style_cfg["fg"]
            self._text_color = style_cfg["text"]
            self._dot_color = style_cfg["dot"]

            # resolve new colors
            new_fg_hex = self._color_to_hex(self._apply_appearance_mode(self._fg_color))
            new_text_hex = self._color_to_hex(self._apply_appearance_mode(self._text_color))
            new_dot_hex = self._color_to_hex(self._apply_appearance_mode(self._dot_color))

            # redraw canvas shape (needed for bg_color of canvas itself)
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._draw_engine.draw_rounded_rect_with_border(
                self._apply_widget_scaling(self._current_width),
                self._apply_widget_scaling(self._current_height),
                self._apply_widget_scaling(self._corner_radius),
                0)

            # cancel any running transition and start a new one
            self._cancel_transition()
            import time
            start_ms = int(time.time() * 1000)
            self._animate_transition(
                old_fg_hex, new_fg_hex,
                old_text_hex, new_text_hex,
                old_dot_hex, new_dot_hex,
                start_ms, 200,
            )

    def set_count(self, n: Optional[int]):
        """Set or clear the count badge value. Pass None to switch back to text mode."""
        self._count = n
        self._text_label.configure(text=self._format_display_text())
        self._layout_content()

    # ── Scaling ────────────────────────────────────────────────────

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    # ── Configure / cget ───────────────────────────────────────────

    def configure(self, **kwargs):
        require_redraw = False
        if "text" in kwargs:
            self._text = kwargs.pop("text")
            self._text_label.configure(text=self._format_display_text())
        if "style" in kwargs:
            self.set_status(self._text, kwargs.pop("style"))
        if "show_dot" in kwargs:
            self._show_dot = kwargs.pop("show_dot")
            self._layout_content()
        if "fg_color" in kwargs:
            self._fg_color = kwargs.pop("fg_color")
            require_redraw = True
        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            require_redraw = True
        if "dot_color" in kwargs:
            self._dot_color = kwargs.pop("dot_color")
            require_redraw = True
        if "size" in kwargs:
            new_size = kwargs.pop("size")
            if new_size in self._SIZE_CONFIG:
                self._size = new_size
                size_cfg = self._SIZE_CONFIG[self._size]
                self._font = CTkFont(size=size_cfg["font_size"])
                self._text_label.configure(
                    font=(self._font.cget("family"), self._font.cget("size"),
                          self._font.cget("weight")))
                dot_font_size = max(6, size_cfg["font_size"] - 4)
                self._dot_label.configure(font=("Segoe UI", dot_font_size))
                self._set_dimensions(height=size_cfg["height"])
                self._layout_content()
                require_redraw = True
        if "count" in kwargs:
            self.set_count(kwargs.pop("count"))
        if "pulse" in kwargs:
            pulse_val = kwargs.pop("pulse")
            if pulse_val and not self._pulse:
                self.start_pulse()
            elif not pulse_val and self._pulse:
                self.stop_pulse()
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
        elif attribute_name == "size":
            return self._size
        elif attribute_name == "count":
            return self._count
        elif attribute_name == "pulse":
            return self._pulse
        else:
            return super().cget(attribute_name)

    # ── Cleanup ────────────────────────────────────────────────────

    def destroy(self):
        """Cancel all pending animations before destroying the widget."""
        self._cancel_transition()
        if self._pulse_after_id is not None:
            self.after_cancel(self._pulse_after_id)
            self._pulse_after_id = None
        super().destroy()
