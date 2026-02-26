import tkinter
import colorsys
from typing import Union, Tuple, Optional, Callable, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkColorPicker(CTkBaseClass):
    """
    Color picker with hue bar, saturation/value square, color preview,
    hex/RGB input fields, and preset color swatches.

    Supports a compact mode (gradient + swatches only, no input fields),
    command callbacks, and StringVar variable binding.

    Usage:
        picker = CTkColorPicker(parent,
            command=on_color_changed,   # callback(hex_color: str)
            variable=color_var,         # tkinter.StringVar
            initial_color="#ff0000",
            width=300,
            height=250,
            compact=False,
        )
        picker.get()        # returns "#rrggbb"
        picker.set("#00ff00")
    """

    # 18 preset swatches: primaries, secondaries, neutrals, pastels
    _PRESET_COLORS = [
        "#ff0000", "#ff8000", "#ffff00", "#00cc00", "#00b3b3", "#0066ff",
        "#4b0082", "#9900cc", "#ff3399", "#ffffff", "#000000", "#808080",
        "#ffb3b3", "#ffd9b3", "#ffffb3", "#b3ffb3", "#b3ffff", "#b3d9ff",
    ]

    def __init__(self,
                 master: Any,
                 width: int = 300,
                 height: int = 250,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 button_color: Optional[Union[str, Tuple[str, str]]] = None,
                 entry_fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 entry_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 label_text_color: Optional[Union[str, Tuple[str, str]]] = None,

                 corner_radius: Optional[int] = None,
                 border_width: int = 0,

                 initial_color: str = "#ff0000",
                 compact: bool = False,
                 command: Optional[Callable[[str], Any]] = None,
                 variable: Optional[tkinter.StringVar] = None,
                 font: Optional[Union[tuple, CTkFont]] = None,
                 **kwargs):

        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # ── configuration ────────────────────────────────────────────
        self._compact = compact
        self._command = command
        self._corner_radius = 6 if corner_radius is None else corner_radius
        self._border_width = border_width

        # colors
        self._fg_color = fg_color or ThemeManager.theme["CTk"]["fg_color"]
        self._border_color = border_color or ("#d4d4d4", "#404040")
        self._button_color = button_color or ThemeManager.theme["CTkButton"]["fg_color"]
        self._entry_fg_color = entry_fg_color or ThemeManager.theme["CTkEntry"]["fg_color"]
        self._entry_text_color = entry_text_color or ThemeManager.theme["CTkEntry"]["text_color"]
        self._label_text_color = label_text_color or ThemeManager.theme["CTkLabel"]["text_color"]

        # font
        self._font = font or CTkFont(size=12)

        # variable binding
        self._variable = variable
        self._variable_callback_name = None
        self._variable_callback_blocked = False

        # ── internal color state (HSV) ───────────────────────────────
        self._hue = 0.0            # 0.0 .. 1.0
        self._saturation = 1.0     # 0.0 .. 1.0
        self._value = 1.0          # 0.0 .. 1.0 (brightness)

        # PhotoImage references (prevent garbage collection)
        self._hue_bar_image = None
        self._sv_square_image = None

        # marker tracking
        self._dragging_hue = False
        self._dragging_sv = False

        # suppress callbacks during programmatic updates
        self._suppress_callbacks = False

        # ── build the widget ─────────────────────────────────────────
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # outer frame holds everything
        fg_resolved = self._apply_appearance_mode(self._fg_color)
        self._outer = tkinter.Frame(self, bg=fg_resolved)
        self._outer.grid(row=0, column=0, sticky="nswe")

        self._build_gradient_area()
        if not self._compact:
            self._build_input_area()
        self._build_swatch_area()

        # ── apply initial color ──────────────────────────────────────
        self._suppress_callbacks = True
        self.set(initial_color)
        self._suppress_callbacks = False

        # ── variable trace ───────────────────────────────────────────
        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add(
                "write", self._variable_callback
            )
            # sync from variable if it has a value
            val = self._variable.get()
            if val and val.startswith("#") and len(val) == 7:
                self._suppress_callbacks = True
                self.set(val)
                self._suppress_callbacks = False

    # ══════════════════════════════════════════════════════════════════
    #  BUILD METHODS
    # ══════════════════════════════════════════════════════════════════

    def _build_gradient_area(self):
        """Build the SV square, hue bar, and color preview swatch."""
        fg_resolved = self._apply_appearance_mode(self._fg_color)

        self._gradient_frame = tkinter.Frame(self._outer, bg=fg_resolved)
        self._gradient_frame.pack(side="top", fill="x", padx=8, pady=(8, 4))

        # ── Saturation/Value square (left) ───────────────────────────
        sv_size = 150
        self._sv_size = sv_size

        self._sv_canvas = tkinter.Canvas(
            self._gradient_frame, width=sv_size, height=sv_size,
            highlightthickness=1, highlightbackground="#555555",
            cursor="crosshair", bg="#000000"
        )
        self._sv_canvas.pack(side="left", padx=(0, 8))
        self._sv_canvas.bind("<Button-1>", self._on_sv_click)
        self._sv_canvas.bind("<B1-Motion>", self._on_sv_drag)

        # ── Right column: hue bar + preview ──────────────────────────
        right_frame = tkinter.Frame(self._gradient_frame, bg=fg_resolved)
        right_frame.pack(side="left", fill="y", expand=True)

        # hue bar
        hue_bar_width = 20
        self._hue_bar_width = hue_bar_width
        self._hue_bar_height = sv_size

        self._hue_canvas = tkinter.Canvas(
            right_frame, width=hue_bar_width, height=self._hue_bar_height,
            highlightthickness=1, highlightbackground="#555555",
            cursor="hand2", bg="#000000"
        )
        self._hue_canvas.pack(side="left", padx=(0, 8))
        self._hue_canvas.bind("<Button-1>", self._on_hue_click)
        self._hue_canvas.bind("<B1-Motion>", self._on_hue_drag)

        # color preview swatch
        preview_frame = tkinter.Frame(right_frame, bg=fg_resolved)
        preview_frame.pack(side="left", fill="y", expand=True)

        preview_label = tkinter.Label(
            preview_frame, text="Preview",
            font=self._resolve_font(size_override=10),
            bg=fg_resolved,
            fg=self._apply_appearance_mode(self._label_text_color)
        )
        preview_label.pack(side="top", pady=(0, 4))

        self._preview_canvas = tkinter.Canvas(
            preview_frame, width=50, height=50,
            highlightthickness=1, highlightbackground="#555555",
            bg="#ff0000"
        )
        self._preview_canvas.pack(side="top")
        self._preview_label = preview_label

        # render initial gradient images
        self._render_hue_bar()
        self._render_sv_square()

    def _build_input_area(self):
        """Build hex and RGB entry fields."""
        fg_resolved = self._apply_appearance_mode(self._fg_color)
        entry_bg = self._apply_appearance_mode(self._entry_fg_color)
        entry_fg = self._apply_appearance_mode(self._entry_text_color)
        label_fg = self._apply_appearance_mode(self._label_text_color)
        font = self._resolve_font(size_override=11)

        self._input_frame = tkinter.Frame(self._outer, bg=fg_resolved)
        self._input_frame.pack(side="top", fill="x", padx=8, pady=4)

        # ── Hex input ────────────────────────────────────────────────
        hex_frame = tkinter.Frame(self._input_frame, bg=fg_resolved)
        hex_frame.pack(side="left", padx=(0, 12))

        tkinter.Label(
            hex_frame, text="Hex:", font=font, bg=fg_resolved, fg=label_fg
        ).pack(side="left", padx=(0, 4))

        self._hex_var = tkinter.StringVar(value="#ff0000")
        self._hex_entry = tkinter.Entry(
            hex_frame, textvariable=self._hex_var, width=8,
            font=font, bg=entry_bg, fg=entry_fg,
            insertbackground=entry_fg, relief="flat",
            highlightthickness=1, highlightbackground="#555555",
            highlightcolor=self._apply_appearance_mode(self._button_color)
        )
        self._hex_entry.pack(side="left")
        self._hex_entry.bind("<Return>", self._on_hex_entry)
        self._hex_entry.bind("<FocusOut>", self._on_hex_entry)

        # ── RGB inputs ───────────────────────────────────────────────
        rgb_frame = tkinter.Frame(self._input_frame, bg=fg_resolved)
        rgb_frame.pack(side="left")

        self._r_var = tkinter.StringVar(value="255")
        self._g_var = tkinter.StringVar(value="0")
        self._b_var = tkinter.StringVar(value="0")

        for label_text, var in [("R:", self._r_var), ("G:", self._g_var), ("B:", self._b_var)]:
            tkinter.Label(
                rgb_frame, text=label_text, font=font, bg=fg_resolved, fg=label_fg
            ).pack(side="left", padx=(4, 2))

            entry = tkinter.Entry(
                rgb_frame, textvariable=var, width=4,
                font=font, bg=entry_bg, fg=entry_fg,
                insertbackground=entry_fg, relief="flat",
                highlightthickness=1, highlightbackground="#555555",
                highlightcolor=self._apply_appearance_mode(self._button_color)
            )
            entry.pack(side="left")
            entry.bind("<Return>", self._on_rgb_entry)
            entry.bind("<FocusOut>", self._on_rgb_entry)

    def _build_swatch_area(self):
        """Build the grid of preset color swatches."""
        fg_resolved = self._apply_appearance_mode(self._fg_color)
        label_fg = self._apply_appearance_mode(self._label_text_color)
        font = self._resolve_font(size_override=10)

        self._swatch_frame = tkinter.Frame(self._outer, bg=fg_resolved)
        self._swatch_frame.pack(side="top", fill="x", padx=8, pady=(4, 8))

        tkinter.Label(
            self._swatch_frame, text="Presets:", font=font,
            bg=fg_resolved, fg=label_fg
        ).pack(side="top", anchor="w", pady=(0, 2))

        grid_frame = tkinter.Frame(self._swatch_frame, bg=fg_resolved)
        grid_frame.pack(side="top", fill="x")

        swatch_size = 18
        cols = 9  # 18 colors / 2 rows = 9 columns

        self._swatch_canvases = []
        for i, color in enumerate(self._PRESET_COLORS):
            row = i // cols
            col = i % cols

            swatch = tkinter.Canvas(
                grid_frame, width=swatch_size, height=swatch_size,
                highlightthickness=1, highlightbackground="#555555",
                cursor="hand2", bg=color
            )
            swatch.grid(row=row, column=col, padx=1, pady=1)
            swatch.bind("<Button-1>", lambda e, c=color: self._on_swatch_click(c))
            self._swatch_canvases.append(swatch)

    # ══════════════════════════════════════════════════════════════════
    #  GRADIENT RENDERING
    # ══════════════════════════════════════════════════════════════════

    def _render_hue_bar(self):
        """Draw the vertical rainbow hue bar using a PhotoImage."""
        w = self._hue_bar_width
        h = self._hue_bar_height

        self._hue_bar_image = tkinter.PhotoImage(width=w, height=h)

        # Build pixel data row by row
        row_data = []
        for y in range(h):
            hue = y / h
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            hex_color = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
            row_data.append("{" + " ".join([hex_color] * w) + "}")

        self._hue_bar_image.put(" ".join(row_data), to=(0, 0))
        self._hue_canvas.create_image(0, 0, anchor="nw", image=self._hue_bar_image)

        # Draw hue marker
        self._draw_hue_marker()

    def _render_sv_square(self):
        """Draw the saturation/value gradient square for the current hue."""
        size = self._sv_size

        self._sv_square_image = tkinter.PhotoImage(width=size, height=size)

        # Build pixel data: x = saturation (0..1), y = value (1..0)
        row_data = []
        for y in range(size):
            val = 1.0 - (y / size)
            row_pixels = []
            for x in range(size):
                sat = x / size
                r, g, b = colorsys.hsv_to_rgb(self._hue, sat, val)
                row_pixels.append(
                    f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
                )
            row_data.append("{" + " ".join(row_pixels) + "}")

        self._sv_square_image.put(" ".join(row_data), to=(0, 0))

        self._sv_canvas.delete("all")
        # Reset cached marker IDs since delete("all") removed them
        self._sv_outer_id = None
        self._sv_inner_id = None
        self._sv_canvas.create_image(0, 0, anchor="nw", image=self._sv_square_image)

        # Draw SV crosshair marker
        self._draw_sv_marker()

    def _draw_hue_marker(self):
        """Draw a horizontal indicator on the hue bar at the current hue."""
        y = int(self._hue * self._hue_bar_height)
        y = max(0, min(self._hue_bar_height - 1, y))
        w = self._hue_bar_width

        if not hasattr(self, "_hue_line_id") or self._hue_line_id is None:
            self._hue_canvas.delete("hue_marker")
            self._hue_line_id = self._hue_canvas.create_line(
                0, y, w, y, fill="#ffffff", width=2, tags="hue_marker")
            self._hue_rect_id = self._hue_canvas.create_rectangle(
                0, y - 1, w, y + 1, outline="#000000", width=1, tags="hue_marker")
        else:
            self._hue_canvas.coords(self._hue_line_id, 0, y, w, y)
            self._hue_canvas.coords(self._hue_rect_id, 0, y - 1, w, y + 1)

    def _draw_sv_marker(self):
        """Draw a crosshair circle on the SV square at the current sat/val."""
        size = self._sv_size
        x = int(self._saturation * size)
        y = int((1.0 - self._value) * size)
        x = max(0, min(size - 1, x))
        y = max(0, min(size - 1, y))

        radius = 5

        if not hasattr(self, "_sv_outer_id") or self._sv_outer_id is None:
            self._sv_canvas.delete("sv_marker")
            self._sv_outer_id = self._sv_canvas.create_oval(
                x - radius, y - radius, x + radius, y + radius,
                outline="#000000", width=2, tags="sv_marker")
            self._sv_inner_id = self._sv_canvas.create_oval(
                x - radius + 1, y - radius + 1, x + radius - 1, y + radius - 1,
                outline="#ffffff", width=1, tags="sv_marker")
        else:
            self._sv_canvas.coords(self._sv_outer_id,
                                   x - radius, y - radius, x + radius, y + radius)
            self._sv_canvas.coords(self._sv_inner_id,
                                   x - radius + 1, y - radius + 1, x + radius - 1, y + radius - 1)

    # ══════════════════════════════════════════════════════════════════
    #  EVENT HANDLERS
    # ══════════════════════════════════════════════════════════════════

    def _on_hue_click(self, event):
        """Handle click on the hue bar."""
        self._dragging_hue = True
        self._update_hue_from_event(event)

    def _on_hue_drag(self, event):
        """Handle drag on the hue bar."""
        self._update_hue_from_event(event)

    def _update_hue_from_event(self, event):
        """Update hue from a mouse event on the hue canvas."""
        h = self._hue_bar_height
        y = max(0, min(h - 1, event.y))
        self._hue = y / h

        # Redraw SV square for new hue
        self._render_sv_square()
        self._draw_hue_marker()
        self._update_from_hsv()

    def _on_sv_click(self, event):
        """Handle click on the SV square."""
        self._dragging_sv = True
        self._update_sv_from_event(event)

    def _on_sv_drag(self, event):
        """Handle drag on the SV square."""
        self._update_sv_from_event(event)

    def _update_sv_from_event(self, event):
        """Update saturation and value from a mouse event on the SV canvas."""
        size = self._sv_size
        x = max(0, min(size - 1, event.x))
        y = max(0, min(size - 1, event.y))
        self._saturation = x / size
        self._value = 1.0 - (y / size)

        self._draw_sv_marker()
        self._update_from_hsv()

    def _on_swatch_click(self, color: str):
        """Handle click on a preset color swatch."""
        self.set(color)

    def _on_hex_entry(self, event=None):
        """Handle hex entry commit (Return or FocusOut)."""
        hex_val = self._hex_var.get().strip()
        if self._is_valid_hex(hex_val):
            self._suppress_callbacks = False
            self.set(hex_val)
        else:
            # Revert to current color
            self._hex_var.set(self._current_hex())

    def _on_rgb_entry(self, event=None):
        """Handle RGB entry commit (Return or FocusOut)."""
        try:
            r = max(0, min(255, int(self._r_var.get())))
            g = max(0, min(255, int(self._g_var.get())))
            b = max(0, min(255, int(self._b_var.get())))
            hex_val = f"#{r:02x}{g:02x}{b:02x}"
            self._suppress_callbacks = False
            self.set(hex_val)
        except (ValueError, TypeError):
            # Revert to current values
            r, g, b = self._current_rgb()
            self._r_var.set(str(r))
            self._g_var.set(str(g))
            self._b_var.set(str(b))

    # ══════════════════════════════════════════════════════════════════
    #  INTERNAL UPDATE LOGIC
    # ══════════════════════════════════════════════════════════════════

    def _update_from_hsv(self):
        """Update all displays and fire callbacks from current HSV state."""
        r_f, g_f, b_f = colorsys.hsv_to_rgb(self._hue, self._saturation, self._value)
        r = int(r_f * 255)
        g = int(g_f * 255)
        b = int(b_f * 255)
        hex_color = f"#{r:02x}{g:02x}{b:02x}"

        # Update preview
        self._preview_canvas.configure(bg=hex_color)

        # Update input fields (if not in compact mode)
        if not self._compact:
            self._hex_var.set(hex_color)
            self._r_var.set(str(r))
            self._g_var.set(str(g))
            self._b_var.set(str(b))

        # Update variable
        if self._variable is not None and not self._variable_callback_blocked:
            self._variable_callback_blocked = True
            self._variable.set(hex_color)
            self._variable_callback_blocked = False

        # Fire command callback
        if not self._suppress_callbacks and self._command is not None:
            self._command(hex_color)

    def _current_hex(self) -> str:
        """Return the current color as a hex string."""
        r_f, g_f, b_f = colorsys.hsv_to_rgb(self._hue, self._saturation, self._value)
        return f"#{int(r_f * 255):02x}{int(g_f * 255):02x}{int(b_f * 255):02x}"

    def _current_rgb(self) -> Tuple[int, int, int]:
        """Return the current color as an (R, G, B) tuple."""
        r_f, g_f, b_f = colorsys.hsv_to_rgb(self._hue, self._saturation, self._value)
        return int(r_f * 255), int(g_f * 255), int(b_f * 255)

    @staticmethod
    def _is_valid_hex(value: str) -> bool:
        """Check if a string is a valid #RRGGBB hex color."""
        if not isinstance(value, str):
            return False
        if len(value) != 7 or not value.startswith("#"):
            return False
        try:
            int(value[1:], 16)
            return True
        except ValueError:
            return False

    def _resolve_font(self, size_override: Optional[int] = None) -> tuple:
        """Resolve a CTkFont or tuple to a plain tkinter font tuple."""
        if isinstance(self._font, CTkFont):
            family = self._font.cget("family")
            size = size_override or self._font.cget("size")
            weight = self._font.cget("weight")
            return (family, size, weight)
        elif isinstance(self._font, tuple):
            if size_override and len(self._font) >= 2:
                return (self._font[0], size_override) + self._font[2:]
            return self._font
        return ("Segoe UI", size_override or 12)

    # ══════════════════════════════════════════════════════════════════
    #  VARIABLE CALLBACK
    # ══════════════════════════════════════════════════════════════════

    def _variable_callback(self, var_name, index, mode):
        """Called when the linked StringVar changes externally."""
        if not self._variable_callback_blocked:
            val = self._variable.get()
            if self._is_valid_hex(val):
                self._variable_callback_blocked = True
                self.set(val)
                self._variable_callback_blocked = False

    # ══════════════════════════════════════════════════════════════════
    #  PUBLIC API
    # ══════════════════════════════════════════════════════════════════

    def get(self) -> str:
        """Return the currently selected color as '#rrggbb'."""
        return self._current_hex()

    def set(self, hex_color: str):
        """Set the color picker to the given '#rrggbb' hex color."""
        if not self._is_valid_hex(hex_color):
            return

        hex_color = hex_color.lower()
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)

        # Convert RGB to HSV
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        self._hue = h
        self._saturation = s
        self._value = v

        # Redraw gradients and markers
        self._render_sv_square()
        self._draw_hue_marker()

        # Update preview and inputs
        self._preview_canvas.configure(bg=hex_color)
        if not self._compact:
            self._hex_var.set(hex_color)
            self._r_var.set(str(r))
            self._g_var.set(str(g))
            self._b_var.set(str(b))

        # Update variable
        if self._variable is not None and not self._variable_callback_blocked:
            self._variable_callback_blocked = True
            self._variable.set(hex_color)
            self._variable_callback_blocked = False

        # Fire command callback
        if not self._suppress_callbacks and self._command is not None:
            self._command(hex_color)

    # ══════════════════════════════════════════════════════════════════
    #  DRAWING (CTkBaseClass override)
    # ══════════════════════════════════════════════════════════════════

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        # Guard: _draw may be triggered by <Configure> before build methods finish
        if not hasattr(self, "_outer"):
            return

        if no_color_updates is False:
            fg = self._apply_appearance_mode(self._fg_color)
            self._outer.configure(bg=fg)
            self._gradient_frame.configure(bg=fg)
            self._swatch_frame.configure(bg=fg)
            if not self._compact and hasattr(self, "_input_frame"):
                self._input_frame.configure(bg=fg)

    # ══════════════════════════════════════════════════════════════════
    #  SCALING
    # ══════════════════════════════════════════════════════════════════

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)

    # ══════════════════════════════════════════════════════════════════
    #  CONFIGURE / CGET
    # ══════════════════════════════════════════════════════════════════

    def configure(self, **kwargs):
        require_redraw = False

        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "initial_color" in kwargs:
            self.set(kwargs.pop("initial_color"))
        if "fg_color" in kwargs:
            self._fg_color = kwargs.pop("fg_color")
            require_redraw = True
        if "border_color" in kwargs:
            self._border_color = kwargs.pop("border_color")
            require_redraw = True
        if "button_color" in kwargs:
            self._button_color = kwargs.pop("button_color")
            require_redraw = True
        if "entry_fg_color" in kwargs:
            self._entry_fg_color = kwargs.pop("entry_fg_color")
            require_redraw = True
        if "entry_text_color" in kwargs:
            self._entry_text_color = kwargs.pop("entry_text_color")
            require_redraw = True
        if "label_text_color" in kwargs:
            self._label_text_color = kwargs.pop("label_text_color")
            require_redraw = True
        if "variable" in kwargs:
            if self._variable is not None and self._variable_callback_name is not None:
                self._variable.trace_remove("write", self._variable_callback_name)
                self._variable_callback_name = None
            self._variable = kwargs.pop("variable")
            if self._variable is not None:
                self._variable_callback_name = self._variable.trace_add(
                    "write", self._variable_callback
                )
                val = self._variable.get()
                if self._is_valid_hex(val):
                    self.set(val)

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "command":
            return self._command
        elif attribute_name == "compact":
            return self._compact
        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "button_color":
            return self._button_color
        elif attribute_name == "entry_fg_color":
            return self._entry_fg_color
        elif attribute_name == "entry_text_color":
            return self._entry_text_color
        elif attribute_name == "label_text_color":
            return self._label_text_color
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "initial_color":
            return self._current_hex()
        else:
            return super().cget(attribute_name)

    # ══════════════════════════════════════════════════════════════════
    #  BIND / UNBIND (delegate to outer frame)
    # ══════════════════════════════════════════════════════════════════

    def bind(self, sequence: str = None, command: Callable = None, add: Union[str, bool] = True):
        """Delegate bind to the outer frame."""
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._outer.bind(sequence, command, add=True)

    def unbind(self, sequence: str = None, funcid: str = None):
        """Delegate unbind to the outer frame."""
        if funcid is not None:
            raise ValueError(
                "'funcid' argument can only be None, because there is a bug in tkinter"
            )
        self._outer.unbind(sequence, None)

    # ══════════════════════════════════════════════════════════════════
    #  CLEANUP
    # ══════════════════════════════════════════════════════════════════

    def destroy(self):
        """Clean up variable traces before destroying."""
        if self._variable is not None and self._variable_callback_name is not None:
            self._variable.trace_remove("write", self._variable_callback_name)
            self._variable_callback_name = None
        # Release PhotoImage references
        self._hue_bar_image = None
        self._sv_square_image = None
        super().destroy()
