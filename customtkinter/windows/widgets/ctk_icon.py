import sys
import tkinter
import tkinter.font as tkfont
from tkinter import TclError
from typing import Union, Tuple, Callable, Optional, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass

# ---------------------------------------------------------------------------
# Icon catalog: curated Unicode symbols chosen for cross-platform rendering.
# Preference is given to characters in the Basic Multilingual Plane that
# render as monochrome glyphs on Windows, macOS, and Linux.
# ---------------------------------------------------------------------------
ICONS: dict = {
    # Navigation
    "home":           "\u2302",  # ⌂
    "arrow_left":     "\u2190",  # ←
    "arrow_right":    "\u2192",  # →
    "arrow_up":       "\u2191",  # ↑
    "arrow_down":     "\u2193",  # ↓
    "chevron_left":   "\u2039",  # ‹
    "chevron_right":  "\u203A",  # ›
    "chevron_up":     "\u25B3",  # △
    "chevron_down":   "\u25BD",  # ▽
    "menu":           "\u2630",  # ☰
    "close":          "\u2715",  # ✕
    "back":           "\u2190",  # ←

    # Actions
    "search":         "\u2315",  # ⌕
    "add":            "\u002B",  # +
    "remove":         "\u2212",  # −
    "edit":           "\u270E",  # ✎
    "delete":         "\u2716",  # ✖
    "check":          "\u2713",  # ✓
    "check_circle":   "\u2714",  # ✔
    "copy":           "\u29C9",  # ⧉
    "paste":          "\u2398",  # ⎘
    "cut":            "\u2702",  # ✂
    "save":           "\u2913",  # ⤓
    "refresh":        "\u21BB",  # ↻
    "undo":           "\u21B6",  # ↶
    "redo":           "\u21B7",  # ↷

    # Status
    "info":           "\u2139",  # ℹ
    "warning":        "\u26A0",  # ⚠
    "error":          "\u2716",  # ✖
    "success":        "\u2714",  # ✔
    "question":       "\u003F",  # ?
    "bell":           "\u2407",  # ␇  (BMP bell symbol)
    "lock":           "\u26BF",  # ⚿
    "unlock":         "\u26BF",  # ⚿  (same glyph, distinguish via color if needed)

    # Objects
    "settings":       "\u2699",  # ⚙
    "user":           "\u263A",  # ☺
    "users":          "\u2687",  # ⚇
    "mail":           "\u2709",  # ✉
    "calendar":       "\u2637",  # ☷
    "clock":          "\u29D7",  # ⧗
    "folder":         "\u2636",  # ☶
    "file":           "\u2610",  # ☐
    "image":          "\u25A3",  # ▣
    "link":           "\u26D3",  # ⛓ (BMP)
    "star":           "\u2605",  # ★
    "star_outline":   "\u2606",  # ☆
    "heart":          "\u2665",  # ♥
    "heart_outline":  "\u2661",  # ♡
    "pin":            "\u25C6",  # ◆
    "tag":            "\u2302",  # ⌂  (re-used for tag)

    # Media
    "play":           "\u25B6",  # ▶
    "pause":          "\u2016",  # ‖
    "stop":           "\u25A0",  # ■
    "record":         "\u26AB",  # ⚫
    "skip_next":      "\u25B6\u25B6",  # ▶▶
    "skip_prev":      "\u25C0\u25C0",  # ◀◀
    "volume":         "\u266B",  # ♫
    "mute":           "\u2022",  # •

    # UI
    "sun":            "\u2600",  # ☀
    "moon":           "\u263E",  # ☾
    "eye":            "\u25C9",  # ◉
    "download":       "\u2913",  # ⤓
    "upload":         "\u2912",  # ⤒
    "filter":         "\u25BD",  # ▽
    "sort_asc":       "\u25B2",  # ▲
    "sort_desc":      "\u25BC",  # ▼
    "expand":         "\u229E",  # ⊞
    "collapse":       "\u229F",  # ⊟
    "drag":           "\u2630",  # ☰
    "more_h":         "\u22EF",  # ⋯
    "more_v":         "\u22EE",  # ⋮
    "external":       "\u2197",  # ↗
    "dashboard":      "\u2588",  # █
    "code":           "\u27E8\u27E9",  # ⟨⟩
    "terminal":       "\u25BA",  # ►
    "database":       "\u2395",  # ⎕
    "power":          "\u23FB",  # ⏻
    "bluetooth":      "\u2687",  # ⚇
    "wifi":           "\u2058",  # (word separator dot)
    "grid":           "\u2637",  # ☷
    "list":           "\u2261",  # ≡
    "minus":          "\u2212",  # −
    "plus":           "\u002B",  # +
    "circle":         "\u25CB",  # ○
    "circle_filled":  "\u25CF",  # ●
    "square":         "\u25A1",  # □
    "square_filled":  "\u25A0",  # ■
    "triangle":       "\u25B3",  # △
    "diamond":        "\u25C7",  # ◇
}

# ---------------------------------------------------------------------------
# Platform-specific symbol fonts, ordered by preference.
# ---------------------------------------------------------------------------
if sys.platform == "darwin":
    _SYMBOL_FONT_FAMILIES = ("Apple Symbols", "Menlo", "Helvetica Neue")
