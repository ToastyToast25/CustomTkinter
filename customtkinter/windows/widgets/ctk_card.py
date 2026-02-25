import tkinter
import math
from typing import Union, Tuple, Optional, Callable, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .ctk_frame import CTkFrame


class CTkCard(CTkFrame):
    """
    Interactive card/panel with animated border glow on hover.
    Extends CTkFrame with hover animation, click handling, and
    optional header/footer sections.

    Usage:
        card = CTkCard(parent, border_width=2, hover_effect=True)
        ctk.CTkLabel(card, text="Title").pack(padx=16, pady=(16, 4))
        ctk.CTkLabel(card, text="Content here").pack(padx=16, pady=(4, 16))
    """

    def __init__(self,
                 master: Any,
                 width: int = 300,
                 height: int = 200,
                 corner_radius: Optional[int] = None,
                 border_width: int = 2,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 hover_border_color: Optional[Union[str, Tuple[str, str]]] = None,

                 hover_effect: bool = True,
                 hover_duration: int = 200,
                 command: Optional[Callable] = None,
                 **kwargs):

        # default border color
        if border_color is None:
            border_color = ("#d4d4d4", "#404040")

        super().__init__(master=master, width=width, height=height,
                         corner_radius=corner_radius, border_width=border_width,
                         bg_color=bg_color, fg_color=fg_color,
                         border_color=border_color, **kwargs)

        self._hover_border_color = hover_border_color or ("#3B8ED0", "#3B8ED0")
        self._base_border_color = border_color
        self._hover_effect = hover_effect
        self._hover_duration = max(50, hover_duration)
        self._command = command

        # animation state
        self._hover_phase = 0.0  # 0.0 = base, 1.0 = full hover
        self._hover_direction = 0  # 1 = hovering in, -1 = hovering out
        self._hover_after_id = None

        # bindings
        if self._hover_effect or self._command:
            self.bind("<Enter>", self._on_enter, add="+")
            self.bind("<Leave>", self._on_leave, add="+")
        if self._command:
            self.bind("<Button-1>", self._on_click, add="+")
            if hasattr(self, '_cursor_manipulation_enabled') and self._cursor_manipulation_enabled:
                self.configure(cursor="hand2")

    def _on_enter(self, event=None):
        if self._hover_effect:
            self._hover_direction = 1
            self._animate_hover()

    def _on_leave(self, event=None):
        if self._hover_effect:
            self._hover_direction = -1
            self._animate_hover()

    def _on_click(self, event=None):
        if self._command is not None:
            self._command()

    def _animate_hover(self):
        """Animate border color transition."""
        if self._hover_after_id is not None:
            self.after_cancel(self._hover_after_id)
            self._hover_after_id = None

        interval = 16  # ~60fps
        step = interval / self._hover_duration

        self._hover_phase += step * self._hover_direction
        self._hover_phase = max(0.0, min(1.0, self._hover_phase))

        # interpolate border color
        base = self._color_to_hex(self._apply_appearance_mode(self._base_border_color))
        target = self._color_to_hex(self._apply_appearance_mode(self._hover_border_color))
        current = self._lerp_hex(base, target, self._ease_out_cubic(self._hover_phase))

        try:
            self._canvas.itemconfig("border_parts", fill=current, outline=current)
        except Exception:
            return

        # continue animation if not at target
        if (self._hover_direction > 0 and self._hover_phase < 1.0) or \
           (self._hover_direction < 0 and self._hover_phase > 0.0):
            self._hover_after_id = self.after(interval, self._animate_hover)

    def _color_to_hex(self, color: str) -> str:
        """Convert any tkinter color to #RRGGBB."""
        if color.startswith("#") and len(color) == 7:
            return color
        try:
            r, g, b = self._canvas.winfo_rgb(color)
            return f"#{r >> 8:02x}{g >> 8:02x}{b >> 8:02x}"
        except Exception:
            return "#333333"

    @staticmethod
    def _lerp_hex(c1: str, c2: str, t: float) -> str:
        """Linearly interpolate between two hex colors."""
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        return f"#{int(r1+(r2-r1)*t):02x}{int(g1+(g2-g1)*t):02x}{int(b1+(b2-b1)*t):02x}"

    @staticmethod
    def _ease_out_cubic(t: float) -> float:
        """Cubic ease-out for smooth deceleration."""
        return 1 - (1 - t) ** 3

    def destroy(self):
        if self._hover_after_id is not None:
            self.after_cancel(self._hover_after_id)
            self._hover_after_id = None
        super().destroy()

    def configure(self, **kwargs):
        if "hover_border_color" in kwargs:
            self._hover_border_color = kwargs.pop("hover_border_color")
        if "hover_effect" in kwargs:
            self._hover_effect = kwargs.pop("hover_effect")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "border_color" in kwargs:
            self._base_border_color = kwargs["border_color"]
        super().configure(**kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "hover_border_color":
            return self._hover_border_color
        elif attribute_name == "hover_effect":
            return self._hover_effect
        elif attribute_name == "hover_duration":
            return self._hover_duration
        elif attribute_name == "command":
            return self._command
        else:
            return super().cget(attribute_name)
