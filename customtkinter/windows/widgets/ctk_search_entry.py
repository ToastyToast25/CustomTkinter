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

    Usage:
        search = CTkSearchEntry(parent, placeholder_text="Search DLCs...",
                                command=on_search, debounce_ms=300)
    """

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

                 placeholder_text: str = "Search...",
                 font: Optional[Union[tuple, CTkFont]] = None,
                 command: Optional[Callable[[str], Any]] = None,
                 debounce_ms: int = 300,
                 show_icon: bool = True,
                 show_clear: bool = True,
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
            self._clear_label.grid(row=0, column=col, padx=(0, 8), sticky="ns")
            self._clear_label.bind("<Button-1>", self._on_clear)
            self._clear_label.bind("<Enter>", self._on_clear_enter)
            self._clear_label.bind("<Leave>", self._on_clear_leave)
            # hide initially
            self._clear_label.grid_remove()
            col += 1
        else:
            self._clear_label = None

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

    def _on_text_change(self, *args):
        """Called when entry text changes — show/hide clear button and debounce command."""
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

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    def destroy(self):
        if self._debounce_after_id is not None:
            self.after_cancel(self._debounce_after_id)
            self._debounce_after_id = None
        super().destroy()

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
        else:
            return super().cget(attribute_name)
