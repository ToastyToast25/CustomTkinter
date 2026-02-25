import tkinter
from typing import Union, Tuple, Optional, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass


class CTkSkeleton(CTkBaseClass):
    """
    Skeleton loading placeholder with shimmer animation.
    Displays a rounded rectangle that pulses between two colors
    to indicate content is loading.

    Usage:
        skeleton = CTkSkeleton(parent, width=200, height=20)
        skeleton.pack(padx=10, pady=5)
        # later, when content is ready:
        skeleton.destroy()
    """

    def __init__(self,
                 master: Any,
                 width: int = 200,
                 height: int = 20,
                 corner_radius: Optional[int] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 shimmer_color: Optional[Union[str, Tuple[str, str]]] = None,

                 speed: int = 1200,
                 animate: bool = True,
                 **kwargs):

        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # colors
        if fg_color is None:
            # derive from theme: slightly lighter/darker than frame bg
            frame_fg = ThemeManager.theme["CTkFrame"]["fg_color"]
            self._fg_color = frame_fg
        else:
            self._fg_color = self._check_color_type(fg_color)

        if shimmer_color is None:
            self._shimmer_color = None  # will be derived in _draw after canvas exists
        else:
            self._shimmer_color = self._check_color_type(shimmer_color)

        # shape
        self._corner_radius = ThemeManager.theme["CTkFrame"]["corner_radius"] if corner_radius is None else corner_radius

        # animation
        self._speed = max(200, speed)
        self._animate = animate
        self._phase = 0.0
        self._after_id = None

        # build
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, sticky="nswe")
        self._draw_engine = DrawEngine(self._canvas)

        self._draw()

        if self._animate:
            self._start_shimmer()

    def _color_to_hex(self, color: str) -> str:
        """Convert any tkinter color (named or hex) to #RRGGBB."""
        if color.startswith("#") and len(color) == 7:
            return color
        try:
            # winfo_rgb returns (r, g, b) in 0-65535 range
            r, g, b = self._canvas.winfo_rgb(color)
            return f"#{r >> 8:02x}{g >> 8:02x}{b >> 8:02x}"
        except Exception:
            return "#333333"

    def _derive_shimmer_color(self):
        """Auto-derive shimmer color from fg_color."""
        base = self._color_to_hex(self._apply_appearance_mode(self._fg_color))
        r, g, b = int(base[1:3], 16), int(base[3:5], 16), int(base[5:7], 16)
        brightness = (r + g + b) / 3
        if brightness > 128:
            r, g, b = max(0, r - 25), max(0, g - 25), max(0, b - 25)
        else:
            r, g, b = min(255, r + 25), min(255, g + 25), min(255, b + 25)
        derived = f"#{r:02x}{g:02x}{b:02x}"
        self._shimmer_color = (derived, derived)

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        if not self._canvas.winfo_exists():
            return

        # derive shimmer color on first draw (canvas must exist for winfo_rgb)
        if self._shimmer_color is None:
            self._derive_shimmer_color()

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(
            self._apply_widget_scaling(self._current_width),
            self._apply_widget_scaling(self._current_height),
            self._apply_widget_scaling(self._corner_radius),
            0)

        if no_color_updates is False or requires_recoloring:
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._canvas.itemconfig("inner_parts",
                                    fill=self._apply_appearance_mode(self._fg_color),
                                    outline=self._apply_appearance_mode(self._fg_color))

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)
        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw()

    @staticmethod
    def _lerp_hex(c1: str, c2: str, t: float) -> str:
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        return f"#{int(r1+(r2-r1)*t):02x}{int(g1+(g2-g1)*t):02x}{int(b1+(b2-b1)*t):02x}"

    def _start_shimmer(self):
        self._phase = 0.0
        self._shimmer_tick()

    def _shimmer_tick(self):
        if not self._animate:
            return
        import math
        if self._shimmer_color is None:
            self._derive_shimmer_color()
        t = (math.sin(self._phase * math.pi * 2) + 1) / 2
        base = self._color_to_hex(self._apply_appearance_mode(self._fg_color))
        shimmer = self._color_to_hex(self._apply_appearance_mode(self._shimmer_color))
        color = self._lerp_hex(base, shimmer, t)
        try:
            self._canvas.itemconfig("inner_parts", fill=color, outline=color)
        except Exception:
            return
        interval = 16  # ~60fps
        self._phase += interval / self._speed
        if self._phase >= 1.0:
            self._phase -= 1.0
        self._after_id = self.after(interval, self._shimmer_tick)

    def stop(self):
        """Stop the shimmer animation."""
        self._animate = False
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        # restore base color
        self._canvas.itemconfig("inner_parts",
                                fill=self._apply_appearance_mode(self._fg_color),
                                outline=self._apply_appearance_mode(self._fg_color))

    def start(self):
        """Start or restart the shimmer animation."""
        if not self._animate:
            self._animate = True
            self._start_shimmer()

    def destroy(self):
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        self._animate = False
        super().destroy()

    def configure(self, **kwargs):
        require_redraw = False
        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            require_redraw = True
        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True
        if "shimmer_color" in kwargs:
            self._shimmer_color = self._check_color_type(kwargs.pop("shimmer_color"))
        if "speed" in kwargs:
            self._speed = max(200, kwargs.pop("speed"))
        if "animate" in kwargs:
            animate = kwargs.pop("animate")
            if animate and not self._animate:
                self.start()
            elif not animate and self._animate:
                self.stop()
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "shimmer_color":
            return self._shimmer_color
        elif attribute_name == "speed":
            return self._speed
        elif attribute_name == "animate":
            return self._animate
        else:
            return super().cget(attribute_name)
