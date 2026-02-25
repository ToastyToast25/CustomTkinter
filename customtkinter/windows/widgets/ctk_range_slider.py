"""
Dual-thumb range slider for selecting a value range.

Features two draggable thumbs with a colored fill between them,
optional value labels, step snapping, and keyboard navigation.

Usage:
    slider = CTkRangeSlider(parent, from_=0, to=100, command=on_change)
    slider.set(25, 75)
    low, high = slider.get()
"""

import tkinter
import sys
import math
from typing import Union, Tuple, Callable, Optional, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkRangeSlider(CTkBaseClass):
    """
    Dual-thumb range slider with value range selection.

    Two draggable thumbs define a range on a track. The track shows
    a colored fill between the thumbs. Supports step snapping,
    value labels, horizontal/vertical orientation, and keyboard control.
    """

    def __init__(
        self,
        master: Any,
        width: Optional[int] = None,
        height: Optional[int] = None,
        corner_radius: Optional[int] = None,
        button_corner_radius: Optional[int] = None,
        border_width: Optional[int] = None,
        button_length: Optional[int] = None,

        bg_color: Union[str, Tuple[str, str]] = "transparent",
        fg_color: Optional[Union[str, Tuple[str, str]]] = None,
        border_color: Union[str, Tuple[str, str]] = "transparent",
        progress_color: Optional[Union[str, Tuple[str, str]]] = None,
        button_color: Optional[Union[str, Tuple[str, str]]] = None,
        button_hover_color: Optional[Union[str, Tuple[str, str]]] = None,

        from_: float = 0,
        to: float = 1,
        number_of_steps: Optional[int] = None,
        scroll_step: Optional[float] = None,
        orientation: str = "horizontal",

        show_value: bool = False,
        value_font: Optional[Union[tuple, CTkFont]] = None,
        value_color: Optional[Union[str, Tuple[str, str]]] = None,
        value_format: str = "{:.0f}",

        hover: bool = True,
        state: str = "normal",
        command: Optional[Callable] = None,
        **kwargs,
    ):
        # defaults based on orientation
        if width is None:
            width = 16 if orientation.lower() == "vertical" else 200
        if height is None:
            height = 200 if orientation.lower() == "vertical" else 16

        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # colors
        self._fg_color = ThemeManager.theme["CTkSlider"]["fg_color"] if fg_color is None else self._check_color_type(fg_color)
        self._border_color = self._check_color_type(border_color, transparency=True)
        self._progress_color = ThemeManager.theme["CTkSlider"]["progress_color"] if progress_color is None else self._check_color_type(progress_color, transparency=True)
        self._button_color = ThemeManager.theme["CTkSlider"]["button_color"] if button_color is None else self._check_color_type(button_color)
        self._button_hover_color = ThemeManager.theme["CTkSlider"]["button_hover_color"] if button_hover_color is None else self._check_color_type(button_hover_color)

        # shape
        self._corner_radius = ThemeManager.theme["CTkSlider"]["corner_radius"] if corner_radius is None else corner_radius
        self._button_corner_radius = ThemeManager.theme["CTkSlider"]["button_corner_radius"] if button_corner_radius is None else button_corner_radius
        self._border_width = ThemeManager.theme["CTkSlider"]["border_width"] if border_width is None else border_width
        self._button_length = ThemeManager.theme["CTkSlider"]["button_length"] if button_length is None else button_length

        if self._corner_radius < self._button_corner_radius:
            self._corner_radius = self._button_corner_radius

        # range
        self._from_ = from_
        self._to = to
        self._number_of_steps = number_of_steps
        self._scroll_step = (1 / (20 if number_of_steps is None else number_of_steps)) if scroll_step is None else scroll_step
        self._orientation = orientation.lower()

        # values (as fractions 0-1)
        self._low_value: float = 0.25
        self._high_value: float = 0.75

        # value display
        self._show_value = show_value
        self._value_format = value_format
        self._value_color = self._check_color_type(value_color) if value_color is not None else self._button_color
        self._value_font = value_font

        # interaction
        self._hover = hover
        self._state = state
        self._command = command
        self._hover_state: Optional[str] = None  # "low", "high", or None
        self._dragging: Optional[str] = None  # "low", "high", or None
        self._focused_thumb: str = "low"  # for keyboard nav

        # canvas
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = CTkCanvas(
            master=self,
            highlightthickness=0,
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._canvas.grid(column=0, row=0, rowspan=1, columnspan=1, sticky="nswe")
        self._draw_engine = DrawEngine(self._canvas)

        self._create_bindings()
        self._set_cursor()
        self._draw()

    # ── Bindings ──────────────────────────────────────────────

    def _create_bindings(self, sequence: Optional[str] = None):
        if sequence is None or sequence == "<Enter>":
            self._canvas.bind("<Enter>", self._on_enter)
        if sequence is None or sequence == "<Leave>":
            self._canvas.bind("<Leave>", self._on_leave)
        if sequence is None or sequence == "<Button-1>":
            self._canvas.bind("<Button-1>", self._on_press)
        if sequence is None or sequence == "<B1-Motion>":
            self._canvas.bind("<B1-Motion>", self._on_drag)
        if sequence is None or sequence == "<ButtonRelease-1>":
            self._canvas.bind("<ButtonRelease-1>", self._on_release)
        if sequence is None or sequence == "<Motion>":
            self._canvas.bind("<Motion>", self._on_motion)

        # keyboard
        if sequence is None or sequence == "<Left>":
            self._canvas.bind("<Left>", lambda e: self._keyboard_step(-1))
        if sequence is None or sequence == "<Right>":
            self._canvas.bind("<Right>", lambda e: self._keyboard_step(1))
        if sequence is None or sequence == "<Up>":
            self._canvas.bind("<Up>", lambda e: self._keyboard_step(1))
        if sequence is None or sequence == "<Down>":
            self._canvas.bind("<Down>", lambda e: self._keyboard_step(-1))
        if sequence is None or sequence == "<Tab>":
            self._canvas.bind("<Tab>", self._switch_thumb_focus)

        # mouse scroll
        if "linux" in sys.platform:
            if sequence is None or sequence == "<Button-4>":
                self._canvas.bind("<Button-4>", lambda e: self._scroll_step_event(1))
            if sequence is None or sequence == "<Button-5>":
                self._canvas.bind("<Button-5>", lambda e: self._scroll_step_event(-1))
        else:
            if sequence is None or sequence == "<MouseWheel>":
                self._canvas.bind("<MouseWheel>", self._mouse_scroll_event)

    def _set_cursor(self):
        if not self._cursor_manipulation_enabled:
            return
        if self._state == "normal":
            cursor = "pointinghand" if sys.platform == "darwin" else "hand2"
        else:
            cursor = "arrow"
        self.configure(cursor=cursor)

    # ── Scaling ───────────────────────────────────────────────

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._draw()

    # ── Drawing ───────────────────────────────────────────────

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        s = self._apply_widget_scaling
        w = s(self._current_width)
        h = s(self._current_height)
        cr = s(self._corner_radius)
        bw = s(self._border_width)
        bl = s(self._button_length)
        bcr = s(self._button_corner_radius)

        horizontal = self._orientation == "horizontal"

        # clear custom drawings
        self._canvas.delete("value_label")
        self._canvas.delete("custom_progress")
        self._canvas.delete("thumb_low")
        self._canvas.delete("thumb_high")

        # draw the base track using draw engine (at value=0 so no built-in progress)
        requires_recoloring = self._draw_engine.draw_rounded_slider_with_border_and_button(
            w, h, cr, bw, bl, bcr,
            0, "w" if horizontal else "s",
        )

        if no_color_updates is False or requires_recoloring:
            bg = self._apply_appearance_mode(self._bg_color)
            self._canvas.configure(bg=bg)

            if self._border_color == "transparent":
                self._canvas.itemconfig("border_parts", fill=bg, outline=bg)
            else:
                bc = self._apply_appearance_mode(self._border_color)
                self._canvas.itemconfig("border_parts", fill=bc, outline=bc)

            fg = self._apply_appearance_mode(self._fg_color)
            self._canvas.itemconfig("inner_parts", fill=fg, outline=fg)
            self._canvas.itemconfig("progress_parts", fill=fg, outline=fg)

            # hide default slider button
            self._canvas.itemconfig("slider_parts", fill=fg, outline=fg)

        # progress fill between thumbs
        prog_c = self._apply_appearance_mode(self._fg_color)
        if self._progress_color != "transparent":
            prog_c = self._apply_appearance_mode(self._progress_color)

        if horizontal:
            track_start = cr + bl / 2
            track_end = w - cr - bl / 2
            track_len = track_end - track_start
            low_x = track_start + self._low_value * track_len
            high_x = track_start + self._high_value * track_len
            cy = h / 2
            track_h = h - 2 * bw
            # progress bar between thumbs
            self._canvas.create_rectangle(
                low_x, cy - track_h / 2 + bw,
                high_x, cy + track_h / 2 - bw,
                fill=prog_c, outline=prog_c, tags="custom_progress",
            )
        else:
            track_start = cr + bl / 2
            track_end = h - cr - bl / 2
            track_len = track_end - track_start
            low_y = track_end - self._low_value * track_len
            high_y = track_end - self._high_value * track_len
            cx = w / 2
            track_w = w - 2 * bw
            self._canvas.create_rectangle(
                cx - track_w / 2 + bw, high_y,
                cx + track_w / 2 - bw, low_y,
                fill=prog_c, outline=prog_c, tags="custom_progress",
            )

        # draw both thumbs
        self._draw_thumb("low")
        self._draw_thumb("high")

        # value labels
        if self._show_value:
            self._draw_value_labels()

    def _draw_thumb(self, which: str):
        """Draw a single thumb (low or high)."""
        s = self._apply_widget_scaling
        w = s(self._current_width)
        h = s(self._current_height)
        bl = s(self._button_length)
        bcr = s(self._button_corner_radius)
        cr = s(self._corner_radius)

        horizontal = self._orientation == "horizontal"
        value = self._low_value if which == "low" else self._high_value

        is_hovered = self._hover_state == which and self._hover and self._state == "normal"

        if is_hovered:
            color = self._apply_appearance_mode(self._button_hover_color)
        else:
            color = self._apply_appearance_mode(self._button_color)

        tag = f"thumb_{which}"

        if horizontal:
            track_start = cr + bl / 2
            track_end = w - cr - bl / 2
            cx = track_start + value * (track_end - track_start)
            cy = h / 2
            self._canvas.create_oval(
                cx - bl / 2, cy - bl / 2,
                cx + bl / 2, cy + bl / 2,
                fill=color, outline=color, tags=tag,
            )
        else:
            track_start = cr + bl / 2
            track_end = h - cr - bl / 2
            cy = track_end - value * (track_end - track_start)
            cx = w / 2
            self._canvas.create_oval(
                cx - bl / 2, cy - bl / 2,
                cx + bl / 2, cy + bl / 2,
                fill=color, outline=color, tags=tag,
            )

    def _draw_value_labels(self):
        """Draw value labels near each thumb."""
        s = self._apply_widget_scaling
        w = s(self._current_width)
        h = s(self._current_height)
        bl = s(self._button_length)
        cr = s(self._corner_radius)

        low_out = self._from_ + self._low_value * (self._to - self._from_)
        high_out = self._from_ + self._high_value * (self._to - self._from_)
        low_text = self._value_format.format(low_out)
        high_text = self._value_format.format(high_out)

        vc = self._apply_appearance_mode(self._value_color)
        font = self._value_font or ("Helvetica", 9)

        horizontal = self._orientation == "horizontal"

        if horizontal:
            track_start = cr + bl / 2
            track_end = w - cr - bl / 2
            low_x = track_start + self._low_value * (track_end - track_start)
            high_x = track_start + self._high_value * (track_end - track_start)
            self._canvas.create_text(
                low_x, -2, text=low_text, fill=vc, font=font,
                anchor="s", tags="value_label",
            )
            self._canvas.create_text(
                high_x, -2, text=high_text, fill=vc, font=font,
                anchor="s", tags="value_label",
            )
        else:
            track_start = cr + bl / 2
            track_end = h - cr - bl / 2
            low_y = track_end - self._low_value * (track_end - track_start)
            high_y = track_end - self._high_value * (track_end - track_start)
            self._canvas.create_text(
                w + 4, low_y, text=low_text, fill=vc, font=font,
                anchor="w", tags="value_label",
            )
            self._canvas.create_text(
                w + 4, high_y, text=high_text, fill=vc, font=font,
                anchor="w", tags="value_label",
            )

    # ── Hit testing ───────────────────────────────────────────

    def _get_value_from_event(self, event) -> float:
        """Convert mouse event to a 0-1 fraction."""
        s = self._apply_widget_scaling
        w = s(self._current_width)
        h = s(self._current_height)
        cr = s(self._corner_radius)
        bl = s(self._button_length)

        if self._orientation == "horizontal":
            track_start = cr + bl / 2
            track_end = w - cr - bl / 2
            raw = (event.x - track_start) / max(1, track_end - track_start)
        else:
            track_start = cr + bl / 2
            track_end = h - cr - bl / 2
            raw = 1.0 - (event.y - track_start) / max(1, track_end - track_start)

        return max(0.0, min(1.0, raw))

    def _nearest_thumb(self, value: float) -> str:
        """Return 'low' or 'high' based on which thumb is closest."""
        dist_low = abs(value - self._low_value)
        dist_high = abs(value - self._high_value)
        if dist_low <= dist_high:
            return "low"
        return "high"

    # ── Mouse events ──────────────────────────────────────────

    def _on_press(self, event):
        if self._state != "normal":
            return
        value = self._get_value_from_event(event)
        self._dragging = self._nearest_thumb(value)
        self._focused_thumb = self._dragging
        self._update_thumb(self._dragging, value)
        self._canvas.focus_set()

    def _on_drag(self, event):
        if self._state != "normal" or self._dragging is None:
            return
        value = self._get_value_from_event(event)
        self._update_thumb(self._dragging, value)

    def _on_release(self, event):
        self._dragging = None

    def _on_motion(self, event):
        """Track which thumb the mouse is near for hover effect."""
        if self._state != "normal" or self._dragging is not None:
            return
        value = self._get_value_from_event(event)
        nearest = self._nearest_thumb(value)

        # check if close enough to a thumb
        s = self._apply_widget_scaling
        bl = s(self._button_length)
        w = s(self._current_width)
        h = s(self._current_height)
        cr = s(self._corner_radius)

        if self._orientation == "horizontal":
            track_start = cr + bl / 2
            track_end = w - cr - bl / 2
            track_len = max(1, track_end - track_start)
            thumb_val = self._low_value if nearest == "low" else self._high_value
            thumb_x = track_start + thumb_val * track_len
            dist = abs(event.x - thumb_x)
        else:
            track_start = cr + bl / 2
            track_end = h - cr - bl / 2
            track_len = max(1, track_end - track_start)
            thumb_val = self._low_value if nearest == "low" else self._high_value
            thumb_y = track_end - thumb_val * track_len
            dist = abs(event.y - thumb_y)

        new_hover = nearest if dist < bl else None
        if new_hover != self._hover_state:
            self._hover_state = new_hover
            self._draw()

    def _on_enter(self, event):
        pass  # hover tracked via _on_motion

    def _on_leave(self, event):
        if self._hover_state is not None:
            self._hover_state = None
            self._draw()

    def _mouse_scroll_event(self, event):
        if self._state != "normal":
            return
        delta = self._scroll_step if event.delta > 0 else -self._scroll_step
        self._keyboard_step(1 if delta > 0 else -1)

    def _scroll_step_event(self, direction: int):
        if self._state != "normal":
            return
        self._keyboard_step(direction)

    # ── Keyboard ──────────────────────────────────────────────

    def _keyboard_step(self, direction: int):
        """Move the focused thumb by one step."""
        if self._state != "normal":
            return
        step = self._scroll_step
        current = self._low_value if self._focused_thumb == "low" else self._high_value
        new_val = current + step * direction
        self._update_thumb(self._focused_thumb, new_val)

    def _switch_thumb_focus(self, event=None):
        """Switch keyboard focus between low and high thumb."""
        self._focused_thumb = "high" if self._focused_thumb == "low" else "low"
        self._hover_state = self._focused_thumb
        self._draw()
        return "break"  # prevent Tab from moving focus out

    # ── Value update ──────────────────────────────────────────

    def _round_to_step_size(self, value: float) -> float:
        if self._number_of_steps is not None:
            step_size = 1.0 / self._number_of_steps
            return round(value / step_size) * step_size
        return value

    def _update_thumb(self, which: str, value: float):
        """Update a thumb value, enforcing no-cross constraint."""
        value = max(0.0, min(1.0, value))
        value = self._round_to_step_size(value)

        if which == "low":
            # low can't exceed high
            value = min(value, self._high_value)
            if value == self._low_value:
                return
            self._low_value = value
        else:
            # high can't go below low
            value = max(value, self._low_value)
            if value == self._high_value:
                return
            self._high_value = value

        self._draw()

        if self._command is not None:
            low_out = self._from_ + self._low_value * (self._to - self._from_)
            high_out = self._from_ + self._high_value * (self._to - self._from_)
            low_out = self._snap_output(low_out)
            high_out = self._snap_output(high_out)
            self._command(low_out, high_out)

    def _snap_output(self, value: float) -> float:
        """Snap output value to step grid."""
        if self._number_of_steps is not None:
            step = (self._to - self._from_) / self._number_of_steps
            return self._from_ + round((value - self._from_) / step) * step
        return value

    # ── Public API ────────────────────────────────────────────

    def set(self, low_value: float, high_value: float):
        """Set both thumb values (in output scale, not 0-1)."""
        rng = self._to - self._from_
        if rng == 0:
            return
        low_frac = (low_value - self._from_) / rng
        high_frac = (high_value - self._from_) / rng
        low_frac = max(0.0, min(1.0, low_frac))
        high_frac = max(0.0, min(1.0, high_frac))
        if low_frac > high_frac:
            low_frac, high_frac = high_frac, low_frac
        self._low_value = self._round_to_step_size(low_frac)
        self._high_value = self._round_to_step_size(high_frac)
        self._draw()

    def get(self) -> Tuple[float, float]:
        """Get both thumb values (in output scale)."""
        low = self._snap_output(self._from_ + self._low_value * (self._to - self._from_))
        high = self._snap_output(self._from_ + self._high_value * (self._to - self._from_))
        return (low, high)

    # ── Configure / cget ──────────────────────────────────────

    def configure(self, require_redraw=False, **kwargs):
        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            require_redraw = True
        if "button_corner_radius" in kwargs:
            self._button_corner_radius = kwargs.pop("button_corner_radius")
            require_redraw = True
        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            require_redraw = True
        if "button_length" in kwargs:
            self._button_length = kwargs.pop("button_length")
            require_redraw = True
        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True
        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"), transparency=True)
            require_redraw = True
        if "progress_color" in kwargs:
            self._progress_color = self._check_color_type(kwargs.pop("progress_color"), transparency=True)
            require_redraw = True
        if "button_color" in kwargs:
            self._button_color = self._check_color_type(kwargs.pop("button_color"))
            require_redraw = True
        if "button_hover_color" in kwargs:
            self._button_hover_color = self._check_color_type(kwargs.pop("button_hover_color"))
            require_redraw = True
        if "from_" in kwargs:
            self._from_ = kwargs.pop("from_")
        if "to" in kwargs:
            self._to = kwargs.pop("to")
        if "number_of_steps" in kwargs:
            self._number_of_steps = kwargs.pop("number_of_steps")
        if "scroll_step" in kwargs:
            self._scroll_step = kwargs.pop("scroll_step")
        if "show_value" in kwargs:
            self._show_value = kwargs.pop("show_value")
            require_redraw = True
        if "value_format" in kwargs:
            self._value_format = kwargs.pop("value_format")
            require_redraw = True
        if "hover" in kwargs:
            self._hover = kwargs.pop("hover")
        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._set_cursor()
            require_redraw = True
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "orientation" in kwargs:
            self._orientation = kwargs.pop("orientation").lower()
            require_redraw = True

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "button_corner_radius":
            return self._button_corner_radius
        elif attribute_name == "border_width":
            return self._border_width
        elif attribute_name == "button_length":
            return self._button_length
        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "progress_color":
            return self._progress_color
        elif attribute_name == "button_color":
            return self._button_color
        elif attribute_name == "button_hover_color":
            return self._button_hover_color
        elif attribute_name == "from_":
            return self._from_
        elif attribute_name == "to":
            return self._to
        elif attribute_name == "number_of_steps":
            return self._number_of_steps
        elif attribute_name == "scroll_step":
            return self._scroll_step
        elif attribute_name == "show_value":
            return self._show_value
        elif attribute_name == "value_format":
            return self._value_format
        elif attribute_name == "hover":
            return self._hover
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "orientation":
            return self._orientation
        else:
            return super().cget(attribute_name)

    # ── Cleanup ───────────────────────────────────────────────

    def destroy(self):
        super().destroy()

    # ── Bind / focus ──────────────────────────────────────────

    def bind(self, sequence: str = None, command: Callable = None, add: Union[str, bool] = True):
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, command, add=True)

    def unbind(self, sequence: str = None, funcid: str = None):
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in"
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._canvas.unbind(sequence, None)
        self._create_bindings(sequence=sequence)

    def focus(self):
        return self._canvas.focus()

    def focus_set(self):
        return self._canvas.focus_set()

    def focus_force(self):
        return self._canvas.focus_force()
