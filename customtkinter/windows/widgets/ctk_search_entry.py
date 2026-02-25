import tkinter
from typing import Union, Tuple, Optional, Callable, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .ctk_entry import CTkEntry
from .font import CTkFont


class CTkSearchEntry(CTkBaseClass):
    """
    Search entry with built-in search icon, clear button, and
    debounced search callback. Fires the command after a configurable
    delay to avoid excessive callbacks while typing.

    Features:
        - Debounced search command
        - Escape to clear / unfocus
        - Enter to submit immediately (bypasses debounce)
        - Focus glow animation on the border
        - Result count badge (e.g. "3 results")
        - Loading state indicator

    Usage:
        search = CTkSearchEntry(parent, placeholder_text="Search DLCs...",
                                command=on_search, debounce_ms=300)
        search.set_result_count(42)
        search.set_loading(True)
    """

    # Default focus glow color (light, dark)
    _DEFAULT_FOCUS_COLOR = ("#3B8ED0", "#3B8ED0")

    def __init__(self,
                 master: Any,
                 width: int = 250,
                 height: int = 32,
                 corner_radius: Optional[int] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 placeholder_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 icon_color: Optional[Union[str, Tuple[str, str]]] = None,
                 clear_button_color: Optional[Union[str, Tuple[str, str]]] = None,
                 clear_button_hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 focus_border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 count_text_color: Optional[Union[str, Tuple[str, str]]] = None,

                 placeholder_text: str = "Search...",
                 font: Optional[Union[tuple, CTkFont]] = None,
                 command: Optional[Callable[[str], Any]] = None,
                 debounce_ms: int = 300,
                 show_icon: bool = True,
                 show_clear: bool = True,
                 focus_glow_duration: int = 150,
                 **kwargs):

        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        self._command = command
        self._debounce_ms = max(0, debounce_ms)
        self._show_icon = show_icon
        self._show_clear = show_clear
        self._debounce_after_id = None

        # colors
        self._fg_color = fg_color or ThemeManager.theme["CTkEntry"]["fg_color"]
        self._border_color = border_color or ThemeManager.theme["CTkEntry"]["border_color"]
        self._text_color = text_color or ThemeManager.theme["CTkEntry"]["text_color"]
        self._icon_color = icon_color or ("#888888", "#888888")
        self._clear_color = clear_button_color or ("#999999", "#777777")
        self._clear_hover_color = clear_button_hover_color or ("#666666", "#aaaaaa")
        self._focus_border_color = focus_border_color or self._DEFAULT_FOCUS_COLOR
        self._count_text_color = count_text_color or ("#888888", "#888888")

        # focus glow animation state
        self._focus_glow_duration = max(50, focus_glow_duration)
        self._focus_phase = 0.0  # 0.0 = normal, 1.0 = full focus glow
        self._focus_direction = 0  # 1 = focusing in, -1 = focusing out
        self._focus_after_id = None

        # result count / loading state
        self._result_count: Optional[int] = None
        self._loading = False

        # shape
        corner = ThemeManager.theme["CTkEntry"]["corner_radius"] if corner_radius is None else corner_radius

        # layout
        self.grid_rowconfigure(0, weight=1)

        col = 0

        # search icon
        if self._show_icon:
            fg = self._apply_appearance_mode(self._fg_color)
            if isinstance(fg, (list, tuple)):
                fg = fg[0]
            self._icon_label = tkinter.Label(
                self,
                text="\U0001F50D",
                font=("Segoe UI", 11),
                fg=self._apply_appearance_mode(self._icon_color),
                bg=fg,
                cursor="xterm",
            )
            self._icon_label.grid(row=0, column=col, padx=(8, 0), sticky="ns")
            self._icon_label.bind("<Button-1>", lambda e: self._entry.focus_set())
            col += 1
        else:
            self._icon_label = None

        # entry widget
        self.grid_columnconfigure(col, weight=1)
        self._entry_col = col
        self._entry = CTkEntry(
            self,
            width=0,
            height=height - 4,
            corner_radius=0,
            border_width=0,
            fg_color="transparent",
            text_color=text_color,
            placeholder_text_color=placeholder_text_color,
            placeholder_text=placeholder_text,
            font=font,
        )
        self._entry.grid(row=0, column=col, sticky="ew", padx=(4 if self._show_icon else 8, 0))
        col += 1

        # clear button
        if self._show_clear:
            fg = self._apply_appearance_mode(self._fg_color)
            if isinstance(fg, (list, tuple)):
                fg = fg[0]
            self._clear_label = tkinter.Label(
                self,
                text="\u2715",
                font=("Segoe UI", 10),
                fg=self._apply_appearance_mode(self._clear_color),
                bg=fg,
                cursor="hand2",
            )
            self._clear_label.grid(row=0, column=col, padx=(0, 2), sticky="ns")
            self._clear_label.bind("<Button-1>", self._on_clear)
            self._clear_label.bind("<Enter>", self._on_clear_enter)
            self._clear_label.bind("<Leave>", self._on_clear_leave)
            # hide initially
            self._clear_label.grid_remove()
            self._clear_col = col
            col += 1
        else:
            self._clear_label = None
            self._clear_col = None

        # result count / loading label
        fg = self._apply_appearance_mode(self._fg_color)
        if isinstance(fg, (list, tuple)):
            fg = fg[0]
        self._count_label = tkinter.Label(
            self,
            text="",
            font=("Segoe UI", 9),
            fg=self._apply_appearance_mode(self._count_text_color),
            bg=fg,
            anchor="e",
        )
        self._count_label.grid(row=0, column=col, padx=(0, 8), sticky="ns")
        self._count_label.grid_remove()  # hidden by default
        self._count_col = col
        col += 1

        # outer frame styling (rounded border)
        self._corner_radius = corner
        self._border_width = 2

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, columnspan=col, sticky="nswe")
        # lower canvas behind other widgets using tkinter's lower
        tkinter.Widget.lower(self._canvas)
        self._draw_engine = DrawEngine(self._canvas)

        self._draw()

        # track text changes
        self._text_var = tkinter.StringVar()
        self._entry.configure(textvariable=self._text_var)
        self._text_var.trace_add("write", self._on_text_change)

        # key bindings on the inner entry widget
        self._entry.bind("<Escape>", self._on_escape)
        self._entry.bind("<Return>", self._on_return)

        # focus glow bindings on the inner entry widget
        self._entry.bind("<FocusIn>", self._on_focus_in, add="+")
        self._entry.bind("<FocusOut>", self._on_focus_out, add="+")

    # ------------------------------------------------------------------
    #  Drawing
    # ------------------------------------------------------------------

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(
            self._apply_widget_scaling(self._current_width),
            self._apply_widget_scaling(self._current_height),
            self._apply_widget_scaling(self._corner_radius),
            self._apply_widget_scaling(self._border_width))

        if no_color_updates is False or requires_recoloring:
            fg = self._apply_appearance_mode(self._fg_color)
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._canvas.itemconfig("inner_parts", fill=fg, outline=fg)
            self._canvas.itemconfig("border_parts",
                                    fill=self._apply_appearance_mode(self._border_color),
                                    outline=self._apply_appearance_mode(self._border_color))

    # ------------------------------------------------------------------
    #  Text change + debounce
    # ------------------------------------------------------------------

    def _on_text_change(self, *args):
        """Called when entry text changes -- show/hide clear button and debounce command."""
        text = self._text_var.get()

        # show/hide clear button
        if self._clear_label is not None:
            if text:
                self._clear_label.grid()
            else:
                self._clear_label.grid_remove()

        # debounce command
        if self._debounce_after_id is not None:
            self.after_cancel(self._debounce_after_id)
            self._debounce_after_id = None

        if self._command is not None:
            if self._debounce_ms > 0:
                self._debounce_after_id = self.after(self._debounce_ms,
                                                      lambda: self._command(text))
            else:
                self._command(text)

    # ------------------------------------------------------------------
    #  Clear button
    # ------------------------------------------------------------------

    def _on_clear(self, event=None):
        """Clear the search text."""
        self._entry.delete(0, "end")
        self._entry.focus_set()

    def _on_clear_enter(self, event=None):
        if self._clear_label:
            self._clear_label.configure(
                fg=self._apply_appearance_mode(self._clear_hover_color))

    def _on_clear_leave(self, event=None):
        if self._clear_label:
            self._clear_label.configure(
                fg=self._apply_appearance_mode(self._clear_color))

    # ------------------------------------------------------------------
    #  Escape to clear / unfocus
    # ------------------------------------------------------------------

    def _on_escape(self, event=None):
        """Escape clears the text. If already empty, removes focus."""
        text = self._text_var.get()
        if text:
            self._entry.delete(0, "end")
        else:
            # Remove focus by shifting it to the master widget
            self.master.focus_set()

    # ------------------------------------------------------------------
    #  Enter to submit immediately
    # ------------------------------------------------------------------

    def _on_return(self, event=None):
        """Enter fires the command immediately, bypassing debounce."""
        # Cancel any pending debounce
        if self._debounce_after_id is not None:
            self.after_cancel(self._debounce_after_id)
            self._debounce_after_id = None

        if self._command is not None:
            self._command(self._text_var.get())

    # ------------------------------------------------------------------
    #  Focus glow animation
    # ------------------------------------------------------------------

    def _on_focus_in(self, event=None):
        """Start animating border toward focus color."""
        self._focus_direction = 1
        self._animate_focus()

    def _on_focus_out(self, event=None):
        """Start animating border back to normal color."""
        self._focus_direction = -1
        self._animate_focus()

    def _animate_focus(self):
        """Animate border color between normal and focus colors."""
        if self._focus_after_id is not None:
            self.after_cancel(self._focus_after_id)
            self._focus_after_id = None

        interval = 16  # ~60fps
        step = interval / self._focus_glow_duration

        self._focus_phase += step * self._focus_direction
        self._focus_phase = max(0.0, min(1.0, self._focus_phase))

        self._apply_focus_border()

        # continue animation if not at target
        if (self._focus_direction > 0 and self._focus_phase < 1.0) or \
           (self._focus_direction < 0 and self._focus_phase > 0.0):
            self._focus_after_id = self.after(interval, self._animate_focus)

    def _apply_focus_border(self):
        """Apply a single frame of the focus glow animation at the current phase."""
        base = self._color_to_hex(
            self._apply_appearance_mode(self._border_color))
        target = self._color_to_hex(
            self._apply_appearance_mode(self._focus_border_color))
        current = self._lerp_hex(base, target, self._ease_out_cubic(self._focus_phase))

        try:
            self._canvas.itemconfig("border_parts", fill=current, outline=current)
        except Exception:
            return

    # ------------------------------------------------------------------
    #  Color utility methods
    # ------------------------------------------------------------------

    def _color_to_hex(self, color: str) -> str:
        """Convert any tkinter color (named or hex) to #RRGGBB."""
        if color.startswith("#") and len(color) == 7:
            return color
        try:
            r, g, b = self._canvas.winfo_rgb(color)
            return f"#{r >> 8:02x}{g >> 8:02x}{b >> 8:02x}"
        except Exception:
            return "#333333"

    @staticmethod
    def _lerp_hex(c1: str, c2: str, t: float) -> str:
        """Linearly interpolate between two hex colors."""
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        return (
            f"#{int(r1 + (r2 - r1) * t):02x}"
            f"{int(g1 + (g2 - g1) * t):02x}"
            f"{int(b1 + (b2 - b1) * t):02x}"
        )

    @staticmethod
    def _ease_out_cubic(t: float) -> float:
        """Cubic ease-out for smooth deceleration."""
        return 1 - (1 - t) ** 3

    # ------------------------------------------------------------------
    #  Result count badge
    # ------------------------------------------------------------------

    def set_result_count(self, count: Optional[int] = None):
        """Show a result count badge (e.g. '3 results'). Pass None to hide."""
        self._result_count = count

        # If loading, don't overwrite the loading indicator
        if self._loading:
            return

        self._update_count_label()

    def _update_count_label(self):
        """Refresh the count label text and visibility based on current state."""
        if self._loading:
            self._count_label.configure(text="...")
            self._count_label.grid()
        elif self._result_count is not None:
            if self._result_count == 1:
                text = "1 result"
            else:
                text = f"{self._result_count} results"
            self._count_label.configure(text=text)
            self._count_label.grid()
        else:
            self._count_label.grid_remove()

    # ------------------------------------------------------------------
    #  Loading state
    # ------------------------------------------------------------------

    def set_loading(self, loading: bool):
        """Show a loading indicator in the count label area.

        When loading=True, displays '...' in place of the result count.
        When loading=False, reverts to the current result count (or hides).
        """
        self._loading = loading
        self._update_count_label()

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def get(self) -> str:
        """Get the current search text."""
        return self._text_var.get()

    def set(self, value: str):
        """Set the search text."""
        self._entry.delete(0, "end")
        self._entry.insert(0, value)

    def clear(self):
        """Clear the search text."""
        self._entry.delete(0, "end")

    def focus_set(self):
        """Focus the search entry."""
        self._entry.focus_set()

    # ------------------------------------------------------------------
    #  Scaling
    # ------------------------------------------------------------------

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    # ------------------------------------------------------------------
    #  Lifecycle
    # ------------------------------------------------------------------

    def destroy(self):
        if self._debounce_after_id is not None:
            self.after_cancel(self._debounce_after_id)
            self._debounce_after_id = None
        if self._focus_after_id is not None:
            self.after_cancel(self._focus_after_id)
            self._focus_after_id = None
        super().destroy()

    # ------------------------------------------------------------------
    #  configure / cget
    # ------------------------------------------------------------------

    def configure(self, **kwargs):
        require_redraw = False
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "debounce_ms" in kwargs:
            self._debounce_ms = max(0, kwargs.pop("debounce_ms"))
        if "placeholder_text" in kwargs:
            self._entry.configure(placeholder_text=kwargs.pop("placeholder_text"))
        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            self._entry.configure(text_color=self._text_color)
        if "fg_color" in kwargs:
            self._fg_color = kwargs.pop("fg_color")
            require_redraw = True
        if "border_color" in kwargs:
            self._border_color = kwargs.pop("border_color")
            require_redraw = True
        if "focus_border_color" in kwargs:
            self._focus_border_color = kwargs.pop("focus_border_color")
        if "focus_glow_duration" in kwargs:
            self._focus_glow_duration = max(50, kwargs.pop("focus_glow_duration"))
        if "count_text_color" in kwargs:
            self._count_text_color = kwargs.pop("count_text_color")
            self._count_label.configure(
                fg=self._apply_appearance_mode(self._count_text_color))
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "debounce_ms":
            return self._debounce_ms
        elif attribute_name == "placeholder_text":
            return self._entry.cget("placeholder_text")
        elif attribute_name == "show_icon":
            return self._show_icon
        elif attribute_name == "show_clear":
            return self._show_clear
        elif attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "border_width":
            return self._border_width
        elif attribute_name == "focus_border_color":
            return self._focus_border_color
        elif attribute_name == "focus_glow_duration":
            return self._focus_glow_duration
        elif attribute_name == "count_text_color":
            return self._count_text_color
        elif attribute_name == "result_count":
            return self._result_count
        elif attribute_name == "loading":
            return self._loading
        else:
            return super().cget(attribute_name)
