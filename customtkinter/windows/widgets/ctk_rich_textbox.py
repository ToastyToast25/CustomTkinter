import tkinter
from typing import Union, Tuple, Optional, Any

from .ctk_textbox import CTkTextbox
from .font import CTkFont


class CTkRichTextbox(CTkTextbox):
    """
    Enhanced CTkTextbox with built-in semantic text styling.
    Provides convenience methods for adding colored, styled text
    without manual tag configuration.

    Usage:
        rtb = CTkRichTextbox(parent, width=400, height=300)
        rtb.add_header("Process Log")
        rtb.add_text("Download started...", style="info")
        rtb.add_text("Completed!", style="success")
        rtb.add_text("WARNING: low disk space", style="warning")
        rtb.add_text("ERROR: file not found", style="error")
    """

    # style -> (light_color, dark_color)
    _STYLE_COLORS = {
        "default": ("#1a1a1a", "#dce4ee"),
        "header":  ("#1e40af", "#60a5fa"),
        "success": ("#166534", "#4ade80"),
        "warning": ("#92400e", "#fbbf24"),
        "error":   ("#991b1b", "#f87171"),
        "info":    ("#1d4ed8", "#93c5fd"),
        "muted":   ("#6b7280", "#6b7280"),
        "code":    ("#7c3aed", "#c4b5fd"),
        "accent":  ("#3B8ED0", "#3B8ED0"),
    }

    def __init__(self,
                 master: Any,
                 width: int = 400,
                 height: int = 200,
                 header_font: Optional[Union[tuple, CTkFont]] = None,
                 code_font: Optional[Union[tuple, CTkFont]] = None,
                 auto_scroll: bool = True,
                 max_lines: int = 0,
                 **kwargs):

        super().__init__(master=master, width=width, height=height, **kwargs)

        self._header_font = header_font or CTkFont(weight="bold", size=14)
        self._code_font = code_font or CTkFont(family="Consolas", size=12)
        self._auto_scroll = auto_scroll
        self._max_lines = max_lines  # 0 = unlimited
        self._line_count = 0

        # configure built-in tags
        self._setup_tags()

    def _setup_tags(self):
        """Configure all built-in semantic tags."""
        for style_name, colors in self._STYLE_COLORS.items():
            color = self._apply_appearance_mode(colors) if isinstance(colors, (list, tuple)) else colors
            self.tag_config(style_name, foreground=color)

        # special font tags
        self.tag_config("header", font=self._header_font)
        self.tag_config("code", font=self._code_font)

        # bold and italic modifiers
        self.tag_config("bold", font=CTkFont(weight="bold"))
        self.tag_config("italic", font=CTkFont(slant="italic"))

    def add_text(self, text: str, style: str = "default", end: str = "\n"):
        """Add text with a semantic style."""
        self._enforce_max_lines()
        self.configure(state="normal")
        self.insert("end", text + end, style)
        self.configure(state="disabled")
        self._line_count += text.count("\n") + (1 if end == "\n" else 0)
        if self._auto_scroll:
            self.see("end")

    def add_header(self, text: str, end: str = "\n"):
        """Add header-styled text (bold, accent color)."""
        self.add_text(text, style="header", end=end)

    def add_success(self, text: str, end: str = "\n"):
        """Add success-styled text (green)."""
        self.add_text(text, style="success", end=end)

    def add_warning(self, text: str, end: str = "\n"):
        """Add warning-styled text (orange/yellow)."""
        self.add_text(text, style="warning", end=end)

    def add_error(self, text: str, end: str = "\n"):
        """Add error-styled text (red)."""
        self.add_text(text, style="error", end=end)

    def add_info(self, text: str, end: str = "\n"):
        """Add info-styled text (blue)."""
        self.add_text(text, style="info", end=end)

    def add_muted(self, text: str, end: str = "\n"):
        """Add muted-styled text (gray)."""
        self.add_text(text, style="muted", end=end)

    def add_code(self, text: str, end: str = "\n"):
        """Add code-styled text (monospace, purple)."""
        self.add_text(text, style="code", end=end)

    def add_separator(self, char: str = "\u2500", width: int = 40):
        """Add a visual separator line."""
        self.add_text(char * width, style="muted")

    def clear(self):
        """Clear all text content."""
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.configure(state="disabled")
        self._line_count = 0

    def _enforce_max_lines(self):
        """Remove oldest lines if max_lines is exceeded."""
        if self._max_lines <= 0:
            return

        while self._line_count >= self._max_lines:
            self.configure(state="normal")
            self.delete("1.0", "2.0")
            self.configure(state="disabled")
            self._line_count -= 1

    def get_line_count(self) -> int:
        """Return the approximate number of lines."""
        return self._line_count

    def configure(self, **kwargs):
        if "auto_scroll" in kwargs:
            self._auto_scroll = kwargs.pop("auto_scroll")
        if "max_lines" in kwargs:
            self._max_lines = kwargs.pop("max_lines")
        super().configure(**kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "auto_scroll":
            return self._auto_scroll
        elif attribute_name == "max_lines":
            return self._max_lines
        else:
            return super().cget(attribute_name)
