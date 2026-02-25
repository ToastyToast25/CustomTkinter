import tkinter
import sys
import math
from typing import Union, Tuple, Optional, Callable, Any, Dict, List

from .core_rendering import CTkCanvas
from .core_rendering import DrawEngine
from .theme import ThemeManager
from .core_widget_classes import CTkBaseClass
from .ctk_scrollbar import CTkScrollbar
from .font import CTkFont
from .utility import pop_from_dict_by_set, check_kwargs_empty


class CTkDataTable(CTkBaseClass):
    """
    Feature-rich data table with sorting, selection, and scrolling.

    Displays tabular data with column headers, sortable columns,
    resizable widths, row selection, and zebra striping.

    Column types:
        - "text" (default): plain text cell
        - "number": right-aligned numeric cell
        - "badge": colored pill with configurable color mapping

    Usage:
        table = CTkDataTable(parent, command=on_row_select)
        table.set_columns([
            {"key": "name", "title": "Name", "width": 200},
            {"key": "status", "title": "Status", "width": 100, "type": "badge"},
        ])
        table.set_data([{"name": "Alice", "status": "Active"}, ...])
    """

    _ROW_HEIGHT = 32
    _HEADER_HEIGHT = 36
    _RESIZE_HANDLE_WIDTH = 6
    _MIN_COLUMN_WIDTH = 40
    _SORT_ARROW_MARGIN = 4
    _CELL_PAD_X = 10
    _BADGE_PAD_X = 6
    _BADGE_PAD_Y = 4
    _BADGE_CORNER_RADIUS = 8
    _PAGE_CONTROLS_HEIGHT = 36

    # default badge color map: value -> (bg_color, text_color)
    _DEFAULT_BADGE_COLORS: Dict[str, Tuple[str, str]] = {
        "active":   ("#D1FAE5", "#065F46"),
        "success":  ("#D1FAE5", "#065F46"),
        "enabled":  ("#D1FAE5", "#065F46"),
        "warning":  ("#FEF3C7", "#92400E"),
        "pending":  ("#FEF3C7", "#92400E"),
        "error":    ("#FEE2E2", "#991B1B"),
        "failed":   ("#FEE2E2", "#991B1B"),
        "disabled": ("#F3F4F6", "#6B7280"),
        "inactive": ("#F3F4F6", "#6B7280"),
        "info":     ("#DBEAFE", "#1E40AF"),
    }

    def __init__(self,
                 master: Any,
                 width: int = 600,
                 height: int = 400,
                 corner_radius: Optional[int] = None,
                 border_width: Optional[int] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 header_fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 header_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 row_color: Optional[Union[str, Tuple[str, str]]] = None,
                 row_alt_color: Optional[Union[str, Tuple[str, str]]] = None,
                 row_hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 row_selected_color: Optional[Union[str, Tuple[str, str]]] = None,
                 scrollbar_button_color: Optional[Union[str, Tuple[str, str]]] = None,
                 scrollbar_button_hover_color: Optional[Union[str, Tuple[str, str]]] = None,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 header_font: Optional[Union[tuple, CTkFont]] = None,
                 select_mode: str = "single",
                 command: Optional[Callable] = None,
                 double_click_command: Optional[Callable] = None,
                 page_size: int = 0,
                 empty_message: str = "No data to display",
                 badge_colors: Optional[Dict[str, Tuple[str, str]]] = None,
                 **kwargs):

        # transfer basic functionality to CTkBaseClass
        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # shape
        self._corner_radius = ThemeManager.theme["CTkFrame"]["corner_radius"] if corner_radius is None else corner_radius
        self._border_width = ThemeManager.theme["CTkFrame"]["border_width"] if border_width is None else border_width

        # colors
        self._fg_color = ThemeManager.theme["CTkFrame"]["fg_color"] if fg_color is None else self._check_color_type(fg_color, transparency=True)
        self._border_color = ThemeManager.theme["CTkFrame"]["border_color"] if border_color is None else self._check_color_type(border_color)
        self._header_fg_color = ("#E5E7EB", "#2D2D2D") if header_fg_color is None else self._check_color_type(header_fg_color)
        self._header_text_color = ("#374151", "#E5E7EB") if header_text_color is None else self._check_color_type(header_text_color)
        self._text_color = ThemeManager.theme["CTkLabel"]["text_color"] if text_color is None else self._check_color_type(text_color)
        self._row_color = ("#FFFFFF", "#1A1A2E") if row_color is None else self._check_color_type(row_color)
        self._row_alt_color = ("#F9FAFB", "#16162A") if row_alt_color is None else self._check_color_type(row_alt_color)
        self._row_hover_color = ("#EFF6FF", "#1E293B") if row_hover_color is None else self._check_color_type(row_hover_color)
        self._row_selected_color = ("#DBEAFE", "#1E3A5F") if row_selected_color is None else self._check_color_type(row_selected_color)
        self._scrollbar_button_color = ThemeManager.theme["CTkScrollbar"]["button_color"] if scrollbar_button_color is None else self._check_color_type(scrollbar_button_color)
        self._scrollbar_button_hover_color = ThemeManager.theme["CTkScrollbar"]["button_hover_color"] if scrollbar_button_hover_color is None else self._check_color_type(scrollbar_button_hover_color)

        # fonts
        self._font = CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)
        self._header_font = CTkFont(weight="bold") if header_font is None else self._check_font_type(header_font)
        if isinstance(self._header_font, CTkFont):
            self._header_font.add_size_configure_callback(self._update_font)

        # behaviour
        self._select_mode = select_mode  # "single", "multi", or "none"
        self._command = command
        self._double_click_command = double_click_command
        self._page_size = page_size  # 0 = no pagination
        self._current_page = 0
        self._empty_message = empty_message
        self._badge_colors = dict(self._DEFAULT_BADGE_COLORS)
        if badge_colors:
            self._badge_colors.update(badge_colors)

        # data state
        self._columns: List[Dict[str, Any]] = []
        self._data: List[Dict[str, Any]] = []
        self._display_data: List[Dict[str, Any]] = []  # sorted/paginated view
        self._display_indices: List[int] = []  # original indices of display_data rows
        self._sort_column: Optional[str] = None
        self._sort_reverse: bool = False
        self._selected_indices: List[int] = []  # indices into _data (original)
        self._hover_display_row: int = -1

        # column resize state
        self._resize_col_index: int = -1
        self._resize_start_x: int = 0
        self._resize_start_width: int = 0

        # --- build widget hierarchy ---
        # outer canvas for rounded border
        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, rowspan=2, columnspan=2, sticky="nsew")
        self._draw_engine = DrawEngine(self._canvas)

        # configure grid: row 0 = content, row 1 = optional page controls
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # inner frame for clipping
        border_offset = max(self._corner_radius, self._border_width)
        self._inner_frame = tkinter.Frame(self, highlightthickness=0, bd=0)
        self._inner_frame.grid(row=0, column=0, sticky="nsew",
                               padx=border_offset, pady=border_offset)
        self._inner_frame.grid_rowconfigure(0, weight=0)  # header
        self._inner_frame.grid_rowconfigure(1, weight=1)  # body
        self._inner_frame.grid_columnconfigure(0, weight=1)

        # header canvas (fixed, no vertical scroll)
        self._header_canvas = tkinter.Canvas(self._inner_frame, highlightthickness=0, bd=0, height=self._HEADER_HEIGHT)
        self._header_canvas.grid(row=0, column=0, sticky="ew")

        # body canvas (scrollable)
        self._body_canvas = tkinter.Canvas(self._inner_frame, highlightthickness=0, bd=0)
        self._body_canvas.grid(row=1, column=0, sticky="nsew")

        # scrollbars
        scrollbar_fg = self._fg_color
        self._y_scrollbar = CTkScrollbar(self,
                                         width=8,
                                         height=0,
                                         border_spacing=0,
                                         fg_color=scrollbar_fg,
                                         button_color=self._scrollbar_button_color,
                                         button_hover_color=self._scrollbar_button_hover_color,
                                         orientation="vertical",
                                         command=self._body_canvas.yview)
        self._x_scrollbar = CTkScrollbar(self,
                                         height=8,
                                         width=0,
                                         border_spacing=0,
                                         fg_color=scrollbar_fg,
                                         button_color=self._scrollbar_button_color,
                                         button_hover_color=self._scrollbar_button_hover_color,
                                         orientation="horizontal",
                                         command=self._on_xscroll)

        self._body_canvas.configure(yscrollcommand=self._y_scrollbar.set,
                                    xscrollcommand=self._x_scrollbar.set)

        self._y_scrollbar.grid(row=0, column=1, sticky="ns",
                               padx=(2, border_offset), pady=border_offset)
        self._x_scrollbar.grid(row=1, column=0, sticky="ew",
                               padx=border_offset, pady=(2, border_offset))

        # pagination frame (shown only when page_size > 0)
        self._page_frame = tkinter.Frame(self._inner_frame, highlightthickness=0, bd=0,
                                         height=self._PAGE_CONTROLS_HEIGHT)
        if self._page_size > 0:
            self._inner_frame.grid_rowconfigure(2, weight=0)
            self._page_frame.grid(row=2, column=0, sticky="ew")

        self._page_label = tkinter.Label(self._page_frame, text="", anchor="center")
        self._page_prev_btn = tkinter.Label(self._page_frame, text="<  Prev", cursor="hand2")
        self._page_next_btn = tkinter.Label(self._page_frame, text="Next  >", cursor="hand2")
        self._page_prev_btn.pack(side="left", padx=8, pady=4)
        self._page_label.pack(side="left", expand=True, fill="x", padx=8, pady=4)
        self._page_next_btn.pack(side="right", padx=8, pady=4)
        self._page_prev_btn.bind("<Button-1>", self._prev_page)
        self._page_next_btn.bind("<Button-1>", self._next_page)

        # bindings
        self._header_canvas.bind("<Button-1>", self._on_header_click)
        self._header_canvas.bind("<Motion>", self._on_header_motion)
        self._header_canvas.bind("<B1-Motion>", self._on_header_drag)
        self._header_canvas.bind("<ButtonRelease-1>", self._on_header_release)
        self._body_canvas.bind("<Button-1>", self._on_body_click)
        self._body_canvas.bind("<Double-Button-1>", self._on_body_double_click)
        self._body_canvas.bind("<Motion>", self._on_body_motion)
        self._body_canvas.bind("<Leave>", self._on_body_leave)

        # mouse wheel
        if "linux" in sys.platform:
            self._body_canvas.bind("<Button-4>", self._on_mousewheel)
            self._body_canvas.bind("<Button-5>", self._on_mousewheel)
        else:
            self._body_canvas.bind("<MouseWheel>", self._on_mousewheel)

        # empty state id
        self._empty_text_id = None

        # initial draw
        self._draw()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        if not self._canvas.winfo_exists():
            return

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(
            self._apply_widget_scaling(self._current_width),
            self._apply_widget_scaling(self._current_height),
            self._apply_widget_scaling(self._corner_radius),
            self._apply_widget_scaling(self._border_width))

        if no_color_updates is False or requires_recoloring:
            if self._fg_color == "transparent":
                inner_color = self._apply_appearance_mode(self._bg_color)
            else:
                inner_color = self._apply_appearance_mode(self._fg_color)

            self._canvas.itemconfig("inner_parts", fill=inner_color, outline=inner_color)
            self._canvas.itemconfig("border_parts",
                                    fill=self._apply_appearance_mode(self._border_color),
                                    outline=self._apply_appearance_mode(self._border_color))
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

            # propagate colors to inner widgets
            self._inner_frame.configure(bg=inner_color)
            self._header_canvas.configure(bg=self._apply_appearance_mode(self._header_fg_color))
            self._body_canvas.configure(bg=self._apply_appearance_mode(self._row_color))
            self._page_frame.configure(bg=inner_color)
            self._page_label.configure(bg=inner_color,
                                       fg=self._apply_appearance_mode(self._text_color),
                                       font=self._apply_font_scaling(self._font))
            self._page_prev_btn.configure(bg=inner_color,
                                          fg=self._apply_appearance_mode(self._text_color),
                                          font=self._apply_font_scaling(self._font))
            self._page_next_btn.configure(bg=inner_color,
                                          fg=self._apply_appearance_mode(self._text_color),
                                          font=self._apply_font_scaling(self._font))

        self._canvas.tag_lower("inner_parts")
        self._canvas.tag_lower("border_parts")

        self._redraw_table()

    def _redraw_table(self):
        """Full redraw of header and body canvases."""
        self._compute_display_data()
        self._draw_header()
        self._draw_body()
        self._update_scroll_region()
        self._update_page_controls()

    # ------------------------------------------------------------------
    # Display data computation (sorting + pagination)
    # ------------------------------------------------------------------

    def _compute_display_data(self):
        """Compute the display data from the raw data, applying sort and pagination."""
        indices = list(range(len(self._data)))

        # sort
        if self._sort_column is not None:
            col_key = self._sort_column
            col_type = self._get_column_type(col_key)

            def sort_key(idx):
                val = self._data[idx].get(col_key, "")
                if col_type == "number":
                    try:
                        return float(val) if val != "" else float("-inf")
                    except (ValueError, TypeError):
                        return float("-inf")
                return str(val).lower()

            indices.sort(key=sort_key, reverse=self._sort_reverse)

        # pagination
        if self._page_size > 0:
            total_pages = self._total_pages()
            if self._current_page >= total_pages:
                self._current_page = max(0, total_pages - 1)
            start = self._current_page * self._page_size
            end = start + self._page_size
            indices = indices[start:end]

        self._display_indices = indices
        self._display_data = [self._data[i] for i in indices]

    def _total_pages(self) -> int:
        if self._page_size <= 0 or len(self._data) == 0:
            return 1
        return math.ceil(len(self._data) / self._page_size)

    # ------------------------------------------------------------------
    # Header drawing
    # ------------------------------------------------------------------

    def _draw_header(self):
        self._header_canvas.delete("all")

        if not self._columns:
            return

        header_bg = self._apply_appearance_mode(self._header_fg_color)
        header_fg = self._apply_appearance_mode(self._header_text_color)
        scaled_font = self._apply_font_scaling(self._header_font)
        h = self._HEADER_HEIGHT

        x = 0
        for i, col in enumerate(self._columns):
            w = col.get("width", 100)

            # background
            self._header_canvas.create_rectangle(x, 0, x + w, h,
                                                  fill=header_bg, outline=header_bg,
                                                  tags=("header_bg", f"hdr_{i}"))

            # separator line
            self._header_canvas.create_line(x + w - 1, 4, x + w - 1, h - 4,
                                             fill=self._apply_appearance_mode(self._border_color),
                                             width=1, tags=("header_sep",))

            # title text
            title = col.get("title", col.get("key", ""))
            text_x = x + self._CELL_PAD_X
            anchor = "w"

            # sort indicator
            sort_indicator = ""
            if self._sort_column == col.get("key"):
                sort_indicator = " \u25B2" if not self._sort_reverse else " \u25BC"

            display_title = title + sort_indicator

            # truncate if needed
            display_title = self._truncate_text(display_title, w - 2 * self._CELL_PAD_X, scaled_font)

            self._header_canvas.create_text(text_x, h // 2,
                                             text=display_title,
                                             fill=header_fg,
                                             font=scaled_font,
                                             anchor="w",
                                             tags=("header_text", f"hdr_text_{i}"))
            x += w

        # extend header background to fill remaining width
        canvas_width = max(self._inner_frame.winfo_width(), x)
        if canvas_width > x:
            self._header_canvas.create_rectangle(x, 0, canvas_width, h,
                                                  fill=header_bg, outline=header_bg,
                                                  tags=("header_bg_extra",))

        self._header_canvas.configure(scrollregion=(0, 0, x, h))

    # ------------------------------------------------------------------
    # Body drawing
    # ------------------------------------------------------------------

    def _draw_body(self):
        self._body_canvas.delete("all")

        if not self._columns:
            self._draw_empty_state()
            return

        if not self._display_data:
            self._draw_empty_state()
            return

        scaled_font = self._apply_font_scaling(self._font)
        row_h = self._ROW_HEIGHT

        row_color = self._apply_appearance_mode(self._row_color)
        alt_color = self._apply_appearance_mode(self._row_alt_color)
        text_fg = self._apply_appearance_mode(self._text_color)
        hover_color = self._apply_appearance_mode(self._row_hover_color)
        selected_color = self._apply_appearance_mode(self._row_selected_color)

        total_width = sum(c.get("width", 100) for c in self._columns)

        for display_row, row_data in enumerate(self._display_data):
            original_idx = self._display_indices[display_row]
            y = display_row * row_h

            # determine row background
            if original_idx in self._selected_indices:
                bg = selected_color
            elif display_row == self._hover_display_row:
                bg = hover_color
            elif display_row % 2 == 0:
                bg = row_color
            else:
                bg = alt_color

            # row background rectangle
            self._body_canvas.create_rectangle(0, y, total_width, y + row_h,
                                                fill=bg, outline=bg,
                                                tags=("row_bg", f"row_{display_row}"))

            # cells
            x = 0
            for col in self._columns:
                col_key = col.get("key", "")
                col_w = col.get("width", 100)
                col_type = col.get("type", "text")
                col_align = col.get("align", None)

                cell_value = row_data.get(col_key, "")
                if cell_value is None:
                    cell_value = ""

                if col_type == "badge":
                    self._draw_badge_cell(x, y, col_w, row_h, str(cell_value),
                                          display_row, scaled_font)
                else:
                    # determine alignment
                    if col_align is None:
                        if col_type == "number":
                            col_align = "right"
                        else:
                            col_align = "left"

                    self._draw_text_cell(x, y, col_w, row_h, str(cell_value),
                                         col_align, text_fg, display_row, scaled_font)
                x += col_w

            # bottom border for row
            self._body_canvas.create_line(0, y + row_h - 1, total_width, y + row_h - 1,
                                           fill=self._apply_appearance_mode(("#E5E7EB", "#2D2D2D")),
                                           width=1, tags=("row_border",))

        self._empty_text_id = None

    def _draw_text_cell(self, x: int, y: int, w: int, h: int, text: str,
                        align: str, fill: str, display_row: int, font: tuple):
        """Draw a plain text cell."""
        usable = w - 2 * self._CELL_PAD_X
        truncated = self._truncate_text(text, usable, font)

        if align == "right":
            text_x = x + w - self._CELL_PAD_X
            anchor = "e"
        elif align == "center":
            text_x = x + w // 2
            anchor = "center"
        else:
            text_x = x + self._CELL_PAD_X
            anchor = "w"

        self._body_canvas.create_text(text_x, y + h // 2,
                                       text=truncated,
                                       fill=fill,
                                       font=font,
                                       anchor=anchor,
                                       tags=("cell_text", f"cell_r{display_row}"))

    def _draw_badge_cell(self, x: int, y: int, w: int, h: int, text: str,
                         display_row: int, font: tuple):
        """Draw a badge (colored pill) cell."""
        if not text:
            return

        lookup_key = text.lower().strip()
        bg_color, fg_color = self._badge_colors.get(lookup_key, ("#E5E7EB", "#374151"))

        # measure text to compute pill size
        text_width = self._measure_text_width(text, font)
        pill_w = text_width + 2 * self._BADGE_PAD_X
        pill_h = h - 2 * self._BADGE_PAD_Y
        pill_x = x + self._CELL_PAD_X
        pill_y = y + self._BADGE_PAD_Y

        r = min(self._BADGE_CORNER_RADIUS, pill_h // 2)

        # draw rounded pill using create_polygon (oval approximation)
        self._draw_rounded_pill(pill_x, pill_y, pill_x + pill_w, pill_y + pill_h,
                                r, bg_color, display_row)

        # text centered in pill
        self._body_canvas.create_text(pill_x + pill_w // 2, y + h // 2,
                                       text=text,
                                       fill=fg_color,
                                       font=font,
                                       anchor="center",
                                       tags=("badge_text", f"cell_r{display_row}"))

    def _draw_rounded_pill(self, x1: int, y1: int, x2: int, y2: int,
                           radius: int, fill: str, display_row: int):
        """Draw a rounded rectangle (pill) on the body canvas."""
        r = radius
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]
        self._body_canvas.create_polygon(points, fill=fill, outline=fill,
                                          smooth=True,
                                          tags=("badge_bg", f"cell_r{display_row}"))

    def _draw_empty_state(self):
        """Draw the empty-state message centered in the body canvas."""
        self._body_canvas.update_idletasks()
        canvas_w = self._body_canvas.winfo_width()
        canvas_h = self._body_canvas.winfo_height()
        if canvas_w <= 1:
            canvas_w = self._desired_width
        if canvas_h <= 1:
            canvas_h = self._desired_height - self._HEADER_HEIGHT

        self._empty_text_id = self._body_canvas.create_text(
            canvas_w // 2, canvas_h // 2,
            text=self._empty_message,
            fill=self._apply_appearance_mode(("#9CA3AF", "#6B7280")),
            font=self._apply_font_scaling(self._font),
            anchor="center",
            tags=("empty_text",))

    # ------------------------------------------------------------------
    # Text measurement and truncation
    # ------------------------------------------------------------------

    def _measure_text_width(self, text: str, font: tuple) -> int:
        """Measure text width in pixels using a temporary canvas text item."""
        tmp_id = self._body_canvas.create_text(0, 0, text=text, font=font, anchor="nw")
        bbox = self._body_canvas.bbox(tmp_id)
        self._body_canvas.delete(tmp_id)
        if bbox:
            return bbox[2] - bbox[0]
        return len(text) * 8  # fallback estimate

    def _truncate_text(self, text: str, max_width: int, font: tuple) -> str:
        """Truncate text with ellipsis if it exceeds max_width pixels."""
        if max_width <= 0:
            return ""
        text_w = self._measure_text_width(text, font)
        if text_w <= max_width:
            return text

        ellipsis = "\u2026"
        ellipsis_w = self._measure_text_width(ellipsis, font)
        avail = max_width - ellipsis_w
        if avail <= 0:
            return ellipsis

        # binary search for optimal truncation point
        lo, hi = 0, len(text)
        best = 0
        while lo <= hi:
            mid = (lo + hi) // 2
            w = self._measure_text_width(text[:mid], font)
            if w <= avail:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1

        return text[:best] + ellipsis

    # ------------------------------------------------------------------
    # Scroll region
    # ------------------------------------------------------------------

    def _update_scroll_region(self):
        """Update the body canvas scroll region based on data dimensions."""
        total_width = sum(c.get("width", 100) for c in self._columns) if self._columns else self._desired_width
        total_height = len(self._display_data) * self._ROW_HEIGHT if self._display_data else 0

        self._body_canvas.configure(scrollregion=(0, 0, total_width, total_height))
        self._header_canvas.configure(scrollregion=(0, 0, total_width, self._HEADER_HEIGHT))

    def _on_xscroll(self, *args):
        """Synchronize horizontal scroll between header and body."""
        self._body_canvas.xview(*args)
        self._header_canvas.xview(*args)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling on body canvas."""
        if sys.platform.startswith("win"):
            delta = -int(event.delta / 120)
        elif sys.platform == "darwin":
            delta = -event.delta
        else:
            delta = -1 if event.num == 4 else 1

        self._body_canvas.yview_scroll(delta, "units")

    # ------------------------------------------------------------------
    # Header interactions (sort + resize)
    # ------------------------------------------------------------------

    def _get_col_at_x(self, canvas_x: float) -> int:
        """Return column index at the given canvas x coordinate, or -1."""
        x = 0
        for i, col in enumerate(self._columns):
            w = col.get("width", 100)
            if x <= canvas_x < x + w:
                return i
            x += w
        return -1

    def _get_resize_col_at_x(self, canvas_x: float) -> int:
        """Return the column index whose right edge is near canvas_x (for resize), or -1."""
        x = 0
        half_handle = self._RESIZE_HANDLE_WIDTH // 2
        for i, col in enumerate(self._columns):
            w = col.get("width", 100)
            right_edge = x + w
            if right_edge - half_handle <= canvas_x <= right_edge + half_handle:
                return i
            x += w
        return -1

    def _canvas_x_from_event(self, event, canvas) -> float:
        """Convert event x to canvas coordinate, accounting for scroll."""
        return canvas.canvasx(event.x)

    def _on_header_click(self, event):
        """Handle header click: start resize or prepare for sort."""
        cx = self._canvas_x_from_event(event, self._header_canvas)

        resize_idx = self._get_resize_col_at_x(cx)
        if resize_idx >= 0:
            self._resize_col_index = resize_idx
            self._resize_start_x = event.x
            self._resize_start_width = self._columns[resize_idx].get("width", 100)
            return

        # mark for sort on release
        self._resize_col_index = -1

    def _on_header_motion(self, event):
        """Update cursor when hovering near column edges."""
        cx = self._canvas_x_from_event(event, self._header_canvas)
        resize_idx = self._get_resize_col_at_x(cx)
        if resize_idx >= 0:
            self._header_canvas.configure(cursor="sb_h_double_arrow")
        else:
            self._header_canvas.configure(cursor="hand2")

    def _on_header_drag(self, event):
        """Handle column resize drag."""
        if self._resize_col_index < 0:
            return

        dx = event.x - self._resize_start_x
        new_width = max(self._MIN_COLUMN_WIDTH, self._resize_start_width + dx)
        self._columns[self._resize_col_index]["width"] = new_width
        self._redraw_table()

    def _on_header_release(self, event):
        """Handle header release: trigger sort if it was a click (not a drag)."""
        if self._resize_col_index >= 0:
            # was a resize operation, don't sort
            self._resize_col_index = -1
            return

        cx = self._canvas_x_from_event(event, self._header_canvas)
        col_idx = self._get_col_at_x(cx)
        if col_idx < 0:
            return

        col_key = self._columns[col_idx].get("key")
        if col_key is None:
            return

        if self._sort_column == col_key:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = col_key
            self._sort_reverse = False

        self._redraw_table()

    # ------------------------------------------------------------------
    # Body interactions (select + hover)
    # ------------------------------------------------------------------

    def _display_row_from_event(self, event) -> int:
        """Return the display row index for a body canvas event, or -1."""
        cy = self._body_canvas.canvasy(event.y)
        row = int(cy // self._ROW_HEIGHT)
        if 0 <= row < len(self._display_data):
            return row
        return -1

    def _on_body_click(self, event):
        """Handle row selection on body click."""
        if self._select_mode == "none":
            return

        display_row = self._display_row_from_event(event)
        if display_row < 0:
            return

        original_idx = self._display_indices[display_row]

        ctrl_held = bool(event.state & 0x0004)
        shift_held = bool(event.state & 0x0001)

        if self._select_mode == "multi" and ctrl_held:
            # toggle selection
            if original_idx in self._selected_indices:
                self._selected_indices.remove(original_idx)
            else:
                self._selected_indices.append(original_idx)
        elif self._select_mode == "multi" and shift_held and self._selected_indices:
            # range selection from last selected to current
            last = self._selected_indices[-1]
            # find display positions
            try:
                last_display = self._display_indices.index(last)
            except ValueError:
                last_display = 0
            lo = min(last_display, display_row)
            hi = max(last_display, display_row)
            for dr in range(lo, hi + 1):
                oi = self._display_indices[dr]
                if oi not in self._selected_indices:
                    self._selected_indices.append(oi)
        else:
            # single select (or multi without modifier)
            self._selected_indices = [original_idx]

        self._redraw_table()

        if self._command is not None:
            self._command(self._selected_indices[:])

    def _on_body_double_click(self, event):
        """Handle double-click on a row."""
        if self._double_click_command is None:
            return

        display_row = self._display_row_from_event(event)
        if display_row < 0:
            return

        original_idx = self._display_indices[display_row]
        self._double_click_command(original_idx)

    def _on_body_motion(self, event):
        """Handle hover highlighting."""
        display_row = self._display_row_from_event(event)
        if display_row != self._hover_display_row:
            self._hover_display_row = display_row
            self._redraw_table()

    def _on_body_leave(self, event):
        """Clear hover state when mouse leaves body."""
        if self._hover_display_row != -1:
            self._hover_display_row = -1
            self._redraw_table()

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    def _update_page_controls(self):
        """Update pagination label and button states."""
        if self._page_size <= 0:
            return

        total = self._total_pages()
        self._page_label.configure(text=f"Page {self._current_page + 1} of {total}")

        # visual feedback for disabled state
        muted = self._apply_appearance_mode(("#9CA3AF", "#6B7280"))
        active = self._apply_appearance_mode(self._text_color)

        self._page_prev_btn.configure(fg=muted if self._current_page <= 0 else active)
        self._page_next_btn.configure(fg=muted if self._current_page >= total - 1 else active)

    def _prev_page(self, event=None):
        if self._current_page > 0:
            self._current_page -= 1
            self._redraw_table()

    def _next_page(self, event=None):
        if self._current_page < self._total_pages() - 1:
            self._current_page += 1
            self._redraw_table()

    # ------------------------------------------------------------------
    # Column helper
    # ------------------------------------------------------------------

    def _get_column_type(self, key: str) -> str:
        for col in self._columns:
            if col.get("key") == key:
                return col.get("type", "text")
        return "text"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_columns(self, columns: List[Dict[str, Any]]):
        """
        Define the table columns.

        Each dict may contain:
            key (str): data dict key for this column (required)
            title (str): display header text (defaults to key)
            width (int): initial column width in pixels (default 100)
            align (str): "left", "center", or "right" (default depends on type)
            type (str): "text", "number", or "badge" (default "text")
        """
        self._columns = []
        for col_spec in columns:
            col = {
                "key": col_spec["key"],
                "title": col_spec.get("title", col_spec["key"]),
                "width": col_spec.get("width", 100),
                "align": col_spec.get("align", None),
                "type": col_spec.get("type", "text"),
            }
            self._columns.append(col)

        self._sort_column = None
        self._sort_reverse = False
        self._redraw_table()

    def set_data(self, rows: List[Dict[str, Any]]):
        """Replace all table data with the given list of row dicts."""
        self._data = list(rows)
        self._selected_indices = []
        self._hover_display_row = -1
        self._current_page = 0
        self._redraw_table()

    def add_row(self, row_dict: Dict[str, Any]):
        """Append a single row to the table data."""
        self._data.append(row_dict)
        self._redraw_table()

    def delete_row(self, index_or_key: Any):
        """
        Delete a row by index (int) or by a dict identifying the row.

        If an int is given, it is treated as the index into the original data list.
        If a dict is given, the first row matching all key/value pairs is removed.
        """
        if isinstance(index_or_key, int):
            if 0 <= index_or_key < len(self._data):
                self._data.pop(index_or_key)
                # clean up selection
                self._selected_indices = [i if i < index_or_key else i - 1
                                           for i in self._selected_indices
                                           if i != index_or_key]
        elif isinstance(index_or_key, dict):
            for i, row in enumerate(self._data):
                if all(row.get(k) == v for k, v in index_or_key.items()):
                    self._data.pop(i)
                    self._selected_indices = [idx if idx < i else idx - 1
                                               for idx in self._selected_indices
                                               if idx != i]
                    break
        self._redraw_table()

    def get_selected(self) -> List[int]:
        """Return a list of selected row indices (into the original data)."""
        return self._selected_indices[:]

    def get_selected_data(self) -> List[Dict[str, Any]]:
        """Return a list of the selected row dicts."""
        return [self._data[i] for i in self._selected_indices if 0 <= i < len(self._data)]

    def sort_by(self, column_key: str, reverse: bool = False):
        """Programmatically sort by a column key."""
        self._sort_column = column_key
        self._sort_reverse = reverse
        self._redraw_table()

    def clear(self):
        """Remove all data and reset selection."""
        self._data = []
        self._selected_indices = []
        self._hover_display_row = -1
        self._current_page = 0
        self._sort_column = None
        self._sort_reverse = False
        self._redraw_table()

    def select_row(self, index: int):
        """Programmatically select a row by its original data index."""
        if 0 <= index < len(self._data) and index not in self._selected_indices:
            if self._select_mode == "single":
                self._selected_indices = [index]
            else:
                self._selected_indices.append(index)
            self._redraw_table()

    def deselect_all(self):
        """Clear all selections."""
        self._selected_indices = []
        self._redraw_table()

    def get_data(self) -> List[Dict[str, Any]]:
        """Return a copy of the current data list."""
        return list(self._data)

    def set_page(self, page: int):
        """Jump to a specific page (0-indexed). Only relevant when page_size > 0."""
        if self._page_size > 0:
            self._current_page = max(0, min(page, self._total_pages() - 1))
            self._redraw_table()

    def update_row(self, index: int, row_dict: Dict[str, Any]):
        """Update a row at the given index with new values."""
        if 0 <= index < len(self._data):
            self._data[index].update(row_dict)
            self._redraw_table()

    # ------------------------------------------------------------------
    # configure / cget
    # ------------------------------------------------------------------

    def configure(self, require_redraw=False, **kwargs):
        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            require_redraw = True

        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "header_fg_color" in kwargs:
            self._header_fg_color = self._check_color_type(kwargs.pop("header_fg_color"))
            require_redraw = True

        if "header_text_color" in kwargs:
            self._header_text_color = self._check_color_type(kwargs.pop("header_text_color"))
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "row_color" in kwargs:
            self._row_color = self._check_color_type(kwargs.pop("row_color"))
            require_redraw = True

        if "row_alt_color" in kwargs:
            self._row_alt_color = self._check_color_type(kwargs.pop("row_alt_color"))
            require_redraw = True

        if "row_hover_color" in kwargs:
            self._row_hover_color = self._check_color_type(kwargs.pop("row_hover_color"))
            require_redraw = True

        if "row_selected_color" in kwargs:
            self._row_selected_color = self._check_color_type(kwargs.pop("row_selected_color"))
            require_redraw = True

        if "scrollbar_button_color" in kwargs:
            self._scrollbar_button_color = self._check_color_type(kwargs.pop("scrollbar_button_color"))
            self._y_scrollbar.configure(button_color=self._scrollbar_button_color)
            self._x_scrollbar.configure(button_color=self._scrollbar_button_color)

        if "scrollbar_button_hover_color" in kwargs:
            self._scrollbar_button_hover_color = self._check_color_type(kwargs.pop("scrollbar_button_hover_color"))
            self._y_scrollbar.configure(button_hover_color=self._scrollbar_button_hover_color)
            self._x_scrollbar.configure(button_hover_color=self._scrollbar_button_hover_color)

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_font)
            require_redraw = True

        if "header_font" in kwargs:
            if isinstance(self._header_font, CTkFont):
                self._header_font.remove_size_configure_callback(self._update_font)
            self._header_font = self._check_font_type(kwargs.pop("header_font"))
            if isinstance(self._header_font, CTkFont):
                self._header_font.add_size_configure_callback(self._update_font)
            require_redraw = True

        if "select_mode" in kwargs:
            self._select_mode = kwargs.pop("select_mode")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "double_click_command" in kwargs:
            self._double_click_command = kwargs.pop("double_click_command")

        if "page_size" in kwargs:
            self._page_size = kwargs.pop("page_size")
            self._current_page = 0
            if self._page_size > 0:
                self._inner_frame.grid_rowconfigure(2, weight=0)
                self._page_frame.grid(row=2, column=0, sticky="ew")
            else:
                self._page_frame.grid_forget()
            require_redraw = True

        if "empty_message" in kwargs:
            self._empty_message = kwargs.pop("empty_message")
            require_redraw = True

        if "badge_colors" in kwargs:
            new_badge_colors = kwargs.pop("badge_colors")
            if new_badge_colors is not None:
                self._badge_colors.update(new_badge_colors)
            require_redraw = True

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
        elif attribute_name == "header_fg_color":
            return self._header_fg_color
        elif attribute_name == "header_text_color":
            return self._header_text_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "row_color":
            return self._row_color
        elif attribute_name == "row_alt_color":
            return self._row_alt_color
        elif attribute_name == "row_hover_color":
            return self._row_hover_color
        elif attribute_name == "row_selected_color":
            return self._row_selected_color
        elif attribute_name == "scrollbar_button_color":
            return self._scrollbar_button_color
        elif attribute_name == "scrollbar_button_hover_color":
            return self._scrollbar_button_hover_color
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "header_font":
            return self._header_font
        elif attribute_name == "select_mode":
            return self._select_mode
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "double_click_command":
            return self._double_click_command
        elif attribute_name == "page_size":
            return self._page_size
        elif attribute_name == "empty_message":
            return self._empty_message
        elif attribute_name == "badge_colors":
            return dict(self._badge_colors)
        else:
            return super().cget(attribute_name)

    # ------------------------------------------------------------------
    # CTkBaseClass overrides
    # ------------------------------------------------------------------

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw()

    def _update_font(self):
        """Callback when CTkFont is reconfigured."""
        self._draw()

    def destroy(self):
        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)
        if isinstance(self._header_font, CTkFont):
            self._header_font.remove_size_configure_callback(self._update_font)
        super().destroy()

    def bind(self, sequence=None, command=None, add=True):
        """Bind events on the body canvas."""
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._body_canvas.bind(sequence, command, add=True)

    def unbind(self, sequence=None, funcid=None):
        """Unbind events from the body canvas."""
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in"
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._body_canvas.unbind(sequence, None)

    def focus(self):
        return self._body_canvas.focus()

    def focus_set(self):
        return self._body_canvas.focus_set()

    def focus_force(self):
        return self._body_canvas.focus_force()
