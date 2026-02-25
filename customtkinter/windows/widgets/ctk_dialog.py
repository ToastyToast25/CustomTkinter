import tkinter
from typing import Union, Tuple, Optional, Callable, Any, List

from .theme import ThemeManager
from .font import CTkFont
from .ctk_button import CTkButton
from .ctk_label import CTkLabel
from .ctk_frame import CTkFrame


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
                 height: Optional[int] = None):

        self._parent = parent
        self._result = None
        self._style = style
        self._buttons = buttons or ["OK"]
        self._default_button = default_button or self._buttons[-1]

        style_config = self._STYLE_CONFIG.get(style, self._STYLE_CONFIG["info"])
        self._icon_text = icon or style_config[0]
        self._accent_color = style_config[1]

        # create toplevel
        self._window = tkinter.Toplevel(parent)
        self._window.title(title)
        self._window.resizable(False, False)
        self._window.transient(parent)

        # styling
        bg = ThemeManager.theme["CTk"]["fg_color"]
        if isinstance(bg, (list, tuple)):
            from .appearance_mode import AppearanceModeTracker
            mode = AppearanceModeTracker.appearance_mode
            bg = bg[mode] if mode < len(bg) else bg[0]
        self._window.configure(bg=bg)

        # icon + message area
        content_frame = tkinter.Frame(self._window, bg=bg)
        content_frame.pack(fill="both", expand=True, padx=24, pady=(20, 12))

        # accent icon
        text_color = ThemeManager.theme["CTkLabel"]["text_color"]
        if isinstance(text_color, (list, tuple)):
            from .appearance_mode import AppearanceModeTracker
            mode = AppearanceModeTracker.appearance_mode
            text_color = text_color[mode] if mode < len(text_color) else text_color[0]

        accent = self._accent_color
        if isinstance(accent, (list, tuple)):
            from .appearance_mode import AppearanceModeTracker
            mode = AppearanceModeTracker.appearance_mode
            accent = accent[mode] if mode < len(accent) else accent[0]

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
            detail_label = tkinter.Label(text_frame, text=detail,
                                         font=("Segoe UI", 11), fg="#888888", bg=bg,
                                         wraplength=width - 100, justify="left", anchor="w")
            detail_label.pack(fill="x", anchor="w", pady=(6, 0))

        # separator line
        sep = tkinter.Frame(self._window, bg="#404040", height=1)
        sep.pack(fill="x", padx=16, pady=(4, 0))

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

    def _on_button(self, value):
        self._result = value
        try:
            self._window.grab_release()
        except Exception:
            pass
        self._window.destroy()

    def get_result(self):
        """Block until dialog closes, return the button text clicked (or None)."""
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
