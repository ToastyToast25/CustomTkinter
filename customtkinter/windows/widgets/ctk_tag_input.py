import tkinter
import sys
from typing import Union, Tuple, Optional, Callable, Any, List

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkTagInput(CTkBaseClass):
    """
    Tag/chip input field where users type values and press Enter (or comma)
    to add tags. Each tag is displayed as a colored pill with a close button.
    Backspace on an empty entry removes the last tag.

    Features:
        - Typed input converted to tags on Enter or comma
        - Backspace removes the last tag when the entry is empty
        - Click the X on any tag to remove it
        - max_tags limit (None for unlimited)
        - Duplicate prevention (configurable)
        - Placeholder text when no tags and entry is empty
        - command callback fires whenever the tag list changes

    Usage:
        tag_input = CTkTagInput(parent, placeholder_text="Add tags...",
                                max_tags=10, command=on_tags_changed)
        tag_input.add_tag("Python")
        tag_input.set_tags(["Python", "Rust", "Go"])
        tags = tag_input.get_tags()
    """

    def __init__(self,
                 master: Any,
                 width: int = 300,
                 height: int = 36,
                 corner_radius: Optional[int] = None,
                 border_width: Optional[int] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 placeholder_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 tag_fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 tag_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 tag_close_color: Optional[Union[str, Tuple[str, str]]] = None,
                 tag_close_hover_color: Optional[Union[str, Tuple[str, str]]] = None,

                 placeholder_text: Optional[str] = "Add tags...",
                 font: Optional[Union[tuple, CTkFont]] = None,
                 tag_font: Optional[Union[tuple, CTkFont]] = None,
                 max_tags: Optional[int] = None,
                 allow_duplicates: bool = False,
                 command: Optional[Callable[[List[str]], Any]] = None,
                 state: str = tkinter.NORMAL,
                 **kwargs):

        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # ── State ────────────────────────────────────────────────────
        self._tags: List[str] = []
        self._tag_widgets: List[dict] = []  # list of {"frame", "label", "close", "text"}
        self._max_tags = max_tags
        self._allow_duplicates = allow_duplicates
        self._command = command
        self._state = state
        self._placeholder_text = placeholder_text
        self._placeholder_text_active = False

        # ── Colors ───────────────────────────────────────────────────
        self._fg_color = fg_color or ThemeManager.theme["CTkEntry"]["fg_color"]
        self._border_color = border_color or ThemeManager.theme["CTkEntry"]["border_color"]
        self._text_color = text_color or ThemeManager.theme["CTkEntry"]["text_color"]
        self._placeholder_text_color = placeholder_text_color or ThemeManager.theme["CTkEntry"]["placeholder_text_color"]

        # Tag pill colors
        self._tag_fg_color = tag_fg_color or ("#3B8ED0", "#1F6AA5")
        self._tag_text_color = tag_text_color or ("#FFFFFF", "#FFFFFF")
        self._tag_close_color = tag_close_color or ("#DCE4EE", "#DCE4EE")
        self._tag_close_hover_color = tag_close_hover_color or ("#FFFFFF", "#FFFFFF")

        # ── Shape ────────────────────────────────────────────────────
        self._corner_radius = ThemeManager.theme["CTkEntry"]["corner_radius"] if corner_radius is None else corner_radius
        self._border_width = ThemeManager.theme["CTkEntry"]["border_width"] if border_width is None else border_width

        # ── Fonts ────────────────────────────────────────────────────
        self._font = CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)

        self._tag_font = CTkFont(size=11) if tag_font is None else self._check_font_type(tag_font)
        if isinstance(self._tag_font, CTkFont):
            self._tag_font.add_size_configure_callback(self._update_tag_font)

        # ── Grid setup ───────────────────────────────────────────────
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Canvas for rounded border ────────────────────────────────
        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, sticky="nswe")
        self._draw_engine = DrawEngine(self._canvas)

        # ── Inner flow container ─────────────────────────────────────
        # This frame sits on top of the canvas and holds tag pills + entry
        inner_bg = self._apply_appearance_mode(self._fg_color)
        self._inner_frame = tkinter.Frame(self, bg=inner_bg, bd=0, highlightthickness=0)
        self._inner_frame.grid(row=0, column=0, sticky="nswe",
                               padx=self._apply_widget_scaling(self._border_width + 2),
                               pady=self._apply_widget_scaling(self._border_width + 1))

        # ── Flow frame for tags (uses pack for wrapping) ─────────────
        self._flow_frame = tkinter.Frame(self._inner_frame, bg=inner_bg, bd=0, highlightthickness=0)
        self._flow_frame.pack(side="left", fill="both", expand=True, padx=2, pady=1)

        # ── Text entry ───────────────────────────────────────────────
        self._entry = tkinter.Entry(self._flow_frame,
                                    bd=0,
                                    highlightthickness=0,
                                    font=self._apply_font_scaling(self._font),
                                    bg=inner_bg,
                                    fg=self._apply_appearance_mode(self._text_color),
                                    insertbackground=self._apply_appearance_mode(self._text_color),
                                    state=self._state)
        self._entry.pack(side="left", fill="both", expand=True, padx=(2, 4), pady=2)

        # ── Bindings ─────────────────────────────────────────────────
        self._create_bindings()

        # ── Placeholder ──────────────────────────────────────────────
        self._activate_placeholder()

        # ── Draw ─────────────────────────────────────────────────────
        self._draw()

        # Clicking anywhere inside focuses the entry
        self._inner_frame.bind("<Button-1>", self._on_container_click)
        self._flow_frame.bind("<Button-1>", self._on_container_click)
        self._canvas.bind("<Button-1>", self._on_container_click)

    # ══════════════════════════════════════════════════════════════════
    #  Bindings
    # ══════════════════════════════════════════════════════════════════

    def _create_bindings(self, sequence: Optional[str] = None):
        """Set up keyboard and focus bindings on the entry."""
        if sequence is None or sequence == "<Return>":
            self._entry.bind("<Return>", self._on_enter_key)
        if sequence is None or sequence == "<Key>":
            self._entry.bind("<Key>", self._on_key_press)
        if sequence is None or sequence == "<FocusIn>":
            self._entry.bind("<FocusIn>", self._on_focus_in)
        if sequence is None or sequence == "<FocusOut>":
            self._entry.bind("<FocusOut>", self._on_focus_out)

    def _on_container_click(self, event=None):
        """Focus the entry when clicking inside the widget area."""
        if self._state != tkinter.DISABLED:
            self._entry.focus_set()

    # ══════════════════════════════════════════════════════════════════
    #  Keyboard event handlers
    # ══════════════════════════════════════════════════════════════════

    def _on_enter_key(self, event=None):
        """Handle Enter key: add current text as a tag."""
        text = self._entry.get().strip()
        if text:
            self._try_add_tag(text)
            self._entry.delete(0, tkinter.END)

    def _on_key_press(self, event=None):
        """Handle comma to add tag, Backspace to remove last tag when empty."""
        if event is None:
            return

        # Comma triggers tag creation
        if event.char == ",":
            text = self._entry.get().strip().rstrip(",")
            if text:
                self._try_add_tag(text)
            self._entry.delete(0, tkinter.END)
            return "break"  # prevent comma from appearing in entry

        # Backspace on empty entry removes the last tag
        if event.keysym == "BackSpace" and self._entry.get() == "" and self._tags:
            self._remove_tag_by_index(len(self._tags) - 1)

    # ══════════════════════════════════════════════════════════════════
    #  Placeholder
    # ══════════════════════════════════════════════════════════════════

    def _activate_placeholder(self):
        """Show placeholder text when there are no tags and entry is empty."""
        if (self._entry.get() == "" and
                not self._tags and
                self._placeholder_text is not None):
            self._placeholder_text_active = True
            self._entry.config(
                fg=self._apply_appearance_mode(self._placeholder_text_color),
                insertbackground=self._apply_appearance_mode(self._placeholder_text_color))
            self._entry.delete(0, tkinter.END)
            self._entry.insert(0, self._placeholder_text)

    def _deactivate_placeholder(self):
        """Remove placeholder text when user starts interacting."""
        if self._placeholder_text_active:
            self._placeholder_text_active = False
            self._entry.config(
                fg=self._apply_appearance_mode(self._text_color),
                insertbackground=self._apply_appearance_mode(self._text_color))
            self._entry.delete(0, tkinter.END)

    def _on_focus_in(self, event=None):
        self._deactivate_placeholder()

    def _on_focus_out(self, event=None):
        self._activate_placeholder()

    # ══════════════════════════════════════════════════════════════════
    #  Tag management (internal)
    # ══════════════════════════════════════════════════════════════════

    def _try_add_tag(self, text: str) -> bool:
        """Attempt to add a tag. Returns True if successful, False otherwise."""
        if self._state == tkinter.DISABLED:
            return False

        text = text.strip()
        if not text:
            return False

        # Check max_tags limit
        if self._max_tags is not None and len(self._tags) >= self._max_tags:
            return False

        # Check duplicates
        if not self._allow_duplicates and text in self._tags:
            return False

        self._tags.append(text)
        self._create_tag_widget(text, len(self._tags) - 1)
        self._invoke_command()
        return True

    def _remove_tag_by_index(self, index: int):
        """Remove a tag at the given index and destroy its widget."""
        if index < 0 or index >= len(self._tags):
            return

        self._tags.pop(index)
        widget_info = self._tag_widgets.pop(index)
        widget_info["frame"].destroy()

        # Update indices for remaining tag close buttons
        for i in range(index, len(self._tag_widgets)):
            # Rebind the close button with the corrected index
            close_label = self._tag_widgets[i]["close"]
            close_label.bind("<ButtonRelease-1>", self._make_remove_handler(i))

        self._invoke_command()

        # Re-activate placeholder if no tags and entry is empty
        if not self._tags and self._entry.get() == "":
            self._activate_placeholder()

    def _make_remove_handler(self, index: int) -> Callable:
        """Create a closure for removing a tag at a specific index."""
        def handler(event=None):
            if self._state != tkinter.DISABLED:
                self._remove_tag_by_index(index)
        return handler

    def _create_tag_widget(self, text: str, index: int):
        """Create the visual pill widget for a tag and insert it before the entry."""
        inner_bg = self._apply_appearance_mode(self._fg_color)
        tag_bg = self._apply_appearance_mode(self._tag_fg_color)
        tag_fg = self._apply_appearance_mode(self._tag_text_color)
        close_fg = self._apply_appearance_mode(self._tag_close_color)

        # Tag frame (pill container)
        tag_frame = tkinter.Frame(self._flow_frame, bg=tag_bg, bd=0,
                                  highlightthickness=0, padx=0, pady=0)

        # Rounded corners via -relief and padding
        # Use a simple background-colored frame as a pill
        tag_frame.configure(bg=tag_bg)

        # Tag text label
        if isinstance(self._tag_font, CTkFont):
            tk_tag_font = self._apply_font_scaling(self._tag_font)
        else:
            tk_tag_font = self._tag_font

        text_label = tkinter.Label(tag_frame, text=text,
                                   font=tk_tag_font,
                                   fg=tag_fg, bg=tag_bg,
                                   padx=0, pady=0)
        text_label.pack(side="left", padx=(6, 0), pady=1)

        # Close button (X)
        close_font = ("Segoe UI", 9, "bold") if sys.platform.startswith("win") else ("SF Display", 9, "bold")
        close_label = tkinter.Label(tag_frame, text="\u00d7",
                                    font=close_font,
                                    fg=close_fg, bg=tag_bg,
                                    cursor="hand2" if sys.platform.startswith("win") else "pointinghand",
                                    padx=0, pady=0)
        close_label.pack(side="left", padx=(2, 5), pady=1)

        # Bind close button events
        close_label.bind("<ButtonRelease-1>", self._make_remove_handler(index))
        close_label.bind("<Enter>", lambda e, cl=close_label: cl.configure(
            fg=self._apply_appearance_mode(self._tag_close_hover_color)))
        close_label.bind("<Leave>", lambda e, cl=close_label: cl.configure(
            fg=self._apply_appearance_mode(self._tag_close_color)))

        # Clicking the tag text also focuses the entry
        text_label.bind("<Button-1>", self._on_container_click)

        # Pack the pill BEFORE the entry (entry is always last)
        self._entry.pack_forget()
        tag_frame.pack(side="left", padx=(2, 1), pady=2)
        self._entry.pack(side="left", fill="both", expand=True, padx=(2, 4), pady=2)

        self._tag_widgets.append({
            "frame": tag_frame,
            "label": text_label,
            "close": close_label,
            "text": text,
        })

    def _rebuild_tag_widgets(self):
        """Destroy all tag widgets and recreate them from the tag list."""
        for widget_info in self._tag_widgets:
            widget_info["frame"].destroy()
        self._tag_widgets.clear()

        for i, tag_text in enumerate(self._tags):
            self._create_tag_widget(tag_text, i)

    def _invoke_command(self):
        """Call the user command callback with the current tag list."""
        if self._command is not None:
            self._command(list(self._tags))

    # ══════════════════════════════════════════════════════════════════
    #  Drawing
    # ══════════════════════════════════════════════════════════════════

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(
            self._apply_widget_scaling(self._current_width),
            self._apply_widget_scaling(self._current_height),
            self._apply_widget_scaling(self._corner_radius),
            self._apply_widget_scaling(self._border_width))

        if no_color_updates is False or requires_recoloring:
            fg = self._apply_appearance_mode(self._fg_color)
            bg = self._apply_appearance_mode(self._bg_color)

            self._canvas.configure(bg=bg)
            self._canvas.itemconfig("inner_parts", fill=fg, outline=fg)
            self._canvas.itemconfig("border_parts",
                                    fill=self._apply_appearance_mode(self._border_color),
                                    outline=self._apply_appearance_mode(self._border_color))

            # Update inner frame and entry backgrounds
            self._inner_frame.configure(bg=fg)
            self._flow_frame.configure(bg=fg)
            self._entry.configure(bg=fg)

            if self._placeholder_text_active:
                self._entry.configure(
                    fg=self._apply_appearance_mode(self._placeholder_text_color),
                    insertbackground=self._apply_appearance_mode(self._placeholder_text_color))
            else:
                self._entry.configure(
                    fg=self._apply_appearance_mode(self._text_color),
                    insertbackground=self._apply_appearance_mode(self._text_color))

            # Update tag widget colors
            self._recolor_tag_widgets()

    def _recolor_tag_widgets(self):
        """Update colors on all existing tag pill widgets."""
        tag_bg = self._apply_appearance_mode(self._tag_fg_color)
        tag_fg = self._apply_appearance_mode(self._tag_text_color)
        close_fg = self._apply_appearance_mode(self._tag_close_color)

        for widget_info in self._tag_widgets:
            widget_info["frame"].configure(bg=tag_bg)
            widget_info["label"].configure(fg=tag_fg, bg=tag_bg)
            widget_info["close"].configure(fg=close_fg, bg=tag_bg)

    # ══════════════════════════════════════════════════════════════════
    #  Font updates
    # ══════════════════════════════════════════════════════════════════

    def _update_font(self):
        """Called when the main CTkFont changes."""
        self._entry.configure(font=self._apply_font_scaling(self._font))

    def _update_tag_font(self):
        """Called when the tag CTkFont changes."""
        if isinstance(self._tag_font, CTkFont):
            tk_font = self._apply_font_scaling(self._tag_font)
        else:
            tk_font = self._tag_font
        for widget_info in self._tag_widgets:
            widget_info["label"].configure(font=tk_font)

    # ══════════════════════════════════════════════════════════════════
    #  Scaling
    # ══════════════════════════════════════════════════════════════════

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)

        self._entry.configure(font=self._apply_font_scaling(self._font))
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height))
        self._inner_frame.grid_configure(
            padx=self._apply_widget_scaling(self._border_width + 2),
            pady=self._apply_widget_scaling(self._border_width + 1))
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    # ══════════════════════════════════════════════════════════════════
    #  Appearance mode change
    # ══════════════════════════════════════════════════════════════════

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)
        self._draw()

    # ══════════════════════════════════════════════════════════════════
    #  configure / cget
    # ══════════════════════════════════════════════════════════════════

    def configure(self, require_redraw=False, **kwargs):
        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            self._inner_frame.grid_configure(
                padx=self._apply_widget_scaling(self._border_width + 2),
                pady=self._apply_widget_scaling(self._border_width + 1))
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True

        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "placeholder_text_color" in kwargs:
            self._placeholder_text_color = self._check_color_type(kwargs.pop("placeholder_text_color"))
            require_redraw = True

        if "tag_fg_color" in kwargs:
            self._tag_fg_color = self._check_color_type(kwargs.pop("tag_fg_color"))
            require_redraw = True

        if "tag_text_color" in kwargs:
            self._tag_text_color = self._check_color_type(kwargs.pop("tag_text_color"))
            require_redraw = True

        if "tag_close_color" in kwargs:
            self._tag_close_color = self._check_color_type(kwargs.pop("tag_close_color"))
            require_redraw = True

        if "tag_close_hover_color" in kwargs:
            self._tag_close_hover_color = self._check_color_type(kwargs.pop("tag_close_hover_color"))

        if "placeholder_text" in kwargs:
            self._placeholder_text = kwargs.pop("placeholder_text")
            if self._placeholder_text_active:
                self._entry.delete(0, tkinter.END)
                if self._placeholder_text is not None:
                    self._entry.insert(0, self._placeholder_text)

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "tag_font" in kwargs:
            if isinstance(self._tag_font, CTkFont):
                self._tag_font.remove_size_configure_callback(self._update_tag_font)
            self._tag_font = self._check_font_type(kwargs.pop("tag_font"))
            if isinstance(self._tag_font, CTkFont):
                self._tag_font.add_size_configure_callback(self._update_tag_font)
            self._update_tag_font()

        if "max_tags" in kwargs:
            self._max_tags = kwargs.pop("max_tags")

        if "allow_duplicates" in kwargs:
            self._allow_duplicates = kwargs.pop("allow_duplicates")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._entry.configure(state=self._state)

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "border_width":
            return self._border_width
        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "placeholder_text_color":
            return self._placeholder_text_color
        elif attribute_name == "tag_fg_color":
            return self._tag_fg_color
        elif attribute_name == "tag_text_color":
            return self._tag_text_color
        elif attribute_name == "tag_close_color":
            return self._tag_close_color
        elif attribute_name == "tag_close_hover_color":
            return self._tag_close_hover_color
        elif attribute_name == "placeholder_text":
            return self._placeholder_text
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "tag_font":
            return self._tag_font
        elif attribute_name == "max_tags":
            return self._max_tags
        elif attribute_name == "allow_duplicates":
            return self._allow_duplicates
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "tags":
            return list(self._tags)
        else:
            return super().cget(attribute_name)

    # ══════════════════════════════════════════════════════════════════
    #  bind / unbind
    # ══════════════════════════════════════════════════════════════════

    def bind(self, sequence=None, command=None, add=True):
        """Bind an event to the internal entry widget."""
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._entry.bind(sequence, command, add=True)

    def unbind(self, sequence=None, funcid=None):
        """Unbind an event from the internal entry widget."""
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in"
                             " tkinter and its not clear whether the internal callbacks"
                             " will be unbinded or not")
        self._entry.unbind(sequence, None)
        self._create_bindings(sequence=sequence)

    # ══════════════════════════════════════════════════════════════════
    #  Public API
    # ══════════════════════════════════════════════════════════════════

    def get_tags(self) -> List[str]:
        """Return a copy of the current tag list."""
        return list(self._tags)

    def add_tag(self, text: str) -> bool:
        """
        Programmatically add a tag. Returns True if the tag was added,
        False if it was rejected (duplicate, max reached, empty, or disabled).
        """
        return self._try_add_tag(text)

    def remove_tag(self, text: str) -> bool:
        """
        Remove the first occurrence of a tag with the given text.
        Returns True if a tag was removed, False if not found.
        """
        try:
            index = self._tags.index(text)
        except ValueError:
            return False
        self._remove_tag_by_index(index)
        return True

    def clear_tags(self):
        """Remove all tags."""
        for widget_info in self._tag_widgets:
            widget_info["frame"].destroy()
        self._tags.clear()
        self._tag_widgets.clear()
        self._invoke_command()
        self._activate_placeholder()

    def set_tags(self, tags: List[str]):
        """Replace all current tags with the given list."""
        # Remove existing tags
        for widget_info in self._tag_widgets:
            widget_info["frame"].destroy()
        self._tags.clear()
        self._tag_widgets.clear()

        # Deactivate placeholder before adding tags
        if self._placeholder_text_active:
            self._deactivate_placeholder()

        # Add new tags (respecting max_tags and duplicates settings)
        for tag_text in tags:
            tag_text = tag_text.strip()
            if not tag_text:
                continue
            if self._max_tags is not None and len(self._tags) >= self._max_tags:
                break
            if not self._allow_duplicates and tag_text in self._tags:
                continue
            self._tags.append(tag_text)
            self._create_tag_widget(tag_text, len(self._tags) - 1)

        self._invoke_command()

        # Re-activate placeholder if still empty
        if not self._tags and self._entry.get() == "":
            self._activate_placeholder()

    def focus(self):
        """Focus the text entry."""
        self._entry.focus()

    def focus_set(self):
        """Focus the text entry."""
        self._entry.focus_set()

    def focus_force(self):
        """Force focus on the text entry."""
        self._entry.focus_force()

    # ══════════════════════════════════════════════════════════════════
    #  Cleanup
    # ══════════════════════════════════════════════════════════════════

    def destroy(self):
        """Clean up font callbacks and tag widgets before destroying."""
        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)

        if isinstance(self._tag_font, CTkFont):
            self._tag_font.remove_size_configure_callback(self._update_tag_font)

        # Destroy tag widget frames explicitly
        for widget_info in self._tag_widgets:
            try:
                widget_info["frame"].destroy()
            except tkinter.TclError:
                pass
        self._tag_widgets.clear()
        self._tags.clear()

        super().destroy()
