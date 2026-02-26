"""
CTkShadowFrame -- A container frame with a simulated drop shadow effect.

Since tkinter has no native shadow or alpha transparency support, shadows
are simulated by layering multiple tkinter.Frame instances behind the main
content area.  Each layer is colored by blending the shadow color into the
parent background at decreasing opacity, producing a soft gradient that
approximates a Gaussian blur shadow.

Usage:
    shadow_frame = CTkShadowFrame(root, elevation=2)
    ctk.CTkLabel(shadow_frame, text="Hello").pack(padx=20, pady=20)

    # Or with explicit shadow parameters:
    shadow_frame = CTkShadowFrame(
        root,
        shadow_color="#000000",
        shadow_offset_x=0,
        shadow_offset_y=6,
        shadow_blur=12,
        shadow_opacity=0.20,
    )
"""

import tkinter
from typing import Union, Tuple, List, Optional, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .ctk_frame import CTkFrame
from .utility.ctk_color_utils import ColorUtils


# Elevation presets: (offset_y, blur, opacity)
_ELEVATION_PRESETS = {
    0: (0, 0, 0.0),
    1: (2, 4, 0.08),
    2: (4, 8, 0.15),
    3: (6, 12, 0.20),
    4: (10, 20, 0.25),
}

# Sentinel to distinguish "not provided" from explicit values
_UNSET = object()


