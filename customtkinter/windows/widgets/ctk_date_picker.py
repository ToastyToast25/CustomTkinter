import tkinter
import datetime
import calendar
from typing import Union, Tuple, Optional, Callable, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkDatePicker(CTkBaseClass):
    """
    Calendar-based date picker widget with entry field, dropdown calendar,
    month/year navigation, today highlighting, and configurable date format.

    Features:
        - Entry field with calendar icon button to open dropdown
        - Calendar grid: 7 columns (Mon-Sun), 6 rows for days
        - Month/Year navigation with left/right arrows
        - Today highlighting with accent ring
        - Click a day to select, closes dropdown
        - Configurable date format (default "%Y-%m-%d")
        - Optional min/max date bounds
        - StringVar variable binding
        - Keyboard: Escape to close, Enter to confirm
        - Command callback on date change

    Usage:
        picker = CTkDatePicker(parent, date_format="%Y-%m-%d",
                               command=on_date_changed)
        picker.get_date()       # returns datetime.date or None
        picker.set_date(datetime.date(2024, 3, 15))
        picker.clear()
    """

    # Calendar icon (Unicode)
    _CALENDAR_ICON = "\U0001F4C5"

    # Day header labels (Monday-first)
    _DAY_HEADERS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

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
                 today_border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 disabled_day_color: Optional[Union[str, Tuple[str, str]]] = None,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 dropdown_font: Optional[Union[tuple, CTkFont]] = None,
                 date_format: str = "%Y-%m-%d",
                 command: Optional[Callable[[datetime.date], Any]] = None,
                 variable: Optional[tkinter.StringVar] = None,
                 min_date: Optional[datetime.date] = None,
                 max_date: Optional[datetime.date] = None,
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

        # colors - dropdown calendar
        self._dropdown_fg_color = dropdown_fg_color or ("#F9F9FA", "#2B2B2B")
        self._dropdown_border_color = dropdown_border_color or ("#979DA2", "#565B5E")
        self._dropdown_text_color = dropdown_text_color or ("#1A1A1A", "#DCE4EE")
        self._dropdown_header_color = dropdown_header_color or ("#3B8ED0", "#1F6AA5")
        self._selected_color = selected_color or ("#3B8ED0", "#1F6AA5")
        self._selected_text_color = selected_text_color or ("#FFFFFF", "#FFFFFF")
        self._today_border_color = today_border_color or ("#3B8ED0", "#1F6AA5")
        self._hover_color = hover_color or ("#D0E0F0", "#3D3D3D")
        self._disabled_day_color = disabled_day_color or ("#B0B0B0", "#555555")

        # font
        self._font = CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)
        self._dropdown_font = dropdown_font

        # state
        self._date_format = date_format
        self._command = command
        self._variable = variable
        self._min_date = min_date
        self._max_date = max_date
        self._state = state

        self._selected_date: Optional[datetime.date] = None
        self._displayed_year: int = datetime.date.today().year
        self._displayed_month: int = datetime.date.today().month
        self._dropdown_open: bool = False
        self._dropdown_window: Optional[tkinter.Toplevel] = None
        self._day_buttons: list = []
        self._hover_after_id: Optional[str] = None

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
                                    justify="left",
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
        """Try to parse the variable's string value into a date."""
        if self._variable is None:
            return
        val = self._variable.get()
        if not val:
            self._selected_date = None
            self._update_entry_display()
            return
        try:
            parsed = datetime.datetime.strptime(val, self._date_format).date()
            self._selected_date = parsed
            self._displayed_year = parsed.year
            self._displayed_month = parsed.month
            self._update_entry_display()
        except ValueError:
            pass

    def _sync_variable(self):
        """Push the current selected date to the variable."""
        if self._variable is not None:
            if self._selected_date is not None:
                self._variable.set(self._selected_date.strftime(self._date_format))
            else:
                self._variable.set("")

    # ------------------------------------------------------------------
    #  Entry display
    # ------------------------------------------------------------------

    def _update_entry_display(self):
        """Update the readonly entry field text."""
        self._entry.configure(state="normal")
        self._entry.delete(0, tkinter.END)
        if self._selected_date is not None:
            self._entry.insert(0, self._selected_date.strftime(self._date_format))
        self._entry.configure(state="readonly")

    # ------------------------------------------------------------------
    #  Dropdown calendar
    # ------------------------------------------------------------------

    def _open_dropdown(self):
        if self._dropdown_open:
            return

        self._dropdown_open = True

        # position below the entry widget
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()

        # if we have a selected date, show that month; otherwise show today's month
        if self._selected_date is not None:
            self._displayed_year = self._selected_date.year
            self._displayed_month = self._selected_date.month

        self._dropdown_window = tkinter.Toplevel(self)
        self._dropdown_window.withdraw()
        self._dropdown_window.overrideredirect(True)
        self._dropdown_window.resizable(False, False)

        # prevent it from appearing in the taskbar on Windows
        self._dropdown_window.transient(self.winfo_toplevel())

        self._build_calendar()

        self._dropdown_window.update_idletasks()
        self._dropdown_window.geometry(f"+{x}+{y}")
        self._dropdown_window.deiconify()

        # grab focus so we can detect clicks outside
        self._dropdown_window.focus_set()
        self._dropdown_window.bind("<FocusOut>", self._on_dropdown_focus_out)
        self._dropdown_window.bind("<Key-Escape>", lambda e: self._close_dropdown())

    def _close_dropdown(self):
        if not self._dropdown_open:
            return

        self._dropdown_open = False
        if self._dropdown_window is not None:
            self._dropdown_window.destroy()
            self._dropdown_window = None
        self._day_buttons.clear()

    def _on_dropdown_focus_out(self, event=None):
        """Close the dropdown when it loses focus, but only if focus went
        somewhere outside the dropdown window."""
        if self._dropdown_window is None:
            return

        # Schedule closing after a small delay to allow focus to settle.
        # This avoids premature closing when clicking child widgets
        # inside the dropdown.
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

        # Check if the focused widget is a descendant of the dropdown
        try:
            focused_path = str(focused)
            dropdown_path = str(self._dropdown_window)
            if not focused_path.startswith(dropdown_path):
                self._close_dropdown()
        except Exception:
            self._close_dropdown()

    # ------------------------------------------------------------------
    #  Calendar building
    # ------------------------------------------------------------------

    def _build_calendar(self):
        """Build/rebuild the calendar grid inside the dropdown toplevel."""
        if self._dropdown_window is None:
            return

        # Clear existing content
        for widget in self._dropdown_window.winfo_children():
            widget.destroy()
        self._day_buttons.clear()

        dd_fg = self._apply_appearance_mode(self._dropdown_fg_color)
        dd_border = self._apply_appearance_mode(self._dropdown_border_color)
        dd_text = self._apply_appearance_mode(self._dropdown_text_color)
        dd_header = self._apply_appearance_mode(self._dropdown_header_color)

        # Outer frame with border effect
        outer_frame = tkinter.Frame(self._dropdown_window, bg=dd_border, padx=1, pady=1)
        outer_frame.pack(fill="both", expand=True)

        inner_frame = tkinter.Frame(outer_frame, bg=dd_fg)
        inner_frame.pack(fill="both", expand=True)

        # Resolve fonts
        if self._dropdown_font is not None:
            if isinstance(self._dropdown_font, CTkFont):
                cal_font = (self._dropdown_font.cget("family"),
                            self._dropdown_font.cget("size"),
                            self._dropdown_font.cget("weight"))
            else:
                cal_font = self._dropdown_font
        else:
            cal_font = ("Segoe UI", 10)

        header_font = (cal_font[0], cal_font[1], "bold") if len(cal_font) >= 2 else ("Segoe UI", 10, "bold")
        nav_font = ("Segoe UI", 12, "bold")
        day_header_font = (cal_font[0], max(8, cal_font[1] - 1)) if len(cal_font) >= 2 else ("Segoe UI", 9)

        # ---- Navigation header ----
        nav_frame = tkinter.Frame(inner_frame, bg=dd_fg)
        nav_frame.pack(fill="x", padx=4, pady=(6, 2))

        left_btn = tkinter.Label(nav_frame, text="\u25C0", font=nav_font,
                                 fg=dd_header, bg=dd_fg, cursor="hand2")
        left_btn.pack(side="left", padx=(4, 0))
        left_btn.bind("<Button-1>", lambda e: self._navigate_month(-1))
        left_btn.bind("<Enter>", lambda e: left_btn.configure(fg=self._apply_appearance_mode(self._button_hover_color)))
        left_btn.bind("<Leave>", lambda e: left_btn.configure(fg=dd_header))

        right_btn = tkinter.Label(nav_frame, text="\u25B6", font=nav_font,
                                  fg=dd_header, bg=dd_fg, cursor="hand2")
        right_btn.pack(side="right", padx=(0, 4))
        right_btn.bind("<Button-1>", lambda e: self._navigate_month(1))
        right_btn.bind("<Enter>", lambda e: right_btn.configure(fg=self._apply_appearance_mode(self._button_hover_color)))
        right_btn.bind("<Leave>", lambda e: right_btn.configure(fg=dd_header))

        month_name = calendar.month_name[self._displayed_month]
        header_text = f"{month_name} {self._displayed_year}"
        header_label = tkinter.Label(nav_frame, text=header_text, font=header_font,
                                     fg=dd_header, bg=dd_fg)
        header_label.pack(expand=True)

        # ---- Separator ----
        sep = tkinter.Frame(inner_frame, bg=dd_border, height=1)
        sep.pack(fill="x", padx=6, pady=(2, 4))

        # ---- Day headers ----
        grid_frame = tkinter.Frame(inner_frame, bg=dd_fg)
        grid_frame.pack(padx=4, pady=(0, 6))

        for col_idx, day_name in enumerate(self._DAY_HEADERS):
            lbl = tkinter.Label(grid_frame, text=day_name, font=day_header_font,
                                fg=self._apply_appearance_mode(self._disabled_day_color),
                                bg=dd_fg, width=3)
            lbl.grid(row=0, column=col_idx, padx=1, pady=(0, 2))

        # ---- Day grid (6 rows x 7 columns) ----
        today = datetime.date.today()
        first_day_of_month = datetime.date(self._displayed_year, self._displayed_month, 1)
        # Monday = 0
        start_weekday = first_day_of_month.weekday()

        # Number of days in month
        days_in_month = calendar.monthrange(self._displayed_year, self._displayed_month)[1]

        # Previous month's trailing days
        if self._displayed_month == 1:
            prev_month = 12
            prev_year = self._displayed_year - 1
        else:
            prev_month = self._displayed_month - 1
            prev_year = self._displayed_year
        days_in_prev_month = calendar.monthrange(prev_year, prev_month)[1]

        cell_size = 30

        day_num = 1
        next_month_day = 1

        for row in range(6):
            for col in range(7):
                cell_index = row * 7 + col

                if cell_index < start_weekday:
                    # Previous month day
                    day = days_in_prev_month - start_weekday + cell_index + 1
                    is_current_month = False
                    cell_date = datetime.date(prev_year, prev_month, day)
                elif day_num <= days_in_month:
                    # Current month day
                    day = day_num
                    is_current_month = True
                    cell_date = datetime.date(self._displayed_year, self._displayed_month, day)
                    day_num += 1
                else:
                    # Next month day
                    day = next_month_day
                    is_current_month = False
                    if self._displayed_month == 12:
                        next_m = 1
                        next_y = self._displayed_year + 1
                    else:
                        next_m = self._displayed_month + 1
                        next_y = self._displayed_year
                    cell_date = datetime.date(next_y, next_m, day)
                    next_month_day += 1

                # Determine cell styling
                is_today = (cell_date == today)
                is_selected = (self._selected_date is not None and cell_date == self._selected_date)
                is_in_range = self._is_date_in_range(cell_date)

                # Create the day cell
                cell = tkinter.Frame(grid_frame, width=cell_size, height=cell_size, bg=dd_fg)
                cell.grid(row=row + 1, column=col, padx=1, pady=1)
                cell.grid_propagate(False)
                cell.columnconfigure(0, weight=1)
                cell.rowconfigure(0, weight=1)

                if is_selected:
                    cell_bg = self._apply_appearance_mode(self._selected_color)
                    cell_fg = self._apply_appearance_mode(self._selected_text_color)
                elif is_today and is_current_month:
                    cell_bg = dd_fg
                    cell_fg = self._apply_appearance_mode(self._today_border_color)
                elif not is_current_month or not is_in_range:
                    cell_bg = dd_fg
                    cell_fg = self._apply_appearance_mode(self._disabled_day_color)
                else:
                    cell_bg = dd_fg
                    cell_fg = dd_text

                day_label = tkinter.Label(cell, text=str(day), font=cal_font,
                                          fg=cell_fg, bg=cell_bg,
                                          width=2, anchor="center")
                day_label.grid(row=0, column=0, sticky="nsew")

                # Today ring: draw a thin border around the cell
                if is_today and is_current_month and not is_selected:
                    today_ring_color = self._apply_appearance_mode(self._today_border_color)
                    cell.configure(bg=today_ring_color, padx=1, pady=1)
                    day_label.configure(bg=dd_fg)

                # Selected cell: fill background with accent
                if is_selected:
                    cell.configure(bg=cell_bg)
                    day_label.configure(bg=cell_bg)

                # Interactive bindings for valid dates
                if is_current_month and is_in_range:
                    self._bind_day_cell(day_label, cell, cell_date, is_selected, is_today, dd_fg)
                elif not is_current_month and is_in_range:
                    # Allow clicking days from adjacent months to navigate there
                    self._bind_adjacent_day_cell(day_label, cell, cell_date)

                self._day_buttons.append((cell, day_label, cell_date))

    def _bind_day_cell(self, label, cell, date, is_selected, is_today, dd_fg):
        """Bind hover and click events to a current-month day cell."""
        hover_bg = self._apply_appearance_mode(self._hover_color)
        normal_bg = cell.cget("bg")
        normal_label_bg = label.cget("bg")

        def on_enter(e):
            if not is_selected:
                if is_today:
                    label.configure(bg=hover_bg)
                else:
                    cell.configure(bg=hover_bg)
                    label.configure(bg=hover_bg)

        def on_leave(e):
            if not is_selected:
                if is_today:
                    label.configure(bg=normal_label_bg)
                else:
                    cell.configure(bg=normal_bg)
                    label.configure(bg=normal_label_bg)

        def on_click(e):
            self._select_date(date)

        label.configure(cursor="hand2")
        label.bind("<Enter>", on_enter)
        label.bind("<Leave>", on_leave)
        label.bind("<Button-1>", on_click)

    def _bind_adjacent_day_cell(self, label, cell, date):
        """Bind click events to a day from an adjacent month."""
        def on_click(e):
            self._select_date(date)

        label.configure(cursor="hand2")
        label.bind("<Button-1>", on_click)

    # ------------------------------------------------------------------
    #  Date selection
    # ------------------------------------------------------------------

    def _select_date(self, date: datetime.date):
        """Select a date, update display, fire callback, close dropdown."""
        if not self._is_date_in_range(date):
            return

        self._selected_date = date
        self._displayed_year = date.year
        self._displayed_month = date.month
        self._update_entry_display()
        self._sync_variable()
        self._close_dropdown()

        if self._command is not None:
            self._command(date)

    def _is_date_in_range(self, date: datetime.date) -> bool:
        """Check if a date falls within the min/max bounds."""
        if self._min_date is not None and date < self._min_date:
            return False
        if self._max_date is not None and date > self._max_date:
            return False
        return True

    # ------------------------------------------------------------------
    #  Month navigation
    # ------------------------------------------------------------------

    def _navigate_month(self, delta: int):
        """Navigate forward or backward by delta months."""
        month = self._displayed_month + delta
        year = self._displayed_year

        while month > 12:
            month -= 12
            year += 1
        while month < 1:
            month += 12
            year -= 1

        self._displayed_month = month
        self._displayed_year = year
        self._build_calendar()

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

    def get_date(self) -> Optional[datetime.date]:
        """Return the currently selected date, or None if no date is selected."""
        return self._selected_date

    def set_date(self, date: datetime.date):
        """Set the selected date programmatically."""
        if not isinstance(date, datetime.date):
            raise TypeError(f"Expected datetime.date, got {type(date).__name__}")
        if not self._is_date_in_range(date):
            raise ValueError(f"Date {date} is outside the allowed range "
                             f"[{self._min_date}, {self._max_date}]")

        self._selected_date = date
        self._displayed_year = date.year
        self._displayed_month = date.month
        self._update_entry_display()
        self._sync_variable()

        if self._command is not None:
            self._command(date)

    def clear(self):
        """Clear the selected date."""
        self._selected_date = None
        self._update_entry_display()
        self._sync_variable()

    def get(self) -> str:
        """Return the entry text (formatted date string or empty)."""
        if self._selected_date is not None:
            return self._selected_date.strftime(self._date_format)
        return ""

    def set(self, value: str):
        """Set the date from a formatted string. Raises ValueError on bad format."""
        if not value:
            self.clear()
            return
        parsed = datetime.datetime.strptime(value, self._date_format).date()
        self.set_date(parsed)

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

        if "today_border_color" in kwargs:
            self._today_border_color = kwargs.pop("today_border_color")

        if "hover_color" in kwargs:
            self._hover_color = kwargs.pop("hover_color")

        if "disabled_day_color" in kwargs:
            self._disabled_day_color = kwargs.pop("disabled_day_color")

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "dropdown_font" in kwargs:
            self._dropdown_font = kwargs.pop("dropdown_font")

        if "date_format" in kwargs:
            self._date_format = kwargs.pop("date_format")
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

        if "min_date" in kwargs:
            self._min_date = kwargs.pop("min_date")

        if "max_date" in kwargs:
            self._max_date = kwargs.pop("max_date")

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
        elif attribute_name == "today_border_color":
            return self._today_border_color
        elif attribute_name == "hover_color":
            return self._hover_color
        elif attribute_name == "disabled_day_color":
            return self._disabled_day_color
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "dropdown_font":
            return self._dropdown_font
        elif attribute_name == "date_format":
            return self._date_format
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "min_date":
            return self._min_date
        elif attribute_name == "max_date":
            return self._max_date
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

        self._close_dropdown()
        super().destroy()
