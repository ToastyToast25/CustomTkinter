import tkinter
from typing import Union, Tuple, Optional, Callable, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .ctk_frame import CTkFrame
from .ctk_label import CTkLabel
from .font import CTkFont


class CTkCollapsibleFrame(CTkFrame):
    """
    Collapsible/accordion frame with a clickable header that expands
    or collapses the content area with smooth animation.

    Usage:
        section = CTkCollapsibleFrame(parent, title="Settings")
        ctk.CTkLabel(section.content, text="Option 1").pack()
        ctk.CTkSwitch(section.content, text="Enable").pack()
    """

    def __init__(self,
                 master: Any,
                 title: str = "Section",
                 width: int = 300,
                 corner_radius: Optional[int] = None,
                 border_width: Optional[int] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 header_color: Optional[Union[str, Tuple[str, str]]] = None,
                 header_hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 title_color: Optional[Union[str, Tuple[str, str]]] = None,
                 arrow_color: Optional[Union[str, Tuple[str, str]]] = None,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 collapsed: bool = False,
                 animate: bool = True,
                 animation_duration: int = 200,
                 command: Optional[Callable] = None,
                 **kwargs):

        super().__init__(master=master, width=width, corner_radius=corner_radius,
                         border_width=border_width, bg_color=bg_color, fg_color=fg_color,
                         border_color=border_color, **kwargs)

        # colors
        self._header_color = header_color  # None = same as fg_color
        self._header_hover_color = header_hover_color or ("#d4d4d4", "#404040")
        self._title_color = title_color or ThemeManager.theme["CTkLabel"]["text_color"]
        self._arrow_color = arrow_color or self._title_color

        # state
        self._title = title
        self._collapsed = collapsed
        self._animate = animate
        self._animation_duration = max(50, animation_duration)
        self._command = command
        self._animating = False
        self._after_id = None

        # font
        self._title_font = font or CTkFont(weight="bold")

        # header frame
        self._header = tkinter.Frame(self, bg=self._apply_appearance_mode(
            self._header_color or self._fg_color))
        self._header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.grid_columnconfigure(0, weight=1)

        # arrow label
        self._arrow_label = tkinter.Label(
            self._header,
            text="\u25B6" if self._collapsed else "\u25BC",
            font=("Segoe UI", 10),
            fg=self._apply_appearance_mode(self._arrow_color),
            bg=self._apply_appearance_mode(self._header_color or self._fg_color),
            cursor="hand2"
        )
        self._arrow_label.pack(side="left", padx=(12, 4), pady=8)

        # title label
        self._title_label = tkinter.Label(
            self._header,
            text=self._title,
            font=self._title_font if isinstance(self._title_font, tuple) else (
                self._title_font.cget("family"), self._title_font.cget("size"),
                self._title_font.cget("weight")),
            fg=self._apply_appearance_mode(self._title_color),
            bg=self._apply_appearance_mode(self._header_color or self._fg_color),
            anchor="w",
            cursor="hand2"
        )
        self._title_label.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=8)

        # content frame (user adds widgets here)
        self._content_frame = CTkFrame(self, fg_color="transparent", corner_radius=0)
        if not self._collapsed:
            self._content_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))

        # bindings
        self._header.bind("<Button-1>", self._on_header_click)
        self._arrow_label.bind("<Button-1>", self._on_header_click)
        self._title_label.bind("<Button-1>", self._on_header_click)
        self._header.bind("<Enter>", self._on_header_enter)
        self._header.bind("<Leave>", self._on_header_leave)
        self._arrow_label.bind("<Enter>", self._on_header_enter)
        self._arrow_label.bind("<Leave>", self._on_header_leave)
        self._title_label.bind("<Enter>", self._on_header_enter)
        self._title_label.bind("<Leave>", self._on_header_leave)

    @property
    def content(self) -> CTkFrame:
        """The content frame where child widgets should be placed."""
        return self._content_frame

    def _on_header_click(self, event=None):
        """Toggle collapsed state."""
        if self._animating:
            return
        self.toggle()

    def _on_header_enter(self, event=None):
        """Hover effect on header."""
        hover_color = self._apply_appearance_mode(self._header_hover_color)
        self._header.configure(bg=hover_color)
        self._arrow_label.configure(bg=hover_color)
        self._title_label.configure(bg=hover_color)

    def _on_header_leave(self, event=None):
        """Remove hover effect."""
        base_color = self._apply_appearance_mode(self._header_color or self._fg_color)
        self._header.configure(bg=base_color)
        self._arrow_label.configure(bg=base_color)
        self._title_label.configure(bg=base_color)

    def toggle(self, animate: Optional[bool] = None):
        """Toggle between collapsed and expanded states."""
        if self._collapsed:
            self.expand(animate=animate)
        else:
            self.collapse(animate=animate)

    def expand(self, animate: Optional[bool] = None):
        """Expand the content area."""
        if not self._collapsed:
            return
        self._collapsed = False
        self._arrow_label.configure(text="\u25BC")
        self._content_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))

        if self._command is not None:
            self._command(self._collapsed)

    def collapse(self, animate: Optional[bool] = None):
        """Collapse the content area."""
        if self._collapsed:
            return
        self._collapsed = True
        self._arrow_label.configure(text="\u25B6")
        self._content_frame.grid_forget()

        if self._command is not None:
            self._command(self._collapsed)

    def is_collapsed(self) -> bool:
        """Return whether the frame is currently collapsed."""
        return self._collapsed

    def destroy(self):
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        super().destroy()

    def configure(self, **kwargs):
        if "title" in kwargs:
            self._title = kwargs.pop("title")
            self._title_label.configure(text=self._title)
        if "collapsed" in kwargs:
            collapsed = kwargs.pop("collapsed")
            if collapsed and not self._collapsed:
                self.collapse()
            elif not collapsed and self._collapsed:
                self.expand()
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "title_color" in kwargs:
            self._title_color = kwargs.pop("title_color")
            self._title_label.configure(fg=self._apply_appearance_mode(self._title_color))
        if "arrow_color" in kwargs:
            self._arrow_color = kwargs.pop("arrow_color")
            self._arrow_label.configure(fg=self._apply_appearance_mode(self._arrow_color))
        super().configure(**kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "title":
            return self._title
        elif attribute_name == "collapsed":
            return self._collapsed
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "title_color":
            return self._title_color
        elif attribute_name == "arrow_color":
            return self._arrow_color
        elif attribute_name == "animate":
            return self._animate
        else:
            return super().cget(attribute_name)
