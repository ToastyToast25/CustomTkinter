import tkinter
import math
from typing import Union, Tuple, Optional, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkAvatar(CTkBaseClass):
    """
    Circular avatar widget that displays an image or initials fallback,
    with an optional status indicator dot.

    Usage:
        avatar = CTkAvatar(parent, text="John Doe", size="medium")
        avatar = CTkAvatar(parent, text="AB", status="online")
        avatar.set_status("away")
    """

    _SIZE_CONFIG = {
        "small":  {"diameter": 32, "font_size": 11, "status_r": 4, "border": 2},
        "medium": {"diameter": 48, "font_size": 16, "status_r": 6, "border": 2},
        "large":  {"diameter": 64, "font_size": 22, "status_r": 8, "border": 3},
        "xlarge": {"diameter": 96, "font_size": 32, "status_r": 10, "border": 3},
    }

    _STATUS_COLORS = {
        "online":  ("#22C55E", "#4ADE80"),
        "offline": ("#9CA3AF", "#6B7280"),
        "away":    ("#F59E0B", "#FBBF24"),
        "busy":    ("#EF4444", "#F87171"),
        None:      None,
    }

    # palette for auto-coloring based on initials
    _BG_PALETTE = [
        ("#3B82F6", "#2563EB"),  # blue
        ("#8B5CF6", "#7C3AED"),  # violet
        ("#EC4899", "#DB2777"),  # pink
        ("#14B8A6", "#0D9488"),  # teal
        ("#F97316", "#EA580C"),  # orange
        ("#06B6D4", "#0891B2"),  # cyan
        ("#84CC16", "#65A30D"),  # lime
        ("#EF4444", "#DC2626"),  # red
    ]

    def __init__(self,
                 master: Any,
                 text: str = "",
                 size: str = "medium",

                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_width: int = 0,

                 status: Optional[str] = None,
                 font: Optional[Union[tuple, CTkFont]] = None,
                 **kwargs):

        self._size_name = size if size in self._SIZE_CONFIG else "medium"
        cfg = self._SIZE_CONFIG[self._size_name]
        diameter = cfg["diameter"]

        super().__init__(master=master, width=diameter + 4, height=diameter + 4,
                         bg_color="transparent", **kwargs)

        self._text = text
        self._initials = self._extract_initials(text)
        self._status = status
        self._border_width_val = border_width

        # auto-pick bg color from palette based on text hash, or use provided
        if fg_color is not None:
            self._fg_color_val = fg_color
        else:
            idx = hash(text) % len(self._BG_PALETTE)
            self._fg_color_val = self._BG_PALETTE[idx]

        self._text_color = text_color or ("#FFFFFF", "#FFFFFF")
        self._border_color_val = border_color or ("#E5E7EB", "#374151")

        # font
        if font is not None:
            self._font = font
        else:
            self._font = CTkFont(size=cfg["font_size"], weight="bold")

        # canvas
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(diameter + 4),
                                 height=self._apply_widget_scaling(diameter + 4))
        self._canvas.grid(row=0, column=0, sticky="nswe")
        self._draw_engine = DrawEngine(self._canvas)

        # pulse animation state for status dot
        self._pulse_after_id = None
        self._pulse_t = 0.0
        self._pulse_direction = 1

        self._draw()

        # start pulse for "online" status
        if self._status == "online":
            self._start_pulse()

    @staticmethod
    def _extract_initials(text: str) -> str:
        """Extract up to 2 initials from a name string."""
        if not text:
            return "?"
        parts = text.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return parts[0][0].upper()

    # ── Drawing ───────────────────────────────────────────────────

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        self._canvas.delete("all")

        cfg = self._SIZE_CONFIG[self._size_name]
        s = self._apply_widget_scaling
        d = cfg["diameter"]
        cx = s((d + 4) / 2)
        cy = s((d + 4) / 2)
        r = s(d / 2)

        bg = self._apply_appearance_mode(self._bg_color)
        self._canvas.configure(bg=bg)

        # border circle (if border_width > 0)
        if self._border_width_val > 0:
            border_c = self._apply_appearance_mode(self._border_color_val)
            br = r + s(self._border_width_val)
            self._canvas.create_oval(
                cx - br, cy - br, cx + br, cy + br,
                fill=border_c, outline=border_c, tags="border"
            )

        # main circle
        fg = self._apply_appearance_mode(self._fg_color_val)
        self._canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=fg, outline=fg, tags="circle"
        )

        # initials text
        text_c = self._apply_appearance_mode(self._text_color)
        font_tuple = self._font if isinstance(self._font, tuple) else (
            self._font.cget("family"), self._font.cget("size"), self._font.cget("weight"))
        self._canvas.create_text(
            cx, cy,
            text=self._initials,
            fill=text_c,
            font=font_tuple,
            tags="text"
        )

        # status indicator dot
        if self._status in self._STATUS_COLORS and self._STATUS_COLORS[self._status] is not None:
            status_c = self._apply_appearance_mode(self._STATUS_COLORS[self._status])
            sr = s(cfg["status_r"])
            # position at bottom-right of circle
            angle = math.pi / 4  # 45 degrees
            sx = cx + r * math.cos(angle) * 0.7
            sy = cy + r * math.sin(angle) * 0.7

            # white ring behind status dot
            ring_r = sr + s(2)
            self._canvas.create_oval(
                sx - ring_r, sy - ring_r, sx + ring_r, sy + ring_r,
                fill=bg, outline=bg, tags="status_ring"
            )
            # status dot
            self._canvas.create_oval(
                sx - sr, sy - sr, sx + sr, sy + sr,
                fill=status_c, outline=status_c, tags="status"
            )

    # ── Public API ────────────────────────────────────────────────

    # ── Pulse animation for status dot ──────────────────────────

    def _start_pulse(self):
        """Start a gentle scale pulse on the status dot."""
        self._stop_pulse()
        self._pulse_t = 0.0
        self._pulse_direction = 1
        self._pulse_tick()

    def _stop_pulse(self):
        if self._pulse_after_id is not None:
            self.after_cancel(self._pulse_after_id)
            self._pulse_after_id = None

    def _pulse_tick(self):
        """Animate the status dot scale between 0.8x and 1.2x."""
        dt = 16.0 / 800.0  # ~800ms per half-cycle
        self._pulse_t += dt * self._pulse_direction
        if self._pulse_t >= 1.0:
            self._pulse_t = 1.0
            self._pulse_direction = -1
        elif self._pulse_t <= 0.0:
            self._pulse_t = 0.0
            self._pulse_direction = 1

        # ease-in-out
        t = self._pulse_t
        eased = t * t * (3.0 - 2.0 * t)
        scale = 0.85 + 0.3 * eased  # 0.85 to 1.15

        # update status dot size on canvas
        self._draw_status_dot(scale)
        self._pulse_after_id = self.after(16, self._pulse_tick)

    def _draw_status_dot(self, scale: float = 1.0):
        """Redraw just the status indicator dot with the given scale."""
        self._canvas.delete("status_ring")
        self._canvas.delete("status")

        if self._status not in self._STATUS_COLORS or self._STATUS_COLORS[self._status] is None:
            return

        cfg = self._SIZE_CONFIG[self._size_name]
        s = self._apply_widget_scaling
        d = cfg["diameter"]
        cx = s((d + 4) / 2)
        cy = s((d + 4) / 2)
        r = s(d / 2)
        bg = self._apply_appearance_mode(self._bg_color)
        status_c = self._apply_appearance_mode(self._STATUS_COLORS[self._status])
        sr = s(cfg["status_r"]) * scale

        angle = math.pi / 4
        sx = cx + r * math.cos(angle) * 0.7
        sy = cy + r * math.sin(angle) * 0.7

        ring_r = sr + s(2)
        self._canvas.create_oval(
            sx - ring_r, sy - ring_r, sx + ring_r, sy + ring_r,
            fill=bg, outline=bg, tags="status_ring"
        )
        self._canvas.create_oval(
            sx - sr, sy - sr, sx + sr, sy + sr,
            fill=status_c, outline=status_c, tags="status"
        )

    def set_status(self, status: Optional[str]):
        """Set the status indicator: 'online', 'offline', 'away', 'busy', or None."""
        old = self._status
        self._status = status
        self._draw()
        # manage pulse
        if status == "online" and old != "online":
            self._start_pulse()
        elif status != "online" and old == "online":
            self._stop_pulse()

    def set_text(self, text: str):
        """Update the display text/name (recalculates initials)."""
        self._text = text
        self._initials = self._extract_initials(text)
        self._draw()

    # ── Scaling ───────────────────────────────────────────────────

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        cfg = self._SIZE_CONFIG[self._size_name]
        d = cfg["diameter"]
        self._canvas.configure(
            width=self._apply_widget_scaling(d + 4),
            height=self._apply_widget_scaling(d + 4))
        self._draw(no_color_updates=True)

    # ── Configure / cget ──────────────────────────────────────────

    def configure(self, **kwargs):
        require_redraw = False
        if "text" in kwargs:
            self._text = kwargs.pop("text")
            self._initials = self._extract_initials(self._text)
            require_redraw = True
        if "status" in kwargs:
            new_status = kwargs.pop("status")
            old_status = self._status
            self._status = new_status
            require_redraw = True
            if new_status == "online" and old_status != "online":
                self._start_pulse()
            elif new_status != "online" and old_status == "online":
                self._stop_pulse()
        if "fg_color" in kwargs:
            self._fg_color_val = kwargs.pop("fg_color")
            require_redraw = True
        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            require_redraw = True
        if "border_color" in kwargs:
            self._border_color_val = kwargs.pop("border_color")
            require_redraw = True
        if "border_width" in kwargs:
            self._border_width_val = kwargs.pop("border_width")
            require_redraw = True
        if "size" in kwargs:
            new_size = kwargs.pop("size")
            if new_size in self._SIZE_CONFIG:
                self._size_name = new_size
                cfg = self._SIZE_CONFIG[new_size]
                self._font = CTkFont(size=cfg["font_size"], weight="bold")
                d = cfg["diameter"]
                self._set_dimensions(width=d + 4, height=d + 4)
                require_redraw = True
        if require_redraw:
            self._draw()
        super().configure(**kwargs)

    def destroy(self):
        self._stop_pulse()
        super().destroy()

    def cget(self, attribute_name: str):
        if attribute_name == "text":
            return self._text
        elif attribute_name == "status":
            return self._status
        elif attribute_name == "size":
            return self._size_name
        elif attribute_name == "fg_color":
            return self._fg_color_val
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "border_color":
            return self._border_color_val
        elif attribute_name == "border_width":
            return self._border_width_val
        else:
            return super().cget(attribute_name)
