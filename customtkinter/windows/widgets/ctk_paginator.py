import sys
import tkinter
from typing import Union, Tuple, Optional, Callable, List, Any

from .theme import ThemeManager
from .core_widget_classes import CTkBaseClass
from .font import CTkFont
from .ctk_button import CTkButton
from .ctk_label import CTkLabel


class CTkPaginator(CTkBaseClass):
    """
    Page navigation control with Previous/Next buttons, numbered page buttons,
    ellipsis for large page counts, and optional "Page X of Y" info label.

    Features:
        - Previous/Next navigation buttons
        - Numbered page buttons with current page highlight
        - Ellipsis (...) for large page counts
        - Optional First/Last page buttons
        - Optional "Page X of Y" info text
        - Keyboard navigation (Left/Right arrows)
        - Configurable max visible page buttons

    Usage:
        paginator = CTkPaginator(parent, total_pages=20, command=on_page_change)
        paginator.set_page(5)
        current = paginator.get_page()

    Arguments:
        total_pages: total number of pages (>= 0)
        current_page: initially selected page (1-based, default 1)
        max_visible_pages: how many page number buttons to show at once (default 7)
        command: callback(page_number: int) when page changes
        show_first_last: show "First" and "Last" buttons (default False)
        show_info: show "Page X of Y" text label (default False)
        button_width: width of each page button (default 32)
        button_height: height of each page button (default 32)
        button_corner_radius: corner radius for page buttons (default None, uses theme)
        fg_color: foreground/background color of the widget frame
        button_color: color for non-selected page buttons
        button_hover_color: hover color for page buttons
        selected_color: color for the selected page button
        selected_hover_color: hover color for the selected page button
        text_color: text color for page buttons
        selected_text_color: text color for the selected page button
        font: font for page buttons
        state: "normal" or "disabled"
    """

    def __init__(self,
                 master: Any,
                 width: int = 0,
                 height: int = 36,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,

                 button_color: Optional[Union[str, Tuple[str, str]]] = None,
                 button_hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 selected_color: Optional[Union[str, Tuple[str, str]]] = None,
                 selected_hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 selected_text_color: Optional[Union[str, Tuple[str, str]]] = None,

                 total_pages: int = 1,
                 current_page: int = 1,
                 max_visible_pages: int = 7,

                 command: Union[Callable[[int], Any], None] = None,
                 show_first_last: bool = False,
                 show_info: bool = False,

                 button_width: int = 32,
                 button_height: int = 32,
                 button_corner_radius: Optional[int] = None,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 state: str = "normal",
                 **kwargs):

        # transfer basic functionality to CTkBaseClass
        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # --- colors ---
        self._fg_color: Union[str, Tuple[str, str]] = (
            "transparent" if fg_color is None
            else self._check_color_type(fg_color, transparency=True)
        )
        self._button_color: Union[str, Tuple[str, str]] = (
            "transparent" if button_color is None
            else self._check_color_type(button_color)
        )
        self._button_hover_color: Union[str, Tuple[str, str]] = (
            ThemeManager.theme["CTkButton"]["hover_color"] if button_hover_color is None
            else self._check_color_type(button_hover_color)
        )
        self._selected_color: Union[str, Tuple[str, str]] = (
            ThemeManager.theme["CTkButton"]["fg_color"] if selected_color is None
            else self._check_color_type(selected_color)
        )
        self._selected_hover_color: Union[str, Tuple[str, str]] = (
            ThemeManager.theme["CTkButton"]["hover_color"] if selected_hover_color is None
            else self._check_color_type(selected_hover_color)
        )
        self._text_color: Union[str, Tuple[str, str]] = (
            ThemeManager.theme["CTkButton"]["text_color"] if text_color is None
            else self._check_color_type(text_color)
        )
        self._selected_text_color: Union[str, Tuple[str, str]] = (
            ThemeManager.theme["CTkButton"]["text_color"] if selected_text_color is None
            else self._check_color_type(selected_text_color)
        )

        # --- shape ---
        self._button_width: int = button_width
        self._button_height: int = button_height
        self._button_corner_radius: Optional[int] = button_corner_radius

        # --- font ---
        self._font: Union[tuple, CTkFont] = CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)

        # --- data ---
        self._total_pages: int = max(0, total_pages)
        self._current_page: int = self._clamp_page(current_page)
        self._max_visible_pages: int = max(1, max_visible_pages)
        self._command: Union[Callable[[int], Any], None] = command
        self._show_first_last: bool = show_first_last
        self._show_info: bool = show_info
        self._state: str = state

        # --- internal widget storage ---
        self._page_buttons: List[CTkButton] = []
        self._nav_buttons: dict = {}  # "first", "prev", "next", "last" -> CTkButton
        self._info_label: Optional[CTkLabel] = None
        self._ellipsis_labels: List[CTkLabel] = []

        # --- inner frame for button layout ---
        self._inner_frame = tkinter.Frame(master=self, borderwidth=0, highlightthickness=0)
        self._inner_frame.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # build and draw
        self._build_paginator()
        self._draw()

        # keyboard navigation
        self._bind_keyboard()

    # ------------------------------------------------------------------
    # Helper: clamp page to valid range
    # ------------------------------------------------------------------

    def _clamp_page(self, page: int) -> int:
        """Clamp page number to valid range [1, total_pages]. Returns 1 if total_pages is 0."""
        if self._total_pages <= 0:
            return 1
        return max(1, min(page, self._total_pages))

    # ------------------------------------------------------------------
    # Keyboard navigation
    # ------------------------------------------------------------------

    def _bind_keyboard(self):
        """Bind Left/Right arrow keys for page navigation."""
        self._inner_frame.bind("<Left>", self._on_key_left)
        self._inner_frame.bind("<Right>", self._on_key_right)
        # Also bind on self so keyboard works when widget has focus
        tkinter.Frame.bind(self, "<Left>", self._on_key_left)
        tkinter.Frame.bind(self, "<Right>", self._on_key_right)

    def _on_key_left(self, event=None):
        """Navigate to previous page on Left arrow key."""
        if self._state != "disabled":
            self._go_to_page(self._current_page - 1)

    def _on_key_right(self, event=None):
        """Navigate to next page on Right arrow key."""
        if self._state != "disabled":
            self._go_to_page(self._current_page + 1)

    # ------------------------------------------------------------------
    # Destroy
    # ------------------------------------------------------------------

    def destroy(self):
        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)
        super().destroy()

    # ------------------------------------------------------------------
    # Scaling & appearance
    # ------------------------------------------------------------------

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._rebuild_all()

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
        self._rebuild_all()

    def _update_font(self):
        """Re-apply font to all buttons when font changes."""
        for btn in self._page_buttons:
            btn.configure(font=self._font)
        for btn in self._nav_buttons.values():
            btn.configure(font=self._font)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        if no_color_updates is False:
            # Update inner frame background
            if self._fg_color == "transparent":
                bg = self._apply_appearance_mode(self._bg_color)
            else:
                bg = self._apply_appearance_mode(self._fg_color)
            self._inner_frame.configure(bg=bg)

    # ------------------------------------------------------------------
    # Compute visible page numbers
    # ------------------------------------------------------------------

    def _compute_page_items(self) -> List[Optional[int]]:
        """
        Compute the list of page numbers (1-based) to display as buttons.
        None entries represent ellipsis positions.

        Returns an empty list if total_pages <= 0.
        """
        total = self._total_pages
        if total <= 0:
            return []

        max_vis = self._max_visible_pages
        current = self._current_page

        # If all pages fit within max_visible_pages, show them all
        if total <= max_vis:
            return list(range(1, total + 1))

        # We always show page 1 and page total.
        # The remaining (max_vis - 2) slots are for middle pages + ellipsis markers.
        # Each ellipsis takes one slot.
        pages: List[Optional[int]] = []

        # Calculate the window of consecutive pages around current_page
        # Reserve 2 slots for first and last page
        # Reserve up to 2 slots for ellipsis (left and right)
        # Remaining slots are for the window around current page
        window_size = max_vis - 2  # slots between first and last

        # Determine if we need left ellipsis, right ellipsis, or both
        # The window range (inclusive) that we want to show between first and last
        half = (window_size - 1) // 2

        # No left ellipsis needed: current page is close to start
        if current <= 1 + window_size - 1:
            # Show pages 1 through (window_size + 1), then ellipsis, then last
            # But we need to fit within max_vis total slots
            # Pages: 1, 2, ..., (max_vis - 2), ..., total
            end = max_vis - 2  # leave room for ellipsis + last
            for p in range(1, end + 1):
                pages.append(p)
            pages.append(None)  # ellipsis
            pages.append(total)
            return pages

        # No right ellipsis needed: current page is close to end
        if current >= total - (window_size - 1):
            # Show first, ellipsis, then last (max_vis - 2) pages
            start = total - (max_vis - 3)  # leave room for first + ellipsis
            pages.append(1)
            pages.append(None)  # ellipsis
            for p in range(start, total + 1):
                pages.append(p)
            return pages

        # Both ellipsis needed: current page is in the middle
        # Slots: 1, ..., [window], ..., total
        # Window slots = max_vis - 4 (first, last, left ellipsis, right ellipsis)
        inner_size = max(1, max_vis - 4)
        inner_half = (inner_size - 1) // 2
        start = current - inner_half
        end = start + inner_size - 1

        # Adjust to not overlap with first or last
        if start <= 2:
            start = 2
            end = start + inner_size - 1
        if end >= total - 1:
            end = total - 1
            start = end - inner_size + 1

        pages.append(1)
        pages.append(None)  # left ellipsis
        for p in range(start, end + 1):
            pages.append(p)
        pages.append(None)  # right ellipsis
        pages.append(total)

        return pages

    # ------------------------------------------------------------------
    # Build paginator buttons
    # ------------------------------------------------------------------

    def _clear_paginator(self):
        """Destroy all existing page buttons, nav buttons, and labels."""
        for btn in self._page_buttons:
            btn.destroy()
        self._page_buttons.clear()

        for btn in self._nav_buttons.values():
            btn.destroy()
        self._nav_buttons.clear()

        for label in self._ellipsis_labels:
            label.destroy()
        self._ellipsis_labels.clear()

        if self._info_label is not None:
            self._info_label.destroy()
            self._info_label = None

    def _build_paginator(self):
        """Build (or rebuild) the full paginator layout."""
        self._clear_paginator()

        if self._fg_color == "transparent":
            frame_bg = self._apply_appearance_mode(self._bg_color)
        else:
            frame_bg = self._apply_appearance_mode(self._fg_color)
        self._inner_frame.configure(bg=frame_bg)

        col = 0

        # --- "First" button ---
        if self._show_first_last:
            first_btn = CTkButton(
                master=self._inner_frame,
                text="\u00ab",  # double left arrow
                width=self._button_width,
                height=self._button_height,
                corner_radius=self._button_corner_radius,
                fg_color="transparent",
                hover_color=self._button_hover_color,
                text_color=self._text_color,
                font=self._font,
                command=self._on_first,
                state=self._get_prev_state(),
            )
            first_btn.grid(row=0, column=col, padx=(0, 2), pady=2)
            self._nav_buttons["first"] = first_btn
            col += 1

        # --- "Previous" button ---
        prev_btn = CTkButton(
            master=self._inner_frame,
            text="\u2039",  # single left arrow
            width=self._button_width,
            height=self._button_height,
            corner_radius=self._button_corner_radius,
            fg_color="transparent",
            hover_color=self._button_hover_color,
            text_color=self._text_color,
            font=self._font,
            command=self._on_prev,
            state=self._get_prev_state(),
        )
        prev_btn.grid(row=0, column=col, padx=(0, 2), pady=2)
        self._nav_buttons["prev"] = prev_btn
        col += 1

        # --- Page number buttons and ellipsis ---
        page_items = self._compute_page_items()
        for item in page_items:
            if item is None:
                # Ellipsis label
                ellipsis_label = CTkLabel(
                    master=self._inner_frame,
                    text="\u2026",  # unicode ellipsis
                    width=self._button_width,
                    height=self._button_height,
                    fg_color="transparent",
                    text_color=self._text_color,
                    font=self._font,
                )
                ellipsis_label.grid(row=0, column=col, padx=1, pady=2)
                self._ellipsis_labels.append(ellipsis_label)
            else:
                # Page number button
                is_current = (item == self._current_page)
                btn = CTkButton(
                    master=self._inner_frame,
                    text=str(item),
                    width=self._button_width,
                    height=self._button_height,
                    corner_radius=self._button_corner_radius,
                    fg_color=self._selected_color if is_current else "transparent",
                    hover_color=self._selected_hover_color if is_current else self._button_hover_color,
                    text_color=self._selected_text_color if is_current else self._text_color,
                    font=self._font,
                    command=self._make_page_command(item),
                    state=self._state,
                )
                btn.grid(row=0, column=col, padx=1, pady=2)
                self._page_buttons.append(btn)
            col += 1

        # --- "Next" button ---
        next_btn = CTkButton(
            master=self._inner_frame,
            text="\u203a",  # single right arrow
            width=self._button_width,
            height=self._button_height,
            corner_radius=self._button_corner_radius,
            fg_color="transparent",
            hover_color=self._button_hover_color,
            text_color=self._text_color,
            font=self._font,
            command=self._on_next,
            state=self._get_next_state(),
        )
        next_btn.grid(row=0, column=col, padx=(2, 0), pady=2)
        self._nav_buttons["next"] = next_btn
        col += 1

        # --- "Last" button ---
        if self._show_first_last:
            last_btn = CTkButton(
                master=self._inner_frame,
                text="\u00bb",  # double right arrow
                width=self._button_width,
                height=self._button_height,
                corner_radius=self._button_corner_radius,
                fg_color="transparent",
                hover_color=self._button_hover_color,
                text_color=self._text_color,
                font=self._font,
                command=self._on_last,
                state=self._get_next_state(),
            )
            last_btn.grid(row=0, column=col, padx=(2, 0), pady=2)
            self._nav_buttons["last"] = last_btn
            col += 1

        # --- Info label "Page X of Y" ---
        if self._show_info:
            info_text = self._get_info_text()
            self._info_label = CTkLabel(
                master=self._inner_frame,
                text=info_text,
                height=self._button_height,
                fg_color="transparent",
                text_color=self._text_color,
                font=self._font,
            )
            self._info_label.grid(row=0, column=col, padx=(8, 0), pady=2)
            col += 1

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    def _get_prev_state(self) -> str:
        """Return 'disabled' if on first page or widget disabled, else 'normal'."""
        if self._state == "disabled":
            return "disabled"
        if self._current_page <= 1 or self._total_pages <= 0:
            return "disabled"
        return "normal"

    def _get_next_state(self) -> str:
        """Return 'disabled' if on last page or widget disabled, else 'normal'."""
        if self._state == "disabled":
            return "disabled"
        if self._current_page >= self._total_pages or self._total_pages <= 0:
            return "disabled"
        return "normal"

    def _get_info_text(self) -> str:
        """Return the 'Page X of Y' info string."""
        if self._total_pages <= 0:
            return "Page 0 of 0"
        return f"Page {self._current_page} of {self._total_pages}"

    def _make_page_command(self, page_number: int) -> Callable:
        """Create a callback closure for a specific page button."""
        def _cmd():
            self._go_to_page(page_number)
        return _cmd

    def _go_to_page(self, page: int):
        """Navigate to the given page, rebuild, and call command callback."""
        if self._total_pages <= 0:
            return

        new_page = self._clamp_page(page)
        if new_page == self._current_page:
            return

        self._current_page = new_page
        self._build_paginator()
        self._draw()

        if self._command is not None:
            self._command(self._current_page)

    def _on_first(self):
        self._go_to_page(1)

    def _on_prev(self):
        self._go_to_page(self._current_page - 1)

    def _on_next(self):
        self._go_to_page(self._current_page + 1)

    def _on_last(self):
        self._go_to_page(self._total_pages)

    def _rebuild_all(self):
        """Fully rebuild the paginator and redraw."""
        self._build_paginator()
        self._draw()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_page(self, page: int):
        """Set the current page (1-based). Out of range values are clamped."""
        self._go_to_page(page)

    def get_page(self) -> int:
        """Return the current page number (1-based)."""
        return self._current_page

    def set_total_pages(self, total_pages: int):
        """Set the total number of pages and rebuild the paginator."""
        self._total_pages = max(0, total_pages)
        self._current_page = self._clamp_page(self._current_page)
        self._rebuild_all()

    # ------------------------------------------------------------------
    # configure / cget
    # ------------------------------------------------------------------

    def configure(self, require_redraw=False, **kwargs):
        if "total_pages" in kwargs:
            self._total_pages = max(0, kwargs.pop("total_pages"))
            self._current_page = self._clamp_page(self._current_page)
            self._build_paginator()
            require_redraw = True

        if "current_page" in kwargs:
            self._current_page = self._clamp_page(kwargs.pop("current_page"))
            self._build_paginator()
            require_redraw = True

        if "max_visible_pages" in kwargs:
            self._max_visible_pages = max(1, kwargs.pop("max_visible_pages"))
            self._build_paginator()
            require_redraw = True

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "show_first_last" in kwargs:
            self._show_first_last = kwargs.pop("show_first_last")
            self._build_paginator()
            require_redraw = True

        if "show_info" in kwargs:
            self._show_info = kwargs.pop("show_info")
            self._build_paginator()
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            require_redraw = True

        if "button_color" in kwargs:
            self._button_color = self._check_color_type(kwargs.pop("button_color"), transparency=True)
            self._build_paginator()
            require_redraw = True

        if "button_hover_color" in kwargs:
            self._button_hover_color = self._check_color_type(kwargs.pop("button_hover_color"))
            self._build_paginator()
            require_redraw = True

        if "selected_color" in kwargs:
            self._selected_color = self._check_color_type(kwargs.pop("selected_color"))
            self._build_paginator()
            require_redraw = True

        if "selected_hover_color" in kwargs:
            self._selected_hover_color = self._check_color_type(kwargs.pop("selected_hover_color"))
            self._build_paginator()
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            self._build_paginator()
            require_redraw = True

        if "selected_text_color" in kwargs:
            self._selected_text_color = self._check_color_type(kwargs.pop("selected_text_color"))
            self._build_paginator()
            require_redraw = True

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_font)
            self._build_paginator()
            require_redraw = True

        if "button_width" in kwargs:
            self._button_width = kwargs.pop("button_width")
            self._build_paginator()
            require_redraw = True

        if "button_height" in kwargs:
            self._button_height = kwargs.pop("button_height")
            self._build_paginator()
            require_redraw = True

        if "button_corner_radius" in kwargs:
            self._button_corner_radius = kwargs.pop("button_corner_radius")
            self._build_paginator()
            require_redraw = True

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._build_paginator()
            require_redraw = True

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "total_pages":
            return self._total_pages
        elif attribute_name == "current_page":
            return self._current_page
        elif attribute_name == "max_visible_pages":
            return self._max_visible_pages
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "show_first_last":
            return self._show_first_last
        elif attribute_name == "show_info":
            return self._show_info
        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "button_color":
            return self._button_color
        elif attribute_name == "button_hover_color":
            return self._button_hover_color
        elif attribute_name == "selected_color":
            return self._selected_color
        elif attribute_name == "selected_hover_color":
            return self._selected_hover_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "selected_text_color":
            return self._selected_text_color
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "button_width":
            return self._button_width
        elif attribute_name == "button_height":
            return self._button_height
        elif attribute_name == "button_corner_radius":
            return self._button_corner_radius
        elif attribute_name == "state":
            return self._state
        else:
            return super().cget(attribute_name)

    # ------------------------------------------------------------------
    # Bind / Unbind
    # ------------------------------------------------------------------

    def bind(self, sequence: str = None, command: Callable = None, add: Union[str, bool] = True):
        """Bind an event to the widget frame and all internal buttons."""
        if not (add == "+" or add is True):
            raise ValueError(
                "'add' argument can only be '+' or True to preserve internal callbacks"
            )
        self._inner_frame.bind(sequence, command, add=True)
        for btn in self._page_buttons:
            btn.bind(sequence, command, add=True)
        for btn in self._nav_buttons.values():
            btn.bind(sequence, command, add=True)

    def unbind(self, sequence: str = None, funcid: Optional[str] = None):
        """Unbind an event from the widget frame and all internal buttons."""
        if funcid is not None:
            raise ValueError(
                "'funcid' argument can only be None, because there is a bug in"
                " tkinter and its not clear whether the internal callbacks will be unbinded or not"
            )
        self._inner_frame.unbind(sequence, None)
        for btn in self._page_buttons:
            btn.unbind(sequence, None)
        for btn in self._nav_buttons.values():
            btn.unbind(sequence, None)

    def focus(self):
        return self._inner_frame.focus()

    def focus_set(self):
        return self._inner_frame.focus_set()

    def focus_force(self):
        return self._inner_frame.focus_force()
