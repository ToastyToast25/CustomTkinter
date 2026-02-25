import tkinter
from typing import Union, Tuple, Optional, Callable, Any, List

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_widget_classes import CTkBaseClass
from .ctk_frame import CTkFrame


class CTkSplitView(CTkBaseClass):
    """
    Resizable two-panel layout with a draggable divider.

    Supports horizontal (left/right) and vertical (top/bottom) orientations.
    Each panel is a standard CTkFrame where child widgets can be placed freely.

    Usage:
        split = CTkSplitView(parent, orientation="horizontal", ratio=0.3)
        CTkLabel(split.panel_1, text="Left").pack()
        CTkLabel(split.panel_2, text="Right").pack()

    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: Any,
                 width: int = 600,
                 height: int = 400,
                 orientation: str = "horizontal",
                 ratio: float = 0.5,
                 min_size: int = 100,
                 divider_width: int = 6,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 divider_color: Optional[Union[str, Tuple[str, str]]] = None,
                 divider_hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 grip_color: Optional[Union[str, Tuple[str, str]]] = None,

                 panel_1_fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 panel_2_fg_color: Optional[Union[str, Tuple[str, str]]] = None,

                 collapsible: bool = False,
                 command: Optional[Callable] = None,
                 **kwargs):

        # transfer basic functionality to CTkBaseClass
        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # orientation
        if orientation not in ("horizontal", "vertical"):
            raise ValueError(f"orientation must be 'horizontal' or 'vertical', got '{orientation}'")
        self._orientation = orientation

        # ratio and constraints
        self._initial_ratio = max(0.0, min(1.0, ratio))
        self._ratio = self._initial_ratio
        self._min_size = max(0, min_size)
        self._divider_width = max(2, divider_width)
        self._collapsible = collapsible

        # callback
        self._command = command

        # determine fg_color of the split view container
        if fg_color is None:
            if isinstance(self.master, CTkFrame):
                if self.master.cget("fg_color") == ThemeManager.theme["CTkFrame"]["fg_color"]:
                    self._fg_color = ThemeManager.theme["CTkFrame"]["top_fg_color"]
                else:
                    self._fg_color = ThemeManager.theme["CTkFrame"]["fg_color"]
            else:
                self._fg_color = ThemeManager.theme["CTkFrame"]["fg_color"]
        else:
            self._fg_color = self._check_color_type(fg_color, transparency=True)

        # divider colors
        self._divider_color = self._check_color_type(
            divider_color if divider_color is not None else ThemeManager.theme["CTkFrame"]["border_color"]
        )
        self._divider_hover_color = self._check_color_type(
            divider_hover_color if divider_hover_color is not None else ("#8a8a8a", "#6a6a6a")
        )
        self._grip_color = self._check_color_type(
            grip_color if grip_color is not None else ("#b0b0b0", "#505050")
        )

        # drag state
        self._dragging = False
        self._drag_start_pos = 0
        self._drag_start_ratio = 0.0
        self._collapsed_panel = None  # None, 1, or 2

        # background canvas covers the entire widget area
        self._bg_canvas = CTkCanvas(master=self, highlightthickness=0)
        self._bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._bg_canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

        # panel 1 (left or top)
        self._panel_1 = CTkFrame(
            self,
            corner_radius=0,
            border_width=0,
            fg_color=panel_1_fg_color if panel_1_fg_color is not None else self._fg_color,
        )

        # panel 2 (right or bottom)
        self._panel_2 = CTkFrame(
            self,
            corner_radius=0,
            border_width=0,
            fg_color=panel_2_fg_color if panel_2_fg_color is not None else self._fg_color,
        )

        # divider frame (tkinter.Frame for direct event binding)
        divider_bg = self._apply_appearance_mode(self._divider_color)
        self._divider = tkinter.Frame(
            self,
            bg=divider_bg,
            highlightthickness=0,
        )

        # grip indicator canvas within the divider
        self._grip_canvas = tkinter.Canvas(
            self._divider,
            highlightthickness=0,
            bg=divider_bg,
        )

        # collapse button (optional, placed inside the divider)
        self._collapse_btn = None
        if self._collapsible:
            self._collapse_btn = tkinter.Label(
                self._divider,
                text=self._get_collapse_icon(),
                font=("Segoe UI", 7),
                fg=self._apply_appearance_mode(self._grip_color),
                bg=divider_bg,
                cursor="hand2",
            )
            self._collapse_btn.bind("<Button-1>", self._on_collapse_click)
            self._collapse_btn.bind("<Enter>", self._on_divider_enter)
            self._collapse_btn.bind("<Leave>", self._on_divider_leave)

        # set cursor based on orientation
        self._drag_cursor = "sb_h_double_arrow" if self._orientation == "horizontal" else "sb_v_double_arrow"
        self._divider.configure(cursor=self._drag_cursor)
        self._grip_canvas.configure(cursor=self._drag_cursor)

        # bind divider events
        self._divider.bind("<Button-1>", self._on_drag_start)
        self._divider.bind("<B1-Motion>", self._on_drag_motion)
        self._divider.bind("<ButtonRelease-1>", self._on_drag_end)
        self._divider.bind("<Double-Button-1>", self._on_double_click)
        self._divider.bind("<Enter>", self._on_divider_enter)
        self._divider.bind("<Leave>", self._on_divider_leave)

        self._grip_canvas.bind("<Button-1>", self._on_drag_start)
        self._grip_canvas.bind("<B1-Motion>", self._on_drag_motion)
        self._grip_canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        self._grip_canvas.bind("<Double-Button-1>", self._on_double_click)
        self._grip_canvas.bind("<Enter>", self._on_divider_enter)
        self._grip_canvas.bind("<Leave>", self._on_divider_leave)

        # perform initial layout
        self._place_layout()

        # listen for resize events on the container
        super().bind("<Configure>", self._on_configure, add=True)

    # ──────────────────────────── properties ────────────────────────────

    @property
    def panel_1(self) -> CTkFrame:
        """The first panel (left for horizontal, top for vertical)."""
        return self._panel_1

    @property
    def panel_2(self) -> CTkFrame:
        """The second panel (right for horizontal, bottom for vertical)."""
        return self._panel_2

    # ──────────────────────────── public methods ────────────────────────

    def set_ratio(self, ratio: float):
        """Programmatically set the split ratio (0.0 to 1.0)."""
        self._collapsed_panel = None
        self._ratio = max(0.0, min(1.0, ratio))
        self._place_layout()
        if self._command is not None:
            self._command(self._ratio)

    def get_ratio(self) -> float:
        """Return the current split ratio."""
        return self._ratio

    def collapse_panel(self, panel: int):
        """Fully collapse panel 1 or panel 2."""
        if panel not in (1, 2):
            raise ValueError("panel must be 1 or 2")
        self._collapsed_panel = panel
        self._place_layout()
        if self._command is not None:
            ratio = 0.0 if panel == 1 else 1.0
            self._command(ratio)

    def expand_panels(self):
        """Restore both panels to the current ratio (un-collapse)."""
        self._collapsed_panel = None
        self._place_layout()
        if self._command is not None:
            self._command(self._ratio)

    # ──────────────────────────── layout ────────────────────────────────

    def _place_layout(self):
        """Place panels and divider according to the current ratio and orientation."""
        w = self._current_width
        h = self._current_height
        dw = self._apply_widget_scaling(self._divider_width)

        if self._orientation == "horizontal":
            self._place_horizontal(w, h, dw)
        else:
            self._place_vertical(w, h, dw)

        self._draw_grip()
        if self._collapsible and self._collapse_btn is not None:
            self._collapse_btn.configure(text=self._get_collapse_icon())

    def _place_horizontal(self, total_w: float, total_h: float, divider_w: float):
        """Layout for horizontal (left/right) split."""
        available = total_w - divider_w
        if available < 0:
            available = 0

        if self._collapsed_panel == 1:
            p1_w = 0
        elif self._collapsed_panel == 2:
            p1_w = available
        else:
            p1_w = available * self._ratio
            # clamp to min sizes
            min_scaled = self._apply_widget_scaling(self._min_size)
            if p1_w < min_scaled and available >= 2 * min_scaled:
                p1_w = min_scaled
            elif available - p1_w < min_scaled and available >= 2 * min_scaled:
                p1_w = available - min_scaled

        p2_w = available - p1_w

        # place panel 1 (bypass CTkBaseClass.place which rejects width/height)
        tkinter.Frame.place(self._panel_1,
            x=0, y=0,
            width=max(0, p1_w),
            height=total_h,
        )

        # place divider
        self._divider.place(
            x=p1_w, y=0,
            width=divider_w,
            height=total_h,
        )

        # place grip canvas centered in divider
        grip_h = min(40, max(20, total_h * 0.1))
        self._grip_canvas.configure(width=int(divider_w), height=int(grip_h))
        self._grip_canvas.place(
            relx=0.5, rely=0.5,
            anchor="center",
            width=divider_w,
            height=grip_h,
        )

        # place collapse button if enabled
        if self._collapsible and self._collapse_btn is not None:
            self._collapse_btn.place(relx=0.5, rely=0.15, anchor="center")

        # place panel 2
        tkinter.Frame.place(self._panel_2,
            x=p1_w + divider_w, y=0,
            width=max(0, p2_w),
            height=total_h,
        )

    def _place_vertical(self, total_w: float, total_h: float, divider_h: float):
        """Layout for vertical (top/bottom) split."""
        available = total_h - divider_h
        if available < 0:
            available = 0

        if self._collapsed_panel == 1:
            p1_h = 0
        elif self._collapsed_panel == 2:
            p1_h = available
        else:
            p1_h = available * self._ratio
            # clamp to min sizes
            min_scaled = self._apply_widget_scaling(self._min_size)
            if p1_h < min_scaled and available >= 2 * min_scaled:
                p1_h = min_scaled
            elif available - p1_h < min_scaled and available >= 2 * min_scaled:
                p1_h = available - min_scaled

        p2_h = available - p1_h

        # place panel 1 (bypass CTkBaseClass.place which rejects width/height)
        tkinter.Frame.place(self._panel_1,
            x=0, y=0,
            width=total_w,
            height=max(0, p1_h),
        )

        # place divider
        self._divider.place(
            x=0, y=p1_h,
            width=total_w,
            height=divider_h,
        )

        # place grip canvas centered in divider
        grip_w = min(40, max(20, total_w * 0.1))
        self._grip_canvas.configure(width=int(grip_w), height=int(divider_h))
        self._grip_canvas.place(
            relx=0.5, rely=0.5,
            anchor="center",
            width=grip_w,
            height=divider_h,
        )

        # place collapse button if enabled
        if self._collapsible and self._collapse_btn is not None:
            self._collapse_btn.place(relx=0.15, rely=0.5, anchor="center")

        # place panel 2
        tkinter.Frame.place(self._panel_2,
            x=0, y=p1_h + divider_h,
            width=total_w,
            height=max(0, p2_h),
        )

    # ──────────────────────────── grip drawing ──────────────────────────

    def _draw_grip(self):
        """Draw small grip dots/lines on the divider to indicate it is draggable."""
        self._grip_canvas.delete("all")
        grip_fill = self._apply_appearance_mode(self._grip_color)
        canvas_bg = self._apply_appearance_mode(self._divider_color)
        self._grip_canvas.configure(bg=canvas_bg)

        cw = self._grip_canvas.winfo_reqwidth()
        ch = self._grip_canvas.winfo_reqheight()

        if self._orientation == "horizontal":
            # draw 3 small horizontal lines centered vertically
            cx = cw / 2
            cy = ch / 2
            line_half_len = max(2, (cw - 4) / 2)
            spacing = max(3, ch * 0.15)
            for i in range(-1, 2):
                y = cy + i * spacing
                self._grip_canvas.create_line(
                    cx - line_half_len, y, cx + line_half_len, y,
                    fill=grip_fill, width=1, tags="grip",
                )
        else:
            # draw 3 small vertical lines centered horizontally
            cx = cw / 2
            cy = ch / 2
            line_half_len = max(2, (ch - 4) / 2)
            spacing = max(3, cw * 0.15)
            for i in range(-1, 2):
                x = cx + i * spacing
                self._grip_canvas.create_line(
                    x, cy - line_half_len, x, cy + line_half_len,
                    fill=grip_fill, width=1, tags="grip",
                )

    # ──────────────────────────── collapse icon ─────────────────────────

    def _get_collapse_icon(self) -> str:
        """Return an arrow character indicating the collapse direction."""
        if self._orientation == "horizontal":
            if self._collapsed_panel == 1:
                return "\u25B6"  # right-pointing (panel 1 collapsed, click to expand)
            elif self._collapsed_panel == 2:
                return "\u25C0"  # left-pointing (panel 2 collapsed, click to expand)
            else:
                return "\u25C0"  # left-pointing (click to collapse panel 1)
        else:
            if self._collapsed_panel == 1:
                return "\u25BC"  # down-pointing (panel 1 collapsed, click to expand)
            elif self._collapsed_panel == 2:
                return "\u25B2"  # up-pointing (panel 2 collapsed, click to expand)
            else:
                return "\u25B2"  # up-pointing (click to collapse panel 1)

    def _on_collapse_click(self, event):
        """Handle click on the collapse button."""
        if self._collapsed_panel is not None:
            # currently collapsed: expand
            self.expand_panels()
        else:
            # collapse panel 1
            self.collapse_panel(1)

    # ──────────────────────────── divider events ────────────────────────

    def _on_divider_enter(self, event):
        """Highlight divider on hover."""
        hover_bg = self._apply_appearance_mode(self._divider_hover_color)
        self._divider.configure(bg=hover_bg)
        self._grip_canvas.configure(bg=hover_bg)
        if self._collapsible and self._collapse_btn is not None:
            self._collapse_btn.configure(bg=hover_bg)

    def _on_divider_leave(self, event):
        """Remove divider highlight."""
        if not self._dragging:
            normal_bg = self._apply_appearance_mode(self._divider_color)
            self._divider.configure(bg=normal_bg)
            self._grip_canvas.configure(bg=normal_bg)
            if self._collapsible and self._collapse_btn is not None:
                self._collapse_btn.configure(bg=normal_bg)

    def _on_drag_start(self, event):
        """Begin dragging the divider."""
        self._dragging = True
        self._drag_start_ratio = self._ratio
        if self._orientation == "horizontal":
            self._drag_start_pos = event.x_root
        else:
            self._drag_start_pos = event.y_root

        # un-collapse if currently collapsed
        if self._collapsed_panel is not None:
            self._collapsed_panel = None

    def _on_drag_motion(self, event):
        """Update ratio while dragging."""
        if not self._dragging:
            return

        dw = self._apply_widget_scaling(self._divider_width)

        if self._orientation == "horizontal":
            total = self._current_width - dw
            delta = event.x_root - self._drag_start_pos
        else:
            total = self._current_height - dw
            delta = event.y_root - self._drag_start_pos

        if total <= 0:
            return

        # compute new ratio
        new_ratio = self._drag_start_ratio + delta / total

        # clamp to min_size constraints
        min_scaled = self._apply_widget_scaling(self._min_size)
        min_ratio = min_scaled / total if total > 0 else 0.0
        max_ratio = 1.0 - min_ratio

        if min_ratio > max_ratio:
            # not enough space for both panels at minimum; allow free dragging
            new_ratio = max(0.0, min(1.0, new_ratio))
        else:
            new_ratio = max(min_ratio, min(max_ratio, new_ratio))

        self._ratio = new_ratio
        self._place_layout()

    def _on_drag_end(self, event):
        """Finish dragging."""
        self._dragging = False

        # check if mouse is still over divider; if not, remove hover
        try:
            mx = event.x_root
            my = event.y_root
            dx = self._divider.winfo_rootx()
            dy = self._divider.winfo_rooty()
            dw = self._divider.winfo_width()
            dh = self._divider.winfo_height()
            if not (dx <= mx <= dx + dw and dy <= my <= dy + dh):
                self._on_divider_leave(event)
        except tkinter.TclError:
            pass

        if self._command is not None:
            self._command(self._ratio)

    def _on_double_click(self, event):
        """Reset to initial ratio on double-click."""
        self._collapsed_panel = None
        self._ratio = self._initial_ratio
        self._place_layout()
        if self._command is not None:
            self._command(self._ratio)

    # ──────────────────────────── resize handling ───────────────────────

    def _on_configure(self, event):
        """Relayout when the container is resized."""
        new_w = self._reverse_widget_scaling(event.width)
        new_h = self._reverse_widget_scaling(event.height)

        if (round(new_w) != round(self._current_width)
                or round(new_h) != round(self._current_height)):
            self._current_width = new_w
            self._current_height = new_h
            self._place_layout()

    # ──────────────────────────── winfo_children ────────────────────────

    def winfo_children(self) -> List[any]:
        """
        winfo_children without internal widgets (bg_canvas, divider),
        because they are part of the CTkSplitView itself, not user children.
        """
        child_widgets = super().winfo_children()
        try:
            child_widgets.remove(self._bg_canvas)
        except ValueError:
            pass
        try:
            child_widgets.remove(self._divider)
        except ValueError:
            pass
        return child_widgets

    # ──────────────────────────── drawing / appearance ──────────────────

    def _draw(self, no_color_updates: bool = False):
        super()._draw(no_color_updates)

        if no_color_updates:
            self._place_layout()
            return

        # update background
        bg = self._apply_appearance_mode(self._bg_color)
        self._bg_canvas.configure(bg=bg)
        tkinter.Frame.configure(self, bg=bg)

        # update divider colors
        divider_bg = self._apply_appearance_mode(self._divider_color)
        self._divider.configure(bg=divider_bg)
        self._grip_canvas.configure(bg=divider_bg)
        if self._collapsible and self._collapse_btn is not None:
            self._collapse_btn.configure(
                bg=divider_bg,
                fg=self._apply_appearance_mode(self._grip_color),
            )

        self._draw_grip()
        self._place_layout()

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._place_layout()

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)
        self._place_layout()

    # ──────────────────────────── configure / cget ──────────────────────

    def configure(self, require_redraw=False, **kwargs):
        if "orientation" in kwargs:
            new_orientation = kwargs.pop("orientation")
            if new_orientation not in ("horizontal", "vertical"):
                raise ValueError(f"orientation must be 'horizontal' or 'vertical', got '{new_orientation}'")
            self._orientation = new_orientation
            self._drag_cursor = (
                "sb_h_double_arrow" if self._orientation == "horizontal" else "sb_v_double_arrow"
            )
            self._divider.configure(cursor=self._drag_cursor)
            self._grip_canvas.configure(cursor=self._drag_cursor)
            require_redraw = True

        if "ratio" in kwargs:
            self._ratio = max(0.0, min(1.0, kwargs.pop("ratio")))
            self._initial_ratio = self._ratio
            self._collapsed_panel = None
            require_redraw = True

        if "min_size" in kwargs:
            self._min_size = max(0, kwargs.pop("min_size"))
            require_redraw = True

        if "divider_width" in kwargs:
            self._divider_width = max(2, kwargs.pop("divider_width"))
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            require_redraw = True

        if "divider_color" in kwargs:
            self._divider_color = self._check_color_type(kwargs.pop("divider_color"))
            require_redraw = True

        if "divider_hover_color" in kwargs:
            self._divider_hover_color = self._check_color_type(kwargs.pop("divider_hover_color"))

        if "grip_color" in kwargs:
            self._grip_color = self._check_color_type(kwargs.pop("grip_color"))
            require_redraw = True

        if "panel_1_fg_color" in kwargs:
            self._panel_1.configure(fg_color=kwargs.pop("panel_1_fg_color"))

        if "panel_2_fg_color" in kwargs:
            self._panel_2.configure(fg_color=kwargs.pop("panel_2_fg_color"))

        if "collapsible" in kwargs:
            self._collapsible = kwargs.pop("collapsible")
            if self._collapsible and self._collapse_btn is None:
                divider_bg = self._apply_appearance_mode(self._divider_color)
                self._collapse_btn = tkinter.Label(
                    self._divider,
                    text=self._get_collapse_icon(),
                    font=("Segoe UI", 7),
                    fg=self._apply_appearance_mode(self._grip_color),
                    bg=divider_bg,
                    cursor="hand2",
                )
                self._collapse_btn.bind("<Button-1>", self._on_collapse_click)
                self._collapse_btn.bind("<Enter>", self._on_divider_enter)
                self._collapse_btn.bind("<Leave>", self._on_divider_leave)
            elif not self._collapsible and self._collapse_btn is not None:
                self._collapse_btn.destroy()
                self._collapse_btn = None
                self._collapsed_panel = None
            require_redraw = True

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "orientation":
            return self._orientation
        elif attribute_name == "ratio":
            return self._ratio
        elif attribute_name == "min_size":
            return self._min_size
        elif attribute_name == "divider_width":
            return self._divider_width

        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "divider_color":
            return self._divider_color
        elif attribute_name == "divider_hover_color":
            return self._divider_hover_color
        elif attribute_name == "grip_color":
            return self._grip_color

        elif attribute_name == "panel_1_fg_color":
            return self._panel_1.cget("fg_color")
        elif attribute_name == "panel_2_fg_color":
            return self._panel_2.cget("fg_color")

        elif attribute_name == "collapsible":
            return self._collapsible
        elif attribute_name == "command":
            return self._command

        else:
            return super().cget(attribute_name)

    # ──────────────────────────── bind / unbind ─────────────────────────

    def bind(self, sequence=None, command=None, add=True):
        """Bind events on the background canvas."""
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._bg_canvas.bind(sequence, command, add=True)

    def unbind(self, sequence=None, funcid=None):
        """Unbind events on the background canvas."""
        if funcid is not None:
            raise ValueError(
                "'funcid' argument can only be None, because there is a bug in"
                " tkinter and its not clear whether the internal callbacks will be unbinded or not"
            )
        self._bg_canvas.unbind(sequence, None)

    # ──────────────────────────── destroy ───────────────────────────────

    def destroy(self):
        """Clean up all child widgets."""
        super().destroy()
