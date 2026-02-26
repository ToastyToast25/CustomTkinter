import tkinter
import calendar
import datetime
from typing import Union, Tuple, Optional, Callable, Any, List

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkCalendarView(CTkBaseClass):
    """
    Inline calendar month-view widget.  Displays a full month grid with
    day-of-week headers, month/year navigation, today highlighting,
    click-to-select, optional multi-select, date bounds, week numbers,
    a configurable first day of week, StringVar binding, and a
    command callback.

    Unlike CTkDatePicker (popup), this widget is rendered inline as a
    permanent panel using canvas-based cell rendering for efficiency.

    Usage:
        cal = CTkCalendarView(parent, command=on_date_selected)
        cal.pack(padx=10, pady=10)
        cal.get_date()                # -> datetime.date or None
        cal.set_date("2025-06-15")    # accepts str or datetime.date
        cal.get_selected_dates()      # -> list of datetime.date
        cal.next_month()
        cal.prev_month()
        cal.go_to_today()
    """

    # Short day-of-week names starting from Monday (index 0)
    _ALL_DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self,
                 master: Any,
                 width: int = 280,
                 height: int = 300,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 header_color: Optional[Union[str, Tuple[str, str]]] = None,
                 nav_button_color: Optional[Union[str, Tuple[str, str]]] = None,
                 nav_button_hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 day_header_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 selected_color: Optional[Union[str, Tuple[str, str]]] = None,
                 selected_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 today_color: Optional[Union[str, Tuple[str, str]]] = None,
                 today_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 other_month_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 disabled_color: Optional[Union[str, Tuple[str, str]]] = None,
                 week_number_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_width: Optional[int] = None,
                 corner_radius: Optional[int] = None,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 header_font: Optional[Union[tuple, CTkFont]] = None,

                 command: Optional[Callable[[datetime.date], Any]] = None,
                 variable: Optional[tkinter.StringVar] = None,
                 date_format: str = "%Y-%m-%d",
                 min_date: Optional[datetime.date] = None,
                 max_date: Optional[datetime.date] = None,
                 multi_select: bool = False,
                 show_week_numbers: bool = False,
                 first_day_of_week: int = 0,
                 show_today_button: bool = True,
                 show_other_month_days: bool = True,
                 state: str = tkinter.NORMAL,
                 **kwargs):

        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # --- shape ---
        self._corner_radius = ThemeManager.theme["CTkFrame"]["corner_radius"] if corner_radius is None else corner_radius
        self._border_width = ThemeManager.theme["CTkFrame"]["border_width"] if border_width is None else border_width

        # --- colors ---
        self._fg_color = ThemeManager.theme["CTkFrame"]["fg_color"] if fg_color is None else self._check_color_type(fg_color)
        self._header_color = header_color or ("#3B8ED0", "#1F6AA5")
        self._nav_button_color = nav_button_color or ("#FFFFFF", "#DCE4EE")
        self._nav_button_hover_color = nav_button_hover_color or ("#DCE4EE", "#FFFFFF")
        self._text_color = ThemeManager.theme["CTkLabel"]["text_color"] if text_color is None else self._check_color_type(text_color)
        self._day_header_text_color = day_header_text_color or ("#5A5A5A", "#999999")
        self._selected_color = selected_color or ("#3B8ED0", "#1F6AA5")
        self._selected_text_color = selected_text_color or ("#FFFFFF", "#FFFFFF")
        self._today_color = today_color or ("#E8F0FE", "#2A3A4A")
        self._today_text_color = today_text_color or ("#3B8ED0", "#1F6AA5")
        self._hover_color = hover_color or ("#D0E0F0", "#3D3D3D")
        self._other_month_text_color = other_month_text_color or ("#B0B0B0", "#555555")
        self._disabled_color = disabled_color or ("#D0D0D0", "#444444")
        self._week_number_text_color = week_number_text_color or ("#8899AA", "#667788")
        self._border_color = ThemeManager.theme["CTkFrame"]["border_color"] if border_color is None else self._check_color_type(border_color)

        # --- fonts ---
        self._font = CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)

        self._header_font = header_font  # None means derived from _font at draw time

        # --- configuration ---
        self._command = command
        self._variable = variable
        self._date_format = date_format
        self._min_date = min_date
        self._max_date = max_date
        self._multi_select = multi_select
        self._show_week_numbers = show_week_numbers
        self._first_day_of_week = max(0, min(6, first_day_of_week))
        self._show_today_button = show_today_button
        self._show_other_month_days = show_other_month_days
        self._state = state

        # --- internal state ---
        today = datetime.date.today()
        self._displayed_year: int = today.year
        self._displayed_month: int = today.month
        self._selected_dates: List[datetime.date] = []
        self._hover_date: Optional[datetime.date] = None

        # Canvas item id caches (for recycling)
        self._cell_bg_ids: List[int] = []
        self._cell_text_ids: List[int] = []
        self._header_text_ids: List[int] = []
        self._week_number_ids: List[int] = []

        # Cell geometry cache: list of (x, y, w, h, date_or_None) for hit-testing
        self._cell_rects: List[Tuple[float, float, float, float, Optional[datetime.date]]] = []

        # Variable callback
        self._variable_callback_name: str = ""
        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._on_variable_change)

        # --- build UI structure ---
        # We use a combination of frames for the header and a canvas for the grid.
        # The outer container is this widget (a tkinter.Frame from CTkBaseClass).

        self.grid_rowconfigure(0, weight=0)  # header row
        self.grid_rowconfigure(1, weight=1)  # calendar grid
        self.grid_rowconfigure(2, weight=0)  # today button row
        self.grid_columnconfigure(0, weight=1)

        # Header frame: nav arrows + month/year label
        self._header_frame = tkinter.Frame(self, height=36)
        self._header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self._header_frame.grid_columnconfigure(1, weight=1)

        self._prev_btn = tkinter.Label(self._header_frame, text="\u25C0", cursor="hand2",
                                        padx=8, pady=4)
        self._prev_btn.grid(row=0, column=0, sticky="w", padx=(6, 0))
        self._prev_btn.bind("<Button-1>", lambda e: self._on_nav(-1))

        self._header_label = tkinter.Label(self._header_frame, anchor="center", pady=4)
        self._header_label.grid(row=0, column=1, sticky="ew")

        self._next_btn = tkinter.Label(self._header_frame, text="\u25B6", cursor="hand2",
                                        padx=8, pady=4)
        self._next_btn.grid(row=0, column=2, sticky="e", padx=(0, 6))
        self._next_btn.bind("<Button-1>", lambda e: self._on_nav(1))

        # Hover effects for nav buttons
        self._prev_btn.bind("<Enter>", lambda e: self._on_nav_enter(self._prev_btn))
        self._prev_btn.bind("<Leave>", lambda e: self._on_nav_leave(self._prev_btn))
        self._next_btn.bind("<Enter>", lambda e: self._on_nav_enter(self._next_btn))
        self._next_btn.bind("<Leave>", lambda e: self._on_nav_leave(self._next_btn))

        # Calendar canvas
        self._canvas = CTkCanvas(master=self, highlightthickness=0)
        self._canvas.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 2))
        self._canvas.bind("<Button-1>", self._on_canvas_click)
        self._canvas.bind("<Motion>", self._on_canvas_motion)
        self._canvas.bind("<Leave>", self._on_canvas_leave)

        # Today button (optional)
        self._today_btn_frame = tkinter.Frame(self)
        if self._show_today_button:
            self._today_btn_frame.grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 6))
        self._today_btn_label = tkinter.Label(self._today_btn_frame, text="Today",
                                               cursor="hand2", padx=8, pady=2)
        self._today_btn_label.pack(expand=True)
        self._today_btn_label.bind("<Button-1>", lambda e: self.go_to_today())
        self._today_btn_label.bind("<Enter>", lambda e: self._on_today_btn_enter())
        self._today_btn_label.bind("<Leave>", lambda e: self._on_today_btn_leave())

        # Parse initial variable value if present
        if self._variable is not None and self._variable.get():
            self._parse_variable_value()

        # Initial draw
        self._draw()

    # ==================================================================
    #  Internal helpers: ordered day names
    # ==================================================================

    def _get_day_names(self) -> List[str]:
        """Return day-of-week names rotated according to first_day_of_week."""
        return self._ALL_DAY_NAMES[self._first_day_of_week:] + self._ALL_DAY_NAMES[:self._first_day_of_week]

    def _weekday_offset(self, date: datetime.date) -> int:
        """Return the column index for a date given the configured first day of week.
        Python weekday(): Monday=0 ... Sunday=6."""
        return (date.weekday() - self._first_day_of_week) % 7

    # ==================================================================
    #  Drawing
    # ==================================================================

    def _draw(self, no_color_updates: bool = False):
        super()._draw(no_color_updates)

        # Resolve all appearance-mode colors once
        fg = self._apply_appearance_mode(self._fg_color)
        header_bg = self._apply_appearance_mode(self._header_color)
        nav_fg = self._apply_appearance_mode(self._nav_button_color)
        text_fg = self._apply_appearance_mode(self._text_color)
        day_header_fg = self._apply_appearance_mode(self._day_header_text_color)
        selected_bg = self._apply_appearance_mode(self._selected_color)
        selected_fg = self._apply_appearance_mode(self._selected_text_color)
        today_bg = self._apply_appearance_mode(self._today_color)
        today_fg = self._apply_appearance_mode(self._today_text_color)
        hover_bg = self._apply_appearance_mode(self._hover_color)
        other_fg = self._apply_appearance_mode(self._other_month_text_color)
        disabled_fg = self._apply_appearance_mode(self._disabled_color)
        wk_fg = self._apply_appearance_mode(self._week_number_text_color)
        border_c = self._apply_appearance_mode(self._border_color)

        # Resolve fonts
        if isinstance(self._font, CTkFont):
            base_font_tuple = (self._font.cget("family"), self._font.cget("size"), self._font.cget("weight"))
        elif isinstance(self._font, tuple):
            base_font_tuple = self._font
        else:
            base_font_tuple = ("Segoe UI", 12)

        font_family = base_font_tuple[0]
        font_size = base_font_tuple[1] if len(base_font_tuple) >= 2 else 12

        if self._header_font is not None:
            if isinstance(self._header_font, CTkFont):
                hdr_font = (self._header_font.cget("family"), self._header_font.cget("size"), "bold")
            elif isinstance(self._header_font, tuple):
                hdr_font = self._header_font
            else:
                hdr_font = (font_family, font_size + 1, "bold")
        else:
            hdr_font = (font_family, font_size + 1, "bold")

        day_font = (font_family, font_size)
        day_header_font = (font_family, max(8, font_size - 1), "bold")
        nav_font = (font_family, font_size + 2, "bold")
        small_font = (font_family, max(8, font_size - 2))
        today_btn_font = (font_family, font_size - 1)

        # ---- Configure header frame colors ----
        self._header_frame.configure(bg=header_bg)
        self._prev_btn.configure(bg=header_bg, fg=nav_fg, font=nav_font)
        self._next_btn.configure(bg=header_bg, fg=nav_fg, font=nav_font)

        month_name = calendar.month_name[self._displayed_month]
        self._header_label.configure(
            text=f"{month_name} {self._displayed_year}",
            bg=header_bg, fg=nav_fg, font=hdr_font
        )

        # ---- Configure today button ----
        self._today_btn_frame.configure(bg=fg)
        self._today_btn_label.configure(bg=fg, fg=self._apply_appearance_mode(self._header_color),
                                         font=today_btn_font)

        # ---- Configure canvas background ----
        self._canvas.configure(bg=fg)

        # ---- Configure widget bg ----
        tkinter.Frame.configure(self, bg=fg)

        # ---- Draw calendar grid on canvas ----
        self._draw_grid(
            fg=fg, text_fg=text_fg, day_header_fg=day_header_fg,
            selected_bg=selected_bg, selected_fg=selected_fg,
            today_bg=today_bg, today_fg=today_fg,
            hover_bg=hover_bg, other_fg=other_fg,
            disabled_fg=disabled_fg, wk_fg=wk_fg,
            day_font=day_font, day_header_font=day_header_font,
            small_font=small_font
        )

    def _draw_grid(self, *, fg, text_fg, day_header_fg, selected_bg, selected_fg,
                   today_bg, today_fg, hover_bg, other_fg, disabled_fg, wk_fg,
                   day_font, day_header_font, small_font):
        """Render the calendar grid onto the canvas, recycling item ids where possible."""

        self._canvas.update_idletasks()
        canvas_w = self._canvas.winfo_width()
        canvas_h = self._canvas.winfo_height()

        if canvas_w <= 1 or canvas_h <= 1:
            # Widget not yet mapped; schedule a redraw after idle
            self._canvas.after_idle(self._draw)
            return

        # --- Layout calculations ---
        num_cols = 7 + (1 if self._show_week_numbers else 0)
        wk_col_offset = 1 if self._show_week_numbers else 0

        col_w = canvas_w / num_cols
        header_row_h = col_w * 0.6  # day-of-week header row
        remaining_h = canvas_h - header_row_h
        num_rows = 6  # always 6 rows to keep consistent sizing
        row_h = remaining_h / num_rows

        # Calendar data
        today = datetime.date.today()
        first_of_month = datetime.date(self._displayed_year, self._displayed_month, 1)
        days_in_month = calendar.monthrange(self._displayed_year, self._displayed_month)[1]
        start_col = self._weekday_offset(first_of_month)

        # Build flat list of (day_date, is_current_month) for the 6x7 grid
        grid_dates: List[Tuple[Optional[datetime.date], bool]] = []

        # Days from previous month
        if start_col > 0:
            if self._displayed_month == 1:
                prev_y, prev_m = self._displayed_year - 1, 12
            else:
                prev_y, prev_m = self._displayed_year, self._displayed_month - 1
            prev_days = calendar.monthrange(prev_y, prev_m)[1]
            for i in range(start_col):
                d = prev_days - start_col + 1 + i
                grid_dates.append((datetime.date(prev_y, prev_m, d), False))

        # Current month
        for d in range(1, days_in_month + 1):
            grid_dates.append((datetime.date(self._displayed_year, self._displayed_month, d), True))

        # Next month fill
        if self._displayed_month == 12:
            next_y, next_m = self._displayed_year + 1, 1
        else:
            next_y, next_m = self._displayed_year, self._displayed_month + 1
        next_d = 1
        while len(grid_dates) < 42:
            grid_dates.append((datetime.date(next_y, next_m, next_d), False))
            next_d += 1

        # --- Delete old items and rebuild (simplest approach for full redraw) ---
        # We delete everything and recreate.  For a typical 42-cell calendar this
        # is fast enough and avoids complex recycling bookkeeping.
        self._canvas.delete("all")
        self._cell_rects.clear()

        # --- Draw day-of-week headers ---
        day_names = self._get_day_names()

        if self._show_week_numbers:
            # Week number column header
            x0 = 0
            cx = x0 + col_w / 2
            cy = header_row_h / 2
            self._canvas.create_text(cx, cy, text="Wk", fill=wk_fg,
                                     font=day_header_font, anchor="center")

        for col_idx, day_name in enumerate(day_names):
            x0 = (col_idx + wk_col_offset) * col_w
            cx = x0 + col_w / 2
            cy = header_row_h / 2
            self._canvas.create_text(cx, cy, text=day_name, fill=day_header_fg,
                                     font=day_header_font, anchor="center")

        # --- Draw separator line under headers ---
        sep_y = header_row_h
        self._canvas.create_line(4, sep_y, canvas_w - 4, sep_y,
                                 fill=day_header_fg, width=1, dash=(2, 2))

        # --- Draw day cells ---
        for idx, (cell_date, is_current_month) in enumerate(grid_dates):
            row = idx // 7
            col = idx % 7

            x0 = (col + wk_col_offset) * col_w
            y0 = header_row_h + row * row_h
            x1 = x0 + col_w
            y1 = y0 + row_h
            cx = (x0 + x1) / 2
            cy = (y0 + y1) / 2

            # Draw week numbers (first column of each row)
            if self._show_week_numbers and col == 0:
                wk_x0 = 0
                wk_cx = wk_x0 + col_w / 2
                wk_cy = cy
                iso_week = cell_date.isocalendar()[1]
                self._canvas.create_text(wk_cx, wk_cy, text=str(iso_week),
                                         fill=wk_fg, font=small_font, anchor="center")

            # Determine cell state
            is_selected = cell_date in self._selected_dates
            is_today = (cell_date == today)
            in_range = self._is_date_in_range(cell_date)
            is_hovered = (cell_date == self._hover_date and is_current_month and in_range)

            # Determine colors
            if is_selected and (is_current_month or self._show_other_month_days):
                cell_bg = selected_bg
                cell_fg_color = selected_fg
            elif is_hovered:
                cell_bg = hover_bg
                cell_fg_color = text_fg
            elif is_today and is_current_month:
                cell_bg = today_bg
                cell_fg_color = today_fg
            else:
                cell_bg = None  # transparent
                if not is_current_month:
                    cell_fg_color = other_fg
                elif not in_range:
                    cell_fg_color = disabled_fg
                else:
                    cell_fg_color = text_fg

            # Draw background rect for highlighted cells
            pad = 2
            if cell_bg is not None:
                # Draw a rounded-ish rectangle (using oval corners approximation via a rectangle for simplicity)
                r = min(col_w, row_h) * 0.15
                self._draw_rounded_rect(x0 + pad, y0 + pad, x1 - pad, y1 - pad, r,
                                        fill=cell_bg, outline=cell_bg)

            # Today ring: if today is not selected, draw a border ring
            if is_today and is_current_month and not is_selected:
                r = min(col_w, row_h) * 0.15
                self._draw_rounded_rect(x0 + pad, y0 + pad, x1 - pad, y1 - pad, r,
                                        fill="" if cell_bg is None else cell_bg,
                                        outline=self._apply_appearance_mode(self._today_color),
                                        width=2)

            # Draw day text
            if is_current_month or self._show_other_month_days:
                self._canvas.create_text(cx, cy, text=str(cell_date.day),
                                         fill=cell_fg_color, font=day_font, anchor="center")

            # Store cell rect for hit-testing (only current month + in-range, or other month if shown)
            if is_current_month or self._show_other_month_days:
                self._cell_rects.append((x0, y0, x1, y1, cell_date))
            else:
                self._cell_rects.append((x0, y0, x1, y1, None))

    def _draw_rounded_rect(self, x0, y0, x1, y1, r, **kwargs):
        """Draw a rounded rectangle on the canvas using arcs and a polygon."""
        # Clamp radius
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        if r < 1:
            self._canvas.create_rectangle(x0, y0, x1, y1, **kwargs)
            return

        # Use a smooth polygon approximation for rounded corners
        points = [
            x0 + r, y0,
            x1 - r, y0,
            x1, y0,
            x1, y0 + r,
            x1, y1 - r,
            x1, y1,
            x1 - r, y1,
            x0 + r, y1,
            x0, y1,
            x0, y1 - r,
            x0, y0 + r,
            x0, y0,
        ]
        self._canvas.create_polygon(points, smooth=True, **kwargs)

    # ==================================================================
    #  Hit testing & mouse events
    # ==================================================================

    def _hit_test(self, x: int, y: int) -> Optional[datetime.date]:
        """Return the date under canvas coordinates (x, y), or None."""
        for (x0, y0, x1, y1, cell_date) in self._cell_rects:
            if cell_date is not None and x0 <= x <= x1 and y0 <= y <= y1:
                return cell_date
        return None

    def _on_canvas_click(self, event):
        if self._state == tkinter.DISABLED:
            return

        date = self._hit_test(event.x, event.y)
        if date is None:
            return
        if not self._is_date_in_range(date):
            return

        # Check if date is in another month - navigate there
        if date.month != self._displayed_month or date.year != self._displayed_year:
            self._displayed_month = date.month
            self._displayed_year = date.year

        if self._multi_select:
            if date in self._selected_dates:
                self._selected_dates.remove(date)
            else:
                self._selected_dates.append(date)
        else:
            self._selected_dates = [date]

        self._sync_variable()
        self._draw()

        if self._command is not None:
            self._command(date)

    def _on_canvas_motion(self, event):
        if self._state == tkinter.DISABLED:
            return

        date = self._hit_test(event.x, event.y)
        if date != self._hover_date:
            self._hover_date = date
            self._draw()

    def _on_canvas_leave(self, event):
        if self._hover_date is not None:
            self._hover_date = None
            self._draw()

    # ==================================================================
    #  Navigation
    # ==================================================================

    def _on_nav(self, delta: int):
        if self._state == tkinter.DISABLED:
            return
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
        self._draw()

    def _on_nav_enter(self, label: tkinter.Label):
        if self._state != tkinter.DISABLED:
            label.configure(fg=self._apply_appearance_mode(self._nav_button_hover_color))

    def _on_nav_leave(self, label: tkinter.Label):
        label.configure(fg=self._apply_appearance_mode(self._nav_button_color))

    def _on_today_btn_enter(self):
        if self._state != tkinter.DISABLED:
            self._today_btn_label.configure(
                fg=self._apply_appearance_mode(self._nav_button_hover_color),
                bg=self._apply_appearance_mode(self._header_color)
            )

    def _on_today_btn_leave(self):
        self._today_btn_label.configure(
            fg=self._apply_appearance_mode(self._header_color),
            bg=self._apply_appearance_mode(self._fg_color)
        )

    # ==================================================================
    #  Date validation
    # ==================================================================

    def _is_date_in_range(self, date: datetime.date) -> bool:
        if self._min_date is not None and date < self._min_date:
            return False
        if self._max_date is not None and date > self._max_date:
            return False
        return True

    # ==================================================================
    #  Variable binding
    # ==================================================================

    def _on_variable_change(self, var_name, index, mode):
        self._parse_variable_value()

    def _parse_variable_value(self):
        if self._variable is None:
            return
        val = self._variable.get()
        if not val:
            self._selected_dates.clear()
            self._draw()
            return
        try:
            parsed = datetime.datetime.strptime(val, self._date_format).date()
            if self._multi_select:
                if parsed not in self._selected_dates:
                    self._selected_dates.append(parsed)
            else:
                self._selected_dates = [parsed]
            self._displayed_year = parsed.year
            self._displayed_month = parsed.month
            self._draw()
        except ValueError:
            pass

    def _sync_variable(self):
        if self._variable is not None:
            if self._selected_dates:
                # For single-select, use the last selected; for multi-select, use the last added
                self._variable.set(self._selected_dates[-1].strftime(self._date_format))
            else:
                self._variable.set("")

    # ==================================================================
    #  Font update callback
    # ==================================================================

    def _update_font(self):
        self._draw()

    # ==================================================================
    #  Scaling overrides
    # ==================================================================

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height))
        self._draw()

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height))
        self._draw()

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)

    # ==================================================================
    #  Public API
    # ==================================================================

    def get_date(self) -> Optional[datetime.date]:
        """Return the most recently selected date, or None."""
        if self._selected_dates:
            return self._selected_dates[-1]
        return None

    def set_date(self, date_or_string: Union[datetime.date, str]):
        """Select a date programmatically. Accepts a datetime.date or a string
        matching the configured date_format."""
        if isinstance(date_or_string, str):
            date = datetime.datetime.strptime(date_or_string, self._date_format).date()
        elif isinstance(date_or_string, datetime.date):
            date = date_or_string
        else:
            raise TypeError(f"Expected datetime.date or str, got {type(date_or_string).__name__}")

        if not self._is_date_in_range(date):
            raise ValueError(f"Date {date} is outside the allowed range "
                             f"[{self._min_date}, {self._max_date}]")

        if self._multi_select:
            if date not in self._selected_dates:
                self._selected_dates.append(date)
        else:
            self._selected_dates = [date]

        self._displayed_year = date.year
        self._displayed_month = date.month
        self._sync_variable()
        self._draw()

        if self._command is not None:
            self._command(date)

    def get_selected_dates(self) -> List[datetime.date]:
        """Return all selected dates as a list (single-element for single-select mode)."""
        return list(self._selected_dates)

    def clear_selection(self):
        """Clear all selected dates."""
        self._selected_dates.clear()
        self._sync_variable()
        self._draw()

    def next_month(self):
        """Navigate to the next month."""
        self._on_nav(1)

    def prev_month(self):
        """Navigate to the previous month."""
        self._on_nav(-1)

    def go_to_today(self):
        """Navigate to the current month and optionally select today."""
        today = datetime.date.today()
        self._displayed_year = today.year
        self._displayed_month = today.month

        if self._is_date_in_range(today):
            if self._multi_select:
                if today not in self._selected_dates:
                    self._selected_dates.append(today)
            else:
                self._selected_dates = [today]
            self._sync_variable()

            if self._command is not None:
                self._command(today)

        self._draw()

    # ==================================================================
    #  configure / cget
    # ==================================================================

    def configure(self, require_redraw=False, **kwargs):
        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True

        if "header_color" in kwargs:
            self._header_color = kwargs.pop("header_color")
            require_redraw = True

        if "nav_button_color" in kwargs:
            self._nav_button_color = kwargs.pop("nav_button_color")
            require_redraw = True

        if "nav_button_hover_color" in kwargs:
            self._nav_button_hover_color = kwargs.pop("nav_button_hover_color")

        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "day_header_text_color" in kwargs:
            self._day_header_text_color = kwargs.pop("day_header_text_color")
            require_redraw = True

        if "selected_color" in kwargs:
            self._selected_color = kwargs.pop("selected_color")
            require_redraw = True

        if "selected_text_color" in kwargs:
            self._selected_text_color = kwargs.pop("selected_text_color")
            require_redraw = True

        if "today_color" in kwargs:
            self._today_color = kwargs.pop("today_color")
            require_redraw = True

        if "today_text_color" in kwargs:
            self._today_text_color = kwargs.pop("today_text_color")
            require_redraw = True

        if "hover_color" in kwargs:
            self._hover_color = kwargs.pop("hover_color")
            require_redraw = True

        if "other_month_text_color" in kwargs:
            self._other_month_text_color = kwargs.pop("other_month_text_color")
            require_redraw = True

        if "disabled_color" in kwargs:
            self._disabled_color = kwargs.pop("disabled_color")
            require_redraw = True

        if "week_number_text_color" in kwargs:
            self._week_number_text_color = kwargs.pop("week_number_text_color")
            require_redraw = True

        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            require_redraw = True

        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            require_redraw = True

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_font)
            require_redraw = True

        if "header_font" in kwargs:
            self._header_font = kwargs.pop("header_font")
            require_redraw = True

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

        if "date_format" in kwargs:
            self._date_format = kwargs.pop("date_format")

        if "min_date" in kwargs:
            self._min_date = kwargs.pop("min_date")
            require_redraw = True

        if "max_date" in kwargs:
            self._max_date = kwargs.pop("max_date")
            require_redraw = True

        if "multi_select" in kwargs:
            self._multi_select = kwargs.pop("multi_select")
            if not self._multi_select and len(self._selected_dates) > 1:
                self._selected_dates = [self._selected_dates[-1]]
            require_redraw = True

        if "show_week_numbers" in kwargs:
            self._show_week_numbers = kwargs.pop("show_week_numbers")
            require_redraw = True

        if "first_day_of_week" in kwargs:
            self._first_day_of_week = max(0, min(6, kwargs.pop("first_day_of_week")))
            require_redraw = True

        if "show_today_button" in kwargs:
            self._show_today_button = kwargs.pop("show_today_button")
            if self._show_today_button:
                self._today_btn_frame.grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 6))
            else:
                self._today_btn_frame.grid_forget()
            require_redraw = True

        if "show_other_month_days" in kwargs:
            self._show_other_month_days = kwargs.pop("show_other_month_days")
            require_redraw = True

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            require_redraw = True

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "header_color":
            return self._header_color
        elif attribute_name == "nav_button_color":
            return self._nav_button_color
        elif attribute_name == "nav_button_hover_color":
            return self._nav_button_hover_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "day_header_text_color":
            return self._day_header_text_color
        elif attribute_name == "selected_color":
            return self._selected_color
        elif attribute_name == "selected_text_color":
            return self._selected_text_color
        elif attribute_name == "today_color":
            return self._today_color
        elif attribute_name == "today_text_color":
            return self._today_text_color
        elif attribute_name == "hover_color":
            return self._hover_color
        elif attribute_name == "other_month_text_color":
            return self._other_month_text_color
        elif attribute_name == "disabled_color":
            return self._disabled_color
        elif attribute_name == "week_number_text_color":
            return self._week_number_text_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "border_width":
            return self._border_width
        elif attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "header_font":
            return self._header_font
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "date_format":
            return self._date_format
        elif attribute_name == "min_date":
            return self._min_date
        elif attribute_name == "max_date":
            return self._max_date
        elif attribute_name == "multi_select":
            return self._multi_select
        elif attribute_name == "show_week_numbers":
            return self._show_week_numbers
        elif attribute_name == "first_day_of_week":
            return self._first_day_of_week
        elif attribute_name == "show_today_button":
            return self._show_today_button
        elif attribute_name == "show_other_month_days":
            return self._show_other_month_days
        elif attribute_name == "state":
            return self._state
        else:
            return super().cget(attribute_name)

    # ==================================================================
    #  Bind / Unbind
    # ==================================================================

    def bind(self, sequence=None, command=None, add=True):
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, command, add=True)

    def unbind(self, sequence=None, funcid=None):
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in"
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._canvas.unbind(sequence, None)
        # Restore internal bindings
        self._canvas.bind("<Button-1>", self._on_canvas_click, add=True)
        self._canvas.bind("<Motion>", self._on_canvas_motion, add=True)
        self._canvas.bind("<Leave>", self._on_canvas_leave, add=True)

    # ==================================================================
    #  Lifecycle
    # ==================================================================

    def destroy(self):
        if self._variable is not None and self._variable_callback_name:
            try:
                self._variable.trace_remove("write", self._variable_callback_name)
            except Exception:
                pass
            self._variable_callback_name = ""

        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)

        self._cell_rects.clear()
        self._selected_dates.clear()

        super().destroy()
