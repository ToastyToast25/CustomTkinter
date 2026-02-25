import tkinter
from typing import Union, Tuple, Optional, Callable, Any, List

from .theme import ThemeManager
from .font import CTkFont
from .ctk_button import CTkButton
from .ctk_label import CTkLabel
from .ctk_frame import CTkFrame
from .appearance_mode import AppearanceModeTracker


def _resolve_color(color):
    """Resolve a (light, dark) color tuple to a single value based on appearance mode."""
    if isinstance(color, (list, tuple)):
        mode = AppearanceModeTracker.appearance_mode
        return color[mode] if mode < len(color) else color[0]
    return color


class CTkDialog:
    """
    Modern styled dialog replacing tkinter.messagebox.
    Supports message, confirm, warning, error, and custom content dialogs.
    Blocks until the user responds (modal).

    Usage:
        result = CTkDialog.ask_yes_no(parent, title="Confirm", message="Delete this?")
        if result:
            do_something()

        CTkDialog.show_info(parent, title="Done", message="Operation completed.")
    """

    # style -> (icon, accent_color)
    _STYLE_CONFIG = {
        "info":    ("\u2139",  ("#3B8ED0", "#3B8ED0")),
        "success": ("\u2713",  ("#2CC985", "#2CC985")),
        "warning": ("\u26A0",  ("#E8A838", "#E8A838")),
        "error":   ("\u2717",  ("#E04545", "#E04545")),
        "question": ("\u003F", ("#3B8ED0", "#3B8ED0")),
    }

    # Stores suppression state for "don't show again" checkboxes, keyed by user-provided string.
    _suppressed: dict[str, bool] = {}

    def __init__(self,
                 parent: Any,
                 title: str = "Dialog",
                 message: str = "",
                 detail: str = "",
                 style: str = "info",
                 buttons: Optional[List[str]] = None,
                 default_button: Optional[str] = None,
                 icon: Optional[str] = None,
                 width: int = 400,
                 height: Optional[int] = None,
                 show_again_key: str = "",
                 _input_mode: bool = False,
                 _placeholder: str = "",
                 _default_value: str = ""):

        self._parent = parent
        self._result = None
        self._style = style
        self._buttons = buttons or ["OK"]
        self._default_button = default_button or self._buttons[-1]
        self._show_again_key = show_again_key
        self._input_mode = _input_mode
        self._input_value: Optional[str] = None

        # If this key is suppressed, skip building the dialog entirely.
        if show_again_key and self._suppressed.get(show_again_key, False):
            self._result = self._default_button
            self._window = None
            return

        style_config = self._STYLE_CONFIG.get(style, self._STYLE_CONFIG["info"])
        self._icon_text = icon or style_config[0]
        self._accent_color = style_config[1]

        # create toplevel
        self._window = tkinter.Toplevel(parent)
        self._window.title(title)
        self._window.resizable(False, False)
        self._window.transient(parent)

        # Start invisible for fade-in
        self._window.attributes("-alpha", 0.0)

        # styling
        bg = _resolve_color(ThemeManager.theme["CTk"]["fg_color"])
        self._window.configure(bg=bg)

        # icon + message area
        content_frame = tkinter.Frame(self._window, bg=bg)
        content_frame.pack(fill="both", expand=True, padx=24, pady=(20, 12))

        # accent icon
        text_color = _resolve_color(ThemeManager.theme["CTkLabel"]["text_color"])
        accent = _resolve_color(self._accent_color)

        icon_label = tkinter.Label(content_frame, text=self._icon_text,
                                   font=("Segoe UI", 28), fg=accent, bg=bg)
        icon_label.pack(side="left", padx=(0, 16), anchor="n")

        # text area
        text_frame = tkinter.Frame(content_frame, bg=bg)
        text_frame.pack(side="left", fill="both", expand=True)

        msg_label = tkinter.Label(text_frame, text=message,
                                  font=("Segoe UI", 13), fg=text_color, bg=bg,
                                  wraplength=width - 100, justify="left", anchor="w")
        msg_label.pack(fill="x", anchor="w")

        if detail:
            detail_color = _resolve_color(("#888888", "#999999"))
            detail_label = tkinter.Label(text_frame, text=detail,
                                         font=("Segoe UI", 11), fg=detail_color, bg=bg,
                                         wraplength=width - 100, justify="left", anchor="w")
            detail_label.pack(fill="x", anchor="w", pady=(6, 0))

        # Input field (for ask_input mode)
        if _input_mode:
            from .ctk_entry import CTkEntry
            self._entry = CTkEntry(
                self._window,
                width=width - 48,
                height=32,
                placeholder_text=_placeholder,
            )
            self._entry.pack(padx=24, pady=(0, 8))
            if _default_value:
                self._entry.insert(0, _default_value)

        # separator line
        sep_color = _resolve_color(("#d4d4d4", "#404040"))
        sep = tkinter.Frame(self._window, bg=sep_color, height=1)
        sep.pack(fill="x", padx=16, pady=(4, 0))

        # "Don't show again" checkbox
        self._dont_show_var: Optional[tkinter.BooleanVar] = None
        if show_again_key:
            from .ctk_checkbox import CTkCheckBox
            self._dont_show_var = tkinter.BooleanVar(value=False)
            checkbox_frame = tkinter.Frame(self._window, bg=bg)
            checkbox_frame.pack(fill="x", padx=16, pady=(8, 0))
            self._dont_show_cb = CTkCheckBox(
                checkbox_frame,
                text="Don't show this again",
                variable=self._dont_show_var,
                height=24,
                checkbox_width=18,
                checkbox_height=18,
                corner_radius=4,
            )
            self._dont_show_cb.pack(side="left")

        # button area
        btn_frame = tkinter.Frame(self._window, bg=bg)
        btn_frame.pack(fill="x", padx=16, pady=12)

        for btn_text in self._buttons:
            is_default = (btn_text == self._default_button)
            btn = CTkButton(
                btn_frame,
                text=btn_text,
                width=90,
                height=32,
                corner_radius=6,
                fg_color=accent if is_default else "transparent",
                hover_color=accent if is_default else ("#d4d4d4", "#404040"),
                text_color=("#ffffff", "#ffffff") if is_default else text_color,
                border_width=1 if not is_default else 0,
                border_color=("#c0c0c0", "#555555"),
                command=lambda t=btn_text: self._on_button(t)
            )
            btn.pack(side="right", padx=(6, 0))

        # key bindings
        self._window.bind("<Return>", lambda e: self._on_button(self._default_button))
        self._window.bind("<Escape>", lambda e: self._on_button(self._buttons[0]
                                                                  if len(self._buttons) == 1
                                                                  else "Cancel"
                                                                  if "Cancel" in self._buttons
                                                                  else self._buttons[0]))

        # center on parent
        self._window.update_idletasks()
        w = max(width, self._window.winfo_reqwidth())
        h = height or self._window.winfo_reqheight()
        px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        self._window.geometry(f"{w}x{h}+{max(0, px)}+{max(0, py)}")

        # make modal
        self._window.grab_set()
        self._window.focus_force()
        self._window.protocol("WM_DELETE_WINDOW", lambda: self._on_button(None))

        # Focus the entry if in input mode
        if _input_mode:
            self._entry.focus()

        # Fade-in animation: 0 -> 1 over 150ms
        self._fade_in(0.0, 150)

    def _fade_in(self, current_alpha: float, remaining_ms: int):
        """Animate the window opacity from current_alpha to 1.0 over remaining_ms."""
        step_ms = 15  # roughly 60fps
        if self._window is None:
            return
        try:
            if remaining_ms <= 0:
                self._window.attributes("-alpha", 1.0)
                return
            new_alpha = min(1.0, current_alpha + (step_ms / 150))
            self._window.attributes("-alpha", new_alpha)
            self._window.after(step_ms, self._fade_in, new_alpha, remaining_ms - step_ms)
        except Exception:
            # Window may have been destroyed during animation
            pass

    def _on_button(self, value):
        # Capture input value before destroying the window
        if self._input_mode and hasattr(self, "_entry"):
            try:
                self._input_value = self._entry.get()
            except Exception:
                self._input_value = None

        # Record suppression preference
        if self._show_again_key and self._dont_show_var is not None:
            try:
                if self._dont_show_var.get():
                    CTkDialog._suppressed[self._show_again_key] = True
            except Exception:
                pass

        self._result = value
        try:
            self._window.grab_release()
        except Exception:
            pass
        self._window.destroy()

    def get_result(self):
        """Block until dialog closes, return the button text clicked (or None)."""
        if self._window is None:
            # Dialog was suppressed; return the pre-set result immediately.
            return self._result
        self._window.wait_window()
        return self._result

    # --- Convenience class methods ---

    @classmethod
    def show_info(cls, parent, title: str = "Info", message: str = "", detail: str = ""):
        """Show an informational dialog with an OK button."""
        d = cls(parent, title=title, message=message, detail=detail,
                style="info", buttons=["OK"])
        return d.get_result()

    @classmethod
    def show_success(cls, parent, title: str = "Success", message: str = "", detail: str = ""):
        """Show a success dialog with an OK button."""
        d = cls(parent, title=title, message=message, detail=detail,
                style="success", buttons=["OK"])
        return d.get_result()

    @classmethod
    def show_warning(cls, parent, title: str = "Warning", message: str = "", detail: str = ""):
        """Show a warning dialog with an OK button."""
        d = cls(parent, title=title, message=message, detail=detail,
                style="warning", buttons=["OK"])
        return d.get_result()

    @classmethod
    def show_error(cls, parent, title: str = "Error", message: str = "", detail: str = ""):
        """Show an error dialog with an OK button."""
        d = cls(parent, title=title, message=message, detail=detail,
                style="error", buttons=["OK"])
        return d.get_result()

    @classmethod
    def ask_yes_no(cls, parent, title: str = "Confirm", message: str = "",
                   detail: str = "") -> bool:
        """Show a yes/no dialog. Returns True if 'Yes' was clicked."""
        d = cls(parent, title=title, message=message, detail=detail,
                style="question", buttons=["No", "Yes"], default_button="Yes")
        return d.get_result() == "Yes"

    @classmethod
    def ask_ok_cancel(cls, parent, title: str = "Confirm", message: str = "",
                      detail: str = "") -> bool:
        """Show an ok/cancel dialog. Returns True if 'OK' was clicked."""
        d = cls(parent, title=title, message=message, detail=detail,
                style="question", buttons=["Cancel", "OK"], default_button="OK")
        return d.get_result() == "OK"

    @classmethod
    def ask_retry_cancel(cls, parent, title: str = "Error", message: str = "",
                         detail: str = "") -> bool:
        """Show a retry/cancel dialog. Returns True if 'Retry' was clicked."""
        d = cls(parent, title=title, message=message, detail=detail,
                style="error", buttons=["Cancel", "Retry"], default_button="Retry")
        return d.get_result() == "Retry"

    @classmethod
    def ask_input(cls, parent, title: str = "Input", message: str = "",
                  detail: str = "", placeholder: str = "",
                  default_value: str = "") -> Optional[str]:
        """Show an input dialog with a text entry field.

        Returns the entered text if OK was clicked, None if cancelled.
        """
        d = cls(parent, title=title, message=message, detail=detail,
                style="question", buttons=["Cancel", "OK"], default_button="OK",
                _input_mode=True, _placeholder=placeholder,
                _default_value=default_value)
        result = d.get_result()
        if result == "OK":
            return d._input_value
        return None
