import tkinter
from typing import Union, Tuple, Optional, Callable, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkTimePicker(CTkBaseClass):
    """
    Time picker widget with hour/minute/second spinners.

    Supports 12-hour (AM/PM) and 24-hour formats with
    scrollable spinner columns and keyboard navigation.

    Features:
        - Entry field showing selected time (HH:MM or HH:MM:SS)
        - Dropdown with hour/minute/second spinner columns
        - Up/down arrow buttons on each spinner column
        - Mouse scroll on spinners to change values
        - Keyboard: arrow keys to change values, Tab between fields, Escape to close
        - 12-hour (AM/PM) and 24-hour mode
        - min_time / max_time bounds
        - StringVar variable binding
        - Command callback on time change
        - Configurable: width, height, corner_radius, border_width, all color params
        - State: normal / disabled / readonly

    Usage:
        picker = CTkTimePicker(parent, time_format="24h")
        picker.set_time(14, 30)
        current = picker.get_time()  # (14, 30, 0)
    """

    # Clock icon (Unicode)
    _CLOCK_ICON = "\U0001F553"

    def __init__(self,
                 master: Any,
                 width: int = 200,
                 height: int = 28,
                 corner_radius: Optional[int] = None,
                 border_width: Optional[int] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 button_color: Optional[Union[str, Tuple[str, str]]] = None,
                 button_hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color_disabled: Optional[Union[str, Tuple[str, str]]] = None,
                 dropdown_fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 dropdown_border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 dropdown_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 dropdown_header_color: Optional[Union[str, Tuple[str, str]]] = None,
                 selected_color: Optional[Union[str, Tuple[str, str]]] = None,
                 selected_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 arrow_color: Optional[Union[str, Tuple[str, str]]] = None,
                 arrow_hover_color: Optional[Union[str, Tuple[str, str]]] = None,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 dropdown_font: Optional[Union[tuple, CTkFont]] = None,
                 time_format: str = "24h",
                 show_seconds: bool = False,
                 command: Optional[Callable[[tuple], Any]] = None,
                 variable: Optional[tkinter.StringVar] = None,
                 min_time: Optional[Tuple[int, int, int]] = None,
                 max_time: Optional[Tuple[int, int, int]] = None,
                 state: str = tkinter.NORMAL,
                 **kwargs):

        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # shape
        self._corner_radius = ThemeManager.theme["CTkEntry"]["corner_radius"] if corner_radius is None else corner_radius
        self._border_width = ThemeManager.theme["CTkEntry"]["border_width"] if border_width is None else border_width

        # colors - entry area
        self._fg_color = ThemeManager.theme["CTkEntry"]["fg_color"] if fg_color is None else self._check_color_type(fg_color)
        self._border_color = ThemeManager.theme["CTkEntry"]["border_color"] if border_color is None else self._check_color_type(border_color)
        self._text_color = ThemeManager.theme["CTkEntry"]["text_color"] if text_color is None else self._check_color_type(text_color)
        self._text_color_disabled = ThemeManager.theme["CTkComboBox"]["text_color_disabled"] if text_color_disabled is None else self._check_color_type(text_color_disabled)
        self._button_color = ThemeManager.theme["CTkComboBox"]["button_color"] if button_color is None else self._check_color_type(button_color)
        self._button_hover_color = ThemeManager.theme["CTkComboBox"]["button_hover_color"] if button_hover_color is None else self._check_color_type(button_hover_color)

        # colors - dropdown spinner
        self._dropdown_fg_color = dropdown_fg_color or ("#F9F9FA", "#2B2B2B")
        self._dropdown_border_color = dropdown_border_color or ("#979DA2", "#565B5E")
        self._dropdown_text_color = dropdown_text_color or ("#1A1A1A", "#DCE4EE")
        self._dropdown_header_color = dropdown_header_color or ("#3B8ED0", "#1F6AA5")
        self._selected_color = selected_color or ("#3B8ED0", "#1F6AA5")
        self._selected_text_color = selected_text_color or ("#FFFFFF", "#FFFFFF")
        self._hover_color = hover_color or ("#D0E0F0", "#3D3D3D")
        self._arrow_color = arrow_color or ("#3B8ED0", "#1F6AA5")
        self._arrow_hover_color = arrow_hover_color or ("#36719F", "#144870")

        # font
        self._font = CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)
        self._dropdown_font = dropdown_font

        # time state
        self._time_format = time_format  # "12h" or "24h"
        self._show_seconds = show_seconds
        self._command = command
        self._variable = variable
        self._min_time = min_time  # (h, m, s) tuple or None
        self._max_time = max_time  # (h, m, s) tuple or None
        self._state = state

        # current time values (always stored in 24h internal representation)
        self._hour: int = 0
        self._minute: int = 0
        self._second: int = 0
        self._time_set: bool = False

        # dropdown state
        self._dropdown_open: bool = False
        self._dropdown_window: Optional[tkinter.Toplevel] = None
        self._focused_spinner: Optional[str] = None  # "hour", "minute", "second", "ampm"
        self._spinner_labels: dict = {}  # maps (column, row) -> label widget
        self._spinner_frames: dict = {}  # maps column name -> frame widget
        self._repeat_after_ids: list = []  # after() ids for auto-repeat arrows

        # variable callback tracking
        self._variable_callback_name: str = ""
        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._on_variable_change)

        # grid layout (1x1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # canvas for rounded background
        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._draw_engine = DrawEngine(self._canvas)

        # inner entry (read-only)
        self._entry = tkinter.Entry(master=self,
                                    state="readonly",
                                    width=1,
                                    bd=0,
                                    justify="center",
                                    highlightthickness=0,
                                    readonlybackground=self._apply_appearance_mode(self._fg_color),
                                    font=self._apply_font_scaling(self._font))

        self._create_grid()
        self._create_bindings()
        self._draw()

        # if variable has an initial value, try to parse it
        if self._variable is not None and self._variable.get():
            self._parse_variable_value()

    # ------------------------------------------------------------------
    #  Grid & Bindings
    # ------------------------------------------------------------------

    def _create_grid(self):
        self._canvas.grid(row=0, column=0, rowspan=1, columnspan=1, sticky="nsew")

        left_section_width = self._current_width - self._current_height
        self._entry.grid(row=0, column=0, rowspan=1, columnspan=1, sticky="ew",
                         padx=(max(self._apply_widget_scaling(self._corner_radius),
                                   self._apply_widget_scaling(3)),
                               max(self._apply_widget_scaling(self._current_width - left_section_width + 3),
                                   self._apply_widget_scaling(3))),
                         pady=self._apply_widget_scaling(self._border_width))

    def _create_bindings(self, sequence: Optional[str] = None):
        if sequence is None:
            self._canvas.tag_bind("right_parts", "<Enter>", self._on_button_enter)
            self._canvas.tag_bind("dropdown_arrow", "<Enter>", self._on_button_enter)
            self._canvas.tag_bind("right_parts", "<Leave>", self._on_button_leave)
            self._canvas.tag_bind("dropdown_arrow", "<Leave>", self._on_button_leave)
            self._canvas.tag_bind("right_parts", "<Button-1>", self._on_button_click)
            self._canvas.tag_bind("dropdown_arrow", "<Button-1>", self._on_button_click)
            self._entry.bind("<Button-1>", self._on_entry_click)
            self._entry.bind("<Key-Escape>", self._on_escape)
            self._entry.bind("<Key-Return>", self._on_return)

    # ------------------------------------------------------------------
    #  Drawing
    # ------------------------------------------------------------------

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        left_section_width = self._current_width - self._current_height
        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border_vertical_split(
            self._apply_widget_scaling(self._current_width),
            self._apply_widget_scaling(self._current_height),
            self._apply_widget_scaling(self._corner_radius),
            self._apply_widget_scaling(self._border_width),
            self._apply_widget_scaling(left_section_width))

        requires_recoloring_2 = self._draw_engine.draw_dropdown_arrow(
            self._apply_widget_scaling(self._current_width - (self._current_height / 2)),
            self._apply_widget_scaling(self._current_height / 2),
            self._apply_widget_scaling(self._current_height / 3))

        if no_color_updates is False or requires_recoloring or requires_recoloring_2:
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

            self._canvas.itemconfig("inner_parts_left",
                                    outline=self._apply_appearance_mode(self._fg_color),
                                    fill=self._apply_appearance_mode(self._fg_color))
            self._canvas.itemconfig("border_parts_left",
                                    outline=self._apply_appearance_mode(self._border_color),
                                    fill=self._apply_appearance_mode(self._border_color))
            self._canvas.itemconfig("inner_parts_right",
                                    outline=self._apply_appearance_mode(self._button_color),
                                    fill=self._apply_appearance_mode(self._button_color))
            self._canvas.itemconfig("border_parts_right",
                                    outline=self._apply_appearance_mode(self._button_color),
                                    fill=self._apply_appearance_mode(self._button_color))

            self._entry.configure(
                bg=self._apply_appearance_mode(self._fg_color),
                fg=self._apply_appearance_mode(self._text_color),
                readonlybackground=self._apply_appearance_mode(self._fg_color),
                disabledbackground=self._apply_appearance_mode(self._fg_color),
                disabledforeground=self._apply_appearance_mode(self._text_color_disabled),
                highlightcolor=self._apply_appearance_mode(self._fg_color),
                insertbackground=self._apply_appearance_mode(self._text_color))

            if self._state == tkinter.DISABLED:
                self._canvas.itemconfig("dropdown_arrow",
                                        fill=self._apply_appearance_mode(self._text_color_disabled))
            else:
                self._canvas.itemconfig("dropdown_arrow",
                                        fill=self._apply_appearance_mode(self._text_color))

    # ------------------------------------------------------------------
    #  Button hover / click
    # ------------------------------------------------------------------

    def _on_button_enter(self, event=None):
        if self._state != tkinter.DISABLED:
            self._canvas.itemconfig("inner_parts_right",
                                    outline=self._apply_appearance_mode(self._button_hover_color),
                                    fill=self._apply_appearance_mode(self._button_hover_color))
            self._canvas.itemconfig("border_parts_right",
                                    outline=self._apply_appearance_mode(self._button_hover_color),
                                    fill=self._apply_appearance_mode(self._button_hover_color))

    def _on_button_leave(self, event=None):
        self._canvas.itemconfig("inner_parts_right",
                                outline=self._apply_appearance_mode(self._button_color),
                                fill=self._apply_appearance_mode(self._button_color))
        self._canvas.itemconfig("border_parts_right",
                                outline=self._apply_appearance_mode(self._button_color),
                                fill=self._apply_appearance_mode(self._button_color))

    def _on_button_click(self, event=None):
        if self._state != tkinter.DISABLED:
            if self._dropdown_open:
                self._close_dropdown()
            else:
                self._open_dropdown()

    def _on_entry_click(self, event=None):
        if self._state != tkinter.DISABLED:
            if self._dropdown_open:
                self._close_dropdown()
            else:
                self._open_dropdown()

    # ------------------------------------------------------------------
    #  Keyboard
    # ------------------------------------------------------------------

    def _on_escape(self, event=None):
        if self._dropdown_open:
            self._close_dropdown()

    def _on_return(self, event=None):
        if self._dropdown_open:
            self._close_dropdown()

    # ------------------------------------------------------------------
    #  Variable binding
    # ------------------------------------------------------------------

    def _on_variable_change(self, var_name, index, mode):
        """Called when the linked StringVar changes externally."""
        self._parse_variable_value()

    def _parse_variable_value(self):
        """Try to parse the variable's string value into a time."""
        if self._variable is None:
            return
        val = self._variable.get()
        if not val:
            self._time_set = False
            self._hour = 0
            self._minute = 0
            self._second = 0
            self._update_entry_display()
            return
        try:
            self._parse_time_string(val)
            self._update_entry_display()
        except ValueError:
            pass

    def _parse_time_string(self, text: str):
        """Parse a time string and set internal values. Supports HH:MM, HH:MM:SS,
        HH:MM AM/PM, and HH:MM:SS AM/PM formats."""
        text = text.strip()
        is_12h = False
        is_pm = False

        # check for AM/PM suffix
        upper = text.upper()
        if upper.endswith("AM") or upper.endswith("PM"):
            is_12h = True
            is_pm = upper.endswith("PM")
            text = text[:-2].strip()

        parts = text.split(":")
        if len(parts) < 2 or len(parts) > 3:
            raise ValueError(f"Invalid time format: {text}")

        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) == 3 else 0

        if is_12h:
            if hour < 1 or hour > 12:
                raise ValueError(f"Invalid 12h hour: {hour}")
            if hour == 12:
                hour = 0
            if is_pm:
                hour += 12

        if not (0 <= hour <= 23):
            raise ValueError(f"Invalid hour: {hour}")
        if not (0 <= minute <= 59):
            raise ValueError(f"Invalid minute: {minute}")
        if not (0 <= second <= 59):
            raise ValueError(f"Invalid second: {second}")

        self._hour = hour
        self._minute = minute
        self._second = second
        self._time_set = True

    def _sync_variable(self):
        """Push the current time to the variable."""
        if self._variable is not None:
            if self._time_set:
                self._variable.set(self._format_time())
            else:
                self._variable.set("")

    # ------------------------------------------------------------------
    #  Time formatting
    # ------------------------------------------------------------------

    def _format_time(self) -> str:
        """Format the current time as a string based on time_format and show_seconds."""
        h, m, s = self._hour, self._minute, self._second

        if self._time_format == "12h":
            period = "AM"
            display_h = h
            if h == 0:
                display_h = 12
            elif h == 12:
                period = "PM"
            elif h > 12:
                display_h = h - 12
                period = "PM"

            if self._show_seconds:
                return f"{display_h:02d}:{m:02d}:{s:02d} {period}"
            else:
                return f"{display_h:02d}:{m:02d} {period}"
        else:
            if self._show_seconds:
                return f"{h:02d}:{m:02d}:{s:02d}"
            else:
                return f"{h:02d}:{m:02d}"

    # ------------------------------------------------------------------
    #  Entry display
    # ------------------------------------------------------------------

    def _update_entry_display(self):
        """Update the readonly entry field text."""
        self._entry.configure(state="normal")
        self._entry.delete(0, tkinter.END)
        if self._time_set:
            self._entry.insert(0, self._format_time())
        self._entry.configure(state="readonly")

    # ------------------------------------------------------------------
    #  Time bounds checking
    # ------------------------------------------------------------------

    def _time_to_seconds(self, h: int, m: int, s: int) -> int:
        """Convert h, m, s to total seconds for comparison."""
        return h * 3600 + m * 60 + s

    def _is_time_in_range(self, h: int, m: int, s: int) -> bool:
        """Check if a time falls within the min/max bounds."""
        total = self._time_to_seconds(h, m, s)
        if self._min_time is not None:
            min_total = self._time_to_seconds(*self._min_time)
            if total < min_total:
                return False
        if self._max_time is not None:
            max_total = self._time_to_seconds(*self._max_time)
            if total > max_total:
                return False
        return True

    def _clamp_time(self):
        """Clamp the current time to min/max bounds."""
        total = self._time_to_seconds(self._hour, self._minute, self._second)
        if self._min_time is not None:
            min_total = self._time_to_seconds(*self._min_time)
            if total < min_total:
                self._hour, self._minute, self._second = self._min_time
        if self._max_time is not None:
            max_total = self._time_to_seconds(*self._max_time)
            if total > max_total:
                self._hour, self._minute, self._second = self._max_time

    # ------------------------------------------------------------------
    #  Dropdown spinner
    # ------------------------------------------------------------------

    def _open_dropdown(self):
        if self._dropdown_open:
            return

        self._dropdown_open = True

        # ensure valid initial time if not yet set
        if not self._time_set:
            self._hour = 0
            self._minute = 0
            self._second = 0
            self._time_set = True
            self._update_entry_display()
            self._sync_variable()

        # position below the entry widget
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()

        self._dropdown_window = tkinter.Toplevel(self)
        self._dropdown_window.withdraw()
        self._dropdown_window.overrideredirect(True)
        self._dropdown_window.resizable(False, False)

        # prevent it from appearing in the taskbar on Windows
        self._dropdown_window.transient(self.winfo_toplevel())

        self._build_spinners()

        self._dropdown_window.update_idletasks()

        # ensure dropdown does not go off-screen
        dd_width = self._dropdown_window.winfo_reqwidth()
        dd_height = self._dropdown_window.winfo_reqheight()
        screen_width = self._dropdown_window.winfo_screenwidth()
        screen_height = self._dropdown_window.winfo_screenheight()

        if x + dd_width > screen_width:
            x = screen_width - dd_width
        if y + dd_height > screen_height:
            y = self.winfo_rooty() - dd_height

        self._dropdown_window.geometry(f"+{x}+{y}")
        self._dropdown_window.deiconify()

        # grab focus so we can detect clicks outside
        self._dropdown_window.focus_set()
        self._dropdown_window.bind("<FocusOut>", self._on_dropdown_focus_out)
        self._dropdown_window.bind("<Key-Escape>", lambda e: self._close_dropdown())
        self._dropdown_window.bind("<Key-Return>", lambda e: self._close_dropdown())

        # keyboard navigation
        self._dropdown_window.bind("<Up>", self._on_key_up)
        self._dropdown_window.bind("<Down>", self._on_key_down)
        self._dropdown_window.bind("<Tab>", self._on_key_tab)
        self._dropdown_window.bind("<Shift-Tab>", self._on_key_shift_tab)

        self._focused_spinner = "hour"

    def _close_dropdown(self):
        if not self._dropdown_open:
            return

        self._dropdown_open = False

        # cancel any pending auto-repeat callbacks
        for after_id in self._repeat_after_ids:
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self._repeat_after_ids.clear()

        if self._dropdown_window is not None:
            self._dropdown_window.destroy()
            self._dropdown_window = None

        self._spinner_labels.clear()
        self._spinner_frames.clear()
        self._focused_spinner = None

    def _on_dropdown_focus_out(self, event=None):
        """Close the dropdown when it loses focus, but only if focus went
        somewhere outside the dropdown window."""
        if self._dropdown_window is None:
            return
        self._dropdown_window.after(100, self._check_focus_and_close)

    def _check_focus_and_close(self):
        """Check whether the focus has truly left the dropdown."""
        if self._dropdown_window is None or not self._dropdown_open:
            return

        try:
            focused = self._dropdown_window.focus_get()
        except KeyError:
            focused = None

        if focused is None:
            self._close_dropdown()
            return

        try:
            focused_path = str(focused)
            dropdown_path = str(self._dropdown_window)
            if not focused_path.startswith(dropdown_path):
                self._close_dropdown()
        except Exception:
            self._close_dropdown()

    # ------------------------------------------------------------------
    #  Spinner building
    # ------------------------------------------------------------------

    def _build_spinners(self):
        """Build the spinner columns inside the dropdown toplevel."""
        if self._dropdown_window is None:
            return

        # Clear existing content
        for widget in self._dropdown_window.winfo_children():
            widget.destroy()
        self._spinner_labels.clear()
        self._spinner_frames.clear()

        dd_fg = self._apply_appearance_mode(self._dropdown_fg_color)
        dd_border = self._apply_appearance_mode(self._dropdown_border_color)
        dd_text = self._apply_appearance_mode(self._dropdown_text_color)
        dd_header = self._apply_appearance_mode(self._dropdown_header_color)
        sel_bg = self._apply_appearance_mode(self._selected_color)
        sel_fg = self._apply_appearance_mode(self._selected_text_color)
        arr_color = self._apply_appearance_mode(self._arrow_color)
        arr_hover = self._apply_appearance_mode(self._arrow_hover_color)

        # Resolve fonts
        if self._dropdown_font is not None:
            if isinstance(self._dropdown_font, CTkFont):
                spinner_font = (self._dropdown_font.cget("family"),
                                self._dropdown_font.cget("size"),
                                self._dropdown_font.cget("weight"))
            else:
                spinner_font = self._dropdown_font
        else:
            spinner_font = ("Segoe UI", 12)

        header_font = (spinner_font[0], max(8, spinner_font[1] - 1)) if len(spinner_font) >= 2 else ("Segoe UI", 10)
        arrow_font = (spinner_font[0], spinner_font[1] + 2, "bold") if len(spinner_font) >= 2 else ("Segoe UI", 14, "bold")
        value_font = (spinner_font[0], spinner_font[1] + 4) if len(spinner_font) >= 2 else ("Segoe UI", 16)
        selected_value_font = (spinner_font[0], spinner_font[1] + 4, "bold") if len(spinner_font) >= 2 else ("Segoe UI", 16, "bold")

        # Outer frame with border effect
        outer_frame = tkinter.Frame(self._dropdown_window, bg=dd_border, padx=1, pady=1)
        outer_frame.pack(fill="both", expand=True)

        inner_frame = tkinter.Frame(outer_frame, bg=dd_fg)
        inner_frame.pack(fill="both", expand=True, padx=1, pady=1)

        # ---- Header ----
        header_frame = tkinter.Frame(inner_frame, bg=dd_fg)
        header_frame.pack(fill="x", padx=6, pady=(8, 2))

        time_label_text = "Select Time"
        header_label = tkinter.Label(header_frame, text=time_label_text, font=header_font,
                                     fg=dd_header, bg=dd_fg)
        header_label.pack()

        # ---- Separator ----
        sep = tkinter.Frame(inner_frame, bg=dd_border, height=1)
        sep.pack(fill="x", padx=6, pady=(4, 6))

        # ---- Spinners container ----
        spinners_frame = tkinter.Frame(inner_frame, bg=dd_fg)
        spinners_frame.pack(padx=8, pady=(0, 8))

        columns = []
        columns.append(("hour", "Hr", self._hour, 23 if self._time_format == "24h" else 12,
                         0 if self._time_format == "24h" else 1))
        columns.append(("minute", "Min", self._minute, 59, 0))
        if self._show_seconds:
            columns.append(("second", "Sec", self._second, 59, 0))

        col_index = 0
        for i, (name, label_text, current_val, max_val, min_val) in enumerate(columns):
            if i > 0:
                # colon separator between spinners
                colon_label = tkinter.Label(spinners_frame, text=":", font=value_font,
                                            fg=dd_text, bg=dd_fg)
                colon_label.grid(row=1, column=col_index, padx=2, pady=0)
                col_index += 1

            self._build_single_spinner(
                spinners_frame, col_index, name, label_text, current_val,
                min_val, max_val, dd_fg, dd_text, dd_header, sel_bg, sel_fg,
                arr_color, arr_hover, header_font, value_font, selected_value_font,
                arrow_font)
            col_index += 1

        # ---- AM/PM toggle (12h mode only) ----
        if self._time_format == "12h":
            colon_label = tkinter.Label(spinners_frame, text=" ", font=value_font,
                                        fg=dd_text, bg=dd_fg)
            colon_label.grid(row=1, column=col_index, padx=1, pady=0)
            col_index += 1

            self._build_ampm_spinner(
                spinners_frame, col_index, dd_fg, dd_text, dd_header, sel_bg, sel_fg,
                arr_color, arr_hover, header_font, value_font, selected_value_font,
                arrow_font)

        # ---- Now button ----
        now_frame = tkinter.Frame(inner_frame, bg=dd_fg)
        now_frame.pack(fill="x", padx=8, pady=(2, 8))

        now_btn = tkinter.Label(now_frame, text="Now", font=header_font,
                                fg=dd_header, bg=dd_fg, cursor="hand2")
        now_btn.pack()
        now_btn.bind("<Button-1>", lambda e: self._set_to_now())
        now_btn.bind("<Enter>", lambda e: now_btn.configure(fg=arr_hover))
        now_btn.bind("<Leave>", lambda e: now_btn.configure(fg=dd_header))

    def _build_single_spinner(self, parent, col, name, label_text, current_val,
                              min_val, max_val, dd_fg, dd_text, dd_header, sel_bg,
                              sel_fg, arr_color, arr_hover, header_font, value_font,
                              selected_value_font, arrow_font):
        """Build a single spinner column (hour, minute, or second)."""
        spinner_frame = tkinter.Frame(parent, bg=dd_fg)
        spinner_frame.grid(row=0, column=col, rowspan=3, padx=4, pady=0)
        self._spinner_frames[name] = spinner_frame

        # Column header label
        col_header = tkinter.Label(spinner_frame, text=label_text, font=header_font,
                                   fg=dd_header, bg=dd_fg)
        col_header.pack(pady=(0, 4))

        # Up arrow
        up_btn = tkinter.Label(spinner_frame, text="\u25B2", font=arrow_font,
                               fg=arr_color, bg=dd_fg, cursor="hand2")
        up_btn.pack(pady=(0, 2))
        up_btn.bind("<Button-1>", lambda e, n=name: self._spinner_increment(n, 1))
        up_btn.bind("<Enter>", lambda e, b=up_btn: b.configure(fg=arr_hover))
        up_btn.bind("<Leave>", lambda e, b=up_btn: b.configure(fg=arr_color))

        # Value display area: show 3 values (prev, current, next) for scroll context
        values_frame = tkinter.Frame(spinner_frame, bg=dd_fg)
        values_frame.pack(pady=2)

        # previous value (dimmed)
        prev_val = (current_val - 1) % (max_val - min_val + 1) + min_val
        prev_label = tkinter.Label(values_frame, text=f"{prev_val:02d}", font=value_font,
                                   fg=self._apply_appearance_mode(self._hover_color), bg=dd_fg,
                                   width=3)
        prev_label.pack(pady=1)
        self._spinner_labels[(name, "prev")] = prev_label

        # current value (selected, highlighted)
        current_frame = tkinter.Frame(values_frame, bg=sel_bg, padx=4, pady=2)
        current_frame.pack(pady=2)
        current_label = tkinter.Label(current_frame, text=f"{current_val:02d}",
                                      font=selected_value_font,
                                      fg=sel_fg, bg=sel_bg, width=3)
        current_label.pack()
        self._spinner_labels[(name, "current")] = current_label
        self._spinner_labels[(name, "current_frame")] = current_frame

        # next value (dimmed)
        next_val = (current_val + 1 - min_val) % (max_val - min_val + 1) + min_val
        next_label = tkinter.Label(values_frame, text=f"{next_val:02d}", font=value_font,
                                   fg=self._apply_appearance_mode(self._hover_color), bg=dd_fg,
                                   width=3)
        next_label.pack(pady=1)
        self._spinner_labels[(name, "next")] = next_label

        # Down arrow
        down_btn = tkinter.Label(spinner_frame, text="\u25BC", font=arrow_font,
                                 fg=arr_color, bg=dd_fg, cursor="hand2")
        down_btn.pack(pady=(2, 0))
        down_btn.bind("<Button-1>", lambda e, n=name: self._spinner_increment(n, -1))
        down_btn.bind("<Enter>", lambda e, b=down_btn: b.configure(fg=arr_hover))
        down_btn.bind("<Leave>", lambda e, b=down_btn: b.configure(fg=arr_color))

        # Mouse wheel binding on the entire spinner frame and all children
        self._bind_mousewheel(spinner_frame, name)
        self._bind_mousewheel(up_btn, name)
        self._bind_mousewheel(down_btn, name)
        self._bind_mousewheel(values_frame, name)
        self._bind_mousewheel(prev_label, name)
        self._bind_mousewheel(current_label, name)
        self._bind_mousewheel(current_frame, name)
        self._bind_mousewheel(next_label, name)

        # Click on prev/next to jump
        prev_label.configure(cursor="hand2")
        prev_label.bind("<Button-1>", lambda e, n=name: self._spinner_increment(n, -1))
        next_label.configure(cursor="hand2")
        next_label.bind("<Button-1>", lambda e, n=name: self._spinner_increment(n, 1))

    def _build_ampm_spinner(self, parent, col, dd_fg, dd_text, dd_header, sel_bg,
                            sel_fg, arr_color, arr_hover, header_font, value_font,
                            selected_value_font, arrow_font):
        """Build the AM/PM toggle spinner."""
        spinner_frame = tkinter.Frame(parent, bg=dd_fg)
        spinner_frame.grid(row=0, column=col, rowspan=3, padx=4, pady=0)
        self._spinner_frames["ampm"] = spinner_frame

        # Column header
        col_header = tkinter.Label(spinner_frame, text="", font=header_font,
                                   fg=dd_header, bg=dd_fg)
        col_header.pack(pady=(0, 4))

        # Up arrow
        up_btn = tkinter.Label(spinner_frame, text="\u25B2", font=arrow_font,
                               fg=arr_color, bg=dd_fg, cursor="hand2")
        up_btn.pack(pady=(0, 2))
        up_btn.bind("<Button-1>", lambda e: self._toggle_ampm())
        up_btn.bind("<Enter>", lambda e, b=up_btn: b.configure(fg=arr_hover))
        up_btn.bind("<Leave>", lambda e, b=up_btn: b.configure(fg=arr_color))

        # Value display
        values_frame = tkinter.Frame(spinner_frame, bg=dd_fg)
        values_frame.pack(pady=2)

        # spacer for alignment with other spinners
        spacer_top = tkinter.Label(values_frame, text="", font=value_font, bg=dd_fg, width=3)
        spacer_top.pack(pady=1)

        is_pm = self._hour >= 12
        current_text = "PM" if is_pm else "AM"

        current_frame = tkinter.Frame(values_frame, bg=sel_bg, padx=4, pady=2)
        current_frame.pack(pady=2)
        current_label = tkinter.Label(current_frame, text=current_text,
                                      font=selected_value_font,
                                      fg=sel_fg, bg=sel_bg, width=3)
        current_label.pack()
        self._spinner_labels[("ampm", "current")] = current_label
        self._spinner_labels[("ampm", "current_frame")] = current_frame

        spacer_bottom = tkinter.Label(values_frame, text="", font=value_font, bg=dd_fg, width=3)
        spacer_bottom.pack(pady=1)

        # Down arrow
        down_btn = tkinter.Label(spinner_frame, text="\u25BC", font=arrow_font,
                                 fg=arr_color, bg=dd_fg, cursor="hand2")
        down_btn.pack(pady=(2, 0))
        down_btn.bind("<Button-1>", lambda e: self._toggle_ampm())
        down_btn.bind("<Enter>", lambda e, b=down_btn: b.configure(fg=arr_hover))
        down_btn.bind("<Leave>", lambda e, b=down_btn: b.configure(fg=arr_color))

        # Mouse wheel
        self._bind_mousewheel(spinner_frame, "ampm")
        self._bind_mousewheel(up_btn, "ampm")
        self._bind_mousewheel(down_btn, "ampm")
        self._bind_mousewheel(values_frame, "ampm")
        self._bind_mousewheel(current_label, "ampm")
        self._bind_mousewheel(current_frame, "ampm")

    def _bind_mousewheel(self, widget, spinner_name: str):
        """Bind mouse wheel events to a widget for a given spinner column."""
        def on_mousewheel(event):
            # Windows and macOS: event.delta is positive for up, negative for down
            # Linux: Button-4 is up, Button-5 is down
            if event.delta > 0:
                delta = 1
            elif event.delta < 0:
                delta = -1
            else:
                delta = 0

            if spinner_name == "ampm":
                if delta != 0:
                    self._toggle_ampm()
            else:
                self._spinner_increment(spinner_name, delta)

        widget.bind("<MouseWheel>", on_mousewheel)

        # Linux scroll support
        def on_scroll_up(event):
            if spinner_name == "ampm":
                self._toggle_ampm()
            else:
                self._spinner_increment(spinner_name, 1)

        def on_scroll_down(event):
            if spinner_name == "ampm":
                self._toggle_ampm()
            else:
                self._spinner_increment(spinner_name, -1)

        widget.bind("<Button-4>", on_scroll_up)
        widget.bind("<Button-5>", on_scroll_down)

    # ------------------------------------------------------------------
    #  Spinner value changes
    # ------------------------------------------------------------------

    def _spinner_increment(self, name: str, delta: int):
        """Increment or decrement a spinner value by delta."""
        if name == "hour":
            if self._time_format == "24h":
                self._hour = (self._hour + delta) % 24
            else:
                # 12h mode: hour cycles 1-12 in display, but stored as 0-23
                display_h = self._hour % 12
                if display_h == 0:
                    display_h = 12
                display_h += delta
                if display_h > 12:
                    display_h = 1
                elif display_h < 1:
                    display_h = 12
                # convert back to 24h
                is_pm = self._hour >= 12
                if display_h == 12:
                    self._hour = 12 if is_pm else 0
                else:
                    self._hour = display_h + (12 if is_pm else 0)
        elif name == "minute":
            self._minute = (self._minute + delta) % 60
        elif name == "second":
            self._second = (self._second + delta) % 60

        self._clamp_time()
        self._update_spinner_display(name)
        self._update_entry_display()
        self._sync_variable()
        self._fire_command()

    def _toggle_ampm(self):
        """Toggle between AM and PM."""
        if self._hour < 12:
            self._hour += 12
        else:
            self._hour -= 12

        self._clamp_time()
        self._update_spinner_display("ampm")
        # also update hour display since internal hour changed
        if ("hour", "current") in self._spinner_labels:
            self._update_spinner_display("hour")
        self._update_entry_display()
        self._sync_variable()
        self._fire_command()

    def _update_spinner_display(self, name: str):
        """Update the visual display of a spinner column."""
        if (name, "current") not in self._spinner_labels:
            return

        current_label = self._spinner_labels[(name, "current")]

        if name == "ampm":
            current_label.configure(text="PM" if self._hour >= 12 else "AM")
            return

        # Determine current value and range
        if name == "hour":
            if self._time_format == "24h":
                val = self._hour
                min_val, max_val = 0, 23
            else:
                val = self._hour % 12
                if val == 0:
                    val = 12
                min_val, max_val = 1, 12
        elif name == "minute":
            val = self._minute
            min_val, max_val = 0, 59
        elif name == "second":
            val = self._second
            min_val, max_val = 0, 59
        else:
            return

        current_label.configure(text=f"{val:02d}")

        # Update prev/next labels
        range_size = max_val - min_val + 1
        prev_val = (val - 1 - min_val) % range_size + min_val
        next_val = (val + 1 - min_val) % range_size + min_val

        if (name, "prev") in self._spinner_labels:
            self._spinner_labels[(name, "prev")].configure(text=f"{prev_val:02d}")
        if (name, "next") in self._spinner_labels:
            self._spinner_labels[(name, "next")].configure(text=f"{next_val:02d}")

    def _set_to_now(self):
        """Set the time to the current system time."""
        import datetime
        now = datetime.datetime.now()
        self._hour = now.hour
        self._minute = now.minute
        self._second = now.second
        self._time_set = True

        self._clamp_time()

        # Update all spinner displays
        for name in ["hour", "minute", "second", "ampm"]:
            self._update_spinner_display(name)
        self._update_entry_display()
        self._sync_variable()
        self._fire_command()

    def _fire_command(self):
        """Fire the command callback with the current time tuple."""
        if self._command is not None:
            self._command((self._hour, self._minute, self._second))

    # ------------------------------------------------------------------
    #  Keyboard navigation in dropdown
    # ------------------------------------------------------------------

    def _on_key_up(self, event=None):
        """Handle Up arrow key in dropdown."""
        if self._focused_spinner == "ampm":
            self._toggle_ampm()
        elif self._focused_spinner is not None:
            self._spinner_increment(self._focused_spinner, 1)

    def _on_key_down(self, event=None):
        """Handle Down arrow key in dropdown."""
        if self._focused_spinner == "ampm":
            self._toggle_ampm()
        elif self._focused_spinner is not None:
            self._spinner_increment(self._focused_spinner, -1)

    def _on_key_tab(self, event=None):
        """Handle Tab key to move focus to the next spinner."""
        order = self._get_spinner_order()
        if self._focused_spinner in order:
            idx = order.index(self._focused_spinner)
            next_idx = (idx + 1) % len(order)
            self._focused_spinner = order[next_idx]
        return "break"  # prevent default tab behavior

    def _on_key_shift_tab(self, event=None):
        """Handle Shift-Tab key to move focus to the previous spinner."""
        order = self._get_spinner_order()
        if self._focused_spinner in order:
            idx = order.index(self._focused_spinner)
            prev_idx = (idx - 1) % len(order)
            self._focused_spinner = order[prev_idx]
        return "break"

    def _get_spinner_order(self) -> list:
        """Return the ordered list of active spinner names."""
        order = ["hour", "minute"]
        if self._show_seconds:
            order.append("second")
        if self._time_format == "12h":
            order.append("ampm")
        return order

    # ------------------------------------------------------------------
    #  Font update
    # ------------------------------------------------------------------

    def _update_font(self):
        self._entry.configure(font=self._apply_font_scaling(self._font))
        self._canvas.grid_forget()
        self._canvas.grid(row=0, column=0, rowspan=1, columnspan=1, sticky="nsew")

    # ------------------------------------------------------------------
    #  Scaling
    # ------------------------------------------------------------------

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._entry.configure(font=self._apply_font_scaling(self._font))
        self._create_grid()
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height))
        self._draw()

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def get_time(self) -> Optional[Tuple[int, int, int]]:
        """Return the currently selected time as (hour, minute, second), or None if not set."""
        if not self._time_set:
            return None
        return (self._hour, self._minute, self._second)

    def set_time(self, hour: int, minute: int, second: int = 0):
        """Set the selected time programmatically.

        Args:
            hour: Hour value (0-23).
            minute: Minute value (0-59).
            second: Second value (0-59), defaults to 0.

        Raises:
            ValueError: If values are out of range or outside min/max bounds.
        """
        if not (0 <= hour <= 23):
            raise ValueError(f"Hour must be 0-23, got {hour}")
        if not (0 <= minute <= 59):
            raise ValueError(f"Minute must be 0-59, got {minute}")
        if not (0 <= second <= 59):
            raise ValueError(f"Second must be 0-59, got {second}")
        if not self._is_time_in_range(hour, minute, second):
            raise ValueError(
                f"Time {hour:02d}:{minute:02d}:{second:02d} is outside the allowed range "
                f"[{self._min_time}, {self._max_time}]")

        self._hour = hour
        self._minute = minute
        self._second = second
        self._time_set = True
        self._update_entry_display()
        self._sync_variable()

        if self._command is not None:
            self._command((self._hour, self._minute, self._second))

    def clear(self):
        """Clear the selected time."""
        self._time_set = False
        self._hour = 0
        self._minute = 0
        self._second = 0
        self._update_entry_display()
        self._sync_variable()

    def get(self) -> str:
        """Return the entry text (formatted time string or empty)."""
        if self._time_set:
            return self._format_time()
        return ""

    def set(self, value: str):
        """Set the time from a formatted string.

        Supported formats: HH:MM, HH:MM:SS, HH:MM AM/PM, HH:MM:SS AM/PM.

        Raises:
            ValueError: If the string cannot be parsed as a time.
        """
        if not value:
            self.clear()
            return
        self._parse_time_string(value)
        self._clamp_time()
        self._update_entry_display()
        self._sync_variable()

        if self._command is not None:
            self._command((self._hour, self._minute, self._second))

    def focus_set(self):
        self._entry.focus_set()

    def focus(self):
        return self._entry.focus()

    def focus_force(self):
        return self._entry.focus_force()

    # ------------------------------------------------------------------
    #  configure / cget
    # ------------------------------------------------------------------

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
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True

        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "button_color" in kwargs:
            self._button_color = self._check_color_type(kwargs.pop("button_color"))
            require_redraw = True

        if "button_hover_color" in kwargs:
            self._button_hover_color = self._check_color_type(kwargs.pop("button_hover_color"))
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "text_color_disabled" in kwargs:
            self._text_color_disabled = self._check_color_type(kwargs.pop("text_color_disabled"))
            require_redraw = True

        if "dropdown_fg_color" in kwargs:
            self._dropdown_fg_color = kwargs.pop("dropdown_fg_color")

        if "dropdown_border_color" in kwargs:
            self._dropdown_border_color = kwargs.pop("dropdown_border_color")

        if "dropdown_text_color" in kwargs:
            self._dropdown_text_color = kwargs.pop("dropdown_text_color")

        if "dropdown_header_color" in kwargs:
            self._dropdown_header_color = kwargs.pop("dropdown_header_color")

        if "selected_color" in kwargs:
            self._selected_color = kwargs.pop("selected_color")

        if "selected_text_color" in kwargs:
            self._selected_text_color = kwargs.pop("selected_text_color")

        if "hover_color" in kwargs:
            self._hover_color = kwargs.pop("hover_color")

        if "arrow_color" in kwargs:
            self._arrow_color = kwargs.pop("arrow_color")

        if "arrow_hover_color" in kwargs:
            self._arrow_hover_color = kwargs.pop("arrow_hover_color")

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "dropdown_font" in kwargs:
            self._dropdown_font = kwargs.pop("dropdown_font")

        if "time_format" in kwargs:
            self._time_format = kwargs.pop("time_format")
            self._update_entry_display()

        if "show_seconds" in kwargs:
            self._show_seconds = kwargs.pop("show_seconds")
            self._update_entry_display()

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "variable" in kwargs:
            if self._variable is not None and self._variable_callback_name:
                self._variable.trace_remove("write", self._variable_callback_name)
                self._variable_callback_name = ""
            self._variable = kwargs.pop("variable")
            if self._variable is not None:
                self._variable_callback_name = self._variable.trace_add("write", self._on_variable_change)
                self._parse_variable_value()

        if "min_time" in kwargs:
            self._min_time = kwargs.pop("min_time")

        if "max_time" in kwargs:
            self._max_time = kwargs.pop("max_time")

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            require_redraw = True

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "border_width":
            return self._border_width
        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "button_color":
            return self._button_color
        elif attribute_name == "button_hover_color":
            return self._button_hover_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "text_color_disabled":
            return self._text_color_disabled
        elif attribute_name == "dropdown_fg_color":
            return self._dropdown_fg_color
        elif attribute_name == "dropdown_border_color":
            return self._dropdown_border_color
        elif attribute_name == "dropdown_text_color":
            return self._dropdown_text_color
        elif attribute_name == "dropdown_header_color":
            return self._dropdown_header_color
        elif attribute_name == "selected_color":
            return self._selected_color
        elif attribute_name == "selected_text_color":
            return self._selected_text_color
        elif attribute_name == "hover_color":
            return self._hover_color
        elif attribute_name == "arrow_color":
            return self._arrow_color
        elif attribute_name == "arrow_hover_color":
            return self._arrow_hover_color
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "dropdown_font":
            return self._dropdown_font
        elif attribute_name == "time_format":
            return self._time_format
        elif attribute_name == "show_seconds":
            return self._show_seconds
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "min_time":
            return self._min_time
        elif attribute_name == "max_time":
            return self._max_time
        elif attribute_name == "state":
            return self._state
        else:
            return super().cget(attribute_name)

    # ------------------------------------------------------------------
    #  Bind / Unbind
    # ------------------------------------------------------------------

    def bind(self, sequence=None, command=None, add=True):
        """Bind event on the entry widget."""
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._entry.bind(sequence, command, add=True)

    def unbind(self, sequence=None, funcid=None):
        """Unbind event from the entry widget."""
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in"
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._entry.unbind(sequence, None)
        self._create_bindings(sequence=sequence)

    # ------------------------------------------------------------------
    #  Lifecycle
    # ------------------------------------------------------------------

    def destroy(self):
        if self._variable is not None and self._variable_callback_name:
            try:
                self._variable.trace_remove("write", self._variable_callback_name)
            except Exception:
                pass
            self._variable_callback_name = ""

        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)

        # cancel any pending auto-repeat callbacks
        for after_id in self._repeat_after_ids:
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self._repeat_after_ids.clear()

        self._close_dropdown()
        super().destroy()
