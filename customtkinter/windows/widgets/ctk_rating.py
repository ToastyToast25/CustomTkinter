import tkinter
import math
from typing import Union, Tuple, Optional, Callable, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkRating(CTkBaseClass):
    """
    Star rating widget with hover preview and click-to-set.

    Supports half-star precision, read-only mode, customizable star count,
    animated scale-pop on click, and smooth hover transitions.

    Usage:
        rating = CTkRating(parent, max_stars=5, command=print)
        rating.set(3.5)
        value = rating.get()

    Read-only mode:
        rating = CTkRating(parent, state="readonly")
        rating.set(4)
    """

    _DEFAULT_STAR_COLOR = ("#F59E0B", "#FBBF24")       # amber filled
    _DEFAULT_EMPTY_COLOR = ("#D1D5DB", "#4B5563")       # gray empty
    _DEFAULT_HOVER_COLOR = ("#FCD34D", "#FDE68A")        # lighter amber on hover

    def __init__(self,
                 master: Any,
                 max_stars: int = 5,
                 initial_value: float = 0.0,
                 allow_half: bool = True,
                 star_size: int = 28,
                 spacing: int = 4,

                 star_color: Optional[Union[str, Tuple[str, str]]] = None,
                 empty_color: Optional[Union[str, Tuple[str, str]]] = None,
                 hover_color: Optional[Union[str, Tuple[str, str]]] = None,

                 state: str = "normal",
                 command: Optional[Callable] = None,
                 **kwargs):

        self._max_stars = max(1, max_stars)
        self._star_size = star_size
        self._spacing = spacing
        self._allow_half = allow_half
        self._value: float = max(0.0, min(float(initial_value), float(self._max_stars)))
        self._hover_value: Optional[float] = None
        self._state = state
        self._command = command

        # colors
        self._star_color = star_color or self._DEFAULT_STAR_COLOR
        self._empty_color = empty_color or self._DEFAULT_EMPTY_COLOR
        self._hover_color = hover_color or self._DEFAULT_HOVER_COLOR

        # animation state
        self._star_scales = [1.0] * self._max_stars   # per-star scale factor
        self._pop_after_ids = [None] * self._max_stars
        self._pop_step_counts = [0] * self._max_stars

        # calculate dimensions
        total_width = self._max_stars * star_size + (self._max_stars - 1) * spacing + 8
        total_height = star_size + 8

        super().__init__(master=master, width=total_width, height=total_height,
                         bg_color="transparent", **kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(total_width),
                                 height=self._apply_widget_scaling(total_height))
        self._canvas.grid(row=0, column=0, sticky="nswe")
        self._draw_engine = DrawEngine(self._canvas)

        # bindings
        if self._state == "normal":
            self._canvas.bind("<Motion>", self._on_motion)
            self._canvas.bind("<Leave>", self._on_leave)
            self._canvas.bind("<Button-1>", self._on_click)

        self._draw()

    # ── Star shape drawing ────────────────────────────────────────

    def _star_polygon(self, cx: float, cy: float, outer_r: float):
        """Return polygon coordinates for a 5-pointed star centered at (cx, cy)."""
        import math
        points = []
        inner_r = outer_r * 0.42
        for i in range(10):
            angle = math.pi / 2 + i * math.pi / 5
            r = outer_r if i % 2 == 0 else inner_r
            points.append(cx + r * math.cos(angle))
            points.append(cy - r * math.sin(angle))
        return points

    def _draw_star(self, index: int, fill_fraction: float, is_hover: bool = False):
        """Draw a single star at the given index with fill_fraction (0.0, 0.5, or 1.0)."""
        tag = f"star_{index}"
        self._canvas.delete(tag)

        s = self._apply_widget_scaling
        size = self._star_size
        cx = s(4 + index * (size + self._spacing) + size / 2)
        cy = s(4 + size / 2)
        base_r = s(size / 2 - 1)
        r = base_r * self._star_scales[index]  # apply pop scale

        empty_c = self._apply_appearance_mode(self._empty_color)

        if is_hover:
            fill_c = self._apply_appearance_mode(self._hover_color)
        else:
            fill_c = self._apply_appearance_mode(self._star_color)

        points = self._star_polygon(cx, cy, r)

        if fill_fraction >= 1.0:
            # fully filled
            self._canvas.create_polygon(points, fill=fill_c, outline=fill_c, tags=tag)
        elif fill_fraction <= 0.0:
            # empty
            self._canvas.create_polygon(points, fill=empty_c, outline=empty_c, tags=tag)
        else:
            # half star: draw empty background, then clip left half
            self._canvas.create_polygon(points, fill=empty_c, outline=empty_c, tags=tag)
            # draw filled left half using a rectangle clip
            left_x = cx - r
            self._canvas.create_rectangle(
                left_x, cy - r - 1, cx, cy + r + 1,
                fill=fill_c, outline=fill_c, tags=(tag, f"star_clip_{index}"),
                stipple=""
            )
            # redraw filled star but clipped via overlaying
            clip_points = self._star_polygon(cx, cy, r)
            self._canvas.create_polygon(clip_points, fill=fill_c, outline=fill_c, tags=(tag, f"star_fill_{index}"))
            # mask right half with empty color
            self._canvas.create_rectangle(
                cx, cy - r - 1, cx + r + 1, cy + r + 1,
                fill="", outline="", tags=(tag, f"star_mask_bg_{index}")
            )
            # draw the right-half star as empty
            self._canvas.create_polygon(clip_points, fill="", outline="", tags=(tag, f"star_outline_{index}"))
            # Simpler approach: just draw two polygons
            self._canvas.delete(tag)
            # Empty background star
            self._canvas.create_polygon(points, fill=empty_c, outline=empty_c, tags=tag)
            # Filled overlay with clip region
            half_points = []
            for i in range(0, len(points), 2):
                px, py = points[i], points[i + 1]
                if px <= cx:
                    half_points.extend([px, py])
                else:
                    # clip to center line
                    half_points.extend([cx, py])

            if len(half_points) >= 6:
                self._canvas.create_polygon(half_points, fill=fill_c, outline=fill_c, tags=tag)

    # ── Drawing ───────────────────────────────────────────────────

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        bg = self._apply_appearance_mode(self._bg_color)
        self._canvas.configure(bg=bg)

        display_value = self._hover_value if self._hover_value is not None else self._value
        is_hover = self._hover_value is not None

        for i in range(self._max_stars):
            star_num = i + 1
            if display_value >= star_num:
                fill = 1.0
            elif self._allow_half and display_value >= star_num - 0.5:
                fill = 0.5
            else:
                fill = 0.0
            self._draw_star(i, fill, is_hover)

    # ── Mouse interaction ─────────────────────────────────────────

    def _get_star_value(self, x: float) -> float:
        """Convert an x coordinate to a star value."""
        s = self._apply_widget_scaling
        size = self._star_size
        spacing = self._spacing

        for i in range(self._max_stars):
            star_left = s(4 + i * (size + spacing))
            star_right = star_left + s(size)
            star_center = (star_left + star_right) / 2

            if star_left <= x <= star_right:
                if self._allow_half and x < star_center:
                    return i + 0.5
                return float(i + 1)

        # beyond all stars
        if x > s(4 + (self._max_stars - 1) * (size + spacing) + size):
            return float(self._max_stars)
        return 0.0

    def _on_motion(self, event):
        if self._state != "normal":
            return
        new_hover = self._get_star_value(event.x)
        if new_hover != self._hover_value:
            self._hover_value = new_hover
            self._canvas.configure(cursor="hand2")
            self._draw()

    def _on_leave(self, event):
        if self._hover_value is not None:
            self._hover_value = None
            self._canvas.configure(cursor="")
            self._draw()

    def _on_click(self, event):
        if self._state != "normal":
            return
        clicked_value = self._get_star_value(event.x)
        # clicking same value clears the rating
        if clicked_value == self._value:
            self._value = 0.0
        else:
            self._value = clicked_value
        self._hover_value = None
        self._draw()
        # trigger scale-pop animation on filled stars
        for i in range(self._max_stars):
            if i + 1 <= self._value or (self._allow_half and i + 0.5 <= self._value):
                self._start_pop(i, delay=i * 30)
        if self._command is not None:
            self._command(self._value)

    # ── Scale-pop animation ───────────────────────────────────────

    def _start_pop(self, index: int, delay: int = 0):
        """Start a scale-pop animation on a star (grows to 1.25x then bounces back)."""
        if self._pop_after_ids[index] is not None:
            self.after_cancel(self._pop_after_ids[index])
        self._star_scales[index] = 1.0
        self._pop_step_counts[index] = 0
        if delay > 0:
            self._pop_after_ids[index] = self.after(delay, lambda: self._pop_tick(index))
        else:
            self._pop_tick(index)

    def _pop_tick(self, index: int):
        """One frame of the pop animation using spring-like ease."""
        total_frames = 12
        step = self._pop_step_counts[index]
        if step > total_frames:
            self._star_scales[index] = 1.0
            self._pop_after_ids[index] = None
            self._draw_star_at(index)
            return

        t = step / total_frames
        # overshoot spring: peaks at ~1.28 then settles to 1.0
        scale = 1.0 + 0.28 * math.sin(t * math.pi) * (1.0 - t * 0.3)
        self._star_scales[index] = scale
        self._pop_step_counts[index] += 1
        self._draw_star_at(index)
        self._pop_after_ids[index] = self.after(16, lambda: self._pop_tick(index))

    def _draw_star_at(self, index: int):
        """Redraw a single star with its current animation scale."""
        display_value = self._hover_value if self._hover_value is not None else self._value
        is_hover = self._hover_value is not None
        star_num = index + 1
        if display_value >= star_num:
            fill = 1.0
        elif self._allow_half and display_value >= star_num - 0.5:
            fill = 0.5
        else:
            fill = 0.0
        self._draw_star(index, fill, is_hover)

    # ── Public API ────────────────────────────────────────────────

    def get(self) -> float:
        """Return the current rating value."""
        return self._value

    def set(self, value: float):
        """Set the rating value programmatically."""
        self._value = max(0.0, min(float(value), float(self._max_stars)))
        self._draw()

    # ── Scaling ───────────────────────────────────────────────────

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    # ── Configure / cget ──────────────────────────────────────────

    def configure(self, **kwargs):
        require_redraw = False
        if "max_stars" in kwargs:
            self._max_stars = max(1, kwargs.pop("max_stars"))
            require_redraw = True
        if "star_color" in kwargs:
            self._star_color = kwargs.pop("star_color")
            require_redraw = True
        if "empty_color" in kwargs:
            self._empty_color = kwargs.pop("empty_color")
            require_redraw = True
        if "hover_color" in kwargs:
            self._hover_color = kwargs.pop("hover_color")
            require_redraw = True
        if "allow_half" in kwargs:
            self._allow_half = kwargs.pop("allow_half")
            require_redraw = True
        if "state" in kwargs:
            self._state = kwargs.pop("state")
            if self._state == "normal":
                self._canvas.bind("<Motion>", self._on_motion)
                self._canvas.bind("<Leave>", self._on_leave)
                self._canvas.bind("<Button-1>", self._on_click)
            else:
                self._canvas.unbind("<Motion>")
                self._canvas.unbind("<Leave>")
                self._canvas.unbind("<Button-1>")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if require_redraw:
            self._draw()
        super().configure(**kwargs)

    def destroy(self):
        for aid in self._pop_after_ids:
            if aid is not None:
                self.after_cancel(aid)
        super().destroy()

    def cget(self, attribute_name: str):
        if attribute_name == "value":
            return self._value
        elif attribute_name == "max_stars":
            return self._max_stars
        elif attribute_name == "star_color":
            return self._star_color
        elif attribute_name == "empty_color":
            return self._empty_color
        elif attribute_name == "hover_color":
            return self._hover_color
        elif attribute_name == "allow_half":
            return self._allow_half
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "command":
            return self._command
        else:
            return super().cget(attribute_name)