elif sys.platform.startswith("win"):
    _SYMBOL_FONT_FAMILIES = ("Segoe UI Symbol", "Segoe UI", "Arial")
else:
    _SYMBOL_FONT_FAMILIES = ("Noto Sans Symbols", "Noto Sans Symbols2",
                             "DejaVu Sans", "FreeSans")

# Cache for the resolved symbol font family on this platform.
_resolved_symbol_font: Optional[str] = None


def _resolve_symbol_font() -> str:
    """Determine the first available symbol font on this platform."""
    global _resolved_symbol_font
    if _resolved_symbol_font is not None:
        return _resolved_symbol_font

    available = set()
    try:
        available = set(tkfont.families())
    except TclError:
        pass

    for family in _SYMBOL_FONT_FAMILIES:
        if family in available:
            _resolved_symbol_font = family
            return family

    # Ultimate fallback -- tkinter's default font will still display many
    # BMP symbols correctly.
    _resolved_symbol_font = "TkDefaultFont"
    return _resolved_symbol_font


class CTkIcon(CTkBaseClass):
    """
    Lightweight icon widget that renders a Unicode symbol character on a
    canvas.  Icons are selected by name from the built-in ``ICONS`` catalog
    or by passing an arbitrary Unicode string.

    The symbol is drawn with a platform-appropriate font (Segoe UI Symbol on
    Windows, Apple Symbols on macOS, Noto Sans Symbols / DejaVu Sans on
    Linux) so that the majority of BMP symbols render correctly without
    bundling an icon font.

    Parameters
    ----------
    icon : str
        An icon name from the ``ICONS`` catalog (e.g. ``"home"``, ``"check"``)
        **or** a raw Unicode string that will be rendered directly.
    size : int
        Desired icon size in pixels (used as the font point-size).  Default 20.
    color : str | tuple[str, str] | None
        Foreground color for the icon.  A two-element tuple supplies separate
        colors for light and dark appearance modes.  *None* inherits the
        current theme ``text_color``.
    hover_color : str | tuple[str, str] | None
        Optional color shown while the mouse hovers over the widget.
    anchor : str
        Canvas text anchor.  Default ``"center"``.
    cursor : str
        Cursor to display when hovering.
    command : callable | None
        Optional callback invoked on ``<ButtonRelease-1>``.
    """

    def __init__(
        self,
        master: Any,
        width: int = 0,
        height: int = 0,

        bg_color: Union[str, Tuple[str, str]] = "transparent",

        icon: str = "circle",
        size: int = 20,
        color: Optional[Union[str, Tuple[str, str]]] = None,
        hover_color: Optional[Union[str, Tuple[str, str]]] = None,
        anchor: str = "center",
        cursor: str = "",
        command: Union[Callable[[], Any], None] = None,
        **kwargs,
    ):
        # If no explicit width/height given, derive from icon size with padding.
        if width == 0:
            width = size + 4
        if height == 0:
            height = size + 4

        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # icon name / raw character
        self._icon_name: str = icon
        self._icon_char: str = ICONS.get(icon, icon)

        # size
        self._icon_size: int = size

        # color
        self._color: Union[str, Tuple[str, str]] = (
            ThemeManager.theme["CTkLabel"]["text_color"]
            if color is None
            else self._check_color_type(color)
        )
        self._hover_color: Optional[Union[str, Tuple[str, str]]] = (
            None if hover_color is None else self._check_color_type(hover_color)
        )

        # other
        self._anchor: str = anchor
        self._cursor: str = cursor
        self._command: Union[Callable[[], Any], None] = command
        self._state: str = tkinter.NORMAL
        self._hover_active: bool = False

        # resolve the platform symbol font
        self._font_family: str = _resolve_symbol_font()

        # configure 1x1 grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # canvas
        self._canvas = CTkCanvas(
            master=self,
            highlightthickness=0,
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._canvas.grid(row=0, column=0, sticky="nswe")
        self._draw_engine = DrawEngine(self._canvas)

        # the canvas text item id (created in _draw)
        self._text_id: Optional[int] = None

        # bindings
        self._canvas.bind("<Enter>", self._on_enter)
        self._canvas.bind("<Leave>", self._on_leave)
        self._canvas.bind("<ButtonRelease-1>", self._on_click)

        if self._cursor:
            self.configure(cursor=self._cursor)

        self._draw()

    # ------------------------------------------------------------------
    # Scaling / appearance hooks
    # ------------------------------------------------------------------

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._draw(no_color_updates=True)

    def _set_appearance_mode(self, mode_string: str):
        super()._set_appearance_mode(mode_string)
        self._draw()

    def _set_dimensions(self, width: int = None, height: int = None):
        super()._set_dimensions(width, height)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._draw()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _get_scaled_font(self) -> Tuple[str, int]:
        """Return a (family, size) tuple with widget scaling applied."""
        scaled_size = int(self._apply_widget_scaling(self._icon_size))
        return (self._font_family, scaled_size)

    def _draw(self, no_color_updates: bool = False):
        super()._draw(no_color_updates)

        scaled_width = self._apply_widget_scaling(self._current_width)
        scaled_height = self._apply_widget_scaling(self._current_height)

        if no_color_updates is False:
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

        # Determine current foreground color
        if self._hover_active and self._hover_color is not None:
            fg = self._apply_appearance_mode(self._hover_color)
        else:
            fg = self._apply_appearance_mode(self._color)

        font_spec = self._get_scaled_font()

        if self._text_id is None:
            # First draw -- create the canvas text item
            self._text_id = self._canvas.create_text(
                round(scaled_width / 2),
                round(scaled_height / 2),
                text=self._icon_char,
                font=font_spec,
                fill=fg,
                anchor=self._anchor,
            )
        else:
            # Subsequent draws -- update in-place
            self._canvas.coords(
                self._text_id,
                round(scaled_width / 2),
                round(scaled_height / 2),
            )
            self._canvas.itemconfigure(
                self._text_id,
                text=self._icon_char,
                font=font_spec,
                fill=fg,
                anchor=self._anchor,
            )

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_enter(self, event=None):
        if self._hover_color is not None and self._state == tkinter.NORMAL:
            self._hover_active = True
            self._draw()

    def _on_leave(self, event=None):
        if self._hover_active:
            self._hover_active = False
            self._draw()

    def _on_click(self, event=None):
        if self._state != tkinter.DISABLED and self._command is not None:
            self._command()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_icon(self, name: str) -> None:
        """Change the displayed icon by catalog name or raw Unicode string."""
        self._icon_name = name
        self._icon_char = ICONS.get(name, name)
        self._draw()

    def get_icon(self) -> str:
        """Return the current icon catalog name (or raw string if custom)."""
        return self._icon_name

    def invoke(self) -> Any:
        """Programmatically invoke the click command (if any)."""
        if self._state != tkinter.DISABLED and self._command is not None:
            return self._command()

    # ------------------------------------------------------------------
    # configure / cget
    # ------------------------------------------------------------------

    def configure(self, require_redraw: bool = False, **kwargs):
        if "icon" in kwargs:
            name = kwargs.pop("icon")
            self._icon_name = name
            self._icon_char = ICONS.get(name, name)
            require_redraw = True

        if "size" in kwargs:
            self._icon_size = kwargs.pop("size")
            require_redraw = True

        if "color" in kwargs:
            self._color = self._check_color_type(kwargs.pop("color"))
            require_redraw = True

        if "hover_color" in kwargs:
            val = kwargs.pop("hover_color")
            self._hover_color = None if val is None else self._check_color_type(val)
            require_redraw = True

        if "anchor" in kwargs:
            self._anchor = kwargs.pop("anchor")
            require_redraw = True

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "state" in kwargs:
            self._state = kwargs.pop("state")

        if "cursor" in kwargs:
            self._cursor = kwargs.pop("cursor")

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "icon":
            return self._icon_name
        elif attribute_name == "size":
            return self._icon_size
        elif attribute_name == "color":
            return self._color
        elif attribute_name == "hover_color":
            return self._hover_color
        elif attribute_name == "anchor":
            return self._anchor
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "cursor":
            return self._cursor
        else:
            return super().cget(attribute_name)

    # ------------------------------------------------------------------
    # bind / unbind
    # ------------------------------------------------------------------

    def bind(self, sequence: str = None, command: Callable = None, add: Union[str, bool] = True):
        """Bind to the internal canvas, preserving internal callbacks."""
        if not (add == "+" or add is True):
            raise ValueError(
                "'add' argument can only be '+' or True to preserve internal callbacks"
            )
        self._canvas.bind(sequence, command, add=True)

    def unbind(self, sequence: str = None, funcid: Optional[str] = None):
        """Unbind from the internal canvas."""
        if funcid is not None:
            raise ValueError(
                "'funcid' argument can only be None, because there is a bug in "
                "tkinter and it is not clear whether internal callbacks will be "
                "unbound or not"
            )
        self._canvas.unbind(sequence, None)
        # Restore internal bindings
        if sequence == "<Enter>" or sequence is None:
            self._canvas.bind("<Enter>", self._on_enter, add=True)
        if sequence == "<Leave>" or sequence is None:
            self._canvas.bind("<Leave>", self._on_leave, add=True)
        if sequence == "<ButtonRelease-1>" or sequence is None:
            self._canvas.bind("<ButtonRelease-1>", self._on_click, add=True)

    def destroy(self):
        try:
            self._canvas.unbind("<Enter>")
            self._canvas.unbind("<Leave>")
            self._canvas.unbind("<ButtonRelease-1>")
        except TclError:
            pass
        super().destroy()

    # ------------------------------------------------------------------
    # Utility class methods
    # ------------------------------------------------------------------

    @staticmethod
    def available_icons() -> Tuple[str, ...]:
        """Return a sorted tuple of all built-in icon names."""
        return tuple(sorted(ICONS.keys()))

    @staticmethod
    def get_icon_char(name: str) -> str:
        """Look up the Unicode character for an icon name.

        Raises ``KeyError`` if *name* is not in the catalog.
        """
        return ICONS[name]
