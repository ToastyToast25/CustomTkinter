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

    # Arrow characters: right-pointing (collapsed), down-pointing (expanded)
    _ARROW_COLLAPSED = "\u25B6"
    _ARROW_EXPANDED = "\u25BC"
    _LOCK_ICON = "\U0001F512"

    # Animation targeting ~60fps
    _ANIM_INTERVAL_MS = 16

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
                 lock: bool = False,
                 **kwargs):

        super().__init__(master=master, width=width, corner_radius=corner_radius,
                         border_width=border_width, bg_color=bg_color, fg_color=fg_color,
                         border_color=border_color, **kwargs)

        # colors
        self._header_color = header_color  # None = same as fg_color
        self._header_hover_color = header_hover_color or ("#d4d4d4", "#404040")
        self._title_color = title_color or ThemeManager.theme["CTkLabel"]["text_color"]
        self._arrow_color = arrow_color or self._title_color

        # focus ring color: a visible outline color for keyboard focus
        self._focus_color = ("#1f6aa5", "#1f6aa5")

        # state
        self._title = title
        self._collapsed = collapsed
        self._animate = animate
        self._animation_duration = max(50, animation_duration)
        self._command = command
        self._animating = False
        self._after_id = None
        self._lock = lock

        # font
        self._title_font = font or CTkFont(weight="bold")

        # header frame - use takefocus=1 for keyboard accessibility
        header_bg = self._apply_appearance_mode(self._header_color or self._fg_color)
        self._header = tkinter.Frame(self, bg=header_bg, takefocus=1,
                                     highlightthickness=2,
                                     highlightcolor=self._apply_appearance_mode(self._focus_color),
                                     highlightbackground=header_bg)
        self._header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.grid_columnconfigure(0, weight=1)

        # arrow label
        self._arrow_label = tkinter.Label(
            self._header,
            text=self._ARROW_COLLAPSED if self._collapsed else self._ARROW_EXPANDED,
            font=("Segoe UI", 10),
            fg=self._apply_appearance_mode(self._arrow_color),
            bg=header_bg,
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
            bg=header_bg,
            anchor="w",
            cursor="hand2"
        )
        self._title_label.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=8)

        # lock icon label (shown when lock=True)
        self._lock_label = tkinter.Label(
            self._header,
            text=self._LOCK_ICON if self._lock else "",
            font=("Segoe UI", 10),
            fg=self._apply_appearance_mode(self._arrow_color),
            bg=header_bg,
        )
        if self._lock:
            self._lock_label.pack(side="right", padx=(0, 12), pady=8)

        # clip frame: a plain tkinter.Frame that acts as the viewport for animation.
        # Its height is animated between 0 and the content's natural height.
        clip_bg = self._apply_appearance_mode(self._fg_color)
        self._clip_frame = tkinter.Frame(self, bg=clip_bg, height=0)
        self._clip_frame.grid_propagate(False)

        # content frame (user adds widgets here) placed inside clip frame
        self._content_frame = CTkFrame(self._clip_frame, fg_color="transparent", corner_radius=0)

        if not self._collapsed:
            # Start expanded: show clip frame and let content determine height.
            # We grid the clip frame, then after idle we capture the natural height.
            self._clip_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
            self._content_frame.place(x=0, y=0, relwidth=1.0)
            # Schedule measurement after the content has been laid out
            self.after_idle(self._measure_and_set_expanded)
        else:
            # Start collapsed: clip frame is gridded but has 0 height
            self._clip_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
            self._clip_frame.configure(height=0)
            self._content_frame.place(x=0, y=0, relwidth=1.0)

        # Mouse bindings for header click and hover
        self._header.bind("<Button-1>", self._on_header_click)
        self._arrow_label.bind("<Button-1>", self._on_header_click)
        self._title_label.bind("<Button-1>", self._on_header_click)
        self._header.bind("<Enter>", self._on_header_enter)
        self._header.bind("<Leave>", self._on_header_leave)
        self._arrow_label.bind("<Enter>", self._on_header_enter)
        self._arrow_label.bind("<Leave>", self._on_header_leave)
        self._title_label.bind("<Enter>", self._on_header_enter)
        self._title_label.bind("<Leave>", self._on_header_leave)

        # Keyboard bindings for accessibility
        self._header.bind("<Return>", self._on_header_click)
        self._header.bind("<space>", self._on_header_click)
        self._header.bind("<FocusIn>", self._on_header_focus_in)
        self._header.bind("<FocusOut>", self._on_header_focus_out)

        # Update lock visual state
        self._apply_lock_state()

    def _measure_and_set_expanded(self):
        """After idle, measure the content's natural height and set clip frame to match."""
        self._content_frame.update_idletasks()
        natural_h = self._content_frame.winfo_reqheight()
        if natural_h > 0:
            self._clip_frame.configure(height=natural_h)

    @property
    def content(self) -> CTkFrame:
        """The content frame where child widgets should be placed."""
        return self._content_frame

    def _on_header_click(self, event=None):
        """Toggle collapsed state."""
        if self._animating or self._lock:
            return
        self.toggle()

    def _on_header_enter(self, event=None):
        """Hover effect on header."""
        if self._lock:
            return
        hover_color = self._apply_appearance_mode(self._header_hover_color)
        self._header.configure(bg=hover_color, highlightbackground=hover_color)
        self._arrow_label.configure(bg=hover_color)
        self._title_label.configure(bg=hover_color)
        self._lock_label.configure(bg=hover_color)

    def _on_header_leave(self, event=None):
        """Remove hover effect."""
        base_color = self._apply_appearance_mode(self._header_color or self._fg_color)
        self._header.configure(bg=base_color, highlightbackground=base_color)
        self._arrow_label.configure(bg=base_color)
        self._title_label.configure(bg=base_color)
        self._lock_label.configure(bg=base_color)

    def _on_header_focus_in(self, event=None):
        """Visual feedback when header receives keyboard focus."""
        focus_color = self._apply_appearance_mode(self._focus_color)
        self._header.configure(highlightcolor=focus_color)

    def _on_header_focus_out(self, event=None):
        """Remove visual feedback when header loses keyboard focus."""
        base_color = self._apply_appearance_mode(self._header_color or self._fg_color)
        self._header.configure(highlightcolor=base_color)

    def _apply_lock_state(self):
        """Update visual state based on lock flag."""
        if self._lock:
            self._lock_label.configure(text=self._LOCK_ICON)
            if not self._lock_label.winfo_ismapped():
                self._lock_label.pack(side="right", padx=(0, 12), pady=8)
            # Change cursor to indicate non-interactive
            self._header.configure(cursor="")
            self._arrow_label.configure(cursor="")
            self._title_label.configure(cursor="")
        else:
            self._lock_label.configure(text="")
            if self._lock_label.winfo_ismapped():
                self._lock_label.pack_forget()
            self._header.configure(cursor="hand2")
            self._arrow_label.configure(cursor="hand2")
            self._title_label.configure(cursor="hand2")

    @staticmethod
    def _ease_out_cubic(t: float) -> float:
        """Ease-out cubic easing function: decelerating to zero velocity."""
        t = t - 1.0
        return t * t * t + 1.0

    def toggle(self, animate: Optional[bool] = None):
        """Toggle between collapsed and expanded states."""
        if self._collapsed:
            self.expand(animate=animate)
        else:
            self.collapse(animate=animate)

    def expand(self, animate: Optional[bool] = None):
        """Expand the content area."""
        if not self._collapsed or self._lock:
            return

        self._collapsed = False

        # Update arrow immediately at the START of the animation
        self._arrow_label.configure(text=self._ARROW_EXPANDED)

        should_animate = animate if animate is not None else self._animate

        if should_animate:
            self._animate_expand()
        else:
            # Instant expand: measure content and set clip frame height
            self._content_frame.update_idletasks()
            target_h = self._content_frame.winfo_reqheight()
            if target_h > 0:
                self._clip_frame.configure(height=target_h)

        if self._command is not None:
            self._command(self._collapsed)

    def collapse(self, animate: Optional[bool] = None):
        """Collapse the content area."""
        if self._collapsed or self._lock:
            return

        self._collapsed = True

        # Update arrow immediately at the START of the animation
        self._arrow_label.configure(text=self._ARROW_COLLAPSED)

        should_animate = animate if animate is not None else self._animate

        if should_animate:
            self._animate_collapse()
        else:
            # Instant collapse: set clip frame height to 0
            self._clip_frame.configure(height=0)

        if self._command is not None:
            self._command(self._collapsed)

    def _animate_expand(self):
        """Animate the clip frame height from 0 to content natural height."""
        if self._animating:
            self._cancel_animation()

        self._content_frame.update_idletasks()
        target_h = self._content_frame.winfo_reqheight()
        if target_h <= 0:
            # Content has no height yet; just set to a reasonable state
            return

        self._animating = True
        total_steps = max(1, self._animation_duration // self._ANIM_INTERVAL_MS)
        self._run_animation_step(0, 0, target_h, total_steps)

    def _animate_collapse(self):
        """Animate the clip frame height from current height to 0."""
        if self._animating:
            self._cancel_animation()

        self._content_frame.update_idletasks()
        start_h = self._content_frame.winfo_reqheight()
        if start_h <= 0:
            self._clip_frame.configure(height=0)
            return

        self._animating = True
        total_steps = max(1, self._animation_duration // self._ANIM_INTERVAL_MS)
        self._run_animation_step(0, start_h, 0, total_steps)

    def _run_animation_step(self, step: int, start_h: int, end_h: int, total_steps: int):
        """Execute one tick of the height animation using ease-out-cubic."""
        if step > total_steps:
            # Animation complete: set final height
            self._clip_frame.configure(height=max(0, end_h))
            self._animating = False
            self._after_id = None
            return

        # Calculate eased progress
        t = step / total_steps if total_steps > 0 else 1.0
        eased_t = self._ease_out_cubic(t)

        # Interpolate height
        current_h = int(start_h + (end_h - start_h) * eased_t)
        current_h = max(0, current_h)

        try:
            self._clip_frame.configure(height=current_h)
        except tkinter.TclError:
            # Widget was destroyed during animation
            self._animating = False
            self._after_id = None
            return

        self._after_id = self.after(
            self._ANIM_INTERVAL_MS,
            self._run_animation_step, step + 1, start_h, end_h, total_steps
        )

    def _cancel_animation(self):
        """Cancel any pending animation callback."""
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        self._animating = False

    def is_collapsed(self) -> bool:
        """Return whether the frame is currently collapsed."""
        return self._collapsed

    def destroy(self):
        self._cancel_animation()
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
        if "animate" in kwargs:
            self._animate = kwargs.pop("animate")
        if "animation_duration" in kwargs:
            self._animation_duration = max(50, kwargs.pop("animation_duration"))
        if "lock" in kwargs:
            self._lock = kwargs.pop("lock")
            self._apply_lock_state()
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
        elif attribute_name == "animation_duration":
            return self._animation_duration
        elif attribute_name == "lock":
            return self._lock
        else:
            return super().cget(attribute_name)
