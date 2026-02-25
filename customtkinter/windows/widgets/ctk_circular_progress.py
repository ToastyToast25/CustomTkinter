import tkinter
import math
from typing import Union, Tuple, Optional, Callable, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkCircularProgress(CTkBaseClass):
    """
    Circular progress indicator with animated value transitions.
    Shows a ring/arc that fills based on the value (0.0 to 1.0).
    Optionally displays percentage text in the center.

    Supports two modes:
        - "determinate" (default): Arc fills proportionally to the value.
        - "indeterminate": A partial arc spins continuously. Use start()/stop().

    Usage:
        cp = CTkCircularProgress(parent, size=100, line_width=8)
        cp.set(0.75)  # 75%

        # Indeterminate spinner
        spinner = CTkCircularProgress(parent, mode="indeterminate")
        spinner.start()

        # Custom text callback
        cp = CTkCircularProgress(parent, text_callback=lambda v: f"{int(v*100)} files")
    """

    def __init__(self,
                 master: Any,
                 size: int = 80,
                 line_width: int = 6,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 progress_color: Optional[Union[str, Tuple[str, str]]] = None,
                 track_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,

                 show_text: bool = True,
                 text_format: str = "{:.0%}",
                 text_callback: Optional[Callable[[float], str]] = None,
                 font: Optional[Union[tuple, CTkFont]] = None,
                 variable: Optional[tkinter.Variable] = None,
                 start_angle: float = 90,
                 mode: str = "determinate",
                 on_complete: Optional[Callable] = None,
                 **kwargs):

        super().__init__(master=master, bg_color=bg_color, width=size, height=size, **kwargs)

        self._size = size
        self._line_width = line_width
        self._value = 0.0
        self._start_angle = start_angle

        # colors
        self._fg_color = fg_color or ThemeManager.theme["CTk"]["fg_color"]
        self._progress_color = progress_color or ThemeManager.theme["CTkProgressBar"]["progress_color"]
        self._track_color = track_color or ("#e0e0e0", "#404040")
        self._text_color = text_color or ThemeManager.theme["CTkLabel"]["text_color"]

        # text
        self._show_text = show_text
        self._text_format = text_format
        self._text_callback = text_callback
        self._font = font or CTkFont(size=max(10, size // 5))

        # variable
        self._variable = variable
        self._variable_callback_name = None
        self._variable_callback_blocked = False

        # animation
        self._target_value = 0.0
        self._anim_after_id = None
        self._on_complete = on_complete

        # mode (determinate / indeterminate)
        self._mode = mode
        self._spinning = False
        self._spin_angle = 0
        self._spin_extent = 90
        self._spin_after_id = None

        # build canvas
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        scaled_size = self._apply_widget_scaling(self._size)
        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=scaled_size,
                                 height=scaled_size)
        self._canvas.grid(row=0, column=0, sticky="nswe")

        # canvas items
        self._track_id = None
        self._arc_id = None
        self._text_id = None

        self._draw()

        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._variable_callback_blocked = True
            self.set(self._variable.get())
            self._variable_callback_blocked = False

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        scaled = self._apply_widget_scaling
        s = scaled(self._size)
        lw = max(1, scaled(self._line_width))
        pad = lw / 2 + scaled(2)

        bg = self._apply_appearance_mode(self._bg_color)
        fg = self._apply_appearance_mode(self._fg_color)
        track = self._apply_appearance_mode(self._track_color)
        progress = self._apply_appearance_mode(self._progress_color)
        text_c = self._apply_appearance_mode(self._text_color)

        # progress arc angles
        if self._mode == "indeterminate":
            arc_start = self._spin_angle
            arc_extent = -self._spin_extent
        else:
            arc_start = self._start_angle
            arc_extent = -self._value * 360  # negative = clockwise

        # Create items on first draw, update on subsequent draws
        if self._track_id is None:
            # First draw — create all canvas items
            self._canvas.configure(bg=bg if bg != "transparent" else fg)

            self._track_id = self._canvas.create_arc(
                pad, pad, s - pad, s - pad,
                start=0, extent=359.99,
                style="arc", width=lw,
                outline=track
            )

            self._arc_id = self._canvas.create_arc(
                pad, pad, s - pad, s - pad,
                start=arc_start, extent=arc_extent,
                style="arc", width=lw,
                outline=progress
            )

            if self._show_text:
                font = self._get_scaled_font(scaled)
                text = self._get_display_text()
                self._text_id = self._canvas.create_text(
                    s / 2, s / 2,
                    text=text, fill=text_c, font=font, anchor="center"
                )
        else:
            # Subsequent draws — update existing items in place
            self._canvas.coords(self._track_id, pad, pad, s - pad, s - pad)
            self._canvas.itemconfigure(self._track_id, width=lw)

            self._canvas.coords(self._arc_id, pad, pad, s - pad, s - pad)
            self._canvas.itemconfigure(self._arc_id, start=arc_start, extent=arc_extent, width=lw)

            if not no_color_updates:
                self._canvas.configure(bg=bg if bg != "transparent" else fg)
                self._canvas.itemconfigure(self._track_id, outline=track)
                self._canvas.itemconfigure(self._arc_id, outline=progress)

            if self._show_text and self._text_id is not None:
                font = self._get_scaled_font(scaled)
                text = self._get_display_text()
                self._canvas.coords(self._text_id, s / 2, s / 2)
                self._canvas.itemconfigure(self._text_id, text=text, font=font)
                if not no_color_updates:
                    self._canvas.itemconfigure(self._text_id, fill=text_c)
            elif self._show_text and self._text_id is None:
                font = self._get_scaled_font(scaled)
                text = self._get_display_text()
                self._text_id = self._canvas.create_text(
                    s / 2, s / 2,
                    text=text, fill=text_c, font=font, anchor="center"
                )
            elif not self._show_text and self._text_id is not None:
                self._canvas.delete(self._text_id)
                self._text_id = None

    def _get_scaled_font(self, scaled):
        """Get the font tuple with scaling applied."""
        font = self._font
        if isinstance(font, CTkFont):
            return (font.cget("family"), int(scaled(font.cget("size"))), font.cget("weight"))
        elif isinstance(font, tuple) and len(font) >= 2:
            return (font[0], int(scaled(font[1]))) + font[2:]
        return font

    def _get_display_text(self) -> str:
        """Get the text to display in the center."""
        if self._text_callback is not None:
            try:
                return self._text_callback(self._value)
            except Exception:
                return f"{self._value:.0%}"
        else:
            try:
                return self._text_format.format(self._value)
            except (ValueError, KeyError):
                return f"{self._value:.0%}"

    def set(self, value: float, animate: bool = False, duration: int = 300):
        """Set the progress value (0.0 to 1.0)."""
        value = max(0.0, min(1.0, float(value)))

        if animate and value != self._value:
            self._target_value = value
            self._animate_to(duration)
        else:
            self._value = value
            self._target_value = value
            self._draw()

            if self._variable is not None and not self._variable_callback_blocked:
                self._variable_callback_blocked = True
                self._variable.set(value)
                self._variable_callback_blocked = False

    def step(self, amount: float = 0.1):
        """Increment the value by amount, clamping at 1.0."""
        new_value = min(1.0, self._value + amount)
        self.set(new_value)

    def start(self):
        """Start the indeterminate spinner. Only effective when mode='indeterminate'."""
        if self._mode != "indeterminate":
            return
        if self._spinning:
            return
        self._spinning = True
        self._spin_tick()

    def stop(self):
        """Stop the indeterminate spinner at its current position."""
        self._spinning = False
        if self._spin_after_id is not None:
            self.after_cancel(self._spin_after_id)
            self._spin_after_id = None

    def _spin_tick(self):
        """Advance the spinner arc by one tick. ~60fps, ~1 revolution per second."""
        if self._spinning:
            self._spin_angle = (self._spin_angle + 6) % 360  # 6 deg * 60fps ~ 360 deg/sec
            self._draw()
            self._spin_after_id = self.after(16, self._spin_tick)

    def _animate_to(self, duration: int):
        """Animate from current value to target value."""
        if self._anim_after_id is not None:
            self.after_cancel(self._anim_after_id)
            self._anim_after_id = None

        start_val = self._value
        target = self._target_value
        elapsed = [0]
        interval = 16  # ~60fps

        def tick():
            elapsed[0] += interval
            t = min(1.0, elapsed[0] / duration)
            # ease out cubic
            t_eased = 1 - (1 - t) ** 3
            self._value = start_val + (target - start_val) * t_eased
            self._draw()
            if t < 1.0:
                self._anim_after_id = self.after(interval, tick)
            else:
                self._anim_after_id = None
                # Fire on_complete callback when animation finishes at 1.0
                if self._on_complete is not None and self._value >= 1.0:
                    self._on_complete()

        tick()

    def get(self) -> float:
        """Get the current progress value."""
        return self._value

    def _variable_callback(self, var_name, index, mode):
        if not self._variable_callback_blocked:
            self.set(self._variable.get())

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        scaled_size = self._apply_widget_scaling(self._size)
        self._canvas.configure(width=scaled_size, height=scaled_size)
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width=None, height=None):
        if width is not None:
            self._size = width
        super()._set_dimensions(width=self._size, height=self._size)
        scaled_size = self._apply_widget_scaling(self._size)
        self._canvas.configure(width=scaled_size, height=scaled_size)
        # Force full rebuild on size change
        self._canvas.delete("all")
        self._track_id = None
        self._arc_id = None
        self._text_id = None
        self._draw()

    def destroy(self):
        if self._anim_after_id is not None:
            self.after_cancel(self._anim_after_id)
            self._anim_after_id = None
        if self._spin_after_id is not None:
            self.after_cancel(self._spin_after_id)
            self._spin_after_id = None
        self._spinning = False
        if self._variable is not None and self._variable_callback_name is not None:
            self._variable.trace_remove("write", self._variable_callback_name)
        super().destroy()

    def configure(self, **kwargs):
        require_redraw = False
        if "size" in kwargs:
            self._size = kwargs.pop("size")
            self._set_dimensions(width=self._size, height=self._size)
        if "line_width" in kwargs:
            self._line_width = kwargs.pop("line_width")
            require_redraw = True
        if "progress_color" in kwargs:
            self._progress_color = kwargs.pop("progress_color")
            require_redraw = True
        if "track_color" in kwargs:
            self._track_color = kwargs.pop("track_color")
            require_redraw = True
        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            require_redraw = True
        if "show_text" in kwargs:
            self._show_text = kwargs.pop("show_text")
            require_redraw = True
        if "text_format" in kwargs:
            self._text_format = kwargs.pop("text_format")
            require_redraw = True
        if "text_callback" in kwargs:
            self._text_callback = kwargs.pop("text_callback")
            require_redraw = True
        if "variable" in kwargs:
            if self._variable is not None:
                self._variable.trace_remove("write", self._variable_callback_name)
            self._variable = kwargs.pop("variable")
            if self._variable is not None:
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
                self.set(self._variable.get())
        if "start_angle" in kwargs:
            self._start_angle = kwargs.pop("start_angle")
            require_redraw = True
        if "mode" in kwargs:
            new_mode = kwargs.pop("mode")
            if new_mode != self._mode:
                # Stop spinner if switching away from indeterminate
                if self._mode == "indeterminate":
                    self.stop()
                self._mode = new_mode
                require_redraw = True
        if "on_complete" in kwargs:
            self._on_complete = kwargs.pop("on_complete")
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "size":
            return self._size
        elif attribute_name == "line_width":
            return self._line_width
        elif attribute_name == "progress_color":
            return self._progress_color
        elif attribute_name == "track_color":
            return self._track_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "show_text":
            return self._show_text
        elif attribute_name == "text_format":
            return self._text_format
        elif attribute_name == "text_callback":
            return self._text_callback
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "start_angle":
            return self._start_angle
        elif attribute_name == "mode":
            return self._mode
        elif attribute_name == "on_complete":
            return self._on_complete
        elif attribute_name == "value":
            return self._value
        else:
            return super().cget(attribute_name)
