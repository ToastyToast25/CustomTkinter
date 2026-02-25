import tkinter
from typing import Union, Tuple, Optional, Callable, Any, List

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkToast(CTkBaseClass):
    """
    Toast notification widget that floats on top of the parent window.
    Shows a message with a colored accent stripe, auto-dismisses after
    a configurable duration, and stacks when multiple toasts are active.

    Usage:
        CTkToast.show_toast(parent, "Operation completed", style="success")
    """

    # style -> (accent_color_light, accent_color_dark)
    _STYLE_COLORS = {
        "success": ("#2CC985", "#2CC985"),
        "info":    ("#3B8ED0", "#3B8ED0"),
        "warning": ("#E8A838", "#E8A838"),
        "error":   ("#E04545", "#E04545"),
    }

    # per-style default durations (ms)
    _STYLE_DURATIONS = {
        "success": 2500,
        "info": 3000,
        "warning": 4000,
        "error": 6000,
    }

    # active toasts per parent, for stacking
    _active_toasts: dict = {}  # maps id(parent) -> list of CTkToast

    def __init__(self,
                 master: Any,
                 message: str = "",
                 style: str = "info",
                 duration: Optional[int] = None,
                 show_close: Optional[bool] = None,
                 width: int = 340,
                 height: int = 48,
                 corner_radius: Optional[int] = None,
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 accent_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 font: Optional[Union[tuple, CTkFont]] = None,
                 command: Optional[Callable] = None,
                 max_visible: int = 3,
                 **kwargs):

        super().__init__(master=master, bg_color="transparent", width=width, height=height, **kwargs)

        # style
        self._style = style if style in self._STYLE_COLORS else "info"
        self._message = message
        self._command = command
        self._max_visible = max_visible
        self._dismissed = False

        # duration
        if duration is not None:
            self._duration = duration
        else:
            base = self._STYLE_DURATIONS.get(self._style, 3000)
            # add time for long messages
            extra = max(0, len(message) - 40) * 50
            self._duration = min(base + extra, 8000)

        self._show_close = show_close if show_close is not None else (self._style == "error")

        # colors
        default_accent = self._STYLE_COLORS.get(self._style, self._STYLE_COLORS["info"])
        self._fg_color = ThemeManager.theme["CTkFrame"]["fg_color"] if fg_color is None else self._check_color_type(fg_color)
        self._accent_color = default_accent if accent_color is None else self._check_color_type(accent_color)
        self._text_color = ThemeManager.theme["CTkLabel"]["text_color"] if text_color is None else self._check_color_type(text_color)

        # shape
        self._corner_radius = ThemeManager.theme["CTkFrame"]["corner_radius"] if corner_radius is None else corner_radius

        # font
        self._font = CTkFont(size=13) if font is None else self._check_font_type(font)

        # after IDs for cleanup
        self._dismiss_after_id = None
        self._fade_after_id = None
        self._current_alpha = 1.0

        # build UI
        self._canvas = CTkCanvas(master=self, highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._draw_engine = DrawEngine(self._canvas)

        # accent stripe (narrow colored bar on left)
        stripe_w = self._apply_widget_scaling(4)
        self._stripe = tkinter.Frame(self, width=stripe_w,
                                     bg=self._apply_appearance_mode(self._accent_color))
        self._stripe.place(x=self._apply_widget_scaling(2), y=self._apply_widget_scaling(6),
                           width=stripe_w,
                           height=self._apply_widget_scaling(self._desired_height - 12))

        # message label
        pad_left = self._apply_widget_scaling(14)
        pad_right = self._apply_widget_scaling(36 if self._show_close else 10)
        self._label = tkinter.Label(self,
                                    text=self._message,
                                    font=self._apply_font_scaling(self._font),
                                    fg=self._apply_appearance_mode(self._text_color),
                                    bg=self._apply_appearance_mode(self._fg_color),
                                    anchor="w",
                                    wraplength=int(self._apply_widget_scaling(width) - pad_left - pad_right))
        self._label.place(x=pad_left, y=0, relheight=1,
                          width=self._apply_widget_scaling(width) - pad_left - pad_right)

        # close button
        if self._show_close:
            self._close_btn = tkinter.Label(self,
                                            text="\u2715",
                                            font=("Arial", 10),
                                            fg=self._apply_appearance_mode(self._text_color),
                                            bg=self._apply_appearance_mode(self._fg_color),
                                            cursor="hand2")
            self._close_btn.place(relx=1.0, x=-self._apply_widget_scaling(24),
                                  rely=0.5, anchor="w",
                                  width=self._apply_widget_scaling(20),
                                  height=self._apply_widget_scaling(20))
            self._close_btn.bind("<Button-1>", lambda e: self.dismiss())
        else:
            self._close_btn = None

        self._draw()

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
            self._canvas.itemconfig("inner_parts",
                                    fill=self._apply_appearance_mode(self._fg_color),
                                    outline=self._apply_appearance_mode(self._fg_color))
            bg = self._apply_appearance_mode(self._fg_color)
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._label.configure(bg=bg, fg=self._apply_appearance_mode(self._text_color))
            self._stripe.configure(bg=self._apply_appearance_mode(self._accent_color))
            if self._close_btn is not None:
                self._close_btn.configure(bg=bg, fg=self._apply_appearance_mode(self._text_color))

    def show(self):
        """Show the toast, positioned at bottom-right of parent."""
        parent = self.master
        parent_id = id(parent)

        # register in active list
        if parent_id not in self._active_toasts:
            self._active_toasts[parent_id] = []
        active = self._active_toasts[parent_id]

        # evict oldest if over max
        while len(active) >= self._max_visible:
            oldest = active[0]
            oldest.dismiss(immediate=True)

        active.append(self)
        self._restack(parent_id)

        # schedule auto-dismiss
        if self._duration > 0:
            self._dismiss_after_id = self.after(self._duration, self.dismiss)

    def dismiss(self, immediate: bool = False):
        """Dismiss the toast, optionally skipping the fade animation."""
        if self._dismissed:
            return
        self._dismissed = True

        if self._dismiss_after_id is not None:
            self.after_cancel(self._dismiss_after_id)
            self._dismiss_after_id = None

        if immediate:
            self._cleanup()
        else:
            self._fade_out()

    def _fade_out(self, step: int = 0):
        """Simple fade: shrink height over 150ms then destroy."""
        total_steps = 6
        if step >= total_steps:
            self._cleanup()
            return
        progress = step / total_steps
        try:
            new_h = max(1, int(self._apply_widget_scaling(self._desired_height) * (1 - progress)))
            # use tkinter.Frame.place_configure to bypass CTkBaseClass height block
            tkinter.Frame.place_configure(self, height=new_h)
        except Exception:
            self._cleanup()
            return
        self._fade_after_id = self.after(25, self._fade_out, step + 1)

    def _cleanup(self):
        """Remove from active list and destroy."""
        if self._fade_after_id is not None:
            self.after_cancel(self._fade_after_id)
            self._fade_after_id = None

        parent_id = id(self.master)
        if parent_id in self._active_toasts:
            try:
                self._active_toasts[parent_id].remove(self)
            except ValueError:
                pass
            # restack remaining
            self._restack(parent_id)
            if not self._active_toasts[parent_id]:
                del self._active_toasts[parent_id]

        if self._command is not None:
            self._command()

        try:
            self.place_forget()
            self.destroy()
        except Exception:
            pass

    @classmethod
    def _restack(cls, parent_id):
        """Reposition all active toasts for a parent, stacking from bottom."""
        if parent_id not in cls._active_toasts:
            return
        active = cls._active_toasts[parent_id]
        margin = 10
        spacing = 6
        y_offset = margin
        for toast in reversed(active):
            h = toast._apply_widget_scaling(toast._desired_height)
            w = toast._apply_widget_scaling(toast._desired_width)
            # use tkinter.Frame.place directly to bypass CTkBaseClass width/height block
            tkinter.Frame.place(toast, in_=toast.master,
                                relx=1.0, rely=1.0,
                                x=-(w + margin),
                                y=-(y_offset + h),
                                width=w, height=h)
            toast.lift()
            y_offset += h + spacing

    def destroy(self):
        if self._dismiss_after_id is not None:
            self.after_cancel(self._dismiss_after_id)
            self._dismiss_after_id = None
        if self._fade_after_id is not None:
            self.after_cancel(self._fade_after_id)
            self._fade_after_id = None
        super().destroy()

    @classmethod
    def show_toast(cls, parent, message: str, style: str = "info", **kwargs) -> "CTkToast":
        """Convenience class method to create and show a toast in one call."""
        toast = cls(parent, message=message, style=style, **kwargs)
        toast.show()
        return toast

    def configure(self, **kwargs):
        if "message" in kwargs:
            self._message = kwargs.pop("message")
            self._label.configure(text=self._message)
        if "accent_color" in kwargs:
            self._accent_color = self._check_color_type(kwargs.pop("accent_color"))
            self._stripe.configure(bg=self._apply_appearance_mode(self._accent_color))
        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            self._label.configure(fg=self._apply_appearance_mode(self._text_color))
        super().configure(**kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "message":
            return self._message
        elif attribute_name == "style":
            return self._style
        elif attribute_name == "duration":
            return self._duration
        elif attribute_name == "accent_color":
            return self._accent_color
        elif attribute_name == "text_color":
            return self._text_color
        else:
            return super().cget(attribute_name)
