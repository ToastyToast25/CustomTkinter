"""
CTkAnimatedFrame — Container with animated page/view transitions.

A frame container that holds multiple "pages" (child frames) and transitions
between them with slide, fade, or crossfade animations.

Usage:
    container = CTkAnimatedFrame(root, transition="slide_left", duration=300)
    page1 = container.add_page("home")
    page2 = container.add_page("settings")

    CTkLabel(page1, text="Home Page").pack()
    CTkLabel(page2, text="Settings").pack()

    container.show_page("home")
    container.show_page("settings")  # animates transition
"""

import tkinter
import time
from tkinter import TclError
from typing import Union, Tuple, Optional, Any, Dict

from .core_widget_classes import CTkBaseClass
from .theme import ThemeManager


# Transition types
TRANSITION_NONE = "none"
TRANSITION_SLIDE_LEFT = "slide_left"
TRANSITION_SLIDE_RIGHT = "slide_right"
TRANSITION_SLIDE_UP = "slide_up"
TRANSITION_SLIDE_DOWN = "slide_down"
TRANSITION_FADE = "fade"

_FRAME_INTERVAL = 16  # ~60 fps


def _ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


class CTkAnimatedFrame(CTkBaseClass):
    """
    A container that holds multiple pages and transitions between them
    with configurable animations.
    """

    def __init__(
        self,
        master: Any,
        width: int = 400,
        height: int = 300,
        corner_radius: Optional[int] = None,
        fg_color: Optional[Union[str, Tuple[str, str]]] = None,
        bg_color: Union[str, Tuple[str, str]] = "transparent",
        border_width: Optional[int] = None,
        border_color: Optional[Union[str, Tuple[str, str]]] = None,
        transition: str = TRANSITION_SLIDE_LEFT,
        duration: int = 300,
        **kwargs,
    ):
        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        self._corner_radius = ThemeManager.theme["CTkFrame"]["corner_radius"] if corner_radius is None else corner_radius
        self._border_width = ThemeManager.theme["CTkFrame"]["border_width"] if border_width is None else border_width
        self._fg_color = ThemeManager.theme["CTkFrame"]["fg_color"] if fg_color is None else self._check_color_type(fg_color, transparency=True)
        self._border_color = ThemeManager.theme["CTkFrame"]["border_color"] if border_color is None else self._check_color_type(border_color)

        self._transition = transition
        self._duration = max(1, duration)

        # Pages dict: name -> tkinter.Frame
        self._pages: Dict[str, tkinter.Frame] = {}
        self._current_page: Optional[str] = None
        self._animating: bool = False
        self._anim_after_id: Optional[str] = None

        # Outer container frame
        self._outer_frame = tkinter.Frame(
            self,
            width=self._apply_widget_scaling(width),
            height=self._apply_widget_scaling(height),
        )
        self._outer_frame.pack_propagate(False)
        self._outer_frame.grid_propagate(False)
        self._outer_frame.pack(fill="both", expand=True)

        # Clip frame — prevents content from showing outside bounds during animation
        self._clip_frame = tkinter.Frame(
            self._outer_frame,
        )
        self._clip_frame.pack(fill="both", expand=True)
        self._clip_frame.pack_propagate(False)

        self._draw()

    def _draw(self, no_color_updates: bool = False) -> None:
        """Update colors."""
        if not no_color_updates:
            fg = self._apply_appearance_mode(self._fg_color)
            if fg == "transparent":
                fg = self._apply_appearance_mode(self._detect_color_of_master())

            try:
                self._outer_frame.configure(bg=fg)
                self._clip_frame.configure(bg=fg)
                tkinter.Frame.configure(self, bg=fg)
            except TclError:
                pass

            # Update all page backgrounds
            for page in self._pages.values():
                try:
                    page.configure(bg=fg)
                except TclError:
                    pass

    def _set_appearance_mode(self, mode_string: str) -> None:
        super()._set_appearance_mode(mode_string)
        self._draw()

    # -- Page management ----------------------------------------------------

    def add_page(self, name: str) -> tkinter.Frame:
        """
        Add a new page and return its frame. Users place widgets inside
        the returned frame.
        """
        if name in self._pages:
            return self._pages[name]

        fg = self._apply_appearance_mode(self._fg_color)
        if fg == "transparent":
            fg = self._apply_appearance_mode(self._detect_color_of_master())

        page = tkinter.Frame(self._clip_frame, bg=fg)
        self._pages[name] = page
        return page

    def remove_page(self, name: str) -> None:
        """Remove a page by name."""
        if name not in self._pages:
            return
        # Cancel animation if the removed page is currently animating
        if self._animating and self._current_page == name:
            self._cancel_animation()
        page = self._pages.pop(name)
        page.destroy()
        if self._current_page == name:
            self._current_page = None

    def get_page(self, name: str) -> Optional[tkinter.Frame]:
        """Get a page frame by name."""
        return self._pages.get(name)

    def get_current_page(self) -> Optional[str]:
        """Return the name of the currently visible page."""
        return self._current_page

    def get_page_names(self) -> list:
        """Return list of all page names."""
        return list(self._pages.keys())

    # -- Transition ---------------------------------------------------------

    def show_page(self, name: str, transition: Optional[str] = None) -> None:
        """
        Switch to the named page with an animated transition.

        Args:
            name: The page name to show
            transition: Override the default transition type for this switch.
                        Pass "none" to skip animation.
        """
        if name not in self._pages:
            raise ValueError(f"Page '{name}' does not exist. Add it with add_page() first.")

        if name == self._current_page:
            return

        trans = transition if transition is not None else self._transition

        # Cancel any running animation
        self._cancel_animation()

        old_page = self._pages.get(self._current_page) if self._current_page else None
        new_page = self._pages[name]

        if old_page is None or trans == TRANSITION_NONE:
            # No animation — just swap
            if old_page is not None:
                old_page.place_forget()
            new_page.place(x=0, y=0, relwidth=1.0, relheight=1.0)
            self._current_page = name
            return

        # Animate transition
        self._current_page = name
        self._animating = True

        if trans == TRANSITION_FADE:
            self._animate_fade(old_page, new_page)
        elif trans in (TRANSITION_SLIDE_LEFT, TRANSITION_SLIDE_RIGHT,
                       TRANSITION_SLIDE_UP, TRANSITION_SLIDE_DOWN):
            self._animate_slide(old_page, new_page, trans)
        else:
            # Unknown transition — just swap
            old_page.place_forget()
            new_page.place(x=0, y=0, relwidth=1.0, relheight=1.0)
            self._animating = False

    def _cancel_animation(self) -> None:
        if self._anim_after_id is not None:
            try:
                self.after_cancel(self._anim_after_id)
            except TclError:
                pass
            self._anim_after_id = None
        self._animating = False

    # -- Slide animation ----------------------------------------------------

    def _animate_slide(self, old_page: tkinter.Frame, new_page: tkinter.Frame, direction: str) -> None:
        """Slide old page out and new page in."""
        w = self._clip_frame.winfo_width()
        h = self._clip_frame.winfo_height()

        if w <= 1 or h <= 1:
            # Widget not yet mapped — try again after idle
            self._anim_after_id = self.after(50, lambda: self._animate_slide(old_page, new_page, direction))
            return

        # Determine slide vectors
        if direction == TRANSITION_SLIDE_LEFT:
            old_end_x, old_end_y = -w, 0
            new_start_x, new_start_y = w, 0
        elif direction == TRANSITION_SLIDE_RIGHT:
            old_end_x, old_end_y = w, 0
            new_start_x, new_start_y = -w, 0
        elif direction == TRANSITION_SLIDE_UP:
            old_end_x, old_end_y = 0, -h
            new_start_x, new_start_y = 0, h
        else:  # SLIDE_DOWN
            old_end_x, old_end_y = 0, h
            new_start_x, new_start_y = 0, -h

        # Place new page at start position
        new_page.place(x=new_start_x, y=new_start_y, width=w, height=h)
        old_page.place(x=0, y=0, width=w, height=h)

        start_time = time.perf_counter()

        def tick():
            elapsed = (time.perf_counter() - start_time) * 1000
            t = min(elapsed / self._duration, 1.0)
            eased = _ease_out_cubic(t)

            # Move old page
            ox = int(old_end_x * eased)
            oy = int(old_end_y * eased)
            try:
                old_page.place_configure(x=ox, y=oy)
            except TclError:
                pass

            # Move new page
            nx = int(new_start_x * (1.0 - eased))
            ny = int(new_start_y * (1.0 - eased))
            try:
                new_page.place_configure(x=nx, y=ny)
            except TclError:
                pass

            if t >= 1.0:
                old_page.place_forget()
                new_page.place(x=0, y=0, relwidth=1.0, relheight=1.0)
                self._animating = False
                self._anim_after_id = None
            else:
                self._anim_after_id = self.after(_FRAME_INTERVAL, tick)

        tick()

    # -- Fade animation -----------------------------------------------------

    def _animate_fade(self, old_page: tkinter.Frame, new_page: tkinter.Frame) -> None:
        """Crossfade between pages using opacity simulation with stipple."""
        w = self._clip_frame.winfo_width()
        h = self._clip_frame.winfo_height()

        if w <= 1 or h <= 1:
            self._anim_after_id = self.after(50, lambda: self._animate_fade(old_page, new_page))
            return

        # For fade, we overlay new page on top and "fade in" by showing it
        # immediately but covering old with new gradually.
        # Tkinter doesn't support real alpha, so we do a quick crossfade:
        # Show new page on top, old underneath, then remove old after duration/2

        # Place both
        old_page.place(x=0, y=0, width=w, height=h)
        new_page.place(x=0, y=0, width=w, height=h)
        new_page.lift()

        start_time = time.perf_counter()
        half_duration = self._duration * 0.5

        def tick():
            elapsed = (time.perf_counter() - start_time) * 1000

            if elapsed >= half_duration:
                # Second half — just show new page
                old_page.place_forget()
                new_page.place(x=0, y=0, relwidth=1.0, relheight=1.0)
                self._animating = False
                self._anim_after_id = None
            else:
                self._anim_after_id = self.after(_FRAME_INTERVAL, tick)

        tick()

    # -- Configure ----------------------------------------------------------

    def configure(self, **kwargs) -> None:
        if "transition" in kwargs:
            self._transition = kwargs.pop("transition")
        if "duration" in kwargs:
            self._duration = max(1, kwargs.pop("duration"))
        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            self._draw()
        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            self._draw()
        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            self._draw()
        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"))
            self._draw()

        super().configure(**kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "transition":
            return self._transition
        elif attribute_name == "duration":
            return self._duration
        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "border_width":
            return self._border_width
        elif attribute_name == "border_color":
            return self._border_color
        else:
            return super().cget(attribute_name)

    def destroy(self) -> None:
        self._cancel_animation()
        super().destroy()
