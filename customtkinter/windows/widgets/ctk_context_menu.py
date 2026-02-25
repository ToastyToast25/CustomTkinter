import tkinter
import sys
from typing import Union, Tuple, Optional, Callable, Any, List

from .theme import ThemeManager
from .font import CTkFont
from .appearance_mode import CTkAppearanceModeBaseClass
from .scaling import CTkScalingBaseClass


class CTkContextMenu(tkinter.Menu, CTkAppearanceModeBaseClass, CTkScalingBaseClass):
    """
    Themed right-click context menu matching CustomTkinter styling.
    Supports items, separators, submenus, and keyboard accelerators.

    Usage:
        menu = CTkContextMenu(widget)
        menu.add_item("Copy", command=on_copy, accelerator="Ctrl+C")
        menu.add_item("Paste", command=on_paste, accelerator="Ctrl+V")
        menu.add_separator()
        menu.add_item("Delete", command=on_delete)
        menu.bind_context(widget)  # auto-bind right-click
    """

    def __init__(self,
                 master: Any = None,

                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 separator_color: Optional[Union[str, Tuple[str, str]]] = None,
                 disabled_color: Optional[Union[str, Tuple[str, str]]] = None,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 width: int = 180,
                 **kwargs):

        tkinter.Menu.__init__(self, master, **kwargs)
        CTkAppearanceModeBaseClass.__init__(self)
        CTkScalingBaseClass.__init__(self, scaling_type="widget")

        self._fg_color = fg_color or ThemeManager.theme["DropdownMenu"]["fg_color"]
        self._hover_color = hover_color or ThemeManager.theme["DropdownMenu"]["hover_color"]
        self._text_color = text_color or ThemeManager.theme["DropdownMenu"]["text_color"]
        self._separator_color = separator_color or ("#c0c0c0", "#555555")
        self._disabled_color = disabled_color or ("#999999", "#666666")
        self._width = width

        self._font = CTkFont() if font is None else font
        self._items: List[dict] = []
        self._bound_widgets: List[Any] = []

        self._configure_appearance()

    def _configure_appearance(self):
        """Apply themed styling to the menu."""
        if sys.platform == "darwin":
            self.configure(tearoff=False,
                           font=self._font if isinstance(self._font, tuple) else (
                               self._font.cget("family"), self._font.cget("size")))
        elif sys.platform.startswith("win"):
            self.configure(
                tearoff=False,
                relief="flat",
                bg=self._apply_appearance_mode(self._fg_color),
                fg=self._apply_appearance_mode(self._text_color),
                activebackground=self._apply_appearance_mode(self._hover_color),
                activeforeground=self._apply_appearance_mode(self._text_color),
                disabledforeground=self._apply_appearance_mode(self._disabled_color),
                borderwidth=self._apply_widget_scaling(4),
                activeborderwidth=self._apply_widget_scaling(4),
                font=self._font if isinstance(self._font, tuple) else (
                    self._font.cget("family"), self._font.cget("size")),
                cursor="hand2"
            )
        else:
            self.configure(
                tearoff=False,
                relief="flat",
                bg=self._apply_appearance_mode(self._fg_color),
                fg=self._apply_appearance_mode(self._text_color),
                activebackground=self._apply_appearance_mode(self._hover_color),
                activeforeground=self._apply_appearance_mode(self._text_color),
                disabledforeground=self._apply_appearance_mode(self._disabled_color),
                borderwidth=0,
                activeborderwidth=0,
                font=self._font if isinstance(self._font, tuple) else (
                    self._font.cget("family"), self._font.cget("size"))
            )

    def add_item(self, label: str,
                 command: Optional[Callable] = None,
                 accelerator: str = "",
                 state: str = "normal",
                 **kwargs):
        """Add a menu item with optional keyboard accelerator text."""
        self._items.append({
            "type": "command",
            "label": label,
            "command": command,
            "accelerator": accelerator,
            "state": state,
        })
        self.add_command(
            label=f"  {label}",
            command=command,
            accelerator=f"  {accelerator}" if accelerator else "",
            state=state,
            **kwargs
        )

    def add_separator(self):
        """Add a separator line between items."""
        self._items.append({"type": "separator"})
        tkinter.Menu.add_separator(self)

    def add_submenu(self, label: str, **kwargs) -> "CTkContextMenu":
        """Add a submenu and return it for further configuration."""
        submenu = CTkContextMenu(
            master=self,
            fg_color=self._fg_color,
            hover_color=self._hover_color,
            text_color=self._text_color,
            font=self._font,
        )
        self._items.append({"type": "cascade", "label": label, "submenu": submenu})
        self.add_cascade(label=f"  {label}", menu=submenu, **kwargs)
        return submenu

    def show(self, x: int, y: int):
        """Show the context menu at the given screen coordinates."""
        try:
            if sys.platform == "darwin" or sys.platform.startswith("win"):
                self.post(int(x), int(y))
            else:
                self.tk_popup(int(x), int(y))
        except Exception:
            pass

    def show_at_cursor(self, event=None):
        """Show the context menu at the current cursor position."""
        if event is not None:
            self.show(event.x_root, event.y_root)

    def bind_context(self, widget: Any):
        """Bind right-click to show this context menu on the widget."""
        if sys.platform == "darwin":
            widget.bind("<Button-2>", self.show_at_cursor, add="+")
            widget.bind("<Control-Button-1>", self.show_at_cursor, add="+")
        else:
            widget.bind("<Button-3>", self.show_at_cursor, add="+")
        self._bound_widgets.append(widget)

    def unbind_context(self, widget: Any):
        """Remove context menu binding from widget."""
        try:
            if sys.platform == "darwin":
                widget.unbind("<Button-2>")
                widget.unbind("<Control-Button-1>")
            else:
                widget.unbind("<Button-3>")
            self._bound_widgets.remove(widget)
        except (ValueError, Exception):
            pass

    def clear(self):
        """Remove all items from the menu."""
        self.delete(0, "end")
        self._items.clear()

    def destroy(self):
        for widget in self._bound_widgets[:]:
            try:
                self.unbind_context(widget)
            except Exception:
                pass
        self._bound_widgets.clear()
        tkinter.Menu.destroy(self)
        CTkAppearanceModeBaseClass.destroy(self)

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
        self._configure_appearance()
