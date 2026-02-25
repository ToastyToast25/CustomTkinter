import tkinter
import webbrowser
from datetime import datetime
from typing import Union, Tuple, Optional, Any, Callable, List, Dict

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

    Features:
        - Semantic text styles: default, header, success, warning, error, info, muted, code, accent
        - Optional timestamps on each line
        - Line highlighting with background color
        - Search with match navigation (next/prev)
        - Clickable links (URLs or callbacks)
        - Batch insert for performance
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

    _HIGHLIGHT_COLOR = ("#fff3cd", "#3d3200")
    _SEARCH_HIGHLIGHT_COLOR = ("#fff176", "#665500")
    _SEARCH_ACTIVE_COLOR = ("#ff8a65", "#bf360c")

    def __init__(self,
                 master: Any,
                 width: int = 400,
                 height: int = 200,
                 header_font: Optional[Union[tuple, CTkFont]] = None,
                 code_font: Optional[Union[tuple, CTkFont]] = None,
                 auto_scroll: bool = True,
                 max_lines: int = 0,
                 show_timestamps: bool = False,
                 **kwargs):

        super().__init__(master=master, width=width, height=height, **kwargs)

        self._header_font = header_font or CTkFont(weight="bold", size=14)
        self._code_font = code_font or CTkFont(family="Consolas", size=12)
        self._auto_scroll = auto_scroll
        self._max_lines = max_lines  # 0 = unlimited
        self._line_count = 0
        self._show_timestamps = show_timestamps

        # link tracking
        self._link_counter = 0
        self._link_callbacks: Dict[str, Callable] = {}

        # search state
        self._search_matches: List[str] = []  # list of text indices for match starts
        self._search_pattern: str = ""
        self._search_current_index: int = -1  # index into _search_matches

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

        # timestamp tag
        timestamp_color = self._apply_appearance_mode(self._STYLE_COLORS["muted"])
        self.tag_config("timestamp", foreground=timestamp_color)

        # highlight tag (for line highlighting)
        highlight_bg = self._apply_appearance_mode(self._HIGHLIGHT_COLOR)
        self.tag_config("_line_highlight", background=highlight_bg)

        # search highlight tags
        search_bg = self._apply_appearance_mode(self._SEARCH_HIGHLIGHT_COLOR)
        self.tag_config("search_highlight", background=search_bg)

        active_bg = self._apply_appearance_mode(self._SEARCH_ACTIVE_COLOR)
        self.tag_config("_search_active", background=active_bg)

    # ─── Timestamps ──────────────────────────────────────────────────

    def _get_timestamp(self) -> str:
        """Return a formatted timestamp string."""
        return datetime.now().strftime("[%H:%M:%S] ")

    def _insert_with_timestamp(self, text: str, style: str, end: str):
        """Insert text with an optional timestamp prefix."""
        if self._show_timestamps:
            ts = self._get_timestamp()
            self.insert("end", ts, "timestamp")
        self.insert("end", text + end, style)

    # ─── Core text methods ───────────────────────────────────────────

    def add_text(self, text: str, style: str = "default", end: str = "\n"):
        """Add text with a semantic style."""
        self._enforce_max_lines()
        self.configure(state="normal")
        self._insert_with_timestamp(text, style, end)
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
        self._search_matches.clear()
        self._search_pattern = ""
        self._search_current_index = -1

    # ─── Line highlighting ───────────────────────────────────────────

    def highlight_line(self, line_number: int, color: Optional[Union[str, Tuple[str, str]]] = None):
        """Highlight a specific line with a background color.

        Args:
            line_number: 1-based line number to highlight.
            color: Background color as a hex string or (light, dark) tuple.
                   Defaults to a warm yellow highlight.
        """
        if color is not None:
            if isinstance(color, (list, tuple)):
                resolved = self._apply_appearance_mode(color)
            else:
                resolved = color
            # Create a per-color highlight tag so different lines can have different colors
            tag_name = f"_line_hl_{line_number}"
            self.tag_config(tag_name, background=resolved)
        else:
            tag_name = "_line_highlight"

        line_start = f"{line_number}.0"
        line_end = f"{line_number}.end"

        self.configure(state="normal")
        self.tag_add(tag_name, line_start, line_end)
        self.configure(state="disabled")

    def clear_highlights(self):
        """Remove all line highlights."""
        self.configure(state="normal")
        # Remove the default highlight tag from all text
        self.tag_remove("_line_highlight", "1.0", "end")
        # Remove any per-line highlight tags
        for tag_name in list(self.tag_names()):
            if isinstance(tag_name, str) and tag_name.startswith("_line_hl_"):
                self.tag_remove(tag_name, "1.0", "end")
                self.tag_delete(tag_name)
        self.configure(state="disabled")

    # ─── Search ──────────────────────────────────────────────────────

    def search_text(self, pattern: str, nocase: bool = True) -> int:
        """Highlight all occurrences of pattern in the text.

        Uses the tkinter.Text.search method for reliable text searching.

        Args:
            pattern: The text pattern to search for.
            nocase: If True, search is case-insensitive.

        Returns:
            The number of matches found.
        """
        self.clear_search()

        if not pattern:
            return 0

        self._search_pattern = pattern
        self._search_matches = []

        self.configure(state="normal")

        count_var = tkinter.IntVar()
        start_pos = "1.0"

        while True:
            pos = self._textbox.search(
                pattern, start_pos, stopindex="end",
                nocase=nocase, count=count_var
            )
            if not pos:
                break

            match_len = count_var.get()
            if match_len == 0:
                break

            end_pos = f"{pos}+{match_len}c"
            self.tag_add("search_highlight", pos, end_pos)
            self._search_matches.append(pos)

            # Advance past this match to avoid infinite loop
            start_pos = end_pos

        self.configure(state="disabled")

        if self._search_matches:
            self._search_current_index = -1

        return len(self._search_matches)

    def clear_search(self):
        """Remove all search highlights and reset search state."""
        self.configure(state="normal")
        self.tag_remove("search_highlight", "1.0", "end")
        self.tag_remove("_search_active", "1.0", "end")
        self.configure(state="disabled")
        self._search_matches.clear()
        self._search_pattern = ""
        self._search_current_index = -1

    def search_next(self) -> Optional[str]:
        """Navigate to the next search match.

        Scrolls to and highlights the next match with an active indicator.

        Returns:
            The text index of the active match, or None if no matches.
        """
        if not self._search_matches:
            return None

        # Remove previous active highlight
        self.configure(state="normal")
        self.tag_remove("_search_active", "1.0", "end")

        self._search_current_index += 1
        if self._search_current_index >= len(self._search_matches):
            self._search_current_index = 0

        pos = self._search_matches[self._search_current_index]
        match_len = len(self._search_pattern)
        end_pos = f"{pos}+{match_len}c"

        self.tag_add("_search_active", pos, end_pos)
        self.configure(state="disabled")

        self.see(pos)
        return pos

    def search_prev(self) -> Optional[str]:
        """Navigate to the previous search match.

        Scrolls to and highlights the previous match with an active indicator.

        Returns:
            The text index of the active match, or None if no matches.
        """
        if not self._search_matches:
            return None

        # Remove previous active highlight
        self.configure(state="normal")
        self.tag_remove("_search_active", "1.0", "end")

        self._search_current_index -= 1
        if self._search_current_index < 0:
            self._search_current_index = len(self._search_matches) - 1

        pos = self._search_matches[self._search_current_index]
        match_len = len(self._search_pattern)
        end_pos = f"{pos}+{match_len}c"

        self.tag_add("_search_active", pos, end_pos)
        self.configure(state="disabled")

        self.see(pos)
        return pos

    # ─── Clickable links ─────────────────────────────────────────────

    def add_link(self,
                 text: str,
                 url_or_callback: Union[str, Callable],
                 style: str = "info",
                 end: str = "\n"):
        """Add clickable link text.

        If url_or_callback is a string starting with "http", clicking
        opens it in the default browser. If it is a callable, it is
        invoked on click.

        Args:
            text: The visible link text.
            url_or_callback: URL string or callback function.
            style: Semantic style for the link color (default "info").
            end: Trailing character (default newline).
        """
        tag_name = f"_link_{self._link_counter}"
        self._link_counter += 1

        # Resolve the foreground color from the style
        colors = self._STYLE_COLORS.get(style, self._STYLE_COLORS["info"])
        fg_color = self._apply_appearance_mode(colors) if isinstance(colors, (list, tuple)) else colors

        # Configure the link tag with underline and color
        self.tag_config(tag_name, foreground=fg_color, underline=True)

        # Set the hand cursor on hover
        self.tag_bind(tag_name, "<Enter>", lambda e: self._textbox.configure(cursor="hand2"))
        self.tag_bind(tag_name, "<Leave>", lambda e: self._textbox.configure(cursor=""))

        # Determine the click action
        if isinstance(url_or_callback, str) and url_or_callback.startswith("http"):
            url = url_or_callback
            callback = lambda e, u=url: webbrowser.open(u)
        elif callable(url_or_callback):
            cb = url_or_callback
            callback = lambda e, c=cb: c()
        else:
            # Treat non-http strings as plain text with no action
            callback = None

        if callback is not None:
            self.tag_bind(tag_name, "<Button-1>", callback)

        self._enforce_max_lines()
        self.configure(state="normal")
        if self._show_timestamps:
            ts = self._get_timestamp()
            self.insert("end", ts, "timestamp")
        self.insert("end", text + end, tag_name)
        self.configure(state="disabled")
        self._line_count += text.count("\n") + (1 if end == "\n" else 0)
        if self._auto_scroll:
            self.see("end")

    # ─── Batch insert ─────────────────────────────────────────────────

    def add_batch(self, items: List[Dict[str, Any]]):
        """Insert multiple items at once for better performance.

        Uses a single state normal/disabled cycle to avoid repeated
        state toggling overhead.

        Each item is a dict that may contain:
            - "text" (str, required): The text content.
            - "style" (str, optional): Semantic style name (default "default").
            - "end" (str, optional): Trailing character (default "\\n").
            - "type" (str, optional): "text" (default), "link", "header",
              "separator".
            - "url_or_callback" (str|callable, optional): For type="link".

        Example:
            rtb.add_batch([
                {"text": "Process started", "style": "info"},
                {"text": "Step 1 complete", "style": "success"},
                {"text": "See docs", "type": "link", "url_or_callback": "https://example.com"},
                {"text": "Warning: low memory", "style": "warning"},
            ])
        """
        if not items:
            return

        self.configure(state="normal")

        for item in items:
            text = item.get("text", "")
            style = item.get("style", "default")
            end = item.get("end", "\n")
            item_type = item.get("type", "text")

            self._enforce_max_lines()

            if item_type == "link":
                url_or_callback = item.get("url_or_callback")
                # Use the internal link setup without state toggling
                self._insert_link_no_state(text, url_or_callback, style, end)
            elif item_type == "header":
                if self._show_timestamps:
                    self.insert("end", self._get_timestamp(), "timestamp")
                self.insert("end", text + end, "header")
            elif item_type == "separator":
                char = item.get("char", "\u2500")
                width = item.get("width", 40)
                self.insert("end", char * width + end, "muted")
            else:
                # Standard text
                if self._show_timestamps:
                    self.insert("end", self._get_timestamp(), "timestamp")
                self.insert("end", text + end, style)

            self._line_count += text.count("\n") + (1 if end == "\n" else 0)

        self.configure(state="disabled")

        if self._auto_scroll:
            self.see("end")

    def _insert_link_no_state(self, text: str, url_or_callback, style: str, end: str):
        """Insert a link without toggling state (for use inside batch operations)."""
        tag_name = f"_link_{self._link_counter}"
        self._link_counter += 1

        colors = self._STYLE_COLORS.get(style, self._STYLE_COLORS["info"])
        fg_color = self._apply_appearance_mode(colors) if isinstance(colors, (list, tuple)) else colors

        self.tag_config(tag_name, foreground=fg_color, underline=True)
        self.tag_bind(tag_name, "<Enter>", lambda e: self._textbox.configure(cursor="hand2"))
        self.tag_bind(tag_name, "<Leave>", lambda e: self._textbox.configure(cursor=""))

        if isinstance(url_or_callback, str) and url_or_callback.startswith("http"):
            url = url_or_callback
            self.tag_bind(tag_name, "<Button-1>", lambda e, u=url: webbrowser.open(u))
        elif callable(url_or_callback):
            cb = url_or_callback
            self.tag_bind(tag_name, "<Button-1>", lambda e, c=cb: c())

        if self._show_timestamps:
            self.insert("end", self._get_timestamp(), "timestamp")
        self.insert("end", text + end, tag_name)

    # ─── Max lines enforcement ────────────────────────────────────────

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

    # ─── configure / cget ─────────────────────────────────────────────

    def configure(self, **kwargs):
        if "auto_scroll" in kwargs:
            self._auto_scroll = kwargs.pop("auto_scroll")
        if "max_lines" in kwargs:
            self._max_lines = kwargs.pop("max_lines")
        if "show_timestamps" in kwargs:
            self._show_timestamps = kwargs.pop("show_timestamps")
        super().configure(**kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "auto_scroll":
            return self._auto_scroll
        elif attribute_name == "max_lines":
            return self._max_lines
        elif attribute_name == "show_timestamps":
            return self._show_timestamps
        else:
            return super().cget(attribute_name)