class CTkShadowFrame(CTkBaseClass):
    """
    Frame with rounded corners, optional border, and a simulated drop shadow.

    The shadow is rendered by placing multiple colored tkinter.Frame layers
    behind the main content canvas.  Each layer blends the ``shadow_color``
    into the detected parent background at progressively lower opacity,
    creating a soft penumbra effect.

    Children are packed/gridded/placed directly inside this widget just like
    a normal ``CTkFrame``.

    Parameters
    ----------
    width, height : int
        Widget dimensions in pixels (before scaling).
    corner_radius : int or None
        Radius for the rounded inner frame.  ``None`` uses the theme default.
    fg_color : str or tuple or None
        Foreground (fill) color.  ``None`` auto-detects from the theme.
    bg_color : str or tuple
        Background / parent color.  ``"transparent"`` (default) auto-detects.
    border_width, border_color : int / str or tuple
        Optional border drawn inside the rounded rectangle.
    shadow_color : str
        Base color for the shadow layers (default ``"#000000"``).
    shadow_offset_x, shadow_offset_y : int
        Pixel offset of the shadow center relative to the frame.
    shadow_blur : int
        Number of pixels the shadow extends beyond the frame edges.
        Internally converted to ``blur // 2`` discrete layers (clamped 0-20).
    shadow_opacity : float
        Peak opacity of the innermost shadow layer (0.0-1.0).
    elevation : int (0-4)
        Convenience preset that sets offset_y, blur, and opacity.
        Explicit shadow_* parameters override the preset.
    """

    def __init__(
        self,
        master: Any,
        width: int = 200,
        height: int = 200,
        corner_radius: Optional[Union[int, str]] = None,
        border_width: Optional[Union[int, str]] = None,

        bg_color: Union[str, Tuple[str, str]] = "transparent",
        fg_color: Optional[Union[str, Tuple[str, str]]] = None,
        border_color: Optional[Union[str, Tuple[str, str]]] = None,

        background_corner_colors: Union[Tuple[Union[str, Tuple[str, str]]], None] = None,
        overwrite_preferred_drawing_method: Union[str, None] = None,

        shadow_color: str = "#000000",
        shadow_offset_x: Any = _UNSET,
        shadow_offset_y: Any = _UNSET,
        shadow_blur: Any = _UNSET,
        shadow_opacity: Any = _UNSET,
        elevation: int = 2,
        **kwargs,
    ):
        # --- resolve elevation preset vs explicit shadow params ---------------
        elevation = max(0, min(4, int(elevation)))
        preset_oy, preset_blur, preset_opacity = _ELEVATION_PRESETS[elevation]

        self._shadow_color: str = shadow_color
        self._shadow_offset_x: int = (
            int(shadow_offset_x) if shadow_offset_x is not _UNSET else 0
        )
        self._shadow_offset_y: int = (
            int(shadow_offset_y) if shadow_offset_y is not _UNSET else preset_oy
        )
        self._shadow_blur: int = max(
            0, min(20, int(shadow_blur) if shadow_blur is not _UNSET else preset_blur)
        )
        self._shadow_opacity: float = max(
            0.0,
            min(1.0, float(shadow_opacity) if shadow_opacity is not _UNSET else preset_opacity),
        )
        self._elevation: int = elevation

        # Track which shadow params were explicitly supplied so that a later
        # elevation change does not overwrite them.
        self._explicit_shadow_offset_x: bool = shadow_offset_x is not _UNSET
        self._explicit_shadow_offset_y: bool = shadow_offset_y is not _UNSET
        self._explicit_shadow_blur: bool = shadow_blur is not _UNSET
        self._explicit_shadow_opacity: bool = shadow_opacity is not _UNSET

        # --- base class init (sets _bg_color, scaling, appearance mode) -------
        super().__init__(
            master=master, bg_color=bg_color, width=width, height=height, **kwargs
        )

        # --- colors -----------------------------------------------------------
        self._border_color = (
            ThemeManager.theme["CTkFrame"]["border_color"]
            if border_color is None
            else self._check_color_type(border_color)
        )

        # Determine fg_color using the same logic as CTkFrame
        if fg_color is None:
            if isinstance(self.master, CTkFrame):
                if self.master._fg_color == ThemeManager.theme["CTkFrame"]["fg_color"]:
                    self._fg_color = ThemeManager.theme["CTkFrame"]["top_fg_color"]
                else:
                    self._fg_color = ThemeManager.theme["CTkFrame"]["fg_color"]
            else:
                self._fg_color = ThemeManager.theme["CTkFrame"]["fg_color"]
        else:
            self._fg_color = self._check_color_type(fg_color, transparency=True)

        self._background_corner_colors = background_corner_colors
        self._overwrite_preferred_drawing_method = overwrite_preferred_drawing_method

        # --- shape ------------------------------------------------------------
        self._corner_radius = (
            ThemeManager.theme["CTkFrame"]["corner_radius"]
            if corner_radius is None
            else corner_radius
        )
        self._border_width = (
            ThemeManager.theme["CTkFrame"]["border_width"]
            if border_width is None
            else border_width
        )

        # --- shadow layers (tkinter.Frame instances) --------------------------
        self._shadow_layers: List[tkinter.Frame] = []

        # --- main rendering canvas (same pattern as CTkFrame) -----------------
        self._canvas = CTkCanvas(
            master=self,
            highlightthickness=0,
            width=self._apply_widget_scaling(self._current_width),
            height=self._apply_widget_scaling(self._current_height),
        )
        self._draw_engine = DrawEngine(self._canvas)

        # Build shadow layers and position everything
        self._build_shadow_layers()

        self._draw(no_color_updates=True)

    # ------------------------------------------------------------------
    #  Shadow layer management
    # ------------------------------------------------------------------

    def _resolve_parent_bg(self) -> str:
        """Return a single hex color string for the current-mode parent background."""
        bg = self._bg_color
        resolved = self._apply_appearance_mode(bg)

        # The resolved value might be a tkinter named color; convert to hex.
        if not resolved.startswith("#"):
            try:
                r, g, b = self.winfo_rgb(resolved)
                resolved = f"#{r >> 8:02x}{g >> 8:02x}{b >> 8:02x}"
            except Exception:
                resolved = "#ffffff"

        # Normalize 3-char shorthand (#abc -> #aabbcc)
        if len(resolved) == 4:
            resolved = (
                "#" + resolved[1] * 2 + resolved[2] * 2 + resolved[3] * 2
            )

        return resolved

    def _compute_num_layers(self) -> int:
        """Derive the number of discrete shadow layers from the blur radius."""
        if self._shadow_blur <= 0 or self._shadow_opacity <= 0.0:
            return 0
        return max(3, min(self._shadow_blur // 2, 10))

    def _build_shadow_layers(self):
        """Create (or recreate) the shadow-layer frames and position them + canvas."""
        self._destroy_shadow_layers()

        parent_bg = self._resolve_parent_bg()
        num_layers = self._compute_num_layers()

        if num_layers > 0:
            for i in range(num_layers):
                # Layer 0 = outermost (lightest), layer num_layers-1 = innermost (darkest)
                layer_opacity = self._shadow_opacity * ((i + 1) / num_layers)
                layer_color = ColorUtils.with_alpha(
                    self._shadow_color, layer_opacity, parent_bg
                )
                frame = tkinter.Frame(
                    self, bg=layer_color, highlightthickness=0, bd=0
                )
                self._shadow_layers.append(frame)

        self._place_shadow_layers()

    def _place_shadow_layers(self):
        """Position all shadow-layer frames and the main canvas using place()."""
        num_layers = len(self._shadow_layers)

        for i, frame in enumerate(self._shadow_layers):
            # reverse_index: outermost layer gets the largest spread
            reverse_index = num_layers - i

            # Each layer extends by spread pixels beyond the main frame on each side.
            spread = self._apply_widget_scaling(reverse_index * 2)

            # Offset is proportional: outermost gets full offset, innermost gets least.
            fraction = reverse_index / num_layers if num_layers > 0 else 0.0
            offset_x = self._apply_widget_scaling(self._shadow_offset_x) * fraction
            offset_y = self._apply_widget_scaling(self._shadow_offset_y) * fraction

            frame.place(
                x=offset_x - spread / 2,
                y=offset_y - spread / 2,
                relwidth=1.0,
                relheight=1.0,
                width=spread,
                height=spread,
            )
            # Push this layer behind all previously placed layers so that the
            # outermost (lightest) sits at the very bottom of the stacking order.
            frame.lower()

        # Main canvas always on top of all shadow layers
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

    def _destroy_shadow_layers(self):
        """Destroy all existing shadow-layer frames."""
        for frame in self._shadow_layers:
            try:
                frame.place_forget()
                frame.destroy()
            except Exception:
                pass
        self._shadow_layers.clear()

    def _recolor_shadow_layers(self):
        """Recompute shadow-layer colors in-place (no destroy/recreate)."""
        parent_bg = self._resolve_parent_bg()
        num_layers = len(self._shadow_layers)

        if num_layers == 0:
            return

        for i, frame in enumerate(self._shadow_layers):
            layer_opacity = self._shadow_opacity * ((i + 1) / num_layers)
            layer_color = ColorUtils.with_alpha(
                self._shadow_color, layer_opacity, parent_bg
            )
            try:
                frame.configure(bg=layer_color)
            except Exception:
                pass

    # ------------------------------------------------------------------
    #  winfo_children -- hide internal layers and canvas
    # ------------------------------------------------------------------

    def winfo_children(self) -> list:
        """Return children excluding the internal canvas and shadow layers."""
        child_widgets = super().winfo_children()
        internal = set(self._shadow_layers)
        internal.add(self._canvas)
        return [w for w in child_widgets if w not in internal]

    # ------------------------------------------------------------------
    #  Scaling
    # ------------------------------------------------------------------

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)

        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._place_shadow_layers()
        self._draw()

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)

        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._place_shadow_layers()
        self._draw()

    # ------------------------------------------------------------------
    #  Drawing (same pattern as CTkFrame)
    # ------------------------------------------------------------------

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        if not self._canvas.winfo_exists():
            return

        if self._background_corner_colors is not None:
            self._draw_engine.draw_background_corners(
                self._apply_widget_scaling(self._current_width),
                self._apply_widget_scaling(self._current_height),
            )
            self._canvas.itemconfig(
                "background_corner_top_left",
                fill=self._apply_appearance_mode(self._background_corner_colors[0]),
            )
            self._canvas.itemconfig(
                "background_corner_top_right",
                fill=self._apply_appearance_mode(self._background_corner_colors[1]),
            )
            self._canvas.itemconfig(
                "background_corner_bottom_right",
                fill=self._apply_appearance_mode(self._background_corner_colors[2]),
            )
            self._canvas.itemconfig(
                "background_corner_bottom_left",
                fill=self._apply_appearance_mode(self._background_corner_colors[3]),
            )
        else:
            self._canvas.delete("background_parts")

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(
            self._apply_widget_scaling(self._current_width),
            self._apply_widget_scaling(self._current_height),
            self._apply_widget_scaling(self._corner_radius),
            self._apply_widget_scaling(self._border_width),
            overwrite_preferred_drawing_method=self._overwrite_preferred_drawing_method,
        )

        if no_color_updates is False or requires_recoloring:
            if self._fg_color == "transparent":
                self._canvas.itemconfig(
                    "inner_parts",
                    fill=self._apply_appearance_mode(self._bg_color),
                    outline=self._apply_appearance_mode(self._bg_color),
                )
            else:
                self._canvas.itemconfig(
                    "inner_parts",
                    fill=self._apply_appearance_mode(self._fg_color),
                    outline=self._apply_appearance_mode(self._fg_color),
                )

            self._canvas.itemconfig(
                "border_parts",
                fill=self._apply_appearance_mode(self._border_color),
                outline=self._apply_appearance_mode(self._border_color),
            )
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

    # ------------------------------------------------------------------
    #  Appearance mode changes
    # ------------------------------------------------------------------

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
        # Shadow colors depend on the parent bg which changes with appearance mode
        self._recolor_shadow_layers()

    # ------------------------------------------------------------------
    #  configure / cget
    # ------------------------------------------------------------------

    def configure(self, require_redraw=False, **kwargs):
        rebuild_shadow = False

        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(
                kwargs.pop("fg_color"), transparency=True
            )
            require_redraw = True

            # Propagate new bg_color to CTk children (same as CTkFrame)
            for child in self.winfo_children():
                if isinstance(child, CTkBaseClass):
                    child.configure(bg_color=self._fg_color)

        if "bg_color" in kwargs:
            # If fg is transparent, propagate bg change to children
            if self._fg_color == "transparent":
                for child in self.winfo_children():
                    if isinstance(child, CTkBaseClass):
                        child.configure(bg_color=self._fg_color)
            rebuild_shadow = True  # bg change affects shadow blend target

        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "background_corner_colors" in kwargs:
            self._background_corner_colors = kwargs.pop("background_corner_colors")
            require_redraw = True

        # --- shadow parameters ------------------------------------------------
        if "shadow_color" in kwargs:
            self._shadow_color = kwargs.pop("shadow_color")
            rebuild_shadow = True

        if "shadow_offset_x" in kwargs:
            self._shadow_offset_x = int(kwargs.pop("shadow_offset_x"))
            self._explicit_shadow_offset_x = True
            rebuild_shadow = True

        if "shadow_offset_y" in kwargs:
            self._shadow_offset_y = int(kwargs.pop("shadow_offset_y"))
            self._explicit_shadow_offset_y = True
            rebuild_shadow = True

        if "shadow_blur" in kwargs:
            self._shadow_blur = max(0, min(20, int(kwargs.pop("shadow_blur"))))
            self._explicit_shadow_blur = True
            rebuild_shadow = True

        if "shadow_opacity" in kwargs:
            self._shadow_opacity = max(
                0.0, min(1.0, float(kwargs.pop("shadow_opacity")))
            )
            self._explicit_shadow_opacity = True
            rebuild_shadow = True

        if "elevation" in kwargs:
            self._elevation = max(0, min(4, int(kwargs.pop("elevation"))))
            preset_oy, preset_blur, preset_opacity = _ELEVATION_PRESETS[
                self._elevation
            ]
            # Only apply preset values for params that were NOT explicitly set
            if not self._explicit_shadow_offset_x:
                self._shadow_offset_x = 0
            if not self._explicit_shadow_offset_y:
                self._shadow_offset_y = preset_oy
            if not self._explicit_shadow_blur:
                self._shadow_blur = preset_blur
            if not self._explicit_shadow_opacity:
                self._shadow_opacity = preset_opacity
            rebuild_shadow = True

        if rebuild_shadow:
            self._build_shadow_layers()
            require_redraw = True

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> any:
        if attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "border_width":
            return self._border_width
        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "background_corner_colors":
            return self._background_corner_colors
        elif attribute_name == "shadow_color":
            return self._shadow_color
        elif attribute_name == "shadow_offset_x":
            return self._shadow_offset_x
        elif attribute_name == "shadow_offset_y":
            return self._shadow_offset_y
        elif attribute_name == "shadow_blur":
            return self._shadow_blur
        elif attribute_name == "shadow_opacity":
            return self._shadow_opacity
        elif attribute_name == "elevation":
            return self._elevation
        else:
            return super().cget(attribute_name)

    # ------------------------------------------------------------------
    #  Bind / unbind (delegate to canvas, same as CTkFrame)
    # ------------------------------------------------------------------

    def bind(self, sequence=None, command=None, add=True):
        """Bind an event on the internal canvas."""
        if not (add == "+" or add is True):
            raise ValueError(
                "'add' argument can only be '+' or True to preserve internal callbacks"
            )
        self._canvas.bind(sequence, command, add=True)

    def unbind(self, sequence=None, funcid=None):
        """Unbind an event from the internal canvas."""
        if funcid is not None:
            raise ValueError(
                "'funcid' argument can only be None, because there is a bug in"
                " tkinter and its not clear whether the internal callbacks"
                " will be unbinded or not"
            )
        self._canvas.unbind(sequence, None)

    # ------------------------------------------------------------------
    #  Lifecycle
    # ------------------------------------------------------------------

    def destroy(self):
        """Clean up shadow layers before destroying the widget tree."""
        self._destroy_shadow_layers()
        super().destroy()
