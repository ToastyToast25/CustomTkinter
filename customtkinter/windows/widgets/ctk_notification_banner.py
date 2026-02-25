import tkinter
import time
from typing import Union, Tuple, Optional, Callable, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkNotificationBanner(CTkBaseClass):
    """
    Persistent notification banner that spans the full width of its container.
    Similar to browser notification bars — slides in from the top, remains visible
    until explicitly dismissed (or until an optional auto-dismiss timer fires).

    Unlike CTkToast (which auto-dismisses and floats), this widget is meant to be
    placed at the top of a frame/window and convey important persistent information
    with an optional action button.

    Styles: "info", "success", "warning", "error"

    Usage:
        banner = CTkNotificationBanner(
            parent,
            message="A new version is available!",
            style="info",
            action_text="Update Now",
            command=on_update,
            dismiss_command=on_dismiss,
            dismissible=True,
        )
        banner.show()   # slide in from top
        banner.dismiss() # slide out and destroy

    Auto-dismiss:
        banner = CTkNotificationBanner(parent, message="Saved!", style="success",
                                        auto_dismiss=3000)
        banner.show()
    """

    # ── Style definitions ──────────────────────────────────────────
    # Each style has (light_mode, dark_mode) color tuples for:
    #   fg       - banner background
    #   text     - message text and icon
    #   accent   - left stripe and action button background
    #   btn_text - action button text color
    #   border   - subtle border color

    _STYLE_COLORS = {
        "info": {
            "fg":       ("#dbeafe", "#1e3a5f"),
            "text":     ("#1e40af", "#93c5fd"),
            "accent":   ("#3b82f6", "#60a5fa"),
            "btn_text": ("#ffffff", "#1e3a5f"),
            "border":   ("#93c5fd", "#2563eb"),
        },
        "success": {
            "fg":       ("#dcfce7", "#14532d"),
            "text":     ("#166534", "#86efac"),
            "accent":   ("#22c55e", "#4ade80"),
            "btn_text": ("#ffffff", "#14532d"),
            "border":   ("#86efac", "#16a34a"),
        },
        "warning": {
            "fg":       ("#fef3c7", "#451a03"),
            "text":     ("#92400e", "#fcd34d"),
            "accent":   ("#f59e0b", "#fbbf24"),
            "btn_text": ("#ffffff", "#451a03"),
            "border":   ("#fcd34d", "#d97706"),
        },
        "error": {
            "fg":       ("#fee2e2", "#450a0a"),
            "text":     ("#991b1b", "#fca5a5"),
            "accent":   ("#ef4444", "#f87171"),
            "btn_text": ("#ffffff", "#450a0a"),
            "border":   ("#fca5a5", "#dc2626"),
        },
    }

    _STYLE_ICONS = {
        "info":    "\u2139",   # i in circle (information)
        "success": "\u2714",   # heavy check mark
        "warning": "\u26A0",   # warning sign
        "error":   "\u2716",   # heavy multiplication x
    }

    def __init__(self,
                 master: Any,
                 message: str = "",
                 style: str = "info",
                 action_text: Optional[str] = None,
                 command: Optional[Callable] = None,
                 dismiss_command: Optional[Callable] = None,
                 dismissible: bool = True,
                 auto_dismiss: int = 0,
                 show_icon: bool = True,
                 width: int = 0,
                 height: int = 44,
                 corner_radius: Optional[int] = None,

                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 accent_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 button_text_color: Optional[Union[str, Tuple[str, str]]] = None,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 icon_font: Optional[Union[tuple, CTkFont]] = None,
                 button_font: Optional[Union[tuple, CTkFont]] = None,
                 **kwargs):

        super().__init__(master=master, bg_color="transparent",
                         width=width, height=height, **kwargs)

        # ── Store parameters ────────────────────────────────────────
        self._style = style if style in self._STYLE_COLORS else "info"
        self._message = message
        self._action_text = action_text
        self._command = command
        self._dismiss_command = dismiss_command
        self._dismissible = dismissible
        self._auto_dismiss = auto_dismiss  # 0 = never, or ms
        self._show_icon = show_icon
        self._corner_radius = 6 if corner_radius is None else corner_radius

        # ── Resolve style colors (user overrides take priority) ─────
        style_cfg = self._STYLE_COLORS.get(self._style, self._STYLE_COLORS["info"])
        self._fg_color = fg_color or style_cfg["fg"]
        self._text_color = text_color or style_cfg["text"]
        self._accent_color = accent_color or style_cfg["accent"]
        self._border_color = border_color or style_cfg["border"]
        self._button_text_color = button_text_color or style_cfg["btn_text"]

        # ── Fonts ───────────────────────────────────────────────────
        self._font = CTkFont(size=13) if font is None else self._check_font_type(font)
        self._icon_font = CTkFont(size=15) if icon_font is None else self._check_font_type(icon_font)
        self._button_font = CTkFont(size=12, weight="bold") if button_font is None else self._check_font_type(button_font)

        # ── Animation state ─────────────────────────────────────────
        self._is_visible = False
        self._dismissed = False
        self._anim_after_id: Optional[str] = None
        self._auto_dismiss_after_id: Optional[str] = None
        self._target_height = height
        self._current_anim_height = 0  # start collapsed for slide-in

        # ── Grid setup ──────────────────────────────────────────────
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Canvas for rounded background ───────────────────────────
        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, sticky="nswe")
        self._draw_engine = DrawEngine(self._canvas)

        # ── Inner layout frame ──────────────────────────────────────
        fg_resolved = self._apply_appearance_mode(self._fg_color)
        self._inner = tkinter.Frame(self, bg=fg_resolved)
        self._inner.grid(row=0, column=0, sticky="nswe")
        self._inner.grid_rowconfigure(0, weight=1)
        # columns: stripe | icon | message (expanding) | action_btn | dismiss_btn
        self._inner.grid_columnconfigure(2, weight=1)

        # ── Accent stripe (left edge) ──────────────────────────────
        stripe_width = 4
        self._stripe = tkinter.Frame(
            self._inner,
            width=self._apply_widget_scaling(stripe_width),
            bg=self._apply_appearance_mode(self._accent_color),
        )
        self._stripe.grid(row=0, column=0, sticky="ns",
                          padx=(0, 0), pady=0)

        # ── Icon label ──────────────────────────────────────────────
        icon_text = self._STYLE_ICONS.get(self._style, "") if self._show_icon else ""
        self._icon_label = tkinter.Label(
            self._inner,
            text=icon_text,
            font=self._resolve_font(self._icon_font),
            fg=self._apply_appearance_mode(self._accent_color),
            bg=fg_resolved,
            anchor="center",
        )
        if self._show_icon:
            self._icon_label.grid(row=0, column=1, padx=(10, 4), pady=4, sticky="ns")

        # ── Message label ───────────────────────────────────────────
        self._message_label = tkinter.Label(
            self._inner,
            text=self._message,
            font=self._resolve_font(self._font),
            fg=self._apply_appearance_mode(self._text_color),
            bg=fg_resolved,
            anchor="w",
            justify="left",
            wraplength=0,  # will be updated on configure/resize
        )
        msg_padx_left = 10 if not self._show_icon else 0
        self._message_label.grid(row=0, column=2, padx=(msg_padx_left, 10),
                                 pady=4, sticky="nsw")

        # ── Action button (optional) ────────────────────────────────
        self._action_btn: Optional[tkinter.Label] = None
        if self._action_text:
            self._action_btn = tkinter.Label(
                self._inner,
                text=self._action_text,
                font=self._resolve_font(self._button_font),
                fg=self._apply_appearance_mode(self._button_text_color),
                bg=self._apply_appearance_mode(self._accent_color),
                padx=10,
                pady=2,
                cursor="hand2",
            )
            self._action_btn.grid(row=0, column=3, padx=(4, 6), pady=6, sticky="ns")
            self._action_btn.bind("<Button-1>", self._on_action_click)
            self._action_btn.bind("<Enter>", self._on_action_enter)
            self._action_btn.bind("<Leave>", self._on_action_leave)

        # ── Dismiss button (X) ──────────────────────────────────────
        self._close_btn: Optional[tkinter.Label] = None
        if self._dismissible:
            self._close_btn = tkinter.Label(
                self._inner,
                text="\u2715",
                font=("Arial", 11),
                fg=self._apply_appearance_mode(self._text_color),
                bg=fg_resolved,
                cursor="hand2",
                padx=4,
            )
            self._close_btn.grid(row=0, column=4, padx=(2, 8), pady=4, sticky="ns")
            self._close_btn.bind("<Button-1>", lambda e: self.dismiss())
            self._close_btn.bind("<Enter>", self._on_close_enter)
            self._close_btn.bind("<Leave>", self._on_close_leave)

        # ── Bottom border line ──────────────────────────────────────
        self._border_line = tkinter.Frame(
            self._inner,
            height=1,
            bg=self._apply_appearance_mode(self._border_color),
        )
        self._border_line.grid(row=1, column=0, columnspan=5, sticky="ew")

        # ── Initial draw ────────────────────────────────────────────
        self._draw()

    # ── Font helper ─────────────────────────────────────────────────

    def _resolve_font(self, font_obj) -> tuple:
        """Convert a CTkFont or tuple font to a tuple suitable for tkinter."""
        if isinstance(font_obj, CTkFont):
            return (font_obj.cget("family"), font_obj.cget("size"),
                    font_obj.cget("weight"))
        return font_obj

    # ── Color helpers ───────────────────────────────────────────────

    @staticmethod
    def _lerp_hex(c1: str, c2: str, t: float) -> str:
        """Linearly interpolate between two hex colors (#RRGGBB)."""
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        return f"#{int(r1 + (r2 - r1) * t):02x}{int(g1 + (g2 - g1) * t):02x}{int(b1 + (b2 - b1) * t):02x}"

    def _color_to_hex(self, color: str) -> str:
        """Resolve any tkinter color string to a #RRGGBB hex string."""
        if color.startswith("#") and len(color) == 7:
            return color
        try:
            r, g, b = self.winfo_rgb(color)
            return f"#{r >> 8:02x}{g >> 8:02x}{b >> 8:02x}"
        except Exception:
            return "#333333"

    # ── Hover effects ───────────────────────────────────────────────

    def _on_action_click(self, event=None):
        """Handle action button click."""
        if self._command is not None:
            self._command()

    def _on_action_enter(self, event=None):
        """Darken action button on hover."""
        if self._action_btn is None:
            return
        accent_hex = self._color_to_hex(self._apply_appearance_mode(self._accent_color))
        darker = self._lerp_hex(accent_hex, "#000000", 0.15)
        self._action_btn.configure(bg=darker)

    def _on_action_leave(self, event=None):
        """Restore action button color on leave."""
        if self._action_btn is None:
            return
        self._action_btn.configure(bg=self._apply_appearance_mode(self._accent_color))

    def _on_close_enter(self, event=None):
        """Highlight close button on hover."""
        if self._close_btn is None:
            return
        accent_hex = self._color_to_hex(self._apply_appearance_mode(self._accent_color))
        self._close_btn.configure(fg=accent_hex)

    def _on_close_leave(self, event=None):
        """Restore close button color on leave."""
        if self._close_btn is None:
            return
        self._close_btn.configure(fg=self._apply_appearance_mode(self._text_color))

    # ── Drawing ─────────────────────────────────────────────────────

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        if not self._canvas.winfo_exists():
            return

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(
            self._apply_widget_scaling(self._current_width),
            self._apply_widget_scaling(self._current_height),
            self._apply_widget_scaling(self._corner_radius),
            0)

        if no_color_updates is False or requires_recoloring:
            fg = self._apply_appearance_mode(self._fg_color)
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._canvas.itemconfig("inner_parts", fill=fg, outline=fg)

            self._inner.configure(bg=fg)
            self._icon_label.configure(
                bg=fg,
                fg=self._apply_appearance_mode(self._accent_color),
            )
            self._message_label.configure(
                bg=fg,
                fg=self._apply_appearance_mode(self._text_color),
            )
            self._stripe.configure(bg=self._apply_appearance_mode(self._accent_color))
            self._border_line.configure(bg=self._apply_appearance_mode(self._border_color))

            if self._action_btn is not None:
                self._action_btn.configure(
                    bg=self._apply_appearance_mode(self._accent_color),
                    fg=self._apply_appearance_mode(self._button_text_color),
                )
            if self._close_btn is not None:
                self._close_btn.configure(
                    bg=fg,
                    fg=self._apply_appearance_mode(self._text_color),
                )

    # ── Animation ───────────────────────────────────────────────────

    def _cancel_animation(self):
        """Cancel any running slide animation."""
        if self._anim_after_id is not None:
            self.after_cancel(self._anim_after_id)
            self._anim_after_id = None

    @staticmethod
    def _ease_out_cubic(t: float) -> float:
        """Ease-out cubic easing function for smooth deceleration."""
        return 1.0 - (1.0 - t) ** 3

    @staticmethod
    def _ease_in_cubic(t: float) -> float:
        """Ease-in cubic easing function for smooth acceleration."""
        return t ** 3

    def _animate_slide_in(self, start_ms: int, duration_ms: int = 250):
        """Animate the banner sliding in from the top (height 0 -> target)."""
        elapsed = int(time.time() * 1000) - start_ms
        if elapsed < 0:
            elapsed = 0

        if elapsed >= duration_ms:
            # final frame: full height
            self._current_anim_height = self._target_height
            self._apply_anim_height(self._target_height)
            self._anim_after_id = None
            self._is_visible = True
            # schedule auto-dismiss if configured
            if self._auto_dismiss > 0:
                self._auto_dismiss_after_id = self.after(
                    self._auto_dismiss, self.dismiss
                )
            return

        t = self._ease_out_cubic(elapsed / duration_ms)
        h = int(self._target_height * t)
        self._current_anim_height = h
        self._apply_anim_height(h)

        self._anim_after_id = self.after(
            16, self._animate_slide_in, start_ms, duration_ms
        )

    def _animate_slide_out(self, start_ms: int, duration_ms: int = 200):
        """Animate the banner sliding out to the top (current height -> 0)."""
        elapsed = int(time.time() * 1000) - start_ms
        if elapsed < 0:
            elapsed = 0

        if elapsed >= duration_ms:
            # final frame: fully collapsed
            self._apply_anim_height(0)
            self._anim_after_id = None
            self._cleanup()
            return

        t = self._ease_in_cubic(elapsed / duration_ms)
        h = int(self._target_height * (1.0 - t))
        self._current_anim_height = h
        self._apply_anim_height(h)

        self._anim_after_id = self.after(
            16, self._animate_slide_out, start_ms, duration_ms
        )

    def _apply_anim_height(self, h: int):
        """Apply the animated height by configuring the tkinter frame directly."""
        scaled_h = max(1, self._apply_widget_scaling(h)) if h > 0 else 1
        try:
            # use tkinter.Frame.configure to bypass CTkBaseClass dimension tracking
            tkinter.Frame.configure(self, height=int(scaled_h))
        except Exception:
            pass

    # ── Public API ──────────────────────────────────────────────────

    def show(self):
        """
        Show the banner with a slide-in animation from the top.
        Typically pack/grid the banner at the top of a container before calling show().
        """
        if self._is_visible or self._dismissed:
            return

        self._cancel_animation()

        # start with zero height
        self._current_anim_height = 0
        self._apply_anim_height(0)

        # begin slide-in
        start_ms = int(time.time() * 1000)
        self._animate_slide_in(start_ms, 250)

    def dismiss(self, immediate: bool = False):
        """
        Dismiss the banner with a slide-out animation.
        If immediate=True, skip the animation and destroy immediately.
        """
        if self._dismissed:
            return
        self._dismissed = True

        # cancel any pending auto-dismiss
        if self._auto_dismiss_after_id is not None:
            self.after_cancel(self._auto_dismiss_after_id)
            self._auto_dismiss_after_id = None

        self._cancel_animation()

        if immediate:
            self._cleanup()
        else:
            start_ms = int(time.time() * 1000)
            self._animate_slide_out(start_ms, 200)

    def _cleanup(self):
        """Remove the banner and invoke the dismiss callback."""
        # fire dismiss callback
        if self._dismiss_command is not None:
            try:
                self._dismiss_command()
            except Exception:
                pass

        try:
            self.pack_forget()
        except Exception:
            pass
        try:
            self.grid_forget()
        except Exception:
            pass
        try:
            self.place_forget()
        except Exception:
            pass

        try:
            self.destroy()
        except Exception:
            pass

    def set_message(self, message: str):
        """Update the banner message text."""
        self._message = message
        self._message_label.configure(text=self._message)

    def set_style(self, style: str):
        """Change the banner style (info, success, warning, error) with immediate redraw."""
        if style not in self._STYLE_COLORS:
            return
        self._style = style
        style_cfg = self._STYLE_COLORS[self._style]
        self._fg_color = style_cfg["fg"]
        self._text_color = style_cfg["text"]
        self._accent_color = style_cfg["accent"]
        self._button_text_color = style_cfg["btn_text"]
        self._border_color = style_cfg["border"]

        # update icon
        if self._show_icon:
            self._icon_label.configure(text=self._STYLE_ICONS.get(self._style, ""))

        self._draw()

    # ── Scaling ─────────────────────────────────────────────────────

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    # ── Configure / cget ────────────────────────────────────────────

    def configure(self, **kwargs):
        require_redraw = False

        if "message" in kwargs:
            self._message = kwargs.pop("message")
            self._message_label.configure(text=self._message)

        if "style" in kwargs:
            self.set_style(kwargs.pop("style"))

        if "action_text" in kwargs:
            new_text = kwargs.pop("action_text")
            self._action_text = new_text
            if self._action_btn is not None:
                if new_text:
                    self._action_btn.configure(text=new_text)
                else:
                    self._action_btn.grid_forget()
                    self._action_btn = None
            elif new_text:
                # create the action button if it didn't exist
                fg_resolved = self._apply_appearance_mode(self._fg_color)
                self._action_btn = tkinter.Label(
                    self._inner,
                    text=new_text,
                    font=self._resolve_font(self._button_font),
                    fg=self._apply_appearance_mode(self._button_text_color),
                    bg=self._apply_appearance_mode(self._accent_color),
                    padx=10,
                    pady=2,
                    cursor="hand2",
                )
                self._action_btn.grid(row=0, column=3, padx=(4, 6), pady=6, sticky="ns")
                self._action_btn.bind("<Button-1>", self._on_action_click)
                self._action_btn.bind("<Enter>", self._on_action_enter)
                self._action_btn.bind("<Leave>", self._on_action_leave)

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "dismiss_command" in kwargs:
            self._dismiss_command = kwargs.pop("dismiss_command")

        if "dismissible" in kwargs:
            self._dismissible = kwargs.pop("dismissible")
            if self._dismissible and self._close_btn is None:
                fg_resolved = self._apply_appearance_mode(self._fg_color)
                self._close_btn = tkinter.Label(
                    self._inner,
                    text="\u2715",
                    font=("Arial", 11),
                    fg=self._apply_appearance_mode(self._text_color),
                    bg=fg_resolved,
                    cursor="hand2",
                    padx=4,
                )
                self._close_btn.grid(row=0, column=4, padx=(2, 8), pady=4, sticky="ns")
                self._close_btn.bind("<Button-1>", lambda e: self.dismiss())
                self._close_btn.bind("<Enter>", self._on_close_enter)
                self._close_btn.bind("<Leave>", self._on_close_leave)
            elif not self._dismissible and self._close_btn is not None:
                self._close_btn.grid_forget()
                self._close_btn.destroy()
                self._close_btn = None

        if "auto_dismiss" in kwargs:
            self._auto_dismiss = kwargs.pop("auto_dismiss")

        if "show_icon" in kwargs:
            self._show_icon = kwargs.pop("show_icon")
            if self._show_icon:
                self._icon_label.configure(
                    text=self._STYLE_ICONS.get(self._style, "")
                )
                self._icon_label.grid(row=0, column=1, padx=(10, 4), pady=4, sticky="ns")
            else:
                self._icon_label.grid_forget()

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "accent_color" in kwargs:
            self._accent_color = self._check_color_type(kwargs.pop("accent_color"))
            require_redraw = True

        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "button_text_color" in kwargs:
            self._button_text_color = self._check_color_type(kwargs.pop("button_text_color"))
            require_redraw = True

        if "font" in kwargs:
            self._font = self._check_font_type(kwargs.pop("font"))
            self._message_label.configure(font=self._resolve_font(self._font))

        if "icon_font" in kwargs:
            self._icon_font = self._check_font_type(kwargs.pop("icon_font"))
            self._icon_label.configure(font=self._resolve_font(self._icon_font))

        if "button_font" in kwargs:
            self._button_font = self._check_font_type(kwargs.pop("button_font"))
            if self._action_btn is not None:
                self._action_btn.configure(font=self._resolve_font(self._button_font))

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "message":
            return self._message
        elif attribute_name == "style":
            return self._style
        elif attribute_name == "action_text":
            return self._action_text
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "dismiss_command":
            return self._dismiss_command
        elif attribute_name == "dismissible":
            return self._dismissible
        elif attribute_name == "auto_dismiss":
            return self._auto_dismiss
        elif attribute_name == "show_icon":
            return self._show_icon
        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "accent_color":
            return self._accent_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "button_text_color":
            return self._button_text_color
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "icon_font":
            return self._icon_font
        elif attribute_name == "button_font":
            return self._button_font
        else:
            return super().cget(attribute_name)

    # ── Cleanup ─────────────────────────────────────────────────────

    def destroy(self):
        """Cancel all pending timers before destroying the widget."""
        self._cancel_animation()
        if self._auto_dismiss_after_id is not None:
            self.after_cancel(self._auto_dismiss_after_id)
            self._auto_dismiss_after_id = None
        super().destroy()
