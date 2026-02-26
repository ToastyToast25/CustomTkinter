import tkinter
from typing import Union, Tuple, Optional, Callable, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont
from .utility import pop_from_dict_by_set, check_kwargs_empty


class CTkSpinbox(CTkBaseClass):
    """
    Numeric spinbox with rounded corners, increment/decrement buttons on the sides,
    border, variable support, keyboard and mouse wheel interaction.

    The left button decrements, the right button increments. Supports integer
    and floating-point values with configurable precision, min/max clamping,
    step size, and hold-to-repeat with acceleration.

    Usage:
        spinbox = CTkSpinbox(parent, min_value=0, max_value=100, step=1)
        spinbox.set(50)
        value = spinbox.get()  # 50

        # Float mode
        spinbox = CTkSpinbox(parent, min_value=0.0, max_value=10.0,
                             step=0.1, float_precision=1)
    """

    _minimum_x_padding = 6

    # Hold-to-repeat timing constants (milliseconds)
    _REPEAT_DELAY = 400
    _REPEAT_INTERVAL_SLOW = 120
    _REPEAT_INTERVAL_FAST = 30
    _REPEAT_ACCEL_AFTER = 8
    _REPEAT_LARGE_STEP_AFTER = 20

    def __init__(self,
                 master: Any,
                 width: int = 150,
                 height: int = 28,
                 corner_radius: Optional[int] = None,
                 border_width: Optional[int] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 button_color: Optional[Union[str, Tuple[str, str]]] = None,
                 button_hover_color: Optional[Union[str, Tuple[str, str]]] = None,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 state: str = tkinter.NORMAL,
                 command: Optional[Callable] = None,
                 variable: Optional[tkinter.Variable] = None,

                 min_value: Union[int, float] = 0,
                 max_value: Union[int, float] = 100,
                 step: Union[int, float] = 1,
                 float_precision: Optional[int] = None,
                 start_value: Optional[Union[int, float]] = None,

                 **kwargs):

        # transfer basic functionality to CTkBaseClass
        super().__init__(master=master, bg_color=bg_color, width=width, height=height)

        # configure grid: [decrement_button | entry | increment_button]
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # left button
        self.grid_columnconfigure(1, weight=1)  # entry expands
        self.grid_columnconfigure(2, weight=0)  # right button

        # -- colors --
        self._fg_color = ThemeManager.theme["CTkEntry"]["fg_color"] if fg_color is None else self._check_color_type(fg_color, transparency=True)
        self._text_color = ThemeManager.theme["CTkEntry"]["text_color"] if text_color is None else self._check_color_type(text_color)
        self._border_color = ThemeManager.theme["CTkEntry"]["border_color"] if border_color is None else self._check_color_type(border_color)
        self._button_color = ThemeManager.theme["CTkButton"]["fg_color"] if button_color is None else self._check_color_type(button_color)
        self._button_hover_color = ThemeManager.theme["CTkButton"]["hover_color"] if button_hover_color is None else self._check_color_type(button_hover_color)

        # -- shape --
        self._corner_radius = ThemeManager.theme["CTkEntry"]["corner_radius"] if corner_radius is None else corner_radius
        self._border_width = ThemeManager.theme["CTkEntry"]["border_width"] if border_width is None else border_width

        # -- numeric settings --
        self._min_value = min_value
        self._max_value = max_value
        self._step = step
        self._float_precision = float_precision

        # ensure min <= max
        if self._min_value > self._max_value:
            self._min_value, self._max_value = self._max_value, self._min_value

        # -- state --
        self._state = state
        self._command = command
        self._variable = variable
        self._variable_callback_name: str = ""
        self._suppress_variable_update = False
        self._suppress_trace = False

        # internal numeric value
        if start_value is not None:
            self._value: Union[int, float] = self._clamp(start_value)
        else:
            self._value: Union[int, float] = self._clamp(self._min_value)

        # -- font --
        self._font = CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)

        # -- hold-to-repeat state --
        self._repeat_after_id: Optional[str] = None
        self._repeat_count: int = 0
        self._repeat_direction: int = 0  # +1 or -1

        # -- button dimensions --
        self._button_width = max(20, int(height * 0.85))

        # -- canvas (background rendering) --
        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._current_width),
                                 height=self._apply_widget_scaling(self._current_height))
        self._draw_engine = DrawEngine(self._canvas)

        # -- entry widget --
        self._entry = tkinter.Entry(master=self,
                                    bd=0,
                                    width=1,
                                    highlightthickness=0,
                                    font=self._apply_font_scaling(self._font),
                                    state=self._state if self._state != "readonly" else "readonly",
                                    justify=tkinter.CENTER)

        # -- left button canvas (decrement) --
        self._btn_left_canvas = tkinter.Canvas(self, bd=0, highlightthickness=0,
                                               cursor="hand2" if self._state == tkinter.NORMAL else "arrow")

        # -- right button canvas (increment) --
        self._btn_right_canvas = tkinter.Canvas(self, bd=0, highlightthickness=0,
                                                cursor="hand2" if self._state == tkinter.NORMAL else "arrow")

        # track arrow canvas item IDs to avoid delete("all")
        self._left_arrow_id: Optional[int] = None
        self._right_arrow_id: Optional[int] = None

        check_kwargs_empty(kwargs, raise_error=True)

        # -- layout --
        self._create_grid()
        self._create_bindings()
        self._draw()
        self._display_value()

        # -- variable binding --
        if self._variable is not None and self._variable != "":
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            # initialize from variable if it has a value
            try:
                var_val = self._variable.get()
                if var_val != "" and var_val != 0:
                    self._value = self._clamp(self._cast_value(var_val))
                    self._display_value()
            except (ValueError, tkinter.TclError):
                pass

    # ==================================================================
    #  Layout & Bindings
    # ==================================================================

    def _create_grid(self):
        scaled_border = self._apply_widget_scaling(self._border_width)
        scaled_btn_width = self._apply_widget_scaling(self._button_width)

        self._canvas.grid(column=0, row=0, columnspan=3, sticky="nswe")

        self._btn_left_canvas.grid(column=0, row=0, sticky="nswe",
                                   padx=(scaled_border, 0),
                                   pady=scaled_border)
        self._btn_left_canvas.configure(width=scaled_btn_width)

        x_pad = self._apply_widget_scaling(
            max(self._minimum_x_padding, min(self._corner_radius, self._current_height / 2))
        )
        y_pad_top = self._apply_widget_scaling(self._border_width)
        y_pad_bot = self._apply_widget_scaling(self._border_width + 1)

        self._entry.grid(column=1, row=0, sticky="nswe",
                         padx=(2, 2),
                         pady=(y_pad_top, y_pad_bot))

        self._btn_right_canvas.grid(column=2, row=0, sticky="nswe",
                                    padx=(0, scaled_border),
                                    pady=scaled_border)
        self._btn_right_canvas.configure(width=scaled_btn_width)

    def _create_bindings(self, sequence: Optional[str] = None):
        """Set up all event bindings for the widget."""
        if sequence is None or sequence == "<FocusOut>":
            self._entry.bind("<FocusOut>", self._on_focus_out)
        if sequence is None or sequence == "<FocusIn>":
            self._entry.bind("<FocusIn>", self._on_focus_in)
        if sequence is None or sequence == "<Return>":
            self._entry.bind("<Return>", self._on_return)
        if sequence is None or sequence == "<KP_Enter>":
            self._entry.bind("<KP_Enter>", self._on_return)

        # keyboard increment/decrement
        if sequence is None or sequence == "<Up>":
            self._entry.bind("<Up>", self._on_key_up)
        if sequence is None or sequence == "<Down>":
            self._entry.bind("<Down>", self._on_key_down)

        # mouse scroll on the entry
        if sequence is None:
            self._entry.bind("<MouseWheel>", self._on_mouse_wheel)
            # Linux scroll events
            self._entry.bind("<Button-4>", lambda e: self._step_value(1))
            self._entry.bind("<Button-5>", lambda e: self._step_value(-1))

        # left button (decrement) press/release/hover
        if sequence is None:
            self._btn_left_canvas.bind("<ButtonPress-1>", self._on_btn_left_press)
            self._btn_left_canvas.bind("<ButtonRelease-1>", self._on_btn_release)
            self._btn_left_canvas.bind("<Enter>", self._on_btn_left_enter)
            self._btn_left_canvas.bind("<Leave>", self._on_btn_leave)

        # right button (increment) press/release/hover
        if sequence is None:
            self._btn_right_canvas.bind("<ButtonPress-1>", self._on_btn_right_press)
            self._btn_right_canvas.bind("<ButtonRelease-1>", self._on_btn_release)
            self._btn_right_canvas.bind("<Enter>", self._on_btn_right_enter)
            self._btn_right_canvas.bind("<Leave>", self._on_btn_leave)

    # ==================================================================
    #  Drawing
    # ==================================================================

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(
            self._apply_widget_scaling(self._current_width),
            self._apply_widget_scaling(self._current_height),
            self._apply_widget_scaling(self._corner_radius),
            self._apply_widget_scaling(self._border_width))

        if requires_recoloring or no_color_updates is False:
            fg = self._apply_appearance_mode(self._fg_color)
            bg = self._apply_appearance_mode(self._bg_color)

            self._canvas.configure(bg=bg)

            if fg == "transparent":
                inner_color = bg
            else:
                inner_color = fg

            self._canvas.itemconfig("inner_parts", fill=inner_color, outline=inner_color)
            self._canvas.itemconfig("border_parts",
                                    fill=self._apply_appearance_mode(self._border_color),
                                    outline=self._apply_appearance_mode(self._border_color))

            # entry colors
            self._entry.configure(bg=inner_color,
                                  disabledbackground=inner_color,
                                  readonlybackground=inner_color,
                                  highlightcolor=inner_color,
                                  fg=self._apply_appearance_mode(self._text_color),
                                  disabledforeground=self._apply_appearance_mode(self._text_color),
                                  insertbackground=self._apply_appearance_mode(self._text_color))

            # button canvases
            btn_color = self._apply_appearance_mode(self._button_color)
            self._btn_left_canvas.configure(bg=btn_color)
            self._btn_right_canvas.configure(bg=btn_color)

            # draw arrow glyphs
            self._draw_arrows()

    def _draw_arrows(self):
        """Draw the left/right arrow triangles on the button canvases."""
        self._btn_left_canvas.update_idletasks()
        self._btn_right_canvas.update_idletasks()

        arrow_color = self._apply_appearance_mode(self._text_color)

        for canvas, direction, attr_name in [
            (self._btn_left_canvas, "left", "_left_arrow_id"),
            (self._btn_right_canvas, "right", "_right_arrow_id"),
        ]:
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w <= 1 or h <= 1:
                # widget not yet mapped, schedule redraw
                self.after(50, self._draw_arrows)
                return

            cx = w / 2
            cy = h / 2
            size = min(w, h) * 0.3

            if direction == "left":
                # left-pointing triangle (decrement)
                points = [cx - size * 0.5, cy,
                          cx + size * 0.5, cy - size * 0.6,
                          cx + size * 0.5, cy + size * 0.6]
            else:
                # right-pointing triangle (increment)
                points = [cx + size * 0.5, cy,
                          cx - size * 0.5, cy - size * 0.6,
                          cx - size * 0.5, cy + size * 0.6]

            existing_id = getattr(self, attr_name)
            if existing_id is not None:
                # reuse existing canvas item
                canvas.coords(existing_id, *points)
                canvas.itemconfigure(existing_id, fill=arrow_color, outline=arrow_color)
            else:
                # create new canvas item
                item_id = canvas.create_polygon(points, fill=arrow_color, outline=arrow_color)
                setattr(self, attr_name, item_id)

    # ==================================================================
    #  Value Management
    # ==================================================================

    def _cast_value(self, value: Any) -> Union[int, float]:
        """Cast a value to the appropriate numeric type based on float_precision."""
        if self._float_precision is not None:
            return float(value)
        else:
            # determine from step and min/max whether to use float
            if isinstance(self._step, float) or isinstance(self._min_value, float) or isinstance(self._max_value, float):
                return float(value)
            else:
                return int(float(value))

    def _clamp(self, value: Union[int, float]) -> Union[int, float]:
        """Clamp value to [min_value, max_value] range and cast to the correct type."""
        low = min(self._min_value, self._max_value)
        high = max(self._min_value, self._max_value)
        clamped = max(low, min(high, value))

        if self._float_precision is not None:
            return round(float(clamped), self._float_precision)
        elif isinstance(self._step, float) or isinstance(self._min_value, float) or isinstance(self._max_value, float):
            return float(clamped)
        else:
            return int(clamped)

    def _format_value(self, value: Union[int, float]) -> str:
        """Format a numeric value for display."""
        if self._float_precision is not None:
            return f"{value:.{self._float_precision}f}"
        elif isinstance(value, float):
            # auto-detect precision from step
            step_str = str(self._step)
            if "." in step_str:
                decimals = len(step_str.split(".")[1])
                return f"{value:.{decimals}f}"
            return str(value)
        else:
            return str(int(value))

    def _parse_entry_text(self, text: str) -> Optional[Union[int, float]]:
        """Parse the entry text back to a numeric value."""
        text = text.strip()
        if text == "" or text == "-" or text == ".":
            return None
        try:
            return self._cast_value(text)
        except (ValueError, OverflowError):
            return None

    def _display_value(self):
        """Update the entry widget to show the current formatted value."""
        self._entry.configure(state=tkinter.NORMAL)
        self._entry.delete(0, tkinter.END)
        self._entry.insert(0, self._format_value(self._value))
        if self._state == "readonly":
            self._entry.configure(state="readonly")
        elif self._state == tkinter.DISABLED:
            self._entry.configure(state=tkinter.DISABLED)

    def _commit_entry(self) -> bool:
        """Parse the entry text, clamp it, update display. Returns True if value changed."""
        text = self._entry.get()
        parsed = self._parse_entry_text(text)

        if parsed is None:
            # invalid input - revert to current value
            self._display_value()
            return False

        new_value = self._clamp(parsed)
        changed = new_value != self._value
        self._value = new_value
        self._display_value()

        if changed:
            self._update_variable()
            self._invoke_command()

        return changed

    def _step_value(self, direction: int, multiplier: float = 1.0):
        """Increment or decrement the value by step * direction * multiplier."""
        if self._state == tkinter.DISABLED:
            return

        # if entry is focused, commit current text first
        try:
            if self._entry.focus_get() == self._entry:
                self._commit_entry()
        except KeyError:
            pass

        actual_step = self._step * multiplier
        new_value = self._value + (actual_step * direction)

        # round to avoid floating point drift
        if self._float_precision is not None:
            new_value = round(new_value, self._float_precision + 2)
        elif isinstance(new_value, float):
            step_str = str(self._step)
            if "." in step_str:
                decimals = len(step_str.split(".")[1])
                new_value = round(new_value, decimals + 2)

        new_value = self._clamp(new_value)

        if new_value != self._value:
            self._value = new_value
            self._display_value()
            self._update_variable()
            self._invoke_command()

    def _update_variable(self):
        """Sync current value to the bound variable."""
        if self._variable is not None and self._variable != "" and not self._suppress_variable_update:
            self._suppress_trace = True
            try:
                self._variable.set(self._value)
            except tkinter.TclError:
                pass
            finally:
                self._suppress_trace = False

    def _invoke_command(self):
        """Call the command callback."""
        if self._command is not None:
            self._command()

    def _variable_callback(self, var_name, index, mode):
        """Called when the bound variable changes externally."""
        if self._suppress_trace:
            return
        try:
            var_val = self._variable.get()
            new_value = self._clamp(self._cast_value(var_val))
            if new_value != self._value:
                self._value = new_value
                self._display_value()
        except (ValueError, tkinter.TclError):
            pass

    # ==================================================================
    #  Event Handlers
    # ==================================================================

    def _on_focus_out(self, event=None):
        """Validate and clamp on focus loss."""
        self._commit_entry()

    def _on_focus_in(self, event=None):
        """Select all text when entry is focused for easy replacement."""
        if self._state == tkinter.NORMAL:
            self._entry.select_range(0, tkinter.END)

    def _on_return(self, event=None):
        """Commit value when Enter is pressed."""
        self._commit_entry()
        return "break"

    def _on_key_up(self, event=None):
        self._step_value(1)
        return "break"

    def _on_key_down(self, event=None):
        self._step_value(-1)
        return "break"

    def _on_mouse_wheel(self, event=None):
        if self._state == tkinter.DISABLED:
            return
        if event.delta > 0:
            self._step_value(1)
        elif event.delta < 0:
            self._step_value(-1)

    # -- Button hover --

    def _on_btn_left_enter(self, event=None):
        if self._state == tkinter.NORMAL:
            hover = self._apply_appearance_mode(self._button_hover_color)
            self._btn_left_canvas.configure(bg=hover)

    def _on_btn_right_enter(self, event=None):
        if self._state == tkinter.NORMAL:
            hover = self._apply_appearance_mode(self._button_hover_color)
            self._btn_right_canvas.configure(bg=hover)

    def _on_btn_leave(self, event=None):
        """Reset button color and cancel repeat."""
        btn_color = self._apply_appearance_mode(self._button_color)
        self._btn_left_canvas.configure(bg=btn_color)
        self._btn_right_canvas.configure(bg=btn_color)

    # -- Hold-to-repeat --

    def _on_btn_left_press(self, event=None):
        if self._state == tkinter.DISABLED:
            return
        self._step_value(-1)
        self._repeat_direction = -1
        self._repeat_count = 0
        self._cancel_repeat()
        self._repeat_after_id = self.after(self._REPEAT_DELAY, self._repeat_step)

    def _on_btn_right_press(self, event=None):
        if self._state == tkinter.DISABLED:
            return
        self._step_value(1)
        self._repeat_direction = 1
        self._repeat_count = 0
        self._cancel_repeat()
        self._repeat_after_id = self.after(self._REPEAT_DELAY, self._repeat_step)

    def _on_btn_release(self, event=None):
        self._cancel_repeat()

    def _repeat_step(self):
        """Execute one repeat step and schedule the next with acceleration."""
        self._repeat_count += 1

        # use larger step after many repeats
        multiplier = 10.0 if self._repeat_count >= self._REPEAT_LARGE_STEP_AFTER else 1.0
        self._step_value(self._repeat_direction, multiplier=multiplier)

        # calculate interval with acceleration
        if self._repeat_count >= self._REPEAT_ACCEL_AFTER:
            progress = min(1.0, (self._repeat_count - self._REPEAT_ACCEL_AFTER) / 12.0)
            interval = int(self._REPEAT_INTERVAL_SLOW +
                           (self._REPEAT_INTERVAL_FAST - self._REPEAT_INTERVAL_SLOW) * progress)
        else:
            interval = self._REPEAT_INTERVAL_SLOW

        self._repeat_after_id = self.after(interval, self._repeat_step)

    def _cancel_repeat(self):
        """Cancel any pending hold-to-repeat callback."""
        if self._repeat_after_id is not None:
            self.after_cancel(self._repeat_after_id)
            self._repeat_after_id = None
        self._repeat_count = 0

    # ==================================================================
    #  Scaling
    # ==================================================================

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)

        self._entry.configure(font=self._apply_font_scaling(self._font))
        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._create_grid()
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    def _update_font(self):
        """Pass font to tkinter entry with applied font scaling."""
        self._entry.configure(font=self._apply_font_scaling(self._font))

        # force grid refresh
        self._canvas.grid_forget()
        self._canvas.grid(column=0, row=0, columnspan=3, sticky="nswe")

    # ==================================================================
    #  Lifecycle
    # ==================================================================

    def destroy(self):
        self._cancel_repeat()

        if self._variable is not None and self._variable_callback_name:
            self._variable.trace_remove("write", self._variable_callback_name)

        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)

        super().destroy()

    # ==================================================================
    #  Public API
    # ==================================================================

    def get(self) -> Union[int, float]:
        """Return the current numeric value.

        If the entry contains unparseable text (user is mid-edit), returns the
        last known valid value.
        """
        parsed = self._parse_entry_text(self._entry.get())
        if parsed is not None:
            return self._clamp(parsed)
        return self._value

    def set(self, value: Union[int, float, str]):
        """Set the value programmatically. The value is clamped to bounds."""
        if isinstance(value, str):
            try:
                value = self._cast_value(value)
            except (ValueError, OverflowError):
                return

        new_value = self._clamp(self._cast_value(value))
        self._value = new_value
        self._display_value()
        self._update_variable()

    def step_up(self, multiplier: float = 1.0):
        """Increment the value by step * multiplier."""
        self._step_value(1, multiplier=multiplier)

    def step_down(self, multiplier: float = 1.0):
        """Decrement the value by step * multiplier."""
        self._step_value(-1, multiplier=multiplier)

    def focus(self):
        self._entry.focus()

    def focus_set(self):
        self._entry.focus_set()

    def focus_force(self):
        self._entry.focus_force()

    # ==================================================================
    #  configure / cget
    # ==================================================================

    def configure(self, require_redraw=False, **kwargs):
        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            self._create_grid()
            require_redraw = True

        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            self._create_grid()
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            require_redraw = True

        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "button_color" in kwargs:
            self._button_color = self._check_color_type(kwargs.pop("button_color"))
            require_redraw = True

        if "button_hover_color" in kwargs:
            self._button_hover_color = self._check_color_type(kwargs.pop("button_hover_color"))
            require_redraw = True

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            entry_state = self._state
            self._entry.configure(state=entry_state)
            cursor = "hand2" if self._state == tkinter.NORMAL else "arrow"
            self._btn_left_canvas.configure(cursor=cursor)
            self._btn_right_canvas.configure(cursor=cursor)

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "variable" in kwargs:
            if self._variable is not None and self._variable != "" and self._variable_callback_name:
                self._variable.trace_remove("write", self._variable_callback_name)
            self._variable = kwargs.pop("variable")
            if self._variable is not None and self._variable != "":
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)

        if "min_value" in kwargs:
            self._min_value = kwargs.pop("min_value")
            if self._min_value > self._max_value:
                self._min_value, self._max_value = self._max_value, self._min_value
            self._value = self._clamp(self._value)
            self._display_value()

        if "max_value" in kwargs:
            self._max_value = kwargs.pop("max_value")
            if self._min_value > self._max_value:
                self._min_value, self._max_value = self._max_value, self._min_value
            self._value = self._clamp(self._value)
            self._display_value()

        if "step" in kwargs:
            self._step = kwargs.pop("step")

        if "float_precision" in kwargs:
            self._float_precision = kwargs.pop("float_precision")
            self._value = self._clamp(self._value)
            self._display_value()

        if "start_value" in kwargs:
            # start_value is only for initial construction; ignore in configure
            kwargs.pop("start_value")

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "border_width":
            return self._border_width
        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "button_color":
            return self._button_color
        elif attribute_name == "button_hover_color":
            return self._button_hover_color
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "min_value":
            return self._min_value
        elif attribute_name == "max_value":
            return self._max_value
        elif attribute_name == "step":
            return self._step
        elif attribute_name == "float_precision":
            return self._float_precision
        elif attribute_name == "value":
            return self._value
        elif attribute_name == "start_value":
            return self._value
        else:
            return super().cget(attribute_name)

    # ==================================================================
    #  bind / unbind
    # ==================================================================

    def bind(self, sequence=None, command=None, add=True):
        """Bind to the internal tkinter.Entry widget."""
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._entry.bind(sequence, command, add=True)

    def unbind(self, sequence=None, funcid=None):
        """Unbind from the internal tkinter.Entry widget."""
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in"
                             " tkinter and its not clear whether the internal callbacks will"
                             " be unbinded or not")
        self._entry.unbind(sequence, None)
        self._create_bindings(sequence=sequence)
