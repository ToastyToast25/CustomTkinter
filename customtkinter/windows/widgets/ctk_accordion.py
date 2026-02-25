import tkinter
from typing import Union, Tuple, Optional, Callable, List, Any

from .ctk_frame import CTkFrame
from .ctk_collapsible_frame import CTkCollapsibleFrame
from .font import CTkFont
from .theme import ThemeManager


class CTkAccordion(CTkFrame):
    """
    Accordion widget that groups multiple collapsible sections.
    In exclusive mode (default), only one section can be open at a time.

    Usage:
        accordion = CTkAccordion(parent)
        section1 = accordion.add_section("General")
        ctk.CTkLabel(section1, text="Option 1").pack()

        section2 = accordion.add_section("Advanced")
        ctk.CTkSlider(section2).pack()
    """

    def __init__(self,
                 master: Any,
                 width: int = 300,
                 corner_radius: Optional[int] = None,
                 border_width: Optional[int] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 section_fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 header_color: Optional[Union[str, Tuple[str, str]]] = None,
                 header_hover_color: Optional[Union[str, Tuple[str, str]]] = None,

                 exclusive: bool = True,
                 animate: bool = True,
                 animation_duration: int = 200,
                 section_spacing: int = 4,
                 font: Optional[Union[tuple, CTkFont]] = None,
                 command: Optional[Callable] = None,
                 **kwargs):

        super().__init__(master=master, width=width, corner_radius=corner_radius,
                         border_width=border_width, bg_color=bg_color,
                         fg_color=fg_color, border_color=border_color, **kwargs)

        self._exclusive = exclusive
        self._animate = animate
        self._animation_duration = animation_duration
        self._section_spacing = section_spacing
        self._font = font
        self._command = command
        self._section_fg_color = section_fg_color
        self._header_color = header_color
        self._header_hover_color = header_hover_color

        self._sections: List[dict] = []  # [{name, frame, collapsed}]
        self._focused_index: int = -1  # keyboard focus tracker

    def add_section(self, title: str, collapsed: bool = True, lock: bool = False) -> CTkFrame:
        """
        Add a new collapsible section. Returns the content frame
        where child widgets should be placed.
        """
        section_kwargs = {
            "title": title,
            "collapsed": collapsed,
            "animate": self._animate,
            "animation_duration": self._animation_duration,
            "lock": lock,
        }
        if self._font is not None:
            section_kwargs["font"] = self._font
        if self._section_fg_color is not None:
            section_kwargs["fg_color"] = self._section_fg_color
        if self._header_color is not None:
            section_kwargs["header_color"] = self._header_color
        if self._header_hover_color is not None:
            section_kwargs["header_hover_color"] = self._header_hover_color

        # create the collapsible frame with our own command wrapper
        cf = CTkCollapsibleFrame(self, **section_kwargs)
        cf.pack(fill="x", pady=(0, self._section_spacing))

        section_info = {
            "name": title,
            "frame": cf,
        }
        self._sections.append(section_info)

        # override the command to handle exclusive behavior
        original_command = cf._command
        cf._command = None  # we'll handle it ourselves
        cf.configure(command=lambda is_collapsed, sec=section_info: self._on_section_toggle(sec, is_collapsed))

        # keyboard navigation: arrow keys move between section headers
        section_idx = len(self._sections) - 1
        cf._header.bind("<Up>", lambda e, i=section_idx: self._focus_section(i - 1))
        cf._header.bind("<Down>", lambda e, i=section_idx: self._focus_section(i + 1))
        cf._header.bind("<Home>", lambda e: self._focus_section(0))
        cf._header.bind("<End>", lambda e: self._focus_section(len(self._sections) - 1))

        # if not collapsed and exclusive, collapse all others
        if not collapsed and self._exclusive:
            for other in self._sections:
                if other is not section_info and not other["frame"].is_collapsed():
                    other["frame"].collapse()

        return cf.content

    def _focus_section(self, index: int):
        """Move keyboard focus to the section at the given index."""
        if not self._sections:
            return
        index = max(0, min(index, len(self._sections) - 1))
        self._focused_index = index
        header = self._sections[index]["frame"]._header
        header.focus_set()
        # scroll the section into view if inside a scrollable parent
        header.update_idletasks()
        self._sections[index]["frame"].update_idletasks()

    def _on_section_toggle(self, section: dict, is_collapsed: bool):
        """Handle section toggle, enforcing exclusive mode."""
        if not is_collapsed and self._exclusive:
            # this section was just expanded, collapse all others
            for other in self._sections:
                if other is not section and not other["frame"].is_collapsed():
                    other["frame"].collapse()

        if self._command is not None:
            self._command(section["name"], is_collapsed)

    # ── Public API ────────────────────────────────────────────────

    def get_sections(self) -> List[str]:
        """Return a list of section names."""
        return [s["name"] for s in self._sections]

    def get_section_content(self, name: str) -> Optional[CTkFrame]:
        """Get the content frame of a section by name."""
        for s in self._sections:
            if s["name"] == name:
                return s["frame"].content
        return None

    def expand_section(self, name: str):
        """Expand a specific section by name."""
        for s in self._sections:
            if s["name"] == name:
                if s["frame"].is_collapsed():
                    s["frame"].expand()
                break

    def collapse_section(self, name: str):
        """Collapse a specific section by name."""
        for s in self._sections:
            if s["name"] == name:
                if not s["frame"].is_collapsed():
                    s["frame"].collapse()
                break

    def collapse_all(self):
        """Collapse all sections."""
        for s in self._sections:
            if not s["frame"].is_collapsed():
                s["frame"].collapse()

    def expand_all(self):
        """Expand all sections (only works when exclusive=False)."""
        if self._exclusive:
            return
        for s in self._sections:
            if s["frame"].is_collapsed():
                s["frame"].expand()

    def remove_section(self, name: str):
        """Remove a section by name."""
        for i, s in enumerate(self._sections):
            if s["name"] == name:
                s["frame"].destroy()
                self._sections.pop(i)
                break

    def focus_section(self, name: str):
        """Move keyboard focus to a section by name."""
        for i, s in enumerate(self._sections):
            if s["name"] == name:
                self._focus_section(i)
                break

    def get_open_section(self) -> Optional[str]:
        """Return the name of the currently open section, or None."""
        for s in self._sections:
            if not s["frame"].is_collapsed():
                return s["name"]
        return None

    # ── Configure / cget ──────────────────────────────────────────

    def configure(self, **kwargs):
        if "exclusive" in kwargs:
            self._exclusive = kwargs.pop("exclusive")
        if "animate" in kwargs:
            self._animate = kwargs.pop("animate")
            for s in self._sections:
                s["frame"].configure(animate=self._animate)
        if "animation_duration" in kwargs:
            self._animation_duration = kwargs.pop("animation_duration")
            for s in self._sections:
                s["frame"].configure(animation_duration=self._animation_duration)
        if "section_spacing" in kwargs:
            self._section_spacing = kwargs.pop("section_spacing")
            for s in self._sections:
                s["frame"].pack_configure(pady=(0, self._section_spacing))
        if "section_fg_color" in kwargs:
            self._section_fg_color = kwargs.pop("section_fg_color")
            for s in self._sections:
                s["frame"].configure(fg_color=self._section_fg_color)
        if "header_color" in kwargs:
            self._header_color = kwargs.pop("header_color")
            for s in self._sections:
                s["frame"].configure(header_color=self._header_color)
        if "header_hover_color" in kwargs:
            self._header_hover_color = kwargs.pop("header_hover_color")
            for s in self._sections:
                s["frame"].configure(header_hover_color=self._header_hover_color)
        if "font" in kwargs:
            self._font = kwargs.pop("font")
            for s in self._sections:
                s["frame"].configure(font=self._font)
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        super().configure(**kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "exclusive":
            return self._exclusive
        elif attribute_name == "animate":
            return self._animate
        elif attribute_name == "animation_duration":
            return self._animation_duration
        elif attribute_name == "section_spacing":
            return self._section_spacing
        elif attribute_name == "section_fg_color":
            return self._section_fg_color
        elif attribute_name == "header_color":
            return self._header_color
        elif attribute_name == "header_hover_color":
            return self._header_hover_color
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "command":
            return self._command
        else:
            return super().cget(attribute_name)

    def destroy(self):
        for s in self._sections:
            s["frame"].destroy()
        self._sections.clear()
        super().destroy()
