"""
Animated toggle switch with smooth sliding thumb and color transitions.

Enhanced alternative to CTkSwitch with:
- Smooth thumb sliding animation (~60fps)
- Track color fade between on/off states
- Size variants: small (24px), medium (32px), large (40px)
- Optional on/off labels inside the track
- Loading state with spinning indicator
- Keyboard support (Space, Enter)

Usage:
    switch = CTkToggleSwitch(parent, size="medium", command=on_toggle)
    switch.toggle()
    switch.set(True)
    switch.start_loading()   # show spinner while async work runs
    switch.stop_loading()
"""

import tkinter
import sys
import math
from typing import Union, Tuple, Callable, Optional, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


_SIZE_PRESETS = {
    "small":  {"track_w": 40, "track_h": 22, "thumb_pad": 3, "thumb_r": 8},
    "medium": {"track_w": 52, "track_h": 28, "thumb_pad": 4, "thumb_r": 10},
    "large":  {"track_w": 64, "track_h": 34, "thumb_pad": 4, "thumb_r": 13},
}


def _lerp_hex(c1: str, c2: str, t: float) -> str:
    """Linearly interpolate between two hex colors."""
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


class CTkToggleSwitch(CTkBaseClass):
    """
    Animated toggle switch with smooth sliding and color transitions.

    Features two visual states with animated transition between them,
    size presets, optional track labels, loading spinner, and full
    keyboard/mouse support.
    """

    def __init__(
        self,
        master: Any,
        width: Optional[int] = None,
        height: Optional[int] = None,
        size: str = "medium",

        bg_color: Union[str, Tuple[str, str]] = "transparent",
        on_color: Optional[Union[str, Tuple[str, str]]] = None,
        off_color: Optional[Union[str, Tuple[str, str]]] = None,
        thumb_color: Optional[Union[str, Tuple[str, str]]] = None,
        thumb_hover_color: Optional[Union[str, Tuple[str, str]]] = None,
        border_color: Union[str, Tuple[str, str]] = "transparent",
        text_color: Optional[Union[str, Tuple[str, str]]] = None,
        text_color_disabled: Optional[Union[str, Tuple[str, str]]] = None,

        text: str = "",
        font: Optional[Union[tuple, CTkFont]] = None,
        on_label: str = "",
        off_label: str = "",

        variable: Union[tkinter.Variable, None] = None,
        onvalue: Union[int, str] = 1,
        offvalue: Union[int, str] = 0,
        command: Union[Callable, None] = None,
        state: str = "normal",
        hover: bool = True,

        animation_duration: int = 200,
        **kwargs,
    ):
        # resolve size preset
        preset = _SIZE_PRESETS.get(size, _SIZE_PRESETS["medium"])
        self._track_width = preset["track_w"]
        self._track_height = preset["track_h"]
        self._thumb_pad = preset["thumb_pad"]
        self._thumb_radius = preset["thumb_r"]
        self._size = size

        # widget overall dimensions
        if width is None:
            width = self._track_width + (8 if not text else 8)
        if height is None:
            height = self._track_height

        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # colors
        self._on_color = self._check_color_type(on_color) if on_color is not None else ("#3b82f6", "#3b82f6")
        self._off_color = self._check_color_type(off_color) if off_color is not None else ("#71717a", "#52525b")
        self._thumb_color = self._check_color_type(thumb_color) if thumb_color is not None else ("#ffffff", "#ffffff")
        self._thumb_hover_color = self._check_color_type(thumb_hover_color) if thumb_hover_color is not None else ("#e4e4e7", "#e4e4e7")
        self._border_color = self._check_color_type(border_color, transparency=True)
        self._text_color = ThemeManager.theme["CTkSwitch"]["text_color"] if text_color is None else self._check_color_type(text_color)
        self._text_color_disabled = ThemeManager.theme["CTkSwitch"]["text_color_disabled"] if text_color_disabled is None else self._check_color_type(text_color_disabled)

        # text
        self._text = text
        self._on_label = on_label
        self._off_label = off_label

        # font
        self._font = CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)

        # state
        self._check_state: bool = False
        self._hover_state: bool = False
        self._hover = hover
        self._state = state
        self._onvalue = onvalue
        self._offvalue = offvalue

        # animation
        self._anim_duration = max(50, animation_duration)
        self._anim_phase: float = 0.0  # 0.0 = off, 1.0 = on
        self._anim_target: float = 0.0
        self._anim_after_id = None

        # loading
        self._loading = False
        self._loading_angle = 0.0
        self._loading_after_id = None

        # variable
        self._command = command
        self._variable = variable
        self._variable_callback_blocked = False
        self._variable_callback_name = None

        # layout grid
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0, minsize=self._apply_widget_scaling(6))
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # background canvas
        self._bg_canvas = CTkCanvas(
            master=self,
            highlightthickness=0,
            width=self._apply_widget_scaling(self._current_width),
            height=self._apply_widget_scaling(self._current_height),
        )
        self._bg_canvas.grid(row=0, column=0, columnspan=3, sticky="nswe")

        # track canvas (where we draw everything custom)
        self._canvas = tkinter.Canvas(
            self,
            highlightthickness=0,
            width=self._apply_widget_scaling(self._track_width),
            height=self._apply_widget_scaling(self._track_height),
            bd=0,
        )
        self._canvas.grid(row=0, column=0, sticky="")

        # optional text label
        self._text_label = None
        if self._text:
            self._text_label = tkinter.Label(
                master=self,
                bd=0, padx=0, pady=0,
                text=self._text,
                justify=tkinter.LEFT,
                font=self._apply_font_scaling(self._font),
            )
            self._text_label.grid(row=0, column=2, sticky="w")
            self._text_label["anchor"] = "w"

        # variable setup
        if self._variable is not None and self._variable != "":
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._check_state = self._variable.get() == self._onvalue
            self._anim_phase = 1.0 if self._check_state else 0.0
            self._anim_target = self._anim_phase

        # bindings
        self._create_bindings()
        self._set_cursor()
        self._draw()

    # ── Bindings ──────────────────────────────────────────────

    def _create_bindings(self, sequence: Optional[str] = None):
        if sequence is None or sequence == "<Enter>":
            self._canvas.bind("<Enter>", self._on_enter)
            if self._text_label:
                self._text_label.bind("<Enter>", self._on_enter)
        if sequence is None or sequence == "<Leave>":
            self._canvas.bind("<Leave>", self._on_leave)
            if self._text_label:
                self._text_label.bind("<Leave>", self._on_leave)
        if sequence is None or sequence == "<Button-1>":
            self._canvas.bind("<Button-1>", self._on_click)
            if self._text_label:
                self._text_label.bind("<Button-1>", self._on_click)
        if sequence is None or sequence == "<space>":
            self._canvas.bind("<space>", self._on_click)
        if sequence is None or sequence == "<Return>":
            self._canvas.bind("<Return>", self._on_click)
        if sequence is None or sequence == "<FocusIn>":
            self._canvas.bind("<FocusIn>", self._on_focus_in)
        if sequence is None or sequence == "<FocusOut>":
            self._canvas.bind("<FocusOut>", self._on_focus_out)

    def _set_cursor(self):
        if not self._cursor_manipulation_enabled:
            return
        cursor = "arrow"
        if self._state == "normal":
            cursor = "pointinghand" if sys.platform == "darwin" else "hand2"
        self._canvas.configure(cursor=cursor)
        if self._text_label:
            self._text_label.configure(cursor=cursor)

    # ── Scaling ───────────────────────────────────────────────

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._bg_canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._canvas.configure(
            width=self._apply_widget_scaling(self._track_width),
            height=self._apply_widget_scaling(self._track_height),
        )
        if self._text_label:
            self._text_label.configure(font=self._apply_font_scaling(self._font))
        self._draw()

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)
        self._bg_canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )

    def _update_font(self):
        if self._text_label:
            self._text_label.configure(font=self._apply_font_scaling(self._font))
            self._bg_canvas.grid_forget()
            self._bg_canvas.grid(row=0, column=0, columnspan=3, sticky="nswe")

    # ── Drawing ───────────────────────────────────────────────

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        s = self._apply_widget_scaling
        tw = s(self._track_width)
        th = s(self._track_height)
        pad = s(self._thumb_pad)
        tr = s(self._thumb_radius)
        cr = th / 2  # track corner radius = half height (pill shape)

        # resolve colors for current appearance mode
        bg = self._apply_appearance_mode(self._bg_color)
        on_c = self._apply_appearance_mode(self._on_color)
        off_c = self._apply_appearance_mode(self._off_color)
        track_c = _lerp_hex(off_c, on_c, self._anim_phase)

        if self._hover_state and self._state == "normal":
            thumb_c = self._apply_appearance_mode(self._thumb_hover_color)
        else:
            thumb_c = self._apply_appearance_mode(self._thumb_color)

        # canvas bg
        self._canvas.configure(bg=bg)
        self._bg_canvas.configure(bg=bg)

        # clear
        self._canvas.delete("all")

        # draw track (rounded rectangle / pill)
        self._draw_pill(0, 0, tw, th, cr, fill=track_c, outline=track_c)

        # border
        if self._border_color != "transparent":
            bc = self._apply_appearance_mode(self._border_color)
            self._draw_pill(0, 0, tw, th, cr, fill="", outline=bc, width=2)

        # thumb position (interpolated)
        eased = _ease_out_cubic(self._anim_phase)
        left_x = pad + tr
        right_x = tw - pad - tr
        cx = left_x + (right_x - left_x) * eased
        cy = th / 2

        # thumb shadow (subtle)
        self._canvas.create_oval(
            cx - tr + 1, cy - tr + 1, cx + tr + 1, cy + tr + 1,
            fill="#00000020" if sys.platform != "win32" else "#333333",
            outline="",
            stipple="gray25" if sys.platform.startswith("win") else "",
        )

        # thumb circle
        self._canvas.create_oval(
            cx - tr, cy - tr, cx + tr, cy + tr,
            fill=thumb_c, outline=thumb_c,
        )

        # loading spinner on thumb
        if self._loading:
            self._draw_spinner(cx, cy, tr * 0.6, self._loading_angle)

        # on/off labels inside track
        if self._on_label or self._off_label:
            label_font_size = max(8, int(th * 0.32))
            lbl_font = ("Helvetica", label_font_size, "bold")
            # on label (left side, visible when on)
            if self._on_label and self._anim_phase > 0.3:
                alpha = min(1.0, (self._anim_phase - 0.3) / 0.4)
                lc = _lerp_hex(track_c, "#ffffff", alpha)
                self._canvas.create_text(
                    pad + tr * 0.8, cy,
                    text=self._on_label, fill=lc, font=lbl_font, anchor="w",
                )
            # off label (right side, visible when off)
            if self._off_label and self._anim_phase < 0.7:
                alpha = min(1.0, (0.7 - self._anim_phase) / 0.4)
                lc = _lerp_hex(track_c, "#ffffff", alpha)
                self._canvas.create_text(
                    tw - pad - tr * 0.8, cy,
                    text=self._off_label, fill=lc, font=lbl_font, anchor="e",
                )

        # focus ring
        if self._canvas.focus_get() == self._canvas:
            self._draw_pill(
                -2, -2, tw + 4, th + 4, cr + 2,
                fill="", outline=self._apply_appearance_mode(self._on_color), width=2,
            )

        # text label colors
        if self._text_label:
            if self._state == "disabled":
                self._text_label.configure(fg=self._apply_appearance_mode(self._text_color_disabled))
            else:
                self._text_label.configure(fg=self._apply_appearance_mode(self._text_color))
            self._text_label.configure(bg=bg)

    def _draw_pill(self, x1, y1, x2, y2, r, **kw):
        """Draw a pill / rounded rectangle on the canvas using two ovals + center rect."""
        self._canvas.create_oval(x1, y1, x1 + 2 * r, y2, **kw)
        self._canvas.create_oval(x2 - 2 * r, y1, x2, y2, **kw)
        fill_kw = {k: v for k, v in kw.items() if k != "width"}
        if "outline" not in fill_kw:
            fill_kw["outline"] = fill_kw.get("fill", "")
        self._canvas.create_rectangle(x1 + r, y1, x2 - r, y2, **fill_kw)

    def _draw_spinner(self, cx, cy, r, angle):
        """Draw a loading arc on the thumb."""
        import math as m
        start = angle
        extent = 270
        x1, y1 = cx - r, cy - r
        x2, y2 = cx + r, cy + r
        self._canvas.create_arc(
            x1, y1, x2, y2,
            start=start, extent=extent,
            style="arc", outline="#3b82f6", width=2,
        )

    # ── Animation ─────────────────────────────────────────────

    def _start_animation(self):
        if self._anim_after_id is not None:
            self.after_cancel(self._anim_after_id)
            self._anim_after_id = None

        interval = 16  # ~60fps
        step = interval / self._anim_duration

        def _animate():
            if self._anim_phase < self._anim_target:
                self._anim_phase = min(self._anim_phase + step, self._anim_target)
            elif self._anim_phase > self._anim_target:
                self._anim_phase = max(self._anim_phase - step, self._anim_target)

            self._draw()

            if abs(self._anim_phase - self._anim_target) > 0.001:
                self._anim_after_id = self.after(interval, _animate)
            else:
                self._anim_phase = self._anim_target
                self._anim_after_id = None
                self._draw()

        self._anim_after_id = self.after(interval, _animate)

    def _start_loading_animation(self):
        if self._loading_after_id is not None:
            return

        def _spin():
            self._loading_angle = (self._loading_angle + 15) % 360
            self._draw()
            if self._loading:
                self._loading_after_id = self.after(33, _spin)

        self._loading_after_id = self.after(33, _spin)

    # ── Public API ────────────────────────────────────────────

    def set(self, state: bool, from_variable_callback=False):
        """Set the switch state programmatically."""
        self._check_state = bool(state)
        self._anim_target = 1.0 if self._check_state else 0.0
        self._start_animation()

        if self._variable is not None and not from_variable_callback:
            self._variable_callback_blocked = True
            self._variable.set(self._onvalue if self._check_state else self._offvalue)
            self._variable_callback_blocked = False

    def toggle(self, event=None):
        """Toggle the switch state."""
        if self._state != "normal" or self._loading:
            return
        self.set(not self._check_state)
        if self._command is not None:
            self._command(self._check_state)

    def get(self) -> Union[int, str]:
        """Get the current value (onvalue or offvalue)."""
        return self._onvalue if self._check_state else self._offvalue

    def get_bool(self) -> bool:
        """Get the current state as a boolean."""
        return self._check_state

    def select(self, from_variable_callback=False):
        self.set(True, from_variable_callback)

    def deselect(self, from_variable_callback=False):
        self.set(False, from_variable_callback)

    def start_loading(self):
        """Show a loading spinner on the thumb."""
        self._loading = True
        self._start_loading_animation()

    def stop_loading(self):
        """Hide the loading spinner."""
        self._loading = False
        if self._loading_after_id is not None:
            self.after_cancel(self._loading_after_id)
            self._loading_after_id = None
        self._draw()

    # ── Events ────────────────────────────────────────────────

    def _on_click(self, event=None):
        self.toggle()

    def _on_enter(self, event=None):
        if self._hover and self._state == "normal":
            self._hover_state = True
            self._draw()

    def _on_leave(self, event=None):
        self._hover_state = False
        self._draw()

    def _on_focus_in(self, event=None):
        self._draw()

    def _on_focus_out(self, event=None):
        self._draw()

    def _variable_callback(self, var_name, index, mode):
        if not self._variable_callback_blocked:
            if self._variable.get() == self._onvalue:
                self.select(from_variable_callback=True)
            elif self._variable.get() == self._offvalue:
                self.deselect(from_variable_callback=True)

    # ── Configure / cget ──────────────────────────────────────

    def configure(self, require_redraw=False, **kwargs):
        if "on_color" in kwargs:
            self._on_color = self._check_color_type(kwargs.pop("on_color"))
            require_redraw = True
        if "off_color" in kwargs:
            self._off_color = self._check_color_type(kwargs.pop("off_color"))
            require_redraw = True
        if "thumb_color" in kwargs:
            self._thumb_color = self._check_color_type(kwargs.pop("thumb_color"))
            require_redraw = True
        if "thumb_hover_color" in kwargs:
            self._thumb_hover_color = self._check_color_type(kwargs.pop("thumb_hover_color"))
            require_redraw = True
        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"), transparency=True)
            require_redraw = True
        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True
        if "text" in kwargs:
            self._text = kwargs.pop("text")
            if self._text_label:
                self._text_label.configure(text=self._text)
        if "on_label" in kwargs:
            self._on_label = kwargs.pop("on_label")
            require_redraw = True
        if "off_label" in kwargs:
            self._off_label = kwargs.pop("off_label")
            require_redraw = True
        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_font)
            self._update_font()
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "variable" in kwargs:
            if self._variable is not None and self._variable != "":
                self._variable.trace_remove("write", self._variable_callback_name)
            self._variable = kwargs.pop("variable")
            if self._variable is not None and self._variable != "":
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
        if "onvalue" in kwargs:
            self._onvalue = kwargs.pop("onvalue")
        if "offvalue" in kwargs:
            self._offvalue = kwargs.pop("offvalue")
        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._set_cursor()
            require_redraw = True
        if "hover" in kwargs:
            self._hover = kwargs.pop("hover")
        if "animation_duration" in kwargs:
            self._anim_duration = max(50, kwargs.pop("animation_duration"))

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "on_color":
            return self._on_color
        elif attribute_name == "off_color":
            return self._off_color
        elif attribute_name == "thumb_color":
            return self._thumb_color
        elif attribute_name == "thumb_hover_color":
            return self._thumb_hover_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "text":
            return self._text
        elif attribute_name == "on_label":
            return self._on_label
        elif attribute_name == "off_label":
            return self._off_label
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "onvalue":
            return self._onvalue
        elif attribute_name == "offvalue":
            return self._offvalue
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "hover":
            return self._hover
        elif attribute_name == "size":
            return self._size
        elif attribute_name == "animation_duration":
            return self._anim_duration
        else:
            return super().cget(attribute_name)

    # ── Cleanup ───────────────────────────────────────────────

    def destroy(self):
        if self._anim_after_id is not None:
            self.after_cancel(self._anim_after_id)
        if self._loading_after_id is not None:
            self.after_cancel(self._loading_after_id)
        if self._variable is not None and self._variable_callback_name is not None:
            self._variable.trace_remove("write", self._variable_callback_name)
        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)
        super().destroy()

    # ── Bind / focus delegation ───────────────────────────────

    def bind(self, sequence: str = None, command: Callable = None, add: Union[str, bool] = True):
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, command, add=True)
        if self._text_label:
            self._text_label.bind(sequence, command, add=True)

    def unbind(self, sequence: str = None, funcid: str = None):
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in"
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._canvas.unbind(sequence, None)
        if self._text_label:
            self._text_label.unbind(sequence, None)
        self._create_bindings(sequence=sequence)

    def focus(self):
        return self._canvas.focus()

    def focus_set(self):
        return self._canvas.focus_set()

    def focus_force(self):
        return self._canvas.focus_force()
