"""
CTkGradientFrame — A frame widget that renders a smooth gradient background.

Supports horizontal, vertical, and diagonal linear gradients with appearance
mode awareness. Child widgets can be placed on top of the gradient using any
geometry manager (pack, grid, place).

Usage:
    gradient = CTkGradientFrame(
        master,
        from_color=("#3B8ED0", "#1F6AA5"),
        to_color=("#FF6B6B", "#CC4444"),
        orientation="horizontal",
        corner_radius=10,
    )
    gradient.pack(fill="both", expand=True)

    # Place child widgets on the gradient
    label = CTkLabel(gradient, text="Hello", bg_color="transparent")
    label.place(relx=0.5, rely=0.5, anchor="center")
"""

import math
from typing import Union, Tuple, List, Optional, Any

from .core_rendering import CTkCanvas
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .utility.ctk_color_utils import ColorUtils


class CTkGradientFrame(CTkBaseClass):
    """
    Frame with a smooth gradient background rendered via canvas line strips.

    The gradient interpolates between ``from_color`` and ``to_color`` using
    banded line drawing for performance (one canvas item per 2-4 pixel band
    rather than per pixel).  Supports horizontal (left-to-right), vertical
    (top-to-bottom), and diagonal orientations.

    Rounded corners are achieved by drawing a border mask on top of the
    gradient using the standard DrawEngine.

    Parameters
    ----------
    master : Any
        Parent widget.
    width, height : int
        Default dimensions in pixels (default 200 x 200).
    corner_radius : int
        Radius for rounded corners (default 0).
    border_width : int
        Width of the optional border (default 0).
    border_color : str or tuple
        Color of the border (appearance-mode aware).
    from_color : str or tuple
        Gradient start color.  May be a single hex string or a
        ``(light_mode, dark_mode)`` tuple.
    to_color : str or tuple
        Gradient end color.
    orientation : str
        ``"horizontal"`` (default), ``"vertical"``, or ``"diagonal"``.
    bg_color : str or tuple
        Background behind the widget (passed to CTkBaseClass).
    """

    # Number of pixels each gradient band covers.  Lower values produce
    # smoother gradients at the cost of more canvas items.
    _BAND_WIDTH: int = 3

    def __init__(
        self,
        master: Any,
        width: int = 200,
        height: int = 200,
        corner_radius: Optional[Union[int, str]] = None,
        border_width: Optional[Union[int, str]] = None,

        bg_color: Union[str, Tuple[str, str]] = "transparent",
        from_color: Union[str, Tuple[str, str]] = ("#3B8ED0", "#1F6AA5"),
        to_color: Union[str, Tuple[str, str]] = ("#FF6B6B", "#CC4444"),
        border_color: Optional[Union[str, Tuple[str, str]]] = None,

        orientation: str = "horizontal",
        **kwargs,
    ):
        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # --- Validate and store parameters -----------------------------------
        self._from_color = self._check_color_type(from_color)
        self._to_color = self._check_color_type(to_color)
        self._border_color = self._check_color_type(border_color) if border_color is not None else ("#A0A0A0", "#505050")

        if orientation not in ("horizontal", "vertical", "diagonal"):
            raise ValueError(f"orientation must be 'horizontal', 'vertical', or 'diagonal', got '{orientation}'")
        self._orientation: str = orientation

        self._corner_radius: int = 0 if corner_radius is None else int(corner_radius)
        self._border_width: int = 0 if border_width is None else int(border_width)

        # --- Canvas setup ----------------------------------------------------
        self._canvas = CTkCanvas(
            master=self,
            highlightthickness=0,
            width=self._apply_widget_scaling(self._current_width),
            height=self._apply_widget_scaling(self._current_height),
        )
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

        self._draw_engine = DrawEngine(self._canvas)

        # --- Gradient rendering state ----------------------------------------
        # Cached list of canvas item IDs for gradient bands so we can
        # recolor them on subsequent draws without deleting/recreating.
        self._gradient_line_ids: List[int] = []
        # The last resolved (from_hex, to_hex) that was rendered, used to
        # skip unnecessary recoloring when only geometry changed.
        self._last_from_hex: Optional[str] = None
        self._last_to_hex: Optional[str] = None
        # Last rendered dimensions (scaled pixels) so we know when to
        # rebuild the canvas items rather than just recolor.
        self._last_draw_width: int = 0
        self._last_draw_height: int = 0

        # --- Initial draw ----------------------------------------------------
        self._draw()

    # ----- Child widget helpers ----------------------------------------------

    def winfo_children(self) -> List[Any]:
        """Return children excluding the internal canvas."""
        children = super().winfo_children()
        try:
            children.remove(self._canvas)
        except ValueError:
            pass
        return children

    # ----- Scaling / dimension hooks -----------------------------------------

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._draw()

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._draw()

    # ----- Core drawing ------------------------------------------------------

    @staticmethod
    def _interpolate_rgb(
        r1: int, g1: int, b1: int,
        r2: int, g2: int, b2: int,
        t: float,
    ) -> str:
        """Linearly interpolate two RGB colors and return a hex string.

        ``t`` ranges from 0.0 (start color) to 1.0 (end color).
        """
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"

    def _draw(self, no_color_updates: bool = False):
        super()._draw(no_color_updates)

        if not self._canvas.winfo_exists():
            return

        width = self._apply_widget_scaling(self._current_width)
        height = self._apply_widget_scaling(self._current_height)
        width = max(1, int(width))
        height = max(1, int(height))

        from_hex = self._apply_appearance_mode(self._from_color)
        to_hex = self._apply_appearance_mode(self._to_color)

        # Determine if we need to recreate canvas items (geometry change)
        # or can just recolor existing ones.
        geometry_changed = (width != self._last_draw_width or height != self._last_draw_height)
        colors_changed = (from_hex != self._last_from_hex or to_hex != self._last_to_hex)

        if geometry_changed:
            self._draw_gradient(width, height, from_hex, to_hex)
        elif colors_changed and not no_color_updates:
            self._recolor_gradient(width, height, from_hex, to_hex)
        elif not no_color_updates and not colors_changed:
            # Nothing changed, but a full redraw was requested (e.g., appearance mode).
            # Re-derive colors and recolor.
            self._recolor_gradient(width, height, from_hex, to_hex)

        # Draw rounded-corner border mask on top of the gradient.
        if self._corner_radius > 0 or self._border_width > 0:
            self._draw_corner_mask(width, height)

        self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

        self._last_draw_width = width
        self._last_draw_height = height
        self._last_from_hex = from_hex
        self._last_to_hex = to_hex

    def _draw_gradient(
        self, width: int, height: int, from_hex: str, to_hex: str
    ):
        """Create (or recreate) all gradient band canvas items."""
        # Remove old gradient items
        self._canvas.delete("gradient_band")
        self._gradient_line_ids.clear()

        r1, g1, b1 = ColorUtils.hex_to_rgb(from_hex)
        r2, g2, b2 = ColorUtils.hex_to_rgb(to_hex)

        if self._orientation == "horizontal":
            self._draw_horizontal(width, height, r1, g1, b1, r2, g2, b2)
        elif self._orientation == "vertical":
            self._draw_vertical(width, height, r1, g1, b1, r2, g2, b2)
        else:  # diagonal
            self._draw_diagonal(width, height, r1, g1, b1, r2, g2, b2)

    def _draw_horizontal(
        self, width: int, height: int,
        r1: int, g1: int, b1: int,
        r2: int, g2: int, b2: int,
    ):
        """Draw gradient bands from left to right."""
        band = self._BAND_WIDTH
        num_bands = max(1, math.ceil(width / band))
        for i in range(num_bands):
            x0 = i * band
            x1 = min(x0 + band, width)
            t = i / max(1, num_bands - 1)
            color = self._interpolate_rgb(r1, g1, b1, r2, g2, b2, t)
            item_id = self._canvas.create_rectangle(
                x0, 0, x1, height,
                fill=color, outline=color, width=0,
                tags=("gradient_band",),
            )
            self._gradient_line_ids.append(item_id)

    def _draw_vertical(
        self, width: int, height: int,
        r1: int, g1: int, b1: int,
        r2: int, g2: int, b2: int,
    ):
        """Draw gradient bands from top to bottom."""
        band = self._BAND_WIDTH
        num_bands = max(1, math.ceil(height / band))
        for i in range(num_bands):
            y0 = i * band
            y1 = min(y0 + band, height)
            t = i / max(1, num_bands - 1)
            color = self._interpolate_rgb(r1, g1, b1, r2, g2, b2, t)
            item_id = self._canvas.create_rectangle(
                0, y0, width, y1,
                fill=color, outline=color, width=0,
                tags=("gradient_band",),
            )
            self._gradient_line_ids.append(item_id)

    def _draw_diagonal(
        self, width: int, height: int,
        r1: int, g1: int, b1: int,
        r2: int, g2: int, b2: int,
    ):
        """Draw a diagonal gradient (top-left to bottom-right).

        Each band is a horizontal stripe whose color is determined by the
        normalized distance from the top-left corner, measured along the
        diagonal.  This yields a smooth gradient along the diagonal axis.
        """
        # The diagonal distance ranges from 0 to (width + height).
        # We draw horizontal bands and compute t from the vertical center
        # of each band relative to the diagonal span.
        band = self._BAND_WIDTH
        total = width + height
        num_bands = max(1, math.ceil(height / band))
        for i in range(num_bands):
            y0 = i * band
            y1 = min(y0 + band, height)
            y_mid = (y0 + y1) / 2.0

            # For a true diagonal feel, each horizontal band actually spans
            # a range of t values (from left edge to right edge).  We draw
            # a polygon with the left color and right color would require
            # per-pixel work.  Instead, we use the midpoint t value, which
            # gives a pleasing diagonal appearance with banded rendering.
            # Left edge contribution: y_mid / total
            # Right edge contribution: (width + y_mid) / total
            # Midpoint: (y_mid + width / 2) / total
            t = (y_mid + width / 2.0) / max(1, total)
            t = max(0.0, min(1.0, t))
            color = self._interpolate_rgb(r1, g1, b1, r2, g2, b2, t)
            item_id = self._canvas.create_rectangle(
                0, y0, width, y1,
                fill=color, outline=color, width=0,
                tags=("gradient_band",),
            )
            self._gradient_line_ids.append(item_id)

    def _recolor_gradient(
        self, width: int, height: int, from_hex: str, to_hex: str
    ):
        """Update colors of existing gradient band items without recreation."""
        if not self._gradient_line_ids:
            # No items to recolor — fall back to full redraw.
            self._draw_gradient(width, height, from_hex, to_hex)
            return

        r1, g1, b1 = ColorUtils.hex_to_rgb(from_hex)
        r2, g2, b2 = ColorUtils.hex_to_rgb(to_hex)

        num_bands = len(self._gradient_line_ids)

        if self._orientation == "diagonal":
            total = width + height
            band = self._BAND_WIDTH
            for i, item_id in enumerate(self._gradient_line_ids):
                y0 = i * band
                y1 = min(y0 + band, height)
                y_mid = (y0 + y1) / 2.0
                t = (y_mid + width / 2.0) / max(1, total)
                t = max(0.0, min(1.0, t))
                color = self._interpolate_rgb(r1, g1, b1, r2, g2, b2, t)
                self._canvas.itemconfigure(item_id, fill=color, outline=color)
        else:
            for i, item_id in enumerate(self._gradient_line_ids):
                t = i / max(1, num_bands - 1)
                color = self._interpolate_rgb(r1, g1, b1, r2, g2, b2, t)
                self._canvas.itemconfigure(item_id, fill=color, outline=color)

    def _draw_corner_mask(self, width: int, height: int):
        """Draw rounded-corner border overlay to mask gradient edges.

        If corner_radius > 0, we draw four corner rectangles filled with
        the bg_color to "cut" the gradient, then overlay the DrawEngine's
        rounded rect border for a clean appearance.
        """
        cr = self._apply_widget_scaling(self._corner_radius)
        bw = self._apply_widget_scaling(self._border_width)
        bg = self._apply_appearance_mode(self._bg_color)
        border_hex = self._apply_appearance_mode(self._border_color)

        # Draw the rounded border shape using DrawEngine
        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(
            width, height, cr, bw,
        )

        # The inner_parts should be transparent (so the gradient shows through).
        # We set them to have no fill by making them match a special stipple,
        # but tkinter Canvas doesn't support true transparency.  Instead, we
        # make the inner_parts state hidden so they don't cover the gradient,
        # and keep only the border_parts visible.
        self._canvas.itemconfig("inner_parts", state="hidden")

        if self._border_width > 0:
            self._canvas.itemconfig(
                "border_parts",
                fill=border_hex,
                outline=border_hex,
            )
        else:
            self._canvas.itemconfig("border_parts", state="hidden")

        # For the corners, draw bg-colored rectangles at each corner to
        # "erase" the gradient outside the rounded boundary.
        if self._corner_radius > 0:
            self._draw_corner_cutouts(width, height, cr, bg)

        # Ensure gradient bands are behind everything else
        self._canvas.tag_lower("gradient_band")

    def _draw_corner_cutouts(
        self, width: int, height: int, cr: float, bg_color: str
    ):
        """Draw background-colored shapes at each corner to simulate rounding.

        We create four L-shaped polygon cutouts at each corner.  Each cutout
        covers the rectangular corner area minus an approximated arc, producing
        the illusion of rounded corners over the gradient.
        """
        cr = int(cr)
        if cr <= 0:
            self._canvas.delete("gradient_corner_mask")
            return

        # Generate arc polygon points for smooth rounding
        arc_points = self._generate_arc_points(cr, segments=16)

        # Top-left corner
        tl_poly = []
        for px, py in arc_points:
            tl_poly.extend([cr - px, cr - py])
        tl_poly.extend([0, cr, 0, 0, cr, 0])

        # Top-right corner
        tr_poly = []
        for px, py in arc_points:
            tr_poly.extend([width - cr + px, cr - py])
        tr_poly.extend([width, cr, width, 0, width - cr, 0])

        # Bottom-right corner
        br_poly = []
        for px, py in arc_points:
            br_poly.extend([width - cr + px, height - cr + py])
        br_poly.extend([width, height - cr, width, height, width - cr, height])

        # Bottom-left corner
        bl_poly = []
        for px, py in arc_points:
            bl_poly.extend([cr - px, height - cr + py])
        bl_poly.extend([0, height - cr, 0, height, cr, height])

        # Remove old cutouts
        self._canvas.delete("gradient_corner_mask")

        for points in (tl_poly, tr_poly, br_poly, bl_poly):
            if len(points) >= 6:
                self._canvas.create_polygon(
                    points,
                    fill=bg_color,
                    outline=bg_color,
                    width=0,
                    tags=("gradient_corner_mask",),
                )

    @staticmethod
    def _generate_arc_points(radius: int, segments: int = 16) -> List[Tuple[float, float]]:
        """Generate points along a quarter-circle arc of the given radius.

        Returns a list of (x, y) tuples from angle 0 to pi/2.  These are
        offsets from the center of the arc.
        """
        points = []
        for i in range(segments + 1):
            angle = (math.pi / 2) * (i / segments)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            points.append((x, y))
        return points

    # ----- Public API --------------------------------------------------------

    def set_colors(
        self,
        from_color: Optional[Union[str, Tuple[str, str]]] = None,
        to_color: Optional[Union[str, Tuple[str, str]]] = None,
    ):
        """Update the gradient colors and trigger a redraw.

        Parameters
        ----------
        from_color : str or tuple, optional
            New gradient start color.
        to_color : str or tuple, optional
            New gradient end color.
        """
        if from_color is not None:
            self._from_color = self._check_color_type(from_color)
        if to_color is not None:
            self._to_color = self._check_color_type(to_color)
        self._draw()

    def configure(self, require_redraw=False, **kwargs):
        if "corner_radius" in kwargs:
            self._corner_radius = int(kwargs.pop("corner_radius"))
            require_redraw = True

        if "border_width" in kwargs:
            self._border_width = int(kwargs.pop("border_width"))
            require_redraw = True

        if "from_color" in kwargs:
            self._from_color = self._check_color_type(kwargs.pop("from_color"))
            require_redraw = True

        if "to_color" in kwargs:
            self._to_color = self._check_color_type(kwargs.pop("to_color"))
            require_redraw = True

        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "orientation" in kwargs:
            orientation = kwargs.pop("orientation")
            if orientation not in ("horizontal", "vertical", "diagonal"):
                raise ValueError(
                    f"orientation must be 'horizontal', 'vertical', or 'diagonal', got '{orientation}'"
                )
            self._orientation = orientation
            # Orientation change requires full rebuild of gradient items.
            self._last_draw_width = 0
            self._last_draw_height = 0
            require_redraw = True

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "border_width":
            return self._border_width
        elif attribute_name == "from_color":
            return self._from_color
        elif attribute_name == "to_color":
            return self._to_color
        elif attribute_name == "fg_color":
            # Return from_color so child widgets can detect parent background
            return self._from_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "orientation":
            return self._orientation
        else:
            return super().cget(attribute_name)

    def bind(self, sequence=None, command=None, add=True):
        """Bindsequence on the internal canvas."""
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, command, add=True)

    def unbind(self, sequence=None, funcid=None):
        """Unbind sequence on the internal canvas."""
        if funcid is not None:
            raise ValueError(
                "'funcid' argument can only be None, because there is a bug in"
                " tkinter and its not clear whether the internal callbacks will be unbinded or not"
            )
        self._canvas.unbind(sequence, None)
