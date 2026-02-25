import tkinter
from typing import Union, Tuple, Optional, Callable, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont
from .utility import pop_from_dict_by_set, check_kwargs_empty


class CTkNumberEntry(CTkBaseClass):
    """
    Numeric entry with increment/decrement buttons.

    Validates input for numbers only, supports int and float modes,
    min/max bounds, step increment, prefix/suffix display,
    and hold-to-repeat buttons with accelerating speed.

    Usage:
        entry = CTkNumberEntry(parent, from_=0, to=100, step=1)
        entry.set(50)
        value = entry.get()  # 50

        # Float mode with prefix/suffix
        price = CTkNumberEntry(parent, from_=0.0, to=999.99, step=0.01,
                               number_type=float, prefix="$", suffix=" USD")

        # With thousands separator
        big = CTkNumberEntry(parent, from_=0, to=1000000, step=1000,
                             thousands_separator=True)
    """

    _minimum_x_padding = 6

    # Hold-to-repeat timing constants (milliseconds)
    _REPEAT_DELAY = 400       # initial delay before repeating starts
    _REPEAT_INTERVAL_SLOW = 120  # interval at start of repeat
    _REPEAT_INTERVAL_FAST = 30   # interval after acceleration kicks in
    _REPEAT_ACCEL_AFTER = 8      # number of repeats before accelerating
    _REPEAT_LARGE_STEP_AFTER = 20  # number of repeats before using 10x step

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

                 from_: Union[int, float] = 0,
                 to: Union[int, float] = 100,
                 step: Union[int, float] = 1,
                 number_type: type = int,
                 prefix: str = "",
                 suffix: str = "",
                 thousands_separator: bool = False,
                 decimal_places: Optional[int] = None,

                 **kwargs):

        # transfer basic functionality to CTkBaseClass
        super().__init__(master=master, bg_color=bg_color, width=width, height=height)

        # configure grid: entry column expands, button column fixed
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # ── colors ──────────────────────────────────────────────
        self._fg_color = ThemeManager.theme["CTkEntry"]["fg_color"] if fg_color is None else self._check_color_type(fg_color, transparency=True)
        self._text_color = ThemeManager.theme["CTkEntry"]["text_color"] if text_color is None else self._check_color_type(text_color)
        self._border_color = ThemeManager.theme["CTkEntry"]["border_color"] if border_color is None else self._check_color_type(border_color)
        self._button_color = ThemeManager.theme["CTkComboBox"]["button_color"] if button_color is None else self._check_color_type(button_color)
        self._button_hover_color = ThemeManager.theme["CTkComboBox"]["button_hover_color"] if button_hover_color is None else self._check_color_type(button_hover_color)

        # ── shape ───────────────────────────────────────────────
        self._corner_radius = ThemeManager.theme["CTkEntry"]["corner_radius"] if corner_radius is None else corner_radius
        self._border_width = ThemeManager.theme["CTkEntry"]["border_width"] if border_width is None else border_width

        # ── numeric settings ────────────────────────────────────
        self._from = from_
        self._to = to
        self._step = step
        self._number_type = number_type
        self._prefix = prefix
        self._suffix = suffix
        self._thousands_separator = thousands_separator

        if decimal_places is not None:
            self._decimal_places = decimal_places
        elif number_type is float:
            # auto-detect from step
            step_str = str(step)
            if "." in step_str:
                self._decimal_places = len(step_str.split(".")[1])
            else:
                self._decimal_places = 2
        else:
            self._decimal_places = 0

        # ensure from_ <= to
        if self._from > self._to:
            self._from, self._to = self._to, self._from

        # ── state ───────────────────────────────────────────────
        self._state = state
        self._command = command
        self._variable = variable
        self._variable_callback_name: str = ""
        self._suppress_variable_update = False
        self._suppress_trace = False

        # internal numeric value
        self._value: Union[int, float] = self._clamp(self._number_type(from_))

        # ── font ────────────────────────────────────────────────
        self._font = CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)

        # ── hold-to-repeat state ────────────────────────────────
        self._repeat_after_id: Optional[str] = None
        self._repeat_count: int = 0
        self._repeat_direction: int = 0  # +1 or -1

        # ── canvas (background rendering) ───────────────────────
        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._current_width),
                                 height=self._apply_widget_scaling(self._current_height))
        self._draw_engine = DrawEngine(self._canvas)

        # ── entry widget ────────────────────────────────────────
        self._entry = tkinter.Entry(master=self,
                                    bd=0,
                                    width=1,
                                    highlightthickness=0,
                                    font=self._apply_font_scaling(self._font),
                                    state=self._state if self._state != "readonly" else "readonly",
                                    justify=tkinter.RIGHT)

        # ── button frame (increment/decrement) ──────────────────
        self._button_width = max(20, int(height * 0.7))
        self._button_frame = tkinter.Frame(self, bd=0, highlightthickness=0, width=self._button_width)
        self._button_frame.grid_rowconfigure(0, weight=1)
        self._button_frame.grid_rowconfigure(1, weight=1)
        self._button_frame.grid_columnconfigure(0, weight=1)

        self._btn_up_canvas = tkinter.Canvas(self._button_frame, bd=0, highlightthickness=0,
                                             cursor="hand2" if self._state == tkinter.NORMAL else "arrow")
        self._btn_down_canvas = tkinter.Canvas(self._button_frame, bd=0, highlightthickness=0,
                                               cursor="hand2" if self._state == tkinter.NORMAL else "arrow")

        self._btn_up_canvas.grid(row=0, column=0, sticky="nsew")
        self._btn_down_canvas.grid(row=1, column=0, sticky="nsew")

        check_kwargs_empty(kwargs, raise_error=True)

        # ── layout ──────────────────────────────────────────────
        self._create_grid()
        self._create_bindings()
        self._draw()
        self._display_value()

        # ── variable binding ────────────────────────────────────
        if self._variable is not None and self._variable != "":
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            # initialize from variable if it has a value
            try:
                var_val = self._variable.get()
                if var_val != "" and var_val != 0:
                    self._value = self._clamp(self._number_type(var_val))
                    self._display_value()
            except (ValueError, tkinter.TclError):
                pass

    # ══════════════════════════════════════════════════════════
    #  Layout & Bindings
    # ══════════════════════════════════════════════════════════

    def _create_grid(self):
        self._canvas.grid(column=0, row=0, columnspan=2, sticky="nswe")

        x_pad = self._apply_widget_scaling(
            max(self._minimum_x_padding, min(self._corner_radius, self._current_height / 2))
        )
        y_pad_top = self._apply_widget_scaling(self._border_width)
        y_pad_bot = self._apply_widget_scaling(self._border_width + 1)

        self._entry.grid(column=0, row=0, sticky="nswe",
                         padx=(x_pad, 2),
                         pady=(y_pad_top, y_pad_bot))

        self._button_frame.grid(column=1, row=0, sticky="nse",
                                padx=(0, self._apply_widget_scaling(self._border_width + 1)),
                                pady=(self._apply_widget_scaling(self._border_width),
                                      self._apply_widget_scaling(self._border_width)))

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
        if sequence is None or sequence == "<Prior>":
            self._entry.bind("<Prior>", self._on_page_up)  # Page Up
        if sequence is None or sequence == "<Next>":
            self._entry.bind("<Next>", self._on_page_down)  # Page Down

        # mouse scroll on the entry
        if sequence is None:
            self._entry.bind("<MouseWheel>", self._on_mouse_wheel)
            # Linux scroll events
            self._entry.bind("<Button-4>", lambda e: self._step_value(1))
            self._entry.bind("<Button-5>", lambda e: self._step_value(-1))

        # button press/release for hold-to-repeat
        if sequence is None:
            self._btn_up_canvas.bind("<ButtonPress-1>", self._on_btn_up_press)
            self._btn_up_canvas.bind("<ButtonRelease-1>", self._on_btn_release)
            self._btn_up_canvas.bind("<Leave>", self._on_btn_leave)
            self._btn_up_canvas.bind("<Enter>", self._on_btn_up_enter)

            self._btn_down_canvas.bind("<ButtonPress-1>", self._on_btn_down_press)
            self._btn_down_canvas.bind("<ButtonRelease-1>", self._on_btn_release)
            self._btn_down_canvas.bind("<Leave>", self._on_btn_leave)
            self._btn_down_canvas.bind("<Enter>", self._on_btn_down_enter)

    # ══════════════════════════════════════════════════════════
    #  Drawing
    # ══════════════════════════════════════════════════════════

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

            # button frame and canvases
            btn_color = self._apply_appearance_mode(self._button_color)
            self._button_frame.configure(bg=btn_color)
            self._btn_up_canvas.configure(bg=btn_color)
            self._btn_down_canvas.configure(bg=btn_color)

            # draw arrow glyphs
            self._draw_arrows()

    def _draw_arrows(self):
        """Draw the up/down arrow triangles on the button canvases."""
        self._btn_up_canvas.update_idletasks()
        self._btn_down_canvas.update_idletasks()

        arrow_color = self._apply_appearance_mode(self._text_color)

        for canvas, direction in [(self._btn_up_canvas, "up"), (self._btn_down_canvas, "down")]:
            canvas.delete("arrow")
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w <= 1 or h <= 1:
                # widget not yet mapped, schedule redraw
                self.after(50, self._draw_arrows)
                return

            cx = w / 2
            cy = h / 2
            size = min(w, h) * 0.3

            if direction == "up":
                points = [cx, cy - size * 0.5,
                          cx - size * 0.6, cy + size * 0.5,
                          cx + size * 0.6, cy + size * 0.5]
            else:
                points = [cx, cy + size * 0.5,
                          cx - size * 0.6, cy - size * 0.5,
                          cx + size * 0.6, cy - size * 0.5]

            canvas.create_polygon(points, fill=arrow_color, outline=arrow_color,
                                  tags="arrow")

    # ══════════════════════════════════════════════════════════
    #  Value Management
    # ══════════════════════════════════════════════════════════

    def _clamp(self, value: Union[int, float]) -> Union[int, float]:
        """Clamp value to [from_, to] range and cast to the correct type."""
        low = min(self._from, self._to)
        high = max(self._from, self._to)
        clamped = max(low, min(high, value))
        return self._number_type(clamped)

    def _format_value(self, value: Union[int, float]) -> str:
        """Format a numeric value for display, including prefix/suffix and separators."""
        if self._number_type is float:
            formatted = f"{value:.{self._decimal_places}f}"
        else:
            formatted = str(int(value))

        if self._thousands_separator:
            if self._number_type is float:
                integer_part, decimal_part = formatted.split(".")
                integer_part = self._add_thousands_sep(integer_part)
                formatted = f"{integer_part}.{decimal_part}"
            else:
                formatted = self._add_thousands_sep(formatted)

        return f"{self._prefix}{formatted}{self._suffix}"

    @staticmethod
    def _add_thousands_sep(integer_str: str) -> str:
        """Add comma separators to an integer string."""
        negative = integer_str.startswith("-")
        digits = integer_str.lstrip("-")
        result = ""
        for i, ch in enumerate(reversed(digits)):
            if i > 0 and i % 3 == 0:
                result = "," + result
            result = ch + result
        return ("-" + result) if negative else result

    def _parse_display(self, text: str) -> Optional[Union[int, float]]:
        """Parse the display string back to a numeric value, stripping prefix/suffix/separators."""
        # strip prefix
        if self._prefix and text.startswith(self._prefix):
            text = text[len(self._prefix):]
        # strip suffix
        if self._suffix and text.endswith(self._suffix):
            text = text[:-len(self._suffix)]

        # remove thousands separators
        text = text.replace(",", "")
        text = text.strip()

        if text == "" or text == "-" or text == ".":
            return None

        try:
            return self._number_type(text)
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
        parsed = self._parse_display(text)

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
        if self._state != tkinter.NORMAL:
            return

        # if entry is focused, commit current text first
        try:
            if self._entry.focus_get() == self._entry:
                self._commit_entry()
        except KeyError:
            pass

        step = self._step * multiplier
        new_value = self._value + (step * direction)

        # round to avoid floating point drift
        if self._number_type is float:
            new_value = round(new_value, self._decimal_places + 2)

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
        """Call the command callback with the current value."""
        if self._command is not None:
            self._command()

    def _variable_callback(self, var_name, index, mode):
        """Called when the bound variable changes externally."""
        if self._suppress_trace:
            return
        try:
            var_val = self._variable.get()
            new_value = self._clamp(self._number_type(var_val))
            if new_value != self._value:
                self._value = new_value
                self._display_value()
        except (ValueError, tkinter.TclError):
            pass

    # ══════════════════════════════════════════════════════════
    #  Event Handlers
    # ══════════════════════════════════════════════════════════

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

    def _on_page_up(self, event=None):
        self._step_value(1, multiplier=10.0)
        return "break"

    def _on_page_down(self, event=None):
        self._step_value(-1, multiplier=10.0)
        return "break"

    def _on_mouse_wheel(self, event=None):
        if self._state != tkinter.NORMAL:
            return
        if event.delta > 0:
            self._step_value(1)
        elif event.delta < 0:
            self._step_value(-1)

    # ── Button hover ────────────────────────────────────────

    def _on_btn_up_enter(self, event=None):
        if self._state == tkinter.NORMAL:
            hover = self._apply_appearance_mode(self._button_hover_color)
            self._btn_up_canvas.configure(bg=hover)

    def _on_btn_down_enter(self, event=None):
        if self._state == tkinter.NORMAL:
            hover = self._apply_appearance_mode(self._button_hover_color)
            self._btn_down_canvas.configure(bg=hover)

    def _on_btn_leave(self, event=None):
        """Reset button color and cancel repeat."""
        btn_color = self._apply_appearance_mode(self._button_color)
        self._btn_up_canvas.configure(bg=btn_color)
        self._btn_down_canvas.configure(bg=btn_color)

    # ── Hold-to-repeat ──────────────────────────────────────

    def _on_btn_up_press(self, event=None):
        if self._state != tkinter.NORMAL:
            return
        self._step_value(1)
        self._repeat_direction = 1
        self._repeat_count = 0
        self._cancel_repeat()
        self._repeat_after_id = self.after(self._REPEAT_DELAY, self._repeat_step)

    def _on_btn_down_press(self, event=None):
        if self._state != tkinter.NORMAL:
            return
        self._step_value(-1)
        self._repeat_direction = -1
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
            # linearly interpolate from slow to fast over the next 12 repeats
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

    # ══════════════════════════════════════════════════════════
    #  Scaling
    # ══════════════════════════════════════════════════════════

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
        self._canvas.grid(column=0, row=0, columnspan=2, sticky="nswe")

    # ══════════════════════════════════════════════════════════
    #  Lifecycle
    # ══════════════════════════════════════════════════════════

    def destroy(self):
        self._cancel_repeat()

        if self._variable is not None and self._variable_callback_name:
            self._variable.trace_remove("write", self._variable_callback_name)

        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)

        super().destroy()

    # ══════════════════════════════════════════════════════════
    #  Public API
    # ══════════════════════════════════════════════════════════

    def get(self) -> Union[int, float]:
        """Return the current numeric value.

        If the entry contains unparseable text (user is mid-edit), returns the
        last known valid value.
        """
        # try to parse what's currently shown
        parsed = self._parse_display(self._entry.get())
        if parsed is not None:
            return self._clamp(parsed)
        return self._value

    def set(self, value: Union[int, float, str]):
        """Set the value programmatically. The value is clamped to bounds."""
        if isinstance(value, str):
            try:
                value = self._number_type(value)
            except (ValueError, OverflowError):
                return

        new_value = self._clamp(self._number_type(value))
        self._value = new_value
        self._display_value()
        self._update_variable()

    def increment(self, multiplier: float = 1.0):
        """Increment the value by step * multiplier."""
        self._step_value(1, multiplier=multiplier)

    def decrement(self, multiplier: float = 1.0):
        """Decrement the value by step * multiplier."""
        self._step_value(-1, multiplier=multiplier)

    def focus(self):
        self._entry.focus()

    def focus_set(self):
        self._entry.focus_set()

    def focus_force(self):
        self._entry.focus_force()

    # ══════════════════════════════════════════════════════════
    #  configure / cget
    # ══════════════════════════════════════════════════════════

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
            self._btn_up_canvas.configure(cursor=cursor)
            self._btn_down_canvas.configure(cursor=cursor)

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "variable" in kwargs:
            if self._variable is not None and self._variable != "" and self._variable_callback_name:
                self._variable.trace_remove("write", self._variable_callback_name)
            self._variable = kwargs.pop("variable")
            if self._variable is not None and self._variable != "":
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)

        if "from_" in kwargs:
            self._from = kwargs.pop("from_")
            if self._from > self._to:
                self._from, self._to = self._to, self._from
            self._value = self._clamp(self._value)
            self._display_value()

        if "to" in kwargs:
            self._to = kwargs.pop("to")
            if self._from > self._to:
                self._from, self._to = self._to, self._from
            self._value = self._clamp(self._value)
            self._display_value()

        if "step" in kwargs:
            self._step = kwargs.pop("step")

        if "number_type" in kwargs:
            self._number_type = kwargs.pop("number_type")
            self._value = self._clamp(self._number_type(self._value))
            self._display_value()

        if "prefix" in kwargs:
            self._prefix = kwargs.pop("prefix")
            self._display_value()

        if "suffix" in kwargs:
            self._suffix = kwargs.pop("suffix")
            self._display_value()

        if "thousands_separator" in kwargs:
            self._thousands_separator = kwargs.pop("thousands_separator")
            self._display_value()

        if "decimal_places" in kwargs:
            self._decimal_places = kwargs.pop("decimal_places")
            self._display_value()

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
        elif attribute_name == "from_":
            return self._from
        elif attribute_name == "to":
            return self._to
        elif attribute_name == "step":
            return self._step
        elif attribute_name == "number_type":
            return self._number_type
        elif attribute_name == "prefix":
            return self._prefix
        elif attribute_name == "suffix":
            return self._suffix
        elif attribute_name == "thousands_separator":
            return self._thousands_separator
        elif attribute_name == "decimal_places":
            return self._decimal_places
        elif attribute_name == "value":
            return self._value
        else:
            return super().cget(attribute_name)

    # ══════════════════════════════════════════════════════════
    #  bind / unbind
    # ══════════════════════════════════════════════════════════

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
