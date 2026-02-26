import tkinter
import math
from typing import Union, Tuple, Optional, Callable, Any, List

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkGauge(CTkBaseClass):
    """
    Visual gauge/meter widget (speedometer style) with arc-based rendering.
    Displays a value on a semi-circular or configurable arc with optional
    color zones, needle indicator, and animated transitions.

    The value is normalized between 0.0 and 1.0 internally, but can be
    mapped to arbitrary min_value/max_value labels for display.

    Usage:
        gauge = CTkGauge(parent, width=250, height=200)
        gauge.set(0.75)

        # With color zones
        gauge = CTkGauge(parent, zones=[
            (0.0, 0.6, "#2ecc71"),
            (0.6, 0.8, "#f1c40f"),
            (0.8, 1.0, "#e74c3c"),
        ])
        gauge.set(0.85, animate=True)

        # With variable binding
        var = tkinter.DoubleVar(value=0.5)
        gauge = CTkGauge(parent, variable=var)
    """

    def __init__(self,
                 master: Any,
                 width: int = 250,
                 height: int = 200,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 track_color: Optional[Union[str, Tuple[str, str]]] = None,
                 progress_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 needle_color: Optional[Union[str, Tuple[str, str]]] = None,
                 label_color: Optional[Union[str, Tuple[str, str]]] = None,

                 line_width: int = 12,
                 start_angle: float = 210,
                 sweep_angle: float = 240,

                 min_value: float = 0,
                 max_value: float = 100,
                 value_format: str = "{:.0f}",

                 show_value: bool = True,
                 show_needle: bool = True,
                 show_min_max: bool = True,
                 label: Optional[str] = None,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 label_font: Optional[Union[tuple, CTkFont]] = None,
                 min_max_font: Optional[Union[tuple, CTkFont]] = None,

                 zones: Optional[List[Tuple[float, float, str]]] = None,
                 variable: Optional[tkinter.Variable] = None,
                 **kwargs):

        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # dimensions
        self._gauge_width = width
        self._gauge_height = height

        # arc geometry (in tkinter's degree system)
        self._start_angle = start_angle
        self._sweep_angle = sweep_angle
        self._line_width = line_width

        # value state
        self._value: float = 0.0  # normalized 0.0 - 1.0
        self._min_value = min_value
        self._max_value = max_value
        self._value_format = value_format

        # colors
        self._fg_color = fg_color or ThemeManager.theme["CTk"]["fg_color"]
        self._track_color = track_color or ("#d0d0d0", "#404040")
        self._progress_color = progress_color or ThemeManager.theme["CTkProgressBar"]["progress_color"]
        self._text_color = text_color or ThemeManager.theme["CTkLabel"]["text_color"]
        self._needle_color = needle_color or ThemeManager.theme["CTkLabel"]["text_color"]
        self._label_color = label_color or ThemeManager.theme["CTkLabel"]["text_color"]

        # display options
        self._show_value = show_value
        self._show_needle = show_needle
        self._show_min_max = show_min_max
        self._label_text = label

        # fonts
        self._font = font or CTkFont(size=max(12, width // 8), weight="bold")
        self._label_font = label_font or CTkFont(size=max(10, width // 14))
        self._min_max_font = min_max_font or CTkFont(size=max(9, width // 18))

        # zones: list of (start_pct, end_pct, color_hex)
        self._zones: Optional[List[Tuple[float, float, str]]] = zones

        # variable binding
        self._variable = variable
        self._variable_callback_name = None
        self._variable_callback_blocked = False

        # animation state
        self._target_value: float = 0.0
        self._anim_after_id = None

        # canvas item IDs (created on first draw)
        self._track_id = None
        self._progress_id = None
        self._needle_id = None
        self._value_text_id = None
        self._label_text_id = None
        self._min_text_id = None
        self._max_text_id = None
        self._zone_ids: List[int] = []

        # build canvas
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._gauge_width),
                                 height=self._apply_widget_scaling(self._gauge_height))
        self._canvas.grid(row=0, column=0, sticky="nswe")

        self._draw()

        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._variable_callback_blocked = True
            self._set_value_from_variable(self._variable.get())
            self._variable_callback_blocked = False

    # -------------------------------------------------------------------
    # Geometry helpers
    # -------------------------------------------------------------------

    def _get_arc_bbox(self, scaled):
        """Calculate the bounding box for the gauge arc, centered in the canvas."""
        w = scaled(self._gauge_width)
        h = scaled(self._gauge_height)
        lw = max(1, scaled(self._line_width))
        pad = lw / 2 + scaled(4)

        # The arc is inscribed in a square; fit the largest square in the canvas
        arc_size = min(w - 2 * pad, (h - pad) * 2)
        # For arcs that are less than a full semicircle, the vertical space needed
        # is less than a full circle's height, so we center horizontally
        cx = w / 2
        # Position the arc so the bottom of the semicircle sits near the bottom
        # of the canvas, leaving room for labels below
        label_reserve = scaled(30) if (self._label_text or self._show_min_max) else scaled(8)
        top = h - label_reserve - arc_size / 2 - pad
        top = max(pad, top)

        x0 = cx - arc_size / 2
        y0 = top
        x1 = cx + arc_size / 2
        y1 = top + arc_size

        return x0, y0, x1, y1, cx, lw

    def _value_to_angle(self, value: float) -> float:
        """Convert a normalized value (0.0-1.0) to a tkinter canvas arc angle (degrees).

        tkinter arcs: 0 degrees = 3 o'clock, angles increase counter-clockwise.
        The gauge sweeps from start_angle by -sweep_angle (clockwise).
        value=0.0 maps to start_angle, value=1.0 maps to start_angle - sweep_angle.
        """
        return self._start_angle - value * self._sweep_angle

    def _angle_to_xy(self, angle_deg: float, cx: float, cy: float, radius: float):
        """Convert a tkinter-style angle (degrees, CCW from east) to canvas (x, y)."""
        rad = math.radians(angle_deg)
        x = cx + radius * math.cos(rad)
        y = cy - radius * math.sin(rad)  # canvas y is inverted
        return x, y

    # -------------------------------------------------------------------
    # Font helper
    # -------------------------------------------------------------------

    def _get_scaled_font(self, font, scaled):
        """Get a font tuple with scaling applied."""
        if isinstance(font, CTkFont):
            return (font.cget("family"), int(scaled(font.cget("size"))), font.cget("weight"))
        elif isinstance(font, tuple) and len(font) >= 2:
            return (font[0], int(scaled(font[1]))) + font[2:]
        return font

    # -------------------------------------------------------------------
    # Display value
    # -------------------------------------------------------------------

    def _get_display_value(self) -> str:
        """Format the current value mapped to [min_value, max_value]."""
        mapped = self._min_value + self._value * (self._max_value - self._min_value)
        try:
            return self._value_format.format(mapped)
        except (ValueError, KeyError):
            return f"{mapped:.0f}"

    # -------------------------------------------------------------------
    # Drawing
    # -------------------------------------------------------------------

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        scaled = self._apply_widget_scaling
        x0, y0, x1, y1, cx, lw = self._get_arc_bbox(scaled)
        cy = (y0 + y1) / 2  # center of the arc circle
        radius = (x1 - x0) / 2

        bg = self._apply_appearance_mode(self._bg_color)
        fg = self._apply_appearance_mode(self._fg_color)
        track_c = self._apply_appearance_mode(self._track_color)
        progress_c = self._apply_appearance_mode(self._progress_color)
        text_c = self._apply_appearance_mode(self._text_color)
        needle_c = self._apply_appearance_mode(self._needle_color)
        label_c = self._apply_appearance_mode(self._label_color)

        # Progress arc extent: fills clockwise from start_angle
        progress_extent = -(self._value * self._sweep_angle)

        if self._track_id is None:
            # -----------------------------------------------------------
            # First draw: create all canvas items
            # -----------------------------------------------------------
            canvas_bg = bg if bg != "transparent" else fg
            self._canvas.configure(bg=canvas_bg)

            # Track arc (full sweep background)
            self._track_id = self._canvas.create_arc(
                x0, y0, x1, y1,
                start=self._start_angle,
                extent=-self._sweep_angle,
                style="arc", width=lw,
                outline=track_c
            )

            # Zone arcs (drawn on top of track, under progress)
            self._draw_zones_create(x0, y0, x1, y1, lw)

            # Progress arc (filled portion)
            self._progress_id = self._canvas.create_arc(
                x0, y0, x1, y1,
                start=self._start_angle,
                extent=progress_extent,
                style="arc", width=lw,
                outline=progress_c
            )

            # Needle
            if self._show_needle:
                nx, ny = self._get_needle_coords(cx, cy, radius, lw)
                self._needle_id = self._canvas.create_line(
                    cx, cy, nx, ny,
                    fill=needle_c, width=max(1, lw // 4), capstyle="round"
                )

            # Center value text
            if self._show_value:
                value_font = self._get_scaled_font(self._font, scaled)
                text_y = cy + scaled(4)
                self._value_text_id = self._canvas.create_text(
                    cx, text_y,
                    text=self._get_display_value(),
                    fill=text_c, font=value_font, anchor="center"
                )

            # Label text (below value)
            if self._label_text:
                label_font = self._get_scaled_font(self._label_font, scaled)
                label_y = cy + scaled(20)
                if self._show_value:
                    label_y = cy + scaled(22)
                self._label_text_id = self._canvas.create_text(
                    cx, label_y,
                    text=self._label_text,
                    fill=label_c, font=label_font, anchor="center"
                )

            # Min / Max labels at arc endpoints
            if self._show_min_max:
                mm_font = self._get_scaled_font(self._min_max_font, scaled)
                min_x, min_y = self._angle_to_xy(self._start_angle, cx, cy, radius + lw / 2 + scaled(10))
                max_x, max_y = self._angle_to_xy(self._start_angle - self._sweep_angle, cx, cy, radius + lw / 2 + scaled(10))

                min_text = self._value_format.format(self._min_value)
                max_text = self._value_format.format(self._max_value)

                self._min_text_id = self._canvas.create_text(
                    min_x, min_y,
                    text=min_text, fill=label_c, font=mm_font, anchor="center"
                )
                self._max_text_id = self._canvas.create_text(
                    max_x, max_y,
                    text=max_text, fill=label_c, font=mm_font, anchor="center"
                )
        else:
            # -----------------------------------------------------------
            # Subsequent draws: update existing items in place
            # -----------------------------------------------------------
            if not no_color_updates:
                canvas_bg = bg if bg != "transparent" else fg
                self._canvas.configure(bg=canvas_bg)

            # Track
            self._canvas.coords(self._track_id, x0, y0, x1, y1)
            self._canvas.itemconfigure(self._track_id,
                                       start=self._start_angle,
                                       extent=-self._sweep_angle,
                                       width=lw)
            if not no_color_updates:
                self._canvas.itemconfigure(self._track_id, outline=track_c)

            # Zone arcs
            self._draw_zones_update(x0, y0, x1, y1, lw, no_color_updates)

            # Progress arc
            self._canvas.coords(self._progress_id, x0, y0, x1, y1)
            self._canvas.itemconfigure(self._progress_id,
                                       start=self._start_angle,
                                       extent=progress_extent,
                                       width=lw)
            if not no_color_updates:
                if self._zones:
                    # When zones are active, color the progress arc to match
                    # the zone at the current value position
                    zone_color = self._get_zone_color_at(self._value)
                    self._canvas.itemconfigure(self._progress_id, outline=zone_color)
                else:
                    self._canvas.itemconfigure(self._progress_id, outline=progress_c)

            # Needle
            if self._show_needle and self._needle_id is not None:
                nx, ny = self._get_needle_coords(cx, cy, radius, lw)
                self._canvas.coords(self._needle_id, cx, cy, nx, ny)
                self._canvas.itemconfigure(self._needle_id, width=max(1, lw // 4))
                if not no_color_updates:
                    self._canvas.itemconfigure(self._needle_id, fill=needle_c)

            # Value text
            if self._show_value and self._value_text_id is not None:
                value_font = self._get_scaled_font(self._font, scaled)
                text_y = cy + scaled(4)
                self._canvas.coords(self._value_text_id, cx, text_y)
                self._canvas.itemconfigure(self._value_text_id,
                                           text=self._get_display_value(),
                                           font=value_font)
                if not no_color_updates:
                    self._canvas.itemconfigure(self._value_text_id, fill=text_c)
            elif self._show_value and self._value_text_id is None:
                value_font = self._get_scaled_font(self._font, scaled)
                text_y = cy + scaled(4)
                self._value_text_id = self._canvas.create_text(
                    cx, text_y,
                    text=self._get_display_value(),
                    fill=text_c, font=value_font, anchor="center"
                )
            elif not self._show_value and self._value_text_id is not None:
                self._canvas.delete(self._value_text_id)
                self._value_text_id = None

            # Label text
            if self._label_text and self._label_text_id is not None:
                label_font = self._get_scaled_font(self._label_font, scaled)
                label_y = cy + scaled(22) if self._show_value else cy + scaled(20)
                self._canvas.coords(self._label_text_id, cx, label_y)
                self._canvas.itemconfigure(self._label_text_id,
                                           text=self._label_text,
                                           font=label_font)
                if not no_color_updates:
                    self._canvas.itemconfigure(self._label_text_id, fill=label_c)
            elif self._label_text and self._label_text_id is None:
                label_font = self._get_scaled_font(self._label_font, scaled)
                label_y = cy + scaled(22) if self._show_value else cy + scaled(20)
                self._label_text_id = self._canvas.create_text(
                    cx, label_y,
                    text=self._label_text,
                    fill=label_c, font=label_font, anchor="center"
                )
            elif not self._label_text and self._label_text_id is not None:
                self._canvas.delete(self._label_text_id)
                self._label_text_id = None

            # Min/Max labels
            if self._show_min_max and self._min_text_id is not None:
                mm_font = self._get_scaled_font(self._min_max_font, scaled)
                min_x, min_y = self._angle_to_xy(self._start_angle, cx, cy, radius + lw / 2 + scaled(10))
                max_x, max_y = self._angle_to_xy(self._start_angle - self._sweep_angle, cx, cy, radius + lw / 2 + scaled(10))

                min_text = self._value_format.format(self._min_value)
                max_text = self._value_format.format(self._max_value)

                self._canvas.coords(self._min_text_id, min_x, min_y)
                self._canvas.itemconfigure(self._min_text_id, text=min_text, font=mm_font)
                self._canvas.coords(self._max_text_id, max_x, max_y)
                self._canvas.itemconfigure(self._max_text_id, text=max_text, font=mm_font)
                if not no_color_updates:
                    self._canvas.itemconfigure(self._min_text_id, fill=label_c)
                    self._canvas.itemconfigure(self._max_text_id, fill=label_c)
            elif self._show_min_max and self._min_text_id is None:
                mm_font = self._get_scaled_font(self._min_max_font, scaled)
                min_x, min_y = self._angle_to_xy(self._start_angle, cx, cy, radius + lw / 2 + scaled(10))
                max_x, max_y = self._angle_to_xy(self._start_angle - self._sweep_angle, cx, cy, radius + lw / 2 + scaled(10))

                min_text = self._value_format.format(self._min_value)
                max_text = self._value_format.format(self._max_value)

                self._min_text_id = self._canvas.create_text(
                    min_x, min_y, text=min_text, fill=label_c, font=mm_font, anchor="center"
                )
                self._max_text_id = self._canvas.create_text(
                    max_x, max_y, text=max_text, fill=label_c, font=mm_font, anchor="center"
                )
            elif not self._show_min_max and self._min_text_id is not None:
                self._canvas.delete(self._min_text_id)
                self._canvas.delete(self._max_text_id)
                self._min_text_id = None
                self._max_text_id = None

    # -------------------------------------------------------------------
    # Zone rendering
    # -------------------------------------------------------------------

    def _draw_zones_create(self, x0, y0, x1, y1, lw):
        """Create zone arc items on first draw."""
        self._zone_ids.clear()
        if not self._zones:
            return
        for start_pct, end_pct, color in self._zones:
            zone_start = self._start_angle - start_pct * self._sweep_angle
            zone_extent = -(end_pct - start_pct) * self._sweep_angle
            zid = self._canvas.create_arc(
                x0, y0, x1, y1,
                start=zone_start, extent=zone_extent,
                style="arc", width=lw,
                outline=color
            )
            self._zone_ids.append(zid)

    def _draw_zones_update(self, x0, y0, x1, y1, lw, no_color_updates):
        """Update existing zone arc items. Handles zone list changes by rebuilding."""
        expected_count = len(self._zones) if self._zones else 0
        if len(self._zone_ids) != expected_count:
            # Zone count changed: delete old, create new
            for zid in self._zone_ids:
                self._canvas.delete(zid)
            self._zone_ids.clear()
            self._draw_zones_create(x0, y0, x1, y1, lw)
            # Ensure progress arc stays on top of zones
            if self._progress_id is not None:
                self._canvas.tag_raise(self._progress_id)
            if self._needle_id is not None:
                self._canvas.tag_raise(self._needle_id)
            return

        if not self._zones:
            return

        for i, (start_pct, end_pct, color) in enumerate(self._zones):
            zid = self._zone_ids[i]
            zone_start = self._start_angle - start_pct * self._sweep_angle
            zone_extent = -(end_pct - start_pct) * self._sweep_angle
            self._canvas.coords(zid, x0, y0, x1, y1)
            self._canvas.itemconfigure(zid, start=zone_start, extent=zone_extent, width=lw)
            if not no_color_updates:
                self._canvas.itemconfigure(zid, outline=color)

    def _get_zone_color_at(self, value: float) -> str:
        """Return the zone color at the given normalized value, or default progress color."""
        if self._zones:
            for start_pct, end_pct, color in self._zones:
                if start_pct <= value <= end_pct:
                    return color
            # If value doesn't fall in any zone, return the last zone's color if past all zones
            if value >= self._zones[-1][1]:
                return self._zones[-1][2]
        return self._apply_appearance_mode(self._progress_color)

    # -------------------------------------------------------------------
    # Needle
    # -------------------------------------------------------------------

    def _get_needle_coords(self, cx, cy, radius, lw):
        """Get the (x, y) endpoint of the needle for the current value."""
        angle = self._value_to_angle(self._value)
        # Needle extends from center to just inside the arc track
        needle_len = radius - lw / 2 - 2
        nx, ny = self._angle_to_xy(angle, cx, cy, needle_len)
        return nx, ny

    # -------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------

    def set(self, value: float, animate: bool = False, duration: int = 400):
        """Set the gauge value (normalized 0.0 to 1.0).

        Args:
            value: Normalized value between 0.0 and 1.0.
            animate: If True, animate the transition with ease-out cubic.
            duration: Animation duration in milliseconds (default 400).
        """
        value = max(0.0, min(1.0, float(value)))

        if animate and value != self._value:
            self._target_value = value
            self._animate_to(duration)
        else:
            self._cancel_animation()
            self._value = value
            self._target_value = value
            self._draw()

            if self._variable is not None and not self._variable_callback_blocked:
                self._variable_callback_blocked = True
                self._variable.set(self._value)
                self._variable_callback_blocked = False

    def get(self) -> float:
        """Get the current normalized gauge value (0.0 to 1.0)."""
        return self._value

    def set_zones(self, zones: Optional[List[Tuple[float, float, str]]]):
        """Set or clear color zones.

        Args:
            zones: List of (start_pct, end_pct, color_hex) tuples, or None to clear.
                   Percentages are normalized 0.0-1.0.
                   Example: [(0.0, 0.6, "#2ecc71"), (0.6, 0.8, "#f1c40f"), (0.8, 1.0, "#e74c3c")]
        """
        self._zones = zones
        self._draw()

    # -------------------------------------------------------------------
    # Animation
    # -------------------------------------------------------------------

    def _animate_to(self, duration: int):
        """Animate from the current value to the target value with ease-out cubic."""
        self._cancel_animation()

        start_val = self._value
        target = self._target_value
        elapsed = [0]
        interval = 16  # ~60fps

        def tick():
            elapsed[0] += interval
            t = min(1.0, elapsed[0] / duration)
            # ease-out cubic: 1 - (1 - t)^3
            t_eased = 1.0 - (1.0 - t) ** 3
            self._value = start_val + (target - start_val) * t_eased
            self._draw()
            if t < 1.0:
                self._anim_after_id = self.after(interval, tick)
            else:
                self._anim_after_id = None
                # Sync variable at end of animation
                if self._variable is not None and not self._variable_callback_blocked:
                    self._variable_callback_blocked = True
                    self._variable.set(self._value)
                    self._variable_callback_blocked = False

        tick()

    def _cancel_animation(self):
        """Cancel any running animation."""
        if self._anim_after_id is not None:
            self.after_cancel(self._anim_after_id)
            self._anim_after_id = None

    # -------------------------------------------------------------------
    # Variable binding
    # -------------------------------------------------------------------

    def _set_value_from_variable(self, var_value):
        """Map a variable value to normalized 0.0-1.0 and set."""
        try:
            val = float(var_value)
        except (TypeError, ValueError):
            val = 0.0
        val = max(0.0, min(1.0, val))
        self._value = val
        self._target_value = val
        self._draw()

    def _variable_callback(self, var_name, index, mode):
        if not self._variable_callback_blocked:
            self._set_value_from_variable(self._variable.get())

    # -------------------------------------------------------------------
    # Scaling / dimensions
    # -------------------------------------------------------------------

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._gauge_width),
            height=self._apply_widget_scaling(self._gauge_height)
        )
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width=None, height=None):
        if width is not None:
            self._gauge_width = width
        if height is not None:
            self._gauge_height = height
        super()._set_dimensions(width=self._gauge_width, height=self._gauge_height)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._gauge_width),
            height=self._apply_widget_scaling(self._gauge_height)
        )
        # Force full rebuild on size change
        self._canvas.delete("all")
        self._track_id = None
        self._progress_id = None
        self._needle_id = None
        self._value_text_id = None
        self._label_text_id = None
        self._min_text_id = None
        self._max_text_id = None
        self._zone_ids.clear()
        self._draw()

    # -------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------

    def destroy(self):
        self._cancel_animation()
        if self._variable is not None and self._variable_callback_name is not None:
            self._variable.trace_remove("write", self._variable_callback_name)
        super().destroy()

    # -------------------------------------------------------------------
    # configure / cget
    # -------------------------------------------------------------------

    def configure(self, require_redraw=False, **kwargs):
        if "width" in kwargs:
            self._gauge_width = kwargs.pop("width")
            self._set_dimensions(width=self._gauge_width)
        if "height" in kwargs:
            self._gauge_height = kwargs.pop("height")
            self._set_dimensions(height=self._gauge_height)
        if "line_width" in kwargs:
            self._line_width = kwargs.pop("line_width")
            require_redraw = True
        if "start_angle" in kwargs:
            self._start_angle = kwargs.pop("start_angle")
            require_redraw = True
        if "sweep_angle" in kwargs:
            self._sweep_angle = kwargs.pop("sweep_angle")
            require_redraw = True
        if "min_value" in kwargs:
            self._min_value = kwargs.pop("min_value")
            require_redraw = True
        if "max_value" in kwargs:
            self._max_value = kwargs.pop("max_value")
            require_redraw = True
        if "value_format" in kwargs:
            self._value_format = kwargs.pop("value_format")
            require_redraw = True
        if "track_color" in kwargs:
            self._track_color = kwargs.pop("track_color")
            require_redraw = True
        if "progress_color" in kwargs:
            self._progress_color = kwargs.pop("progress_color")
            require_redraw = True
        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            require_redraw = True
        if "needle_color" in kwargs:
            self._needle_color = kwargs.pop("needle_color")
            require_redraw = True
        if "label_color" in kwargs:
            self._label_color = kwargs.pop("label_color")
            require_redraw = True
        if "show_value" in kwargs:
            self._show_value = kwargs.pop("show_value")
            require_redraw = True
        if "show_needle" in kwargs:
            new_show = kwargs.pop("show_needle")
            if new_show != self._show_needle:
                self._show_needle = new_show
                if not self._show_needle and self._needle_id is not None:
                    self._canvas.delete(self._needle_id)
                    self._needle_id = None
                elif self._show_needle and self._needle_id is None:
                    # Will be created on next draw
                    pass
                require_redraw = True
        if "show_min_max" in kwargs:
            self._show_min_max = kwargs.pop("show_min_max")
            require_redraw = True
        if "label" in kwargs:
            self._label_text = kwargs.pop("label")
            require_redraw = True
        if "font" in kwargs:
            self._font = kwargs.pop("font")
            require_redraw = True
        if "label_font" in kwargs:
            self._label_font = kwargs.pop("label_font")
            require_redraw = True
        if "min_max_font" in kwargs:
            self._min_max_font = kwargs.pop("min_max_font")
            require_redraw = True
        if "zones" in kwargs:
            self._zones = kwargs.pop("zones")
            require_redraw = True
        if "variable" in kwargs:
            if self._variable is not None and self._variable_callback_name is not None:
                self._variable.trace_remove("write", self._variable_callback_name)
                self._variable_callback_name = None
            self._variable = kwargs.pop("variable")
            if self._variable is not None:
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
                self._set_value_from_variable(self._variable.get())

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "width":
            return self._gauge_width
        elif attribute_name == "height":
            return self._gauge_height
        elif attribute_name == "line_width":
            return self._line_width
        elif attribute_name == "start_angle":
            return self._start_angle
        elif attribute_name == "sweep_angle":
            return self._sweep_angle
        elif attribute_name == "min_value":
            return self._min_value
        elif attribute_name == "max_value":
            return self._max_value
        elif attribute_name == "value_format":
            return self._value_format
        elif attribute_name == "track_color":
            return self._track_color
        elif attribute_name == "progress_color":
            return self._progress_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "needle_color":
            return self._needle_color
        elif attribute_name == "label_color":
            return self._label_color
        elif attribute_name == "show_value":
            return self._show_value
        elif attribute_name == "show_needle":
            return self._show_needle
        elif attribute_name == "show_min_max":
            return self._show_min_max
        elif attribute_name == "label":
            return self._label_text
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "label_font":
            return self._label_font
        elif attribute_name == "min_max_font":
            return self._min_max_font
        elif attribute_name == "zones":
            return self._zones
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "value":
            return self._value
        else:
            return super().cget(attribute_name)

    # -------------------------------------------------------------------
    # Standard widget bindings
    # -------------------------------------------------------------------

    def bind(self, sequence: str = None, command: Callable = None, add: Union[str, bool] = True):
        """Bind event to the canvas."""
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, command, add=True)

    def unbind(self, sequence: str = None, funcid: str = None):
        """Unbind event from the canvas."""
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in"
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._canvas.unbind(sequence, None)

    def focus(self):
        return self._canvas.focus()

    def focus_set(self):
        return self._canvas.focus_set()

    def focus_force(self):
        return self._canvas.focus_force()
