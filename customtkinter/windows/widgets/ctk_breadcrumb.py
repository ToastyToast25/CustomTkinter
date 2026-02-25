import copy
import tkinter
import sys
from typing import Union, Tuple, List, Callable, Optional, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont
from .utility import check_kwargs_empty


class CTkBreadcrumb(CTkBaseClass):
    """
    Breadcrumb navigation widget showing a clickable path hierarchy.

    Each segment except the last is clickable and shows hover effects.
    The last segment (current page) is displayed in bold/accent style.
    When there are more items than max_items, middle items are collapsed
    into an ellipsis ("...").

    Arguments:
        items: list of path segment strings
        separator: separator string between segments (default " > ")
        command: callback(index: int, text: str) when a clickable segment is clicked
        max_items: collapse middle items if more than this many (0 = no collapse)
        font: font for segment labels
        separator_font: font for separator labels (defaults to font)
        text_color: color for clickable (non-last) segments
        text_color_current: color for the last (current) segment
        separator_color: color for separator characters
        hover_color: text color on hover for clickable segments
        fg_color: background fill color
        corner_radius: corner rounding radius
    """

    def __init__(self,
                 master: Any,
                 width: int = 0,
                 height: int = 28,
                 corner_radius: Optional[int] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,

                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color_current: Optional[Union[str, Tuple[str, str]]] = None,
                 separator_color: Optional[Union[str, Tuple[str, str]]] = None,
                 hover_color: Optional[Union[str, Tuple[str, str]]] = None,

                 items: Optional[List[str]] = None,
                 separator: str = " > ",
                 command: Union[Callable[[int, str], Any], None] = None,
                 max_items: int = 0,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 separator_font: Optional[Union[tuple, CTkFont]] = None,
                 **kwargs):

        # transfer basic functionality to CTkBaseClass
        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # --- colors ---
        # Use CTkButton theme colors for clickable segments (accent),
        # CTkLabel theme colors for current segment (regular text)
        self._fg_color: Union[str, Tuple[str, str]] = (
            "transparent" if fg_color is None
            else self._check_color_type(fg_color, transparency=True)
        )
        self._text_color: Union[str, Tuple[str, str]] = (
            ThemeManager.theme["CTkButton"]["fg_color"] if text_color is None
            else self._check_color_type(text_color)
        )
        self._text_color_current: Union[str, Tuple[str, str]] = (
            ThemeManager.theme["CTkLabel"]["text_color"] if text_color_current is None
            else self._check_color_type(text_color_current)
        )
        self._separator_color: Union[str, Tuple[str, str]] = (
            ThemeManager.theme["CTkLabel"]["text_color"] if separator_color is None
            else self._check_color_type(separator_color)
        )
        self._hover_color: Union[str, Tuple[str, str]] = (
            ThemeManager.theme["CTkButton"]["hover_color"] if hover_color is None
            else self._check_color_type(hover_color)
        )

        # --- shape ---
        self._corner_radius: int = (
            ThemeManager.theme["CTkLabel"]["corner_radius"] if corner_radius is None
            else corner_radius
        )

        # --- fonts ---
        self._font: Union[tuple, CTkFont] = CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_fonts)

        self._separator_font: Union[tuple, CTkFont] = (
            self._font if separator_font is None
            else self._check_font_type(separator_font)
        )
        if separator_font is not None and isinstance(self._separator_font, CTkFont):
            self._separator_font.add_size_configure_callback(self._update_fonts)

        # --- data ---
        self._items: List[str] = list(items) if items is not None else []
        self._separator: str = separator
        self._command: Union[Callable[[int, str], Any], None] = command
        self._max_items: int = max_items

        # --- internal widget storage ---
        # _segment_labels: list of tkinter.Label for each displayed segment
        # _separator_labels: list of tkinter.Label for separators between segments
        # _display_map: list of (original_index, text) for each displayed segment
        self._segment_labels: List[tkinter.Label] = []
        self._separator_labels: List[tkinter.Label] = []
        self._display_map: List[Tuple[Optional[int], str]] = []  # (original_index or None, text)

        # --- canvas and draw engine ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, sticky="nswe")
        self._draw_engine = DrawEngine(self._canvas)

        # --- inner frame for segment layout (placed on top of canvas) ---
        self._inner_frame = tkinter.Frame(master=self, bg="white", borderwidth=0,
                                          highlightthickness=0)
        self._inner_frame.grid(row=0, column=0, sticky="nsw")

        # build and draw
        self._build_segments()
        self._draw()

    def destroy(self):
        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_fonts)
        if (self._separator_font is not self._font
                and isinstance(self._separator_font, CTkFont)):
            self._separator_font.remove_size_configure_callback(self._update_fonts)
        super().destroy()

    # ------------------------------------------------------------------
    # Scaling & appearance
    # ------------------------------------------------------------------

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._rebuild_all()

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
        self._rebuild_all()

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._draw()

    def _update_fonts(self):
        """Re-apply scaled fonts to all segment and separator labels."""
        for label in self._segment_labels:
            label.configure(font=self._apply_font_scaling(self._font))
        for label in self._separator_labels:
            label.configure(font=self._apply_font_scaling(self._separator_font))

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(
            self._apply_widget_scaling(self._current_width),
            self._apply_widget_scaling(self._current_height),
            self._apply_widget_scaling(self._corner_radius),
            0,  # no border
        )

        if no_color_updates is False or requires_recoloring:
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

            if self._fg_color == "transparent":
                inner_color = self._apply_appearance_mode(self._bg_color)
            else:
                inner_color = self._apply_appearance_mode(self._fg_color)

            self._canvas.itemconfig("inner_parts", outline=inner_color, fill=inner_color)

            # update inner frame and label backgrounds
            self._inner_frame.configure(bg=inner_color)
            self._recolor_labels()

    def _get_bg_for_labels(self) -> str:
        """Return the resolved background color string for label widgets."""
        if self._fg_color == "transparent":
            return self._apply_appearance_mode(self._bg_color)
        else:
            return self._apply_appearance_mode(self._fg_color)

    def _recolor_labels(self):
        """Apply current colors to all segment and separator labels."""
        bg = self._get_bg_for_labels()

        for i, label in enumerate(self._segment_labels):
            original_index = self._display_map[i][0]
            is_last_real = self._is_last_display(i)
            is_ellipsis = original_index is None

            if is_ellipsis:
                label.configure(fg=self._apply_appearance_mode(self._separator_color), bg=bg)
            elif is_last_real:
                label.configure(fg=self._apply_appearance_mode(self._text_color_current), bg=bg)
            else:
                label.configure(fg=self._apply_appearance_mode(self._text_color), bg=bg)

        for label in self._separator_labels:
            label.configure(
                fg=self._apply_appearance_mode(self._separator_color),
                bg=bg,
            )

    def _is_last_display(self, display_index: int) -> bool:
        """Check if the given display index is the final real segment."""
        return display_index == len(self._display_map) - 1

    # ------------------------------------------------------------------
    # Segment building
    # ------------------------------------------------------------------

    def _compute_display_items(self) -> List[Tuple[Optional[int], str]]:
        """
        Compute the list of (original_index_or_None, text) tuples to display.

        If max_items > 0 and len(items) > max_items, collapse the middle items
        into an ellipsis entry with original_index=None.

        Keeps the first item and the last (max_items - 2) items, with "..." in between.
        If max_items <= 2, keeps first and last only.
        """
        items = self._items
        if not items:
            return []

        if self._max_items <= 0 or len(items) <= self._max_items:
            return [(i, text) for i, text in enumerate(items)]

        # Collapse: show first item, ellipsis, then trailing items
        # Number of trailing items to keep (at least 1 = the last item)
        tail_count = max(self._max_items - 2, 1)
        if self._max_items <= 2:
            tail_count = 1

        result: List[Tuple[Optional[int], str]] = []
        # First item
        result.append((0, items[0]))
        # Ellipsis
        result.append((None, "\u2026"))  # unicode ellipsis character
        # Trailing items
        start = len(items) - tail_count
        for i in range(start, len(items)):
            result.append((i, items[i]))
        return result

    def _clear_segments(self):
        """Destroy all existing segment and separator labels."""
        for label in self._segment_labels:
            label.destroy()
        for label in self._separator_labels:
            label.destroy()
        self._segment_labels.clear()
        self._separator_labels.clear()
        self._display_map.clear()

    def _build_segments(self):
        """Build (or rebuild) all segment and separator labels."""
        self._clear_segments()
        self._display_map = self._compute_display_items()

        bg = self._get_bg_for_labels()
        self._inner_frame.configure(bg=bg)

        col = 0
        for display_idx, (original_index, text) in enumerate(self._display_map):
            is_last = self._is_last_display(display_idx)
            is_ellipsis = original_index is None

            # Determine font: bold for last segment
            if is_last and not is_ellipsis:
                seg_font = self._get_bold_font()
            else:
                seg_font = self._apply_font_scaling(self._font)

            # Determine text color
            if is_ellipsis:
                fg = self._apply_appearance_mode(self._separator_color)
            elif is_last:
                fg = self._apply_appearance_mode(self._text_color_current)
            else:
                fg = self._apply_appearance_mode(self._text_color)

            label = tkinter.Label(
                master=self._inner_frame,
                text=text,
                font=seg_font,
                fg=fg,
                bg=bg,
                padx=0,
                pady=0,
                borderwidth=0,
                highlightthickness=0,
            )

            # Make clickable segments interactive (not last, not ellipsis)
            if not is_last and not is_ellipsis:
                self._bind_clickable(label, original_index, text)

            label.grid(row=0, column=col, sticky="w", padx=(2 if col == 0 else 0, 0))
            self._segment_labels.append(label)
            col += 1

            # Add separator after this segment (except after the last)
            if not is_last:
                sep_label = tkinter.Label(
                    master=self._inner_frame,
                    text=self._separator,
                    font=self._apply_font_scaling(self._separator_font),
                    fg=self._apply_appearance_mode(self._separator_color),
                    bg=bg,
                    padx=0,
                    pady=0,
                    borderwidth=0,
                    highlightthickness=0,
                )
                sep_label.grid(row=0, column=col, sticky="w")
                self._separator_labels.append(sep_label)
                col += 1

    def _bind_clickable(self, label: tkinter.Label, original_index: int, text: str):
        """Bind hover and click events to a clickable segment label."""
        # Set hand cursor
        if sys.platform == "darwin":
            label.configure(cursor="pointinghand")
        else:
            label.configure(cursor="hand2")

        def on_enter(event, lbl=label):
            lbl.configure(fg=self._apply_appearance_mode(self._hover_color))
            # Apply underline: get current font and add underline
            current_font = lbl.cget("font")
            try:
                # tkinter font strings can be parsed; simplest approach is a Font object
                import tkinter.font as tkfont
                f = tkfont.Font(font=current_font)
                f.configure(underline=True)
                lbl.configure(font=f)
            except Exception:
                pass

        def on_leave(event, lbl=label):
            lbl.configure(fg=self._apply_appearance_mode(self._text_color))
            lbl.configure(font=self._apply_font_scaling(self._font))

        def on_click(event, idx=original_index, txt=text):
            if self._command is not None:
                self._command(idx, txt)

        label.bind("<Enter>", on_enter)
        label.bind("<Leave>", on_leave)
        label.bind("<ButtonRelease-1>", on_click)

    def _get_bold_font(self):
        """Return the current font with bold weight applied, respecting scaling."""
        scaled = self._apply_font_scaling(self._font)
        if isinstance(self._font, CTkFont):
            # Create a bold variant by copying parameters
            try:
                import tkinter.font as tkfont
                f = tkfont.Font(font=scaled)
                f.configure(weight="bold")
                return f
            except Exception:
                return scaled
        elif isinstance(scaled, tuple):
            # tuple font: (family, size, ?weight, ...)
            if len(scaled) >= 3:
                return (scaled[0], scaled[1], "bold") + scaled[3:]
            elif len(scaled) == 2:
                return (scaled[0], scaled[1], "bold")
            else:
                return scaled
        else:
            return scaled

    def _rebuild_all(self):
        """Fully rebuild segments and redraw."""
        self._build_segments()
        self._draw()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_items(self, items: List[str]):
        """Replace all breadcrumb items and rebuild the widget."""
        self._items = list(items)
        self._rebuild_all()

    def push(self, item: str):
        """Append a new item to the end of the breadcrumb path."""
        self._items.append(item)
        self._rebuild_all()

    def pop(self) -> str:
        """Remove and return the last breadcrumb item. Raises IndexError if empty."""
        if not self._items:
            raise IndexError("pop from empty breadcrumb")
        removed = self._items.pop()
        self._rebuild_all()
        return removed

    def get_items(self) -> List[str]:
        """Return a copy of the current breadcrumb items list."""
        return copy.copy(self._items)

    # ------------------------------------------------------------------
    # configure / cget
    # ------------------------------------------------------------------

    def configure(self, require_redraw=False, **kwargs):
        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "text_color_current" in kwargs:
            self._text_color_current = self._check_color_type(kwargs.pop("text_color_current"))
            require_redraw = True

        if "separator_color" in kwargs:
            self._separator_color = self._check_color_type(kwargs.pop("separator_color"))
            require_redraw = True

        if "hover_color" in kwargs:
            self._hover_color = self._check_color_type(kwargs.pop("hover_color"))
            # hover color is applied dynamically on enter, no full redraw needed

        if "items" in kwargs:
            self._items = list(kwargs.pop("items"))
            self._build_segments()
            require_redraw = True

        if "separator" in kwargs:
            self._separator = kwargs.pop("separator")
            self._build_segments()
            require_redraw = True

        if "command" in kwargs:
            self._command = kwargs.pop("command")
            # Rebuild to re-bind click handlers
            self._build_segments()
            require_redraw = True

        if "max_items" in kwargs:
            self._max_items = kwargs.pop("max_items")
            self._build_segments()
            require_redraw = True

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_fonts)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_fonts)
            self._build_segments()
            require_redraw = True

        if "separator_font" in kwargs:
            if (self._separator_font is not self._font
                    and isinstance(self._separator_font, CTkFont)):
                self._separator_font.remove_size_configure_callback(self._update_fonts)
            new_sep_font = kwargs.pop("separator_font")
            if new_sep_font is None:
                self._separator_font = self._font
            else:
                self._separator_font = self._check_font_type(new_sep_font)
                if isinstance(self._separator_font, CTkFont):
                    self._separator_font.add_size_configure_callback(self._update_fonts)
            self._build_segments()
            require_redraw = True

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "text_color_current":
            return self._text_color_current
        elif attribute_name == "separator_color":
            return self._separator_color
        elif attribute_name == "hover_color":
            return self._hover_color
        elif attribute_name == "items":
            return copy.copy(self._items)
        elif attribute_name == "separator":
            return self._separator
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "max_items":
            return self._max_items
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "separator_font":
            return self._separator_font
        else:
            return super().cget(attribute_name)

    def bind(self, sequence: str = None, command: Callable = None, add: str = True):
        """Bind an event to the canvas and all internal labels."""
        if not (add == "+" or add is True):
            raise ValueError(
                "'add' argument can only be '+' or True to preserve internal callbacks"
            )
        self._canvas.bind(sequence, command, add=True)
        for label in self._segment_labels:
            label.bind(sequence, command, add=True)
        for label in self._separator_labels:
            label.bind(sequence, command, add=True)

    def unbind(self, sequence: str = None, funcid: Optional[str] = None):
        """Unbind an event from the canvas and all internal labels."""
        if funcid is not None:
            raise ValueError(
                "'funcid' argument can only be None, because there is a bug in"
                " tkinter and its not clear whether the internal callbacks will be unbinded or not"
            )
        self._canvas.unbind(sequence, None)
        for label in self._segment_labels:
            label.unbind(sequence, None)
        for label in self._separator_labels:
            label.unbind(sequence, None)
