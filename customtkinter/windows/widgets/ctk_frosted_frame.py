"""
CTkFrostedFrame — Glassmorphism / frosted glass panel for CustomTkinter.

Simulates a frosted glass effect using semi-transparent tinted backgrounds
with a subtle border glow. Since tkinter has no real blur or alpha compositing,
the effect is approximated using:
  1. A tinted background color (parent bg blended with a tint color at low alpha)
  2. A bright/contrasting border to simulate the glass edge refraction
  3. An optional noise/stipple pattern on the background for texture

Usage:
    panel = CTkFrostedFrame(root, tint_color="#ffffff", tint_opacity=0.08)
    CTkLabel(panel, text="Frosted content").pack(padx=20, pady=20)
"""

import tkinter
from typing import Union, Tuple, Optional, Any

from .core_widget_classes import CTkBaseClass
from .core_rendering import CTkCanvas
from .core_rendering import DrawEngine
from .theme import ThemeManager


class CTkFrostedFrame(CTkBaseClass):
    """
    A frame with a glassmorphism / frosted-glass appearance.

    The frost effect is achieved by:
    - Detecting the parent's background color
    - Blending a tint color onto it at low opacity (8-15%)
    - Drawing a semi-transparent bright border (glass edge)
    - Using a lighter/darker inner fill to suggest translucency
    """

    def __init__(
        self,
        master: Any,
        width: int = 300,
        height: int = 200,
        corner_radius: Optional[int] = None,
        border_width: int = 1,

        bg_color: Union[str, Tuple[str, str]] = "transparent",
        tint_color: Union[str, Tuple[str, str]] = ("#ffffff", "#ffffff"),
        tint_opacity: float = 0.08,
        border_color: Union[str, Tuple[str, str]] = ("#ffffff", "#444444"),
        border_opacity: float = 0.25,
        noise: bool = False,

        **kwargs,
    ):
        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        self._corner_radius = ThemeManager.theme["CTkFrame"]["corner_radius"] if corner_radius is None else corner_radius
        self._border_width = border_width

        self._tint_color = self._check_color_type(tint_color)
        self._tint_opacity = max(0.0, min(1.0, tint_opacity))
        self._border_color = self._check_color_type(border_color)
        self._border_opacity = max(0.0, min(1.0, border_opacity))
        self._noise = noise

        # Canvas for the frosted background
        self._canvas = CTkCanvas(
            master=self,
            highlightthickness=0,
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._canvas.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._draw_engine = DrawEngine(self._canvas)

        # Interior frame for child widgets
        self._interior = tkinter.Frame(self._canvas, highlightthickness=0, bd=0)
        self._interior_window_id = None

        self._draw()

    @property
    def interior(self) -> tkinter.Frame:
        """Return the interior frame. Place child widgets here."""
        return self._interior

    # Allow packing/gridding widgets directly in the frosted frame
    def winfo_children(self):
        """Return only user-placed children, not internal canvas."""
        return [child for child in super().winfo_children() if child is not self._canvas]

    # -- Drawing ------------------------------------------------------------

    def _draw(self, no_color_updates: bool = False) -> None:
        super()._draw(no_color_updates)

        scaled_w = self._apply_widget_scaling(self._desired_width)
        scaled_h = self._apply_widget_scaling(self._desired_height)
        scaled_cr = self._apply_widget_scaling(self._corner_radius)
        scaled_bw = self._apply_widget_scaling(self._border_width)

        self._canvas.configure(
            width=scaled_w,
            height=scaled_h,
        )

        if not no_color_updates:
            # Detect parent background
            parent_bg = self._apply_appearance_mode(self._detect_color_of_master())

            # Compute frosted fill: tint blended onto parent bg
            tint = self._apply_appearance_mode(self._tint_color)
            frost_fill = self._blend(parent_bg, tint, self._tint_opacity)

            # Compute border: border color blended onto parent bg
            border_c = self._apply_appearance_mode(self._border_color)
            frost_border = self._blend(parent_bg, border_c, self._border_opacity)

            # Draw the rounded rectangle
            requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(
                scaled_w, scaled_h, scaled_cr, scaled_bw
            )

            if requires_recoloring or not no_color_updates:
                self._canvas.configure(bg=parent_bg)
                self._canvas.itemconfig("inner_parts", fill=frost_fill, outline=frost_fill)
                if self._border_width > 0:
                    self._canvas.itemconfig("border_parts", fill=frost_border, outline=frost_border)

                # Apply stipple noise pattern for texture
                if self._noise:
                    self._canvas.itemconfig("inner_parts", stipple="gray25")
                else:
                    self._canvas.itemconfig("inner_parts", stipple="")

                self._interior.configure(bg=frost_fill)

            # Place interior frame inside the rounded rect
            pad = scaled_cr // 2 + scaled_bw
            if self._interior_window_id is None:
                self._interior_window_id = self._canvas.create_window(
                    pad, pad,
                    window=self._interior,
                    anchor="nw",
                    width=max(1, scaled_w - 2 * pad),
                    height=max(1, scaled_h - 2 * pad),
                    tags="interior",
                )
            else:
                self._canvas.coords(self._interior_window_id, pad, pad)
                self._canvas.itemconfigure(
                    self._interior_window_id,
                    width=max(1, scaled_w - 2 * pad),
                    height=max(1, scaled_h - 2 * pad),
                )

    def _set_appearance_mode(self, mode_string: str) -> None:
        super()._set_appearance_mode(mode_string)
        self._draw()

    def _set_scaling(self, new_widget_scaling, new_spacing_scaling, new_window_scaling) -> None:
        super()._set_scaling(new_widget_scaling, new_spacing_scaling, new_window_scaling)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._draw()

    def _set_dimensions(self, width=None, height=None) -> None:
        super()._set_dimensions(width, height)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._draw()

    # -- Color blending -----------------------------------------------------

    @staticmethod
    def _blend(bg_hex: str, fg_hex: str, alpha: float) -> str:
        """Blend fg onto bg at given alpha (0-1). Returns hex string."""
        try:
            bg = bg_hex.lstrip("#")
            fg = fg_hex.lstrip("#")
            # Handle named colors
            if len(bg) < 6 or len(fg) < 6:
                return fg_hex
            rb, gb, bb = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
            rf, gf, bf = int(fg[0:2], 16), int(fg[2:4], 16), int(fg[4:6], 16)
            r = int(rb + (rf - rb) * alpha)
            g = int(gb + (gf - gb) * alpha)
            b = int(bb + (bf - bb) * alpha)
            return f"#{max(0,min(255,r)):02x}{max(0,min(255,g)):02x}{max(0,min(255,b)):02x}"
        except (ValueError, IndexError):
            return fg_hex

    # -- Configure / cget ---------------------------------------------------

    def configure(self, **kwargs) -> None:
        requires_redraw = False

        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            requires_redraw = True
        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            requires_redraw = True
        if "tint_color" in kwargs:
            self._tint_color = self._check_color_type(kwargs.pop("tint_color"))
            requires_redraw = True
        if "tint_opacity" in kwargs:
            self._tint_opacity = max(0.0, min(1.0, kwargs.pop("tint_opacity")))
            requires_redraw = True
        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"))
            requires_redraw = True
        if "border_opacity" in kwargs:
            self._border_opacity = max(0.0, min(1.0, kwargs.pop("border_opacity")))
            requires_redraw = True
        if "noise" in kwargs:
            self._noise = kwargs.pop("noise")
            requires_redraw = True

        super().configure(**kwargs)

        if requires_redraw:
            self._draw()

    def cget(self, attribute_name: str):
        if attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "fg_color":
            # Return tint_color so child widgets can detect parent background
            return self._tint_color
        elif attribute_name == "border_width":
            return self._border_width
        elif attribute_name == "tint_color":
            return self._tint_color
        elif attribute_name == "tint_opacity":
            return self._tint_opacity
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "border_opacity":
            return self._border_opacity
        elif attribute_name == "noise":
            return self._noise
        else:
            return super().cget(attribute_name)

    def bind(self, sequence=None, command=None, add=True):
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal bindings")
        return self._canvas.bind(sequence, command, add="+")

    def unbind(self, sequence=None, funcid=None):
        if funcid is not None:
            raise ValueError("'funcid' must be None to avoid unbinding internal callbacks")
        self._canvas.unbind(sequence, None)

    def destroy(self) -> None:
        super().destroy()
