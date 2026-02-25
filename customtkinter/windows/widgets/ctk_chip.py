import tkinter
import sys
from typing import Union, Tuple, Callable, Optional, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkChip(CTkBaseClass):
    """
    Compact chip/tag widget with rounded pill shape, optional close button,
    selectable state, optional leading icon, multiple color styles, and hover effect.

    Useful for displaying selected items, filters, categories, or tags.

    Usage:
        chip = CTkChip(parent, text="Python", icon="\U0001f40d", style="primary")
        chip = CTkChip(parent, text="Remove me", closeable=True,
                       close_command=lambda: chip.destroy())
        chip.select()
        chip.toggle()
        if chip.is_selected():
            print("selected")

    Styles: "default", "primary", "success", "warning", "error"
    """

    # ── Style color definitions ─────────────────────────────────────
    # Each entry: (light_mode, dark_mode) tuples for fg, fg_selected,
    # text, text_selected, hover, hover_selected, close, close_hover.

    _STYLE_COLORS = {
        "default": {
            "fg":             ("#e5e7eb", "#374151"),
            "fg_selected":    ("#6b7280", "#4b5563"),
            "text":           ("#374151", "#d1d5db"),
            "text_selected":  ("#ffffff", "#ffffff"),
            "hover":          ("#d1d5db", "#4b5563"),
            "hover_selected": ("#4b5563", "#6b7280"),
            "close":          ("#6b7280", "#9ca3af"),
            "close_hover":    ("#374151", "#e5e7eb"),
        },
        "primary": {
            "fg":             ("#dbeafe", "#1e3a5f"),
            "fg_selected":    ("#3b82f6", "#2563eb"),
            "text":           ("#1e40af", "#93c5fd"),
            "text_selected":  ("#ffffff", "#ffffff"),
            "hover":          ("#bfdbfe", "#264a73"),
            "hover_selected": ("#2563eb", "#1d4ed8"),
            "close":          ("#3b82f6", "#60a5fa"),
            "close_hover":    ("#1e40af", "#ffffff"),
        },
        "success": {
            "fg":             ("#dcfce7", "#14532d"),
            "fg_selected":    ("#22c55e", "#16a34a"),
            "text":           ("#166534", "#86efac"),
            "text_selected":  ("#ffffff", "#ffffff"),
            "hover":          ("#bbf7d0", "#1a6b3a"),
            "hover_selected": ("#16a34a", "#15803d"),
            "close":          ("#22c55e", "#4ade80"),
            "close_hover":    ("#166534", "#ffffff"),
        },
        "warning": {
            "fg":             ("#fef3c7", "#451a03"),
            "fg_selected":    ("#f59e0b", "#d97706"),
            "text":           ("#92400e", "#fcd34d"),
            "text_selected":  ("#ffffff", "#ffffff"),
            "hover":          ("#fde68a", "#5c2a06"),
            "hover_selected": ("#d97706", "#b45309"),
            "close":          ("#f59e0b", "#fbbf24"),
            "close_hover":    ("#92400e", "#ffffff"),
        },
        "error": {
            "fg":             ("#fecaca", "#450a0a"),
            "fg_selected":    ("#ef4444", "#dc2626"),
            "text":           ("#991b1b", "#fca5a5"),
            "text_selected":  ("#ffffff", "#ffffff"),
            "hover":          ("#fca5a5", "#5c1111"),
            "hover_selected": ("#dc2626", "#b91c1c"),
            "close":          ("#ef4444", "#f87171"),
            "close_hover":    ("#991b1b", "#ffffff"),
        },
    }

    def __init__(self,
                 master: Any,
                 width: int = 0,
                 height: int = 28,
                 corner_radius: Optional[int] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 fg_color_selected: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color_selected: Optional[Union[str, Tuple[str, str]]] = None,
                 hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 hover_color_selected: Optional[Union[str, Tuple[str, str]]] = None,
                 close_color: Optional[Union[str, Tuple[str, str]]] = None,
                 close_hover_color: Optional[Union[str, Tuple[str, str]]] = None,

                 text: str = "Chip",
                 icon: Optional[str] = None,
                 font: Optional[Union[tuple, CTkFont]] = None,
                 style: str = "default",
                 closeable: bool = False,
                 selected: bool = False,
                 state: str = "normal",
                 hover: bool = True,

                 command: Union[Callable[[], Any], None] = None,
                 close_command: Union[Callable[[], Any], None] = None,
                 **kwargs):

        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # ── Core state ──────────────────────────────────────────────
        self._text = text
        self._icon = icon
        self._style = style if style in self._STYLE_COLORS else "default"
        self._closeable = closeable
        self._selected = selected
        self._state = state
        self._hover_enabled = hover
        self._command = command
        self._close_command = close_command
        self._mouse_inside = False
        self._mouse_inside_close = False

        # ── Shape ───────────────────────────────────────────────────
        self._corner_radius = 14 if corner_radius is None else corner_radius

        # ── Colors (user overrides take priority over style) ────────
        style_cfg = self._STYLE_COLORS[self._style]
        self._fg_color = fg_color or style_cfg["fg"]
        self._fg_color_selected = fg_color_selected or style_cfg["fg_selected"]
        self._text_color = text_color or style_cfg["text"]
        self._text_color_selected = text_color_selected or style_cfg["text_selected"]
        self._hover_color = hover_color or style_cfg["hover"]
        self._hover_color_selected = hover_color_selected or style_cfg["hover_selected"]
        self._close_color = close_color or style_cfg["close"]
        self._close_hover_color = close_hover_color or style_cfg["close_hover"]

        # ── Font ────────────────────────────────────────────────────
        self._font = CTkFont(size=12) if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)

        # ── Grid setup ──────────────────────────────────────────────
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Canvas (rounded background) ─────────────────────────────
        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, sticky="nswe")
        self._draw_engine = DrawEngine(self._canvas)

        # ── Inner layout frame ──────────────────────────────────────
        self._inner = tkinter.Frame(self, bg=self._apply_appearance_mode(self._resolve_fg()))
        self._inner.grid(row=0, column=0, sticky="nswe")

        # ── Icon label (optional) ───────────────────────────────────
        self._icon_label: Optional[tkinter.Label] = None
        if self._icon is not None and self._icon != "":
            self._icon_label = tkinter.Label(
                self._inner,
                text=self._icon,
                font=self._resolve_tk_font(size_offset=-1),
                fg=self._apply_appearance_mode(self._resolve_text_color()),
                bg=self._apply_appearance_mode(self._resolve_fg()),
            )

        # ── Text label ──────────────────────────────────────────────
        self._text_label = tkinter.Label(
            self._inner,
            text=self._text,
            font=self._resolve_tk_font(),
            fg=self._apply_appearance_mode(self._resolve_text_color()),
            bg=self._apply_appearance_mode(self._resolve_fg()),
        )

        # ── Close button (optional) ─────────────────────────────────
        self._close_label: Optional[tkinter.Label] = None
        if self._closeable:
            self._close_label = tkinter.Label(
                self._inner,
                text="\u00d7",  # multiplication sign ×
                font=("Segoe UI", 11, "bold"),
                fg=self._apply_appearance_mode(self._close_color),
                bg=self._apply_appearance_mode(self._resolve_fg()),
                cursor="hand2" if sys.platform.startswith("win") else "pointinghand",
            )

        # ── Layout & draw ───────────────────────────────────────────
        self._layout_content()
        self._create_bindings()
        self._set_cursor()
        self._draw()

    # ── Font helpers ────────────────────────────────────────────────

    def _resolve_tk_font(self, size_offset: int = 0) -> tuple:
        """Return a tk-compatible font tuple from the current _font."""
        if isinstance(self._font, CTkFont):
            family = self._font.cget("family")
            size = self._font.cget("size") + size_offset
            weight = self._font.cget("weight")
            return (family, size, weight)
        elif isinstance(self._font, tuple):
            if len(self._font) >= 2 and size_offset != 0:
                return (self._font[0], self._font[1] + size_offset) + self._font[2:]
            return self._font
        return ("Segoe UI", 12 + size_offset)

    def _update_font(self):
        """Called when CTkFont configuration changes."""
        tk_font = self._resolve_tk_font()
        self._text_label.configure(font=tk_font)
        if self._icon_label is not None:
            self._icon_label.configure(font=self._resolve_tk_font(size_offset=-1))
        self._canvas.grid_forget()
        self._canvas.grid(row=0, column=0, sticky="nswe")

    # ── Color resolution ────────────────────────────────────────────

    def _resolve_fg(self) -> Union[str, Tuple[str, str]]:
        """Return the fg_color based on the current selected state."""
        return self._fg_color_selected if self._selected else self._fg_color

    def _resolve_text_color(self) -> Union[str, Tuple[str, str]]:
        """Return the text color based on the current selected state."""
        return self._text_color_selected if self._selected else self._text_color

    def _resolve_hover(self) -> Union[str, Tuple[str, str]]:
        """Return the hover color based on the current selected state."""
        return self._hover_color_selected if self._selected else self._hover_color

    # ── Layout ──────────────────────────────────────────────────────

    def _layout_content(self):
        """Pack icon, text, and close labels with correct padding."""
        if self._icon_label is not None:
            self._icon_label.pack_forget()
        self._text_label.pack_forget()
        if self._close_label is not None:
            self._close_label.pack_forget()

        # Determine left padding: smaller if icon provides visual weight
        has_icon = self._icon_label is not None
        has_close = self._close_label is not None

        if has_icon:
            self._icon_label.pack(side="left", padx=(8, 0), pady=2)
            self._text_label.pack(side="left", padx=(3, 10 if not has_close else 2), pady=2)
        else:
            self._text_label.pack(side="left", padx=(10, 10 if not has_close else 2), pady=2)

        if has_close:
            self._close_label.pack(side="left", padx=(0, 6), pady=2)

    # ── Bindings ────────────────────────────────────────────────────

    def _create_bindings(self):
        """Set up mouse event bindings on all interactive parts."""
        # Main chip click and hover — bind to canvas, inner frame, text, icon
        for widget in self._get_body_widgets():
            widget.bind("<Enter>", self._on_enter, add="+")
            widget.bind("<Leave>", self._on_leave, add="+")
            widget.bind("<ButtonRelease-1>", self._on_click, add="+")

        # Close button gets its own hover/click bindings
        if self._close_label is not None:
            self._close_label.bind("<Enter>", self._on_close_enter, add="+")
            self._close_label.bind("<Leave>", self._on_close_leave, add="+")
            self._close_label.bind("<ButtonRelease-1>", self._on_close_click, add="+")

    def _get_body_widgets(self) -> list:
        """Return the list of widgets that form the clickable chip body."""
        widgets = [self._canvas, self._inner, self._text_label]
        if self._icon_label is not None:
            widgets.append(self._icon_label)
        return widgets

    def _set_cursor(self):
        """Set the mouse cursor based on state and commands."""
        if self._cursor_manipulation_enabled:
            if self._state == tkinter.DISABLED:
                cursor = "arrow"
            elif self._command is not None:
                cursor = "hand2" if sys.platform.startswith("win") else "pointinghand"
            else:
                cursor = "arrow"
            for widget in self._get_body_widgets():
                try:
                    widget.configure(cursor=cursor)
                except tkinter.TclError:
                    pass

    # ── Hover events ────────────────────────────────────────────────

    def _on_enter(self, event=None):
        """Mouse enters the chip body."""
        self._mouse_inside = True
        if self._hover_enabled and self._state != tkinter.DISABLED:
            hover_fg = self._apply_appearance_mode(self._resolve_hover())
            self._canvas.itemconfig("inner_parts", fill=hover_fg, outline=hover_fg)
            self._inner.configure(bg=hover_fg)
            self._text_label.configure(bg=hover_fg)
            if self._icon_label is not None:
                self._icon_label.configure(bg=hover_fg)
            if self._close_label is not None:
                self._close_label.configure(bg=hover_fg)

    def _on_leave(self, event=None):
        """Mouse leaves the chip body."""
        self._mouse_inside = False
        if self._state != tkinter.DISABLED:
            self._apply_current_colors()

    def _on_close_enter(self, event=None):
        """Mouse enters the close button."""
        self._mouse_inside_close = True
        if self._state != tkinter.DISABLED and self._close_label is not None:
            self._close_label.configure(
                fg=self._apply_appearance_mode(self._close_hover_color))

    def _on_close_leave(self, event=None):
        """Mouse leaves the close button."""
        self._mouse_inside_close = False
        if self._state != tkinter.DISABLED and self._close_label is not None:
            self._close_label.configure(
                fg=self._apply_appearance_mode(self._close_color))

    # ── Click events ────────────────────────────────────────────────

    def _on_click(self, event=None):
        """Handle click on the chip body."""
        if self._mouse_inside and self._state != tkinter.DISABLED:
            if self._command is not None:
                self._command()

    def _on_close_click(self, event=None):
        """Handle click on the close button."""
        if self._mouse_inside_close and self._state != tkinter.DISABLED:
            if self._close_command is not None:
                self._close_command()

    # ── Drawing ─────────────────────────────────────────────────────

    def _apply_current_colors(self):
        """Apply the current state colors to all widget parts (no canvas redraw)."""
        fg = self._apply_appearance_mode(self._resolve_fg())
        text_fg = self._apply_appearance_mode(self._resolve_text_color())

        self._canvas.itemconfig("inner_parts", fill=fg, outline=fg)
        self._inner.configure(bg=fg)
        self._text_label.configure(bg=fg, fg=text_fg)
        if self._icon_label is not None:
            self._icon_label.configure(bg=fg, fg=text_fg)
        if self._close_label is not None:
            close_fg = self._apply_appearance_mode(self._close_color)
            self._close_label.configure(bg=fg, fg=close_fg)

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(
            self._apply_widget_scaling(self._current_width),
            self._apply_widget_scaling(self._current_height),
            self._apply_widget_scaling(self._corner_radius),
            0)

        if no_color_updates is False or requires_recoloring:
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._apply_current_colors()

    # ── Scaling ─────────────────────────────────────────────────────

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
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

    # ── Public API: Selection ───────────────────────────────────────

    def select(self):
        """Set the chip to the selected state."""
        if not self._selected:
            self._selected = True
            self._draw()

    def deselect(self):
        """Set the chip to the unselected state."""
        if self._selected:
            self._selected = False
            self._draw()

    def toggle(self):
        """Toggle between selected and unselected states."""
        self._selected = not self._selected
        self._draw()

    def is_selected(self) -> bool:
        """Return True if the chip is currently in the selected state."""
        return self._selected

    # ── Public API: Invoke ──────────────────────────────────────────

    def invoke(self):
        """Programmatically trigger the chip click command."""
        if self._state != tkinter.DISABLED and self._command is not None:
            return self._command()

    def invoke_close(self):
        """Programmatically trigger the close command."""
        if self._state != tkinter.DISABLED and self._close_command is not None:
            return self._close_command()

    # ── Configure / cget ────────────────────────────────────────────

    def configure(self, require_redraw=False, **kwargs):
        if "text" in kwargs:
            self._text = kwargs.pop("text")
            self._text_label.configure(text=self._text)

        if "icon" in kwargs:
            new_icon = kwargs.pop("icon")
            if new_icon != self._icon:
                self._icon = new_icon
                if self._icon is not None and self._icon != "":
                    if self._icon_label is None:
                        self._icon_label = tkinter.Label(
                            self._inner,
                            text=self._icon,
                            font=self._resolve_tk_font(size_offset=-1),
                            fg=self._apply_appearance_mode(self._resolve_text_color()),
                            bg=self._apply_appearance_mode(self._resolve_fg()),
                        )
                        self._create_bindings()
                    else:
                        self._icon_label.configure(text=self._icon)
                else:
                    if self._icon_label is not None:
                        self._icon_label.destroy()
                        self._icon_label = None
                self._layout_content()
                require_redraw = True

        if "style" in kwargs:
            new_style = kwargs.pop("style")
            if new_style in self._STYLE_COLORS and new_style != self._style:
                self._style = new_style
                style_cfg = self._STYLE_COLORS[self._style]
                self._fg_color = style_cfg["fg"]
                self._fg_color_selected = style_cfg["fg_selected"]
                self._text_color = style_cfg["text"]
                self._text_color_selected = style_cfg["text_selected"]
                self._hover_color = style_cfg["hover"]
                self._hover_color_selected = style_cfg["hover_selected"]
                self._close_color = style_cfg["close"]
                self._close_hover_color = style_cfg["close_hover"]
                require_redraw = True

        if "closeable" in kwargs:
            new_closeable = kwargs.pop("closeable")
            if new_closeable != self._closeable:
                self._closeable = new_closeable
                if self._closeable:
                    if self._close_label is None:
                        self._close_label = tkinter.Label(
                            self._inner,
                            text="\u00d7",
                            font=("Segoe UI", 11, "bold"),
                            fg=self._apply_appearance_mode(self._close_color),
                            bg=self._apply_appearance_mode(self._resolve_fg()),
                            cursor="hand2" if sys.platform.startswith("win") else "pointinghand",
                        )
                        self._close_label.bind("<Enter>", self._on_close_enter, add="+")
                        self._close_label.bind("<Leave>", self._on_close_leave, add="+")
                        self._close_label.bind("<ButtonRelease-1>", self._on_close_click, add="+")
                else:
                    if self._close_label is not None:
                        self._close_label.destroy()
                        self._close_label = None
                self._layout_content()
                require_redraw = True

        if "selected" in kwargs:
            new_selected = kwargs.pop("selected")
            if new_selected != self._selected:
                self._selected = new_selected
                require_redraw = True

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._set_cursor()
            require_redraw = True

        if "hover" in kwargs:
            self._hover_enabled = kwargs.pop("hover")

        if "command" in kwargs:
            self._command = kwargs.pop("command")
            self._set_cursor()

        if "close_command" in kwargs:
            self._close_command = kwargs.pop("close_command")

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "fg_color" in kwargs:
            self._fg_color = kwargs.pop("fg_color")
            require_redraw = True

        if "fg_color_selected" in kwargs:
            self._fg_color_selected = kwargs.pop("fg_color_selected")
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            require_redraw = True

        if "text_color_selected" in kwargs:
            self._text_color_selected = kwargs.pop("text_color_selected")
            require_redraw = True

        if "hover_color" in kwargs:
            self._hover_color = kwargs.pop("hover_color")

        if "hover_color_selected" in kwargs:
            self._hover_color_selected = kwargs.pop("hover_color_selected")

        if "close_color" in kwargs:
            self._close_color = kwargs.pop("close_color")
            require_redraw = True

        if "close_hover_color" in kwargs:
            self._close_hover_color = kwargs.pop("close_hover_color")

        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            require_redraw = True

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "text":
            return self._text
        elif attribute_name == "icon":
            return self._icon
        elif attribute_name == "style":
            return self._style
        elif attribute_name == "closeable":
            return self._closeable
        elif attribute_name == "selected":
            return self._selected
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "hover":
            return self._hover_enabled
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "close_command":
            return self._close_command
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "fg_color_selected":
            return self._fg_color_selected
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "text_color_selected":
            return self._text_color_selected
        elif attribute_name == "hover_color":
            return self._hover_color
        elif attribute_name == "hover_color_selected":
            return self._hover_color_selected
        elif attribute_name == "close_color":
            return self._close_color
        elif attribute_name == "close_hover_color":
            return self._close_hover_color
        elif attribute_name == "corner_radius":
            return self._corner_radius
        else:
            return super().cget(attribute_name)

    # ── Bind / unbind ───────────────────────────────────────────────

    def bind(self, sequence: str = None, command: Callable = None, add: Union[str, bool] = True):
        """Bind an event to the chip. The 'add' argument must be '+' or True."""
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, command, add=True)
        self._text_label.bind(sequence, command, add=True)
        if self._icon_label is not None:
            self._icon_label.bind(sequence, command, add=True)
        if self._close_label is not None:
            self._close_label.bind(sequence, command, add=True)

    def unbind(self, sequence: str = None, funcid: str = None):
        """Unbind an event from the chip."""
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in"
                             " tkinter and its not clear whether the internal callbacks"
                             " will be unbinded or not")
        self._canvas.unbind(sequence, None)
        self._text_label.unbind(sequence, None)
        if self._icon_label is not None:
            self._icon_label.unbind(sequence, None)
        if self._close_label is not None:
            self._close_label.unbind(sequence, None)
        self._create_bindings()

    # ── Cleanup ─────────────────────────────────────────────────────

    def destroy(self):
        """Clean up font callbacks before destroying the widget."""
        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)
        super().destroy()
