import tkinter
from typing import Union, Tuple, List, Dict, Callable, Optional, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkNavigationRail(CTkBaseClass):
    """
    Vertical sidebar navigation component inspired by Material Design's NavigationRail.
    Displays a list of navigation items vertically, each with an icon and optional text.
    Supports compact (icon-only) and expanded (icon + text) modes, badge counts,
    separator groups, top/bottom item sections, and a command callback.

    For detailed information check out the documentation.
    """

    # class-level layout constants
    _item_height_expanded: int = 56
    _item_height_compact: int = 48
    _compact_width: int = 64
    _indicator_width: int = 3
    _badge_radius: int = 9
    _separator_height: int = 1
    _separator_padding: int = 8
    _icon_text_spacing: int = 4

    def __init__(self,
                 master: Any,
                 width: int = 200,
                 height: int = 400,
                 corner_radius: Optional[int] = None,
                 border_width: Optional[int] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 active_color: Optional[Union[str, Tuple[str, str]]] = None,
                 active_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color_disabled: Optional[Union[str, Tuple[str, str]]] = None,
                 indicator_color: Optional[Union[str, Tuple[str, str]]] = None,
                 badge_color: Optional[Union[str, Tuple[str, str]]] = None,
                 badge_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 separator_color: Optional[Union[str, Tuple[str, str]]] = None,

                 items: Optional[List[Dict[str, Any]]] = None,
                 bottom_items: Optional[List[Dict[str, Any]]] = None,
                 command: Union[Callable[[str], Any], None] = None,
                 compact: bool = False,
                 state: str = "normal",

                 font: Optional[Union[tuple, CTkFont]] = None,
                 icon_font: Optional[Union[tuple, CTkFont]] = None,
                 **kwargs):

        # transfer basic functionality to CTkBaseClass
        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # shape
        self._corner_radius = ThemeManager.theme["CTkFrame"]["corner_radius"] if corner_radius is None else corner_radius
        self._border_width = ThemeManager.theme["CTkFrame"]["border_width"] if border_width is None else border_width

        # colors — reuse CTkFrame / CTkButton theme keys as sensible defaults
        self._fg_color = self._resolve_fg_color(fg_color)
        self._border_color = ThemeManager.theme["CTkFrame"]["border_color"] if border_color is None else self._check_color_type(border_color)
        self._active_color = ThemeManager.theme["CTkButton"]["fg_color"] if active_color is None else self._check_color_type(active_color)
        self._active_text_color = ThemeManager.theme["CTkButton"]["text_color"] if active_text_color is None else self._check_color_type(active_text_color)
        self._hover_color = ThemeManager.theme["CTkButton"]["hover_color"] if hover_color is None else self._check_color_type(hover_color)
        self._text_color = ThemeManager.theme["CTkLabel"]["text_color"] if text_color is None else self._check_color_type(text_color)
        self._text_color_disabled = ThemeManager.theme["CTkButton"]["text_color_disabled"] if text_color_disabled is None else self._check_color_type(text_color_disabled)
        self._indicator_color = ThemeManager.theme["CTkButton"]["fg_color"] if indicator_color is None else self._check_color_type(indicator_color)
        self._badge_color = ("#DB3B21", "#DB3B21") if badge_color is None else self._check_color_type(badge_color)
        self._badge_text_color = ("#FFFFFF", "#FFFFFF") if badge_text_color is None else self._check_color_type(badge_text_color)
        self._separator_color = ThemeManager.theme["CTkFrame"]["border_color"] if separator_color is None else self._check_color_type(separator_color)

        # fonts
        self._font = CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)

        self._icon_font = CTkFont(size=20) if icon_font is None else self._check_font_type(icon_font)
        if isinstance(self._icon_font, CTkFont):
            self._icon_font.add_size_configure_callback(self._update_font)

        # state
        self._state: str = state
        self._compact: bool = compact
        self._command: Union[Callable[[str], Any], None] = command

        # data
        self._items: List[Dict[str, Any]] = list(items) if items is not None else []
        self._bottom_items: List[Dict[str, Any]] = list(bottom_items) if bottom_items is not None else []
        self._current_value: str = ""
        self._badges: Dict[str, int] = {}
        self._hover_item: Optional[str] = None

        # populate initial badges from item defs
        for item in self._items + self._bottom_items:
            if "badge" in item and item["badge"] is not None and item["badge"] > 0:
                self._badges[item["name"]] = item["badge"]

        # store expanded width for toggling compact mode
        self._expanded_width: int = width

        # keyboard focus state
        self._focus_index: int = -1  # index into _all_navigable_items()
        self._has_focus: bool = False

        # tooltip for compact mode
        self._tooltip: Optional[CTkToolTip] = None
        self._tooltip_name: Optional[str] = None

        # animation state
        self._anim_after_id = None
        self._anim_target_width: Optional[int] = None

        # canvas + draw engine for the rounded-rect background
        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
        self._draw_engine = DrawEngine(self._canvas)

        # bindings for interaction
        self._canvas.bind("<Motion>", self._on_motion)
        self._canvas.bind("<Leave>", self._on_leave)
        self._canvas.bind("<ButtonRelease-1>", self._on_click)

        # keyboard bindings
        self._canvas.configure(takefocus=1)
        self._canvas.bind("<FocusIn>", self._on_focus_in)
        self._canvas.bind("<FocusOut>", self._on_focus_out)
        self._canvas.bind("<Up>", self._on_key_up)
        self._canvas.bind("<Down>", self._on_key_down)
        self._canvas.bind("<Return>", self._on_key_select)
        self._canvas.bind("<space>", self._on_key_select)
        self._canvas.bind("<Home>", self._on_key_home)
        self._canvas.bind("<End>", self._on_key_end)

        # initial draw
        if self._compact:
            super().configure(width=self._apply_widget_scaling(self._compact_width))
        self._draw()

    def _resolve_fg_color(self, fg_color):
        """Determine fg_color using the same logic as CTkFrame."""
        if fg_color is None:
            from .ctk_frame import CTkFrame
            if isinstance(self.master, CTkFrame):
                if self.master._fg_color == ThemeManager.theme["CTkFrame"]["fg_color"]:
                    return ThemeManager.theme["CTkFrame"]["top_fg_color"]
                else:
                    return ThemeManager.theme["CTkFrame"]["fg_color"]
            else:
                return ThemeManager.theme["CTkFrame"]["fg_color"]
        else:
            return self._check_color_type(fg_color, transparency=True)

    # ------------------------------------------------------------------
    # Overrides from CTkBaseClass
    # ------------------------------------------------------------------

    def destroy(self):
        if self._anim_after_id is not None:
            self.after_cancel(self._anim_after_id)
            self._anim_after_id = None
        self._hide_compact_tooltip()
        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)
        if isinstance(self._icon_font, CTkFont):
            self._icon_font.remove_size_configure_callback(self._update_font)
        super().destroy()

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)
        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw()

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)

    def _update_font(self):
        """Redraw when font changes."""
        self._draw()

    def winfo_children(self):
        child_widgets = super().winfo_children()
        try:
            child_widgets.remove(self._canvas)
            return child_widgets
        except ValueError:
            return child_widgets

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        if not self._canvas.winfo_exists():
            return

        # draw rounded rect background
        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(
            self._apply_widget_scaling(self._current_width),
            self._apply_widget_scaling(self._current_height),
            self._apply_widget_scaling(self._corner_radius),
            self._apply_widget_scaling(self._border_width))

        if no_color_updates is False or requires_recoloring:
            if self._fg_color == "transparent":
                self._canvas.itemconfig("inner_parts",
                                        fill=self._apply_appearance_mode(self._bg_color),
                                        outline=self._apply_appearance_mode(self._bg_color))
            else:
                self._canvas.itemconfig("inner_parts",
                                        fill=self._apply_appearance_mode(self._fg_color),
                                        outline=self._apply_appearance_mode(self._fg_color))
            self._canvas.itemconfig("border_parts",
                                    fill=self._apply_appearance_mode(self._border_color),
                                    outline=self._apply_appearance_mode(self._border_color))
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

        # now draw all item elements on top of the background rect
        self._draw_items()

    def _draw_items(self):
        """Draw all navigation items onto the canvas."""
        # clear previous item drawings
        self._canvas.delete("nav_item")

        is_compact = self._compact
        item_h = self._apply_widget_scaling(self._item_height_compact if is_compact else self._item_height_expanded)
        total_width = self._apply_widget_scaling(self._current_width)
        indicator_w = self._apply_widget_scaling(self._indicator_width)
        border_w = self._apply_widget_scaling(self._border_width)

        # resolve colors
        active_bg = self._apply_appearance_mode(self._active_color)
        active_fg = self._apply_appearance_mode(self._active_text_color)
        hover_bg = self._apply_appearance_mode(self._hover_color)
        normal_fg = self._apply_appearance_mode(self._text_color)
        disabled_fg = self._apply_appearance_mode(self._text_color_disabled)
        indicator_color = self._apply_appearance_mode(self._indicator_color)
        separator_color = self._apply_appearance_mode(self._separator_color)
        badge_bg = self._apply_appearance_mode(self._badge_color)
        badge_fg = self._apply_appearance_mode(self._badge_text_color)

        text_font = self._apply_font_scaling(self._font)
        icon_font_scaled = self._apply_font_scaling(self._icon_font)

        disabled = self._state == "disabled"
        text_color_normal = disabled_fg if disabled else normal_fg

        # ---- Draw top items ----
        y_offset = border_w
        self._item_regions: List[Dict[str, Any]] = []  # store clickable regions

        y_offset = self._draw_item_section(
            self._items, y_offset, item_h, total_width, indicator_w, border_w,
            is_compact, active_bg, active_fg, hover_bg, text_color_normal,
            indicator_color, separator_color, badge_bg, badge_fg,
            text_font, icon_font_scaled, disabled, section="top")

        # ---- Draw bottom items (anchored to the bottom) ----
        total_height = self._apply_widget_scaling(self._current_height)
        bottom_count = self._count_drawable_items(self._bottom_items)
        bottom_section_height = bottom_count * item_h
        y_bottom_start = total_height - bottom_section_height - border_w

        # draw separator between top and bottom if both exist
        if len(self._items) > 0 and len(self._bottom_items) > 0:
            sep_y = y_bottom_start - self._apply_widget_scaling(self._separator_padding)
            sep_pad = self._apply_widget_scaling(12)
            self._canvas.create_line(
                sep_pad, sep_y, total_width - sep_pad, sep_y,
                fill=separator_color, width=1, tags="nav_item")

        self._draw_item_section(
            self._bottom_items, y_bottom_start, item_h, total_width, indicator_w, border_w,
            is_compact, active_bg, active_fg, hover_bg, text_color_normal,
            indicator_color, separator_color, badge_bg, badge_fg,
            text_font, icon_font_scaled, disabled, section="bottom")

    def _count_drawable_items(self, items: List[Dict[str, Any]]) -> int:
        """Count items that take up a full row (excluding separators as separate rows)."""
        return sum(1 for i in items if i.get("name") != "__separator__")

    def _draw_item_section(self, items, y_offset, item_h, total_width, indicator_w, border_w,
                           is_compact, active_bg, active_fg, hover_bg, text_color_normal,
                           indicator_color, separator_color, badge_bg, badge_fg,
                           text_font, icon_font_scaled, disabled, section):
        """Draw a section of items (top or bottom). Returns the y_offset after drawing."""

        for item in items:
            # handle separators
            if item.get("name") == "__separator__":
                sep_pad = self._apply_widget_scaling(12)
                sep_y = y_offset + self._apply_widget_scaling(self._separator_padding)
                self._canvas.create_line(
                    sep_pad, sep_y, total_width - sep_pad, sep_y,
                    fill=separator_color, width=1, tags="nav_item")
                y_offset += self._apply_widget_scaling(self._separator_padding * 2 + self._separator_height)
                continue

            name = item.get("name", "")
            icon = item.get("icon", "")
            text = item.get("text", name)
            is_active = (name == self._current_value)
            is_hover = (name == self._hover_item and not is_active)

            # draw item background (active or hover)
            item_pad = self._apply_widget_scaling(4)

            if is_active:
                self._canvas.create_rectangle(
                    item_pad, y_offset + 1,
                    total_width - item_pad, y_offset + item_h - 1,
                    fill=active_bg, outline=active_bg,
                    tags="nav_item")
                # draw left-edge indicator bar
                self._canvas.create_rectangle(
                    border_w, y_offset + self._apply_widget_scaling(8),
                    border_w + indicator_w, y_offset + item_h - self._apply_widget_scaling(8),
                    fill=indicator_color, outline=indicator_color,
                    tags="nav_item")
                item_text_color = active_fg
            elif is_hover and not disabled:
                self._canvas.create_rectangle(
                    item_pad, y_offset + 1,
                    total_width - item_pad, y_offset + item_h - 1,
                    fill=hover_bg, outline=hover_bg,
                    tags="nav_item")
                item_text_color = text_color_normal
            else:
                item_text_color = text_color_normal

            # draw keyboard focus ring
            if self._has_focus and self._focus_index >= 0:
                nav_items = self._all_navigable_items()
                if self._focus_index < len(nav_items) and nav_items[self._focus_index] == name:
                    focus_color = self._apply_appearance_mode(("#1f6aa5", "#1f6aa5"))
                    self._canvas.create_rectangle(
                        item_pad + 1, y_offset + 2,
                        total_width - item_pad - 1, y_offset + item_h - 2,
                        outline=focus_color, width=2,
                        tags="nav_item")

            # draw icon and text
            if is_compact:
                # icon centered, no text
                icon_x = total_width / 2
                icon_y = y_offset + item_h / 2
                self._canvas.create_text(
                    icon_x, icon_y,
                    text=icon, fill=item_text_color,
                    font=icon_font_scaled, anchor="center",
                    tags="nav_item")
            else:
                # icon on the left, text to the right
                icon_pad_left = self._apply_widget_scaling(16)
                text_pad_left = self._apply_widget_scaling(44)

                icon_y = y_offset + item_h / 2
                self._canvas.create_text(
                    icon_pad_left, icon_y,
                    text=icon, fill=item_text_color,
                    font=icon_font_scaled, anchor="w",
                    tags="nav_item")

                self._canvas.create_text(
                    text_pad_left, icon_y,
                    text=text, fill=item_text_color,
                    font=text_font, anchor="w",
                    tags="nav_item")

            # draw badge if present
            badge_count = self._badges.get(name, 0)
            if badge_count > 0:
                badge_text = str(badge_count) if badge_count <= 99 else "99+"
                badge_r = self._apply_widget_scaling(self._badge_radius)

                if is_compact:
                    badge_cx = total_width / 2 + self._apply_widget_scaling(12)
                    badge_cy = y_offset + self._apply_widget_scaling(10)
                else:
                    badge_cx = total_width - self._apply_widget_scaling(20)
                    badge_cy = y_offset + item_h / 2

                # badge background
                badge_w = max(badge_r * 2, self._apply_widget_scaling(len(badge_text) * 7 + 6))
                self._canvas.create_oval(
                    badge_cx - badge_w / 2, badge_cy - badge_r,
                    badge_cx + badge_w / 2, badge_cy + badge_r,
                    fill=badge_bg, outline=badge_bg,
                    tags="nav_item")
                # badge text
                badge_font = self._apply_font_scaling(CTkFont(size=10, weight="bold"))
                self._canvas.create_text(
                    badge_cx, badge_cy,
                    text=badge_text, fill=badge_fg,
                    font=badge_font, anchor="center",
                    tags="nav_item")

            # record region for hit-testing
            self._item_regions.append({
                "name": name,
                "y_start": y_offset,
                "y_end": y_offset + item_h,
            })

            y_offset += item_h

        return y_offset

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def _hit_test(self, y: float) -> Optional[str]:
        """Return the item name at the given y coordinate, or None."""
        if not hasattr(self, '_item_regions'):
            return None
        for region in self._item_regions:
            if region["y_start"] <= y <= region["y_end"]:
                return region["name"]
        return None

    def _all_navigable_items(self) -> List[str]:
        """Return flat list of all navigable item names (excluding separators)."""
        names = []
        for item in self._items:
            if item.get("name") != "__separator__":
                names.append(item["name"])
        for item in self._bottom_items:
            if item.get("name") != "__separator__":
                names.append(item["name"])
        return names

    def _on_motion(self, event):
        if self._state == "disabled":
            return
        name = self._hit_test(event.y)
        if name != self._hover_item:
            self._hover_item = name
            self._draw()
        # compact-mode tooltip
        if self._compact and name:
            self._show_compact_tooltip(name, event)
        elif self._tooltip:
            self._hide_compact_tooltip()

    def _on_leave(self, event=None):
        if self._hover_item is not None:
            self._hover_item = None
            self._draw()
        self._hide_compact_tooltip()

    def _on_click(self, event):
        if self._state == "disabled":
            return
        name = self._hit_test(event.y)
        if name is not None and name != "":
            self.set_active(name)
            if self._command is not None:
                self._command(name)

    # -- Keyboard navigation -----------------------------------------------

    def _on_focus_in(self, event=None):
        self._has_focus = True
        if self._focus_index < 0:
            # auto-focus the active item or the first item
            nav = self._all_navigable_items()
            if self._current_value in nav:
                self._focus_index = nav.index(self._current_value)
            elif nav:
                self._focus_index = 0
        self._draw()

    def _on_focus_out(self, event=None):
        self._has_focus = False
        self._draw()

    def _on_key_up(self, event=None):
        if self._state == "disabled":
            return
        nav = self._all_navigable_items()
        if not nav:
            return
        self._focus_index = max(0, self._focus_index - 1)
        self._draw()

    def _on_key_down(self, event=None):
        if self._state == "disabled":
            return
        nav = self._all_navigable_items()
        if not nav:
            return
        self._focus_index = min(len(nav) - 1, self._focus_index + 1)
        self._draw()

    def _on_key_home(self, event=None):
        if self._state == "disabled":
            return
        nav = self._all_navigable_items()
        if nav:
            self._focus_index = 0
            self._draw()

    def _on_key_end(self, event=None):
        if self._state == "disabled":
            return
        nav = self._all_navigable_items()
        if nav:
            self._focus_index = len(nav) - 1
            self._draw()

    def _on_key_select(self, event=None):
        if self._state == "disabled":
            return
        nav = self._all_navigable_items()
        if 0 <= self._focus_index < len(nav):
            name = nav[self._focus_index]
            self.set_active(name)
            if self._command is not None:
                self._command(name)

    # -- Compact-mode tooltips ---------------------------------------------

    def _show_compact_tooltip(self, name: str, event):
        """Show a tooltip with the item's text label in compact mode."""
        if self._tooltip_name == name and self._tooltip is not None:
            return  # already showing for this item
        self._hide_compact_tooltip()
        self._tooltip_name = name
        # find display text for this item
        text = name
        for item in self._items + self._bottom_items:
            if item.get("name") == name:
                text = item.get("text", name)
                break
        # create a lightweight tooltip Toplevel
        try:
            tw = tkinter.Toplevel(self)
            tw.wm_overrideredirect(True)
            tw.wm_attributes("-topmost", True)
            x = self.winfo_rootx() + self.winfo_width() + 4
            y = self.winfo_rooty() + event.y - 12
            tw.wm_geometry(f"+{x}+{y}")
            label = tkinter.Label(tw, text=text, justify="left",
                                  bg="#2D2D2D", fg="#FFFFFF",
                                  font=("Segoe UI", 11),
                                  padx=8, pady=4)
            label.pack()
            self._tooltip = tw
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def _get_all_names(self) -> set:
        """Return a set of all navigable item names (excluding separators)."""
        return {i["name"] for i in self._items + self._bottom_items if i.get("name") != "__separator__"}

    def set_active(self, name: str):
        """Set the active (selected) navigation item by name."""
        if name not in self._get_all_names():
            raise ValueError(f"CTkNavigationRail has no item named '{name}'")
        if name != self._current_value:
            self._current_value = name
            self._draw()

    def get_active(self) -> str:
        """Return the name of the currently active item, or empty string."""
        return self._current_value

    def set_badge(self, name: str, count: int):
        """Set or update the badge count for the given item."""
        if name not in self._get_all_names():
            raise ValueError(f"CTkNavigationRail has no item named '{name}'")
        if count > 0:
            self._badges[name] = count
        else:
            self._badges.pop(name, None)
        self._draw()

    def clear_badge(self, name: str):
        """Remove the badge from the given item."""
        self._badges.pop(name, None)
        self._draw()

    def _hide_compact_tooltip(self):
        """Destroy the current compact-mode tooltip Toplevel."""
        if self._tooltip is not None:
            try:
                self._tooltip.destroy()
            except tkinter.TclError:
                pass
            self._tooltip = None
        self._tooltip_name = None

    # -- Smooth compact/expand animation -----------------------------------

    def set_compact(self, compact: bool):
        """Toggle between compact (icon-only) and expanded (icon + text) mode with smooth animation."""
        if compact != self._compact:
            self._compact = compact
            self._hide_compact_tooltip()
            target = self._compact_width if self._compact else self._expanded_width
            self._animate_width(target)

    def _animate_width(self, target_width: int, duration_ms: int = 200):
        """Smoothly animate the rail width to the target."""
        if self._anim_after_id is not None:
            self.after_cancel(self._anim_after_id)
            self._anim_after_id = None

        start_width = self._current_width
        total_steps = max(1, duration_ms // 16)
        self._anim_target_width = target_width
        self._run_width_anim(0, start_width, target_width, total_steps)

    def _run_width_anim(self, step: int, start_w: int, end_w: int, total_steps: int):
        """Execute one frame of the width animation."""
        if step > total_steps:
            self._set_dimensions(width=end_w)
            self._anim_after_id = None
            return

        t = step / total_steps if total_steps > 0 else 1.0
        # ease-out cubic
        t2 = t - 1.0
        eased = t2 * t2 * t2 + 1.0
        current_w = int(start_w + (end_w - start_w) * eased)

        try:
            self._set_dimensions(width=current_w)
        except Exception:
            self._anim_after_id = None
            return

        self._anim_after_id = self.after(16, self._run_width_anim, step + 1, start_w, end_w, total_steps)

    def get(self) -> str:
        """Alias for get_active — return the name of the currently selected item."""
        return self._current_value

    def set(self, name: str):
        """Alias for set_active — select a navigation item by name."""
        self.set_active(name)

    # ------------------------------------------------------------------
    # configure / cget
    # ------------------------------------------------------------------

    def configure(self, require_redraw=False, **kwargs):
        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            require_redraw = True

        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "active_color" in kwargs:
            self._active_color = self._check_color_type(kwargs.pop("active_color"))
            require_redraw = True

        if "active_text_color" in kwargs:
            self._active_text_color = self._check_color_type(kwargs.pop("active_text_color"))
            require_redraw = True

        if "hover_color" in kwargs:
            self._hover_color = self._check_color_type(kwargs.pop("hover_color"))
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "text_color_disabled" in kwargs:
            self._text_color_disabled = self._check_color_type(kwargs.pop("text_color_disabled"))
            require_redraw = True

        if "indicator_color" in kwargs:
            self._indicator_color = self._check_color_type(kwargs.pop("indicator_color"))
            require_redraw = True

        if "badge_color" in kwargs:
            self._badge_color = self._check_color_type(kwargs.pop("badge_color"))
            require_redraw = True

        if "badge_text_color" in kwargs:
            self._badge_text_color = self._check_color_type(kwargs.pop("badge_text_color"))
            require_redraw = True

        if "separator_color" in kwargs:
            self._separator_color = self._check_color_type(kwargs.pop("separator_color"))
            require_redraw = True

        if "items" in kwargs:
            self._items = list(kwargs.pop("items"))
            # re-sync badges
            for item in self._items:
                if "badge" in item and item["badge"] is not None and item["badge"] > 0:
                    self._badges[item["name"]] = item["badge"]
            require_redraw = True

        if "bottom_items" in kwargs:
            self._bottom_items = list(kwargs.pop("bottom_items"))
            for item in self._bottom_items:
                if "badge" in item and item["badge"] is not None and item["badge"] > 0:
                    self._badges[item["name"]] = item["badge"]
            require_redraw = True

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "compact" in kwargs:
            compact = kwargs.pop("compact")
            self.set_compact(compact)

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            require_redraw = True

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_font)
            require_redraw = True

        if "icon_font" in kwargs:
            if isinstance(self._icon_font, CTkFont):
                self._icon_font.remove_size_configure_callback(self._update_font)
            self._icon_font = self._check_font_type(kwargs.pop("icon_font"))
            if isinstance(self._icon_font, CTkFont):
                self._icon_font.add_size_configure_callback(self._update_font)
            require_redraw = True

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> any:
        if attribute_name == "corner_radius":
            return self._corner_radius
        elif attribute_name == "border_width":
            return self._border_width

        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "border_color":
            return self._border_color
        elif attribute_name == "active_color":
            return self._active_color
        elif attribute_name == "active_text_color":
            return self._active_text_color
        elif attribute_name == "hover_color":
            return self._hover_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "text_color_disabled":
            return self._text_color_disabled
        elif attribute_name == "indicator_color":
            return self._indicator_color
        elif attribute_name == "badge_color":
            return self._badge_color
        elif attribute_name == "badge_text_color":
            return self._badge_text_color
        elif attribute_name == "separator_color":
            return self._separator_color

        elif attribute_name == "items":
            return [d.copy() for d in self._items]
        elif attribute_name == "bottom_items":
            return [d.copy() for d in self._bottom_items]
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "compact":
            return self._compact
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "icon_font":
            return self._icon_font

        else:
            return super().cget(attribute_name)

    def bind(self, sequence=None, command=None, add=True):
        """ called on the tkinter.Canvas """
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, command, add=True)

    def unbind(self, sequence=None, funcid=None):
        """ called on the tkinter.Canvas """
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in"
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._canvas.unbind(sequence, None)
        # restore internal bindings
        self._canvas.bind("<Motion>", self._on_motion, add=True)
        self._canvas.bind("<Leave>", self._on_leave, add=True)
        self._canvas.bind("<ButtonRelease-1>", self._on_click, add=True)
