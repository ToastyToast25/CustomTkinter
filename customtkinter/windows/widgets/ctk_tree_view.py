import tkinter
import sys
import uuid
from typing import Union, Tuple, Optional, Callable, Any, Dict, List

from .core_rendering import CTkCanvas
from .core_rendering import DrawEngine
from .theme import ThemeManager
from .core_widget_classes import CTkBaseClass
from .ctk_scrollbar import CTkScrollbar
from .font import CTkFont


class _TreeNode:
    """Internal data structure representing a single node in the tree."""

    __slots__ = (
        "node_id", "parent_id", "text", "icon", "data", "badge",
        "children", "expanded", "visible", "depth",
    )

    def __init__(self, node_id: str, parent_id: str, text: str,
                 icon: Optional[str], data: Any, badge: Optional[str],
                 depth: int):
        self.node_id: str = node_id
        self.parent_id: str = parent_id
        self.text: str = text
        self.icon: Optional[str] = icon
        self.data: Any = data
        self.badge: Optional[str] = badge
        self.children: List[str] = []
        self.expanded: bool = False
        self.visible: bool = True
        self.depth: int = depth


class CTkTreeView(CTkBaseClass):
    """
    Hierarchical tree view with expandable nodes.

    Displays nested data with expand/collapse controls,
    selection highlighting, keyboard navigation, and
    optional icons and badges per node.

    Usage:
        tree = CTkTreeView(parent, command=on_select)
        root = tree.insert("", "Root Node")
        child = tree.insert(root, "Child Node", icon="folder")
        tree.expand(root)
    """

    # Arrow characters for expand/collapse indicators
    _ARROW_EXPANDED = "\u25BC"   # down-pointing triangle
    _ARROW_COLLAPSED = "\u25B6"  # right-pointing triangle
    _LEAF_BULLET = "\u2022"      # bullet for leaf nodes

    def __init__(self,
                 master: Any,
                 width: int = 300,
                 height: int = 400,
                 corner_radius: Optional[int] = None,
                 border_width: Optional[int] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 select_color: Optional[Union[str, Tuple[str, str]]] = None,
                 select_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 guide_color: Optional[Union[str, Tuple[str, str]]] = None,
                 arrow_color: Optional[Union[str, Tuple[str, str]]] = None,
                 badge_color: Optional[Union[str, Tuple[str, str]]] = None,
                 badge_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 highlight_color: Optional[Union[str, Tuple[str, str]]] = None,

                 scrollbar_fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 scrollbar_button_color: Optional[Union[str, Tuple[str, str]]] = None,
                 scrollbar_button_hover_color: Optional[Union[str, Tuple[str, str]]] = None,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 row_height: int = 28,
                 indent_size: int = 20,
                 show_guides: bool = True,
                 select_mode: str = "single",
                 enable_dnd: bool = False,

                 command: Optional[Callable] = None,
                 **kwargs):

        # transfer basic functionality to CTkBaseClass
        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # --- colors ---
        self._fg_color = self._check_color_type(fg_color, transparency=True) if fg_color is not None else ThemeManager.theme["CTkFrame"]["fg_color"]
        self._border_color = self._check_color_type(border_color) if border_color is not None else ThemeManager.theme["CTkFrame"]["border_color"]
        self._text_color = self._check_color_type(text_color) if text_color is not None else ThemeManager.theme["CTkLabel"]["text_color"]
        self._select_color = self._check_color_type(select_color) if select_color is not None else ThemeManager.theme["CTkButton"]["fg_color"]
        self._select_text_color = self._check_color_type(select_text_color) if select_text_color is not None else ThemeManager.theme["CTkButton"]["text_color"]
        self._hover_color = self._check_color_type(hover_color) if hover_color is not None else ThemeManager.theme["CTkButton"]["hover_color"]
        self._guide_color = self._check_color_type(guide_color) if guide_color is not None else ("#C0C0C0", "#505050")
        self._arrow_color = self._check_color_type(arrow_color) if arrow_color is not None else self._text_color
        self._badge_color = self._check_color_type(badge_color) if badge_color is not None else ("#E0E0E0", "#404040")
        self._badge_text_color = self._check_color_type(badge_text_color) if badge_text_color is not None else self._text_color
        self._highlight_color = self._check_color_type(highlight_color) if highlight_color is not None else ("#FFFF00", "#665500")

        # --- shape ---
        self._corner_radius = ThemeManager.theme["CTkFrame"]["corner_radius"] if corner_radius is None else corner_radius
        self._border_width = ThemeManager.theme["CTkFrame"]["border_width"] if border_width is None else border_width

        # --- tree configuration ---
        self._row_height = row_height
        self._indent_size = indent_size
        self._show_guides = show_guides
        self._select_mode = select_mode  # "single", "multiple", "none"
        self._enable_dnd = enable_dnd
        self._command = command

        # --- font ---
        self._font = CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._on_font_update)

        # --- internal state ---
        self._nodes: Dict[str, _TreeNode] = {}        # node_id -> _TreeNode
        self._root_children: List[str] = []            # top-level node IDs in order
        self._selected: List[str] = []                 # currently selected node IDs
        self._focus_node: Optional[str] = None         # keyboard focus node
        self._hover_node: Optional[str] = None         # mouse hover node
        self._visible_nodes: List[str] = []            # ordered list of currently visible node IDs
        self._search_term: str = ""                    # current search/filter text
        self._search_matches: set = set()              # node IDs matching search
        self._dnd_source: Optional[str] = None         # drag source node ID
        self._dnd_target: Optional[str] = None         # drag target node ID
        self._dnd_active: bool = False

        # --- canvas and drawing infrastructure ---
        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._draw_engine = DrawEngine(self._canvas)

        # --- inner canvas for scrollable tree content ---
        border_offset = self._corner_radius + self._border_width
        self._inner_canvas = tkinter.Canvas(
            self,
            highlightthickness=0,
            bd=0,
            bg=self._apply_appearance_mode(self._fg_color),
        )
        self._inner_canvas.place(
            x=self._apply_widget_scaling(border_offset),
            y=self._apply_widget_scaling(border_offset),
            relwidth=1.0,
            relheight=1.0,
            width=-self._apply_widget_scaling(border_offset * 2 + 16),
            height=-self._apply_widget_scaling(border_offset * 2),
        )

        # --- scrollbar ---
        self._scrollbar = CTkScrollbar(
            master=self,
            orientation="vertical",
            command=self._inner_canvas.yview,
            fg_color=scrollbar_fg_color if scrollbar_fg_color is not None else "transparent",
            button_color=scrollbar_button_color,
            button_hover_color=scrollbar_button_hover_color,
        )
        tkinter.Frame.place(
            self._scrollbar,
            relx=1.0,
            x=-self._apply_widget_scaling(border_offset + 14),
            y=self._apply_widget_scaling(border_offset),
            relheight=1.0,
            height=-self._apply_widget_scaling(border_offset * 2),
            width=self._apply_widget_scaling(14),
        )
        self._inner_canvas.configure(yscrollcommand=self._scrollbar.set)
        self._set_scroll_increments()

        # --- event bindings ---
        self._inner_canvas.bind("<Button-1>", self._on_click)
        self._inner_canvas.bind("<Double-Button-1>", self._on_double_click)
        self._inner_canvas.bind("<Motion>", self._on_motion)
        self._inner_canvas.bind("<Leave>", self._on_leave)
        self._inner_canvas.bind("<KeyPress>", self._on_key_press)
        self._inner_canvas.bind("<FocusIn>", self._on_focus_in)
        self._inner_canvas.bind("<FocusOut>", self._on_focus_out)

        if sys.platform.startswith("win"):
            self._inner_canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        elif sys.platform == "darwin":
            self._inner_canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        else:
            self._inner_canvas.bind("<Button-4>", self._on_mouse_wheel)
            self._inner_canvas.bind("<Button-5>", self._on_mouse_wheel)

        if self._enable_dnd:
            self._inner_canvas.bind("<B1-Motion>", self._on_drag_motion)
            self._inner_canvas.bind("<ButtonRelease-1>", self._on_drag_release)

        # draw the outer frame
        self._draw()

    # ---------------------------------------------------------------
    # Drawing
    # ---------------------------------------------------------------

    def _draw(self, no_color_updates: bool = False):
        super()._draw(no_color_updates)

        if not self._canvas.winfo_exists():
            return

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(
            self._apply_widget_scaling(self._current_width),
            self._apply_widget_scaling(self._current_height),
            self._apply_widget_scaling(self._corner_radius),
            self._apply_widget_scaling(self._border_width),
        )

        if no_color_updates is False or requires_recoloring:
            if self._fg_color == "transparent":
                self._canvas.itemconfig("inner_parts",
                                        fill=self._apply_appearance_mode(self._bg_color),
                                        outline=self._apply_appearance_mode(self._bg_color))
                bg = self._apply_appearance_mode(self._bg_color)
            else:
                self._canvas.itemconfig("inner_parts",
                                        fill=self._apply_appearance_mode(self._fg_color),
                                        outline=self._apply_appearance_mode(self._fg_color))
                bg = self._apply_appearance_mode(self._fg_color)

            self._canvas.itemconfig("border_parts",
                                    fill=self._apply_appearance_mode(self._border_color),
                                    outline=self._apply_appearance_mode(self._border_color))
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._inner_canvas.configure(bg=bg)

        self._redraw_tree()

    def _redraw_tree(self):
        """Rebuild the visible node list and redraw all rows on the inner canvas."""
        self._inner_canvas.delete("all")
        self._visible_nodes = self._build_visible_list()

        row_h = self._apply_widget_scaling(self._row_height)
        canvas_width = self._inner_canvas.winfo_width()
        if canvas_width <= 1:
            canvas_width = self._apply_widget_scaling(self._desired_width - 2 * (self._corner_radius + self._border_width) - 16)

        total_height = int(row_h * len(self._visible_nodes))

        # Determine background color for the tree area
        if self._fg_color == "transparent":
            bg_color = self._apply_appearance_mode(self._bg_color)
        else:
            bg_color = self._apply_appearance_mode(self._fg_color)

        text_color = self._apply_appearance_mode(self._text_color)
        select_color = self._apply_appearance_mode(self._select_color)
        select_text_color = self._apply_appearance_mode(self._select_text_color)
        hover_color = self._apply_appearance_mode(self._hover_color)
        guide_color = self._apply_appearance_mode(self._guide_color)
        arrow_color = self._apply_appearance_mode(self._arrow_color)
        badge_bg = self._apply_appearance_mode(self._badge_color)
        badge_fg = self._apply_appearance_mode(self._badge_text_color)
        highlight_color = self._apply_appearance_mode(self._highlight_color)

        scaled_indent = self._apply_widget_scaling(self._indent_size)
        font_tuple = self._apply_font_scaling(self._font)
        small_font = (font_tuple[0], max(int(font_tuple[1] * 0.8), -9)) if len(font_tuple) >= 2 else font_tuple
        arrow_font = (font_tuple[0], font_tuple[1]) if len(font_tuple) >= 2 else font_tuple

        for i, node_id in enumerate(self._visible_nodes):
            node = self._nodes[node_id]
            y_top = int(i * row_h)
            y_center = int(y_top + row_h / 2)
            x_offset = int(node.depth * scaled_indent) + self._apply_widget_scaling(8)

            is_selected = node_id in self._selected
            is_hover = node_id == self._hover_node and not is_selected
            is_focus = node_id == self._focus_node
            is_search_match = node_id in self._search_matches

            # --- Row background ---
            if is_selected:
                self._inner_canvas.create_rectangle(
                    0, y_top, canvas_width, y_top + row_h,
                    fill=select_color, outline=select_color, tags=("row", f"row_{node_id}"),
                )
                row_text_color = select_text_color
            elif is_hover:
                self._inner_canvas.create_rectangle(
                    0, y_top, canvas_width, y_top + row_h,
                    fill=hover_color, outline=hover_color, tags=("row", f"row_{node_id}"),
                )
                row_text_color = text_color
            else:
                row_text_color = text_color

            # --- Search highlight background ---
            if is_search_match and not is_selected:
                self._inner_canvas.create_rectangle(
                    0, y_top, canvas_width, y_top + row_h,
                    fill=highlight_color, outline=highlight_color, tags=("highlight",),
                )
                row_text_color = text_color

            # --- Focus ring ---
            if is_focus:
                self._inner_canvas.create_rectangle(
                    1, y_top + 1, canvas_width - 1, y_top + row_h - 1,
                    outline=select_color, width=1, dash=(2, 2),
                    tags=("focus_ring",),
                )

            # --- Indent guide lines ---
            if self._show_guides and node.depth > 0:
                for d in range(node.depth):
                    guide_x = int(d * scaled_indent + self._apply_widget_scaling(8) + scaled_indent / 2)
                    self._inner_canvas.create_line(
                        guide_x, y_top, guide_x, y_top + row_h,
                        fill=guide_color, width=1, dash=(1, 3),
                        tags=("guide",),
                    )

            # --- Expand/collapse arrow or leaf bullet ---
            has_children = len(node.children) > 0
            arrow_x = x_offset + self._apply_widget_scaling(6)

            if has_children:
                arrow_text = self._ARROW_EXPANDED if node.expanded else self._ARROW_COLLAPSED
                self._inner_canvas.create_text(
                    arrow_x, y_center,
                    text=arrow_text,
                    fill=arrow_color if not is_selected else select_text_color,
                    font=arrow_font,
                    anchor="center",
                    tags=("arrow", f"arrow_{node_id}"),
                )
            else:
                self._inner_canvas.create_text(
                    arrow_x, y_center,
                    text=self._LEAF_BULLET,
                    fill=guide_color if not is_selected else select_text_color,
                    font=arrow_font,
                    anchor="center",
                    tags=("leaf",),
                )

            # --- Icon ---
            text_x = arrow_x + self._apply_widget_scaling(14)
            if node.icon:
                self._inner_canvas.create_text(
                    text_x, y_center,
                    text=node.icon,
                    fill=row_text_color,
                    font=font_tuple,
                    anchor="w",
                    tags=("icon", f"icon_{node_id}"),
                )
                text_x += self._apply_widget_scaling(18)

            # --- Node text ---
            self._inner_canvas.create_text(
                text_x, y_center,
                text=node.text,
                fill=row_text_color,
                font=font_tuple,
                anchor="w",
                tags=("text", f"text_{node_id}"),
            )

            # --- Badge ---
            if node.badge:
                badge_text = str(node.badge)
                # Measure badge text width approximately
                badge_w = max(self._apply_widget_scaling(20), len(badge_text) * self._apply_widget_scaling(8) + self._apply_widget_scaling(10))
                badge_h = self._apply_widget_scaling(16)
                badge_x = canvas_width - self._apply_widget_scaling(24) - badge_w
                badge_y_top = y_center - badge_h // 2
                badge_y_bot = y_center + badge_h // 2
                radius = badge_h // 2

                self._inner_canvas.create_oval(
                    badge_x, badge_y_top, badge_x + badge_h, badge_y_bot,
                    fill=badge_bg if not is_selected else select_text_color,
                    outline="",
                    tags=("badge",),
                )
                self._inner_canvas.create_rectangle(
                    badge_x + radius, badge_y_top, badge_x + badge_w - radius, badge_y_bot,
                    fill=badge_bg if not is_selected else select_text_color,
                    outline="",
                    tags=("badge",),
                )
                self._inner_canvas.create_oval(
                    badge_x + badge_w - badge_h, badge_y_top, badge_x + badge_w, badge_y_bot,
                    fill=badge_bg if not is_selected else select_text_color,
                    outline="",
                    tags=("badge",),
                )
                self._inner_canvas.create_text(
                    badge_x + badge_w / 2, y_center,
                    text=badge_text,
                    fill=badge_fg if not is_selected else select_color,
                    font=small_font,
                    anchor="center",
                    tags=("badge_text",),
                )

        # Update scroll region
        self._inner_canvas.configure(scrollregion=(0, 0, canvas_width, max(total_height, 1)))

    def _build_visible_list(self) -> List[str]:
        """Build the ordered list of visible node IDs based on expansion state."""
        result: List[str] = []
        self._walk_nodes(self._root_children, result)
        return result

    def _walk_nodes(self, children: List[str], result: List[str]):
        """Recursively collect visible nodes in tree order."""
        for node_id in children:
            if node_id not in self._nodes:
                continue
            node = self._nodes[node_id]
            if not node.visible:
                continue
            result.append(node_id)
            if node.expanded and node.children:
                self._walk_nodes(node.children, result)

    # ---------------------------------------------------------------
    # Scrolling
    # ---------------------------------------------------------------

    def _set_scroll_increments(self):
        if sys.platform.startswith("win"):
            self._inner_canvas.configure(yscrollincrement=1)
        elif sys.platform == "darwin":
            self._inner_canvas.configure(yscrollincrement=8)
        else:
            self._inner_canvas.configure(yscrollincrement=30)

    def _on_mouse_wheel(self, event):
        if sys.platform.startswith("win"):
            self._inner_canvas.yview_scroll(-int(event.delta / 120) * 3, "units")
        elif sys.platform == "darwin":
            self._inner_canvas.yview_scroll(-event.delta, "units")
        else:
            if event.num == 4:
                self._inner_canvas.yview_scroll(-3, "units")
            else:
                self._inner_canvas.yview_scroll(3, "units")

    def _ensure_visible(self, node_id: str):
        """Scroll to make the given node visible."""
        if node_id not in self._visible_nodes:
            return

        idx = self._visible_nodes.index(node_id)
        row_h = self._apply_widget_scaling(self._row_height)
        canvas_height = self._inner_canvas.winfo_height()
        if canvas_height <= 1:
            return

        total_height = row_h * len(self._visible_nodes)
        if total_height <= canvas_height:
            return

        y_top = idx * row_h
        y_bot = y_top + row_h

        view_top = self._inner_canvas.yview()[0] * total_height
        view_bot = self._inner_canvas.yview()[1] * total_height

        if y_top < view_top:
            self._inner_canvas.yview_moveto(y_top / total_height)
        elif y_bot > view_bot:
            self._inner_canvas.yview_moveto((y_bot - canvas_height) / total_height)

    # ---------------------------------------------------------------
    # Hit testing
    # ---------------------------------------------------------------

    def _node_at_y(self, y: int) -> Optional[str]:
        """Return the node_id at the given canvas y coordinate, or None."""
        # Convert widget y to canvas coordinate
        canvas_y = self._inner_canvas.canvasy(y)
        row_h = self._apply_widget_scaling(self._row_height)
        if row_h <= 0:
            return None
        idx = int(canvas_y / row_h)
        if 0 <= idx < len(self._visible_nodes):
            return self._visible_nodes[idx]
        return None

    def _is_arrow_hit(self, node_id: str, x: int) -> bool:
        """Check if the click x coordinate is over the arrow area of the given node."""
        if node_id not in self._nodes:
            return False
        node = self._nodes[node_id]
        if not node.children:
            return False

        scaled_indent = self._apply_widget_scaling(self._indent_size)
        arrow_x = int(node.depth * scaled_indent + self._apply_widget_scaling(8) + self._apply_widget_scaling(6))
        half_w = self._apply_widget_scaling(10)
        canvas_x = self._inner_canvas.canvasx(x)
        return abs(canvas_x - arrow_x) <= half_w

    # ---------------------------------------------------------------
    # Mouse events
    # ---------------------------------------------------------------

    def _on_click(self, event):
        self._inner_canvas.focus_set()
        node_id = self._node_at_y(event.y)
        if node_id is None:
            if self._select_mode != "none":
                self._selected.clear()
                self._redraw_tree()
                self._fire_command()
            return

        # Click on arrow toggles expand/collapse
        if self._is_arrow_hit(node_id, event.x):
            self.toggle(node_id)
            return

        # Selection
        if self._select_mode == "single":
            self._selected = [node_id]
            self._focus_node = node_id
        elif self._select_mode == "multiple":
            if node_id in self._selected:
                self._selected.remove(node_id)
            else:
                self._selected.append(node_id)
            self._focus_node = node_id
        # "none" mode: no selection

        self._redraw_tree()
        self._fire_command()

    def _on_double_click(self, event):
        node_id = self._node_at_y(event.y)
        if node_id is None:
            return
        if node_id in self._nodes and self._nodes[node_id].children:
            self.toggle(node_id)

    def _on_motion(self, event):
        node_id = self._node_at_y(event.y)
        if node_id != self._hover_node:
            self._hover_node = node_id
            self._redraw_tree()

    def _on_leave(self, event):
        if self._hover_node is not None:
            self._hover_node = None
            self._redraw_tree()

    def _on_focus_in(self, event):
        if self._focus_node is None and self._visible_nodes:
            self._focus_node = self._visible_nodes[0]
            self._redraw_tree()

    def _on_focus_out(self, event):
        pass  # keep focus node for when focus returns

    # ---------------------------------------------------------------
    # Drag and drop
    # ---------------------------------------------------------------

    def _on_drag_motion(self, event):
        if not self._enable_dnd:
            return

        if not self._dnd_active:
            # Start drag from currently selected node
            source = self._node_at_y(event.y)
            if source and source in self._nodes:
                self._dnd_source = source
                self._dnd_active = True

        if self._dnd_active:
            target = self._node_at_y(event.y)
            if target != self._dnd_target:
                self._dnd_target = target
                self._redraw_tree()

                # Draw drop indicator
                if self._dnd_target and self._dnd_target in self._visible_nodes:
                    idx = self._visible_nodes.index(self._dnd_target)
                    row_h = self._apply_widget_scaling(self._row_height)
                    y = int((idx + 1) * row_h)
                    canvas_width = self._inner_canvas.winfo_width()
                    self._inner_canvas.create_line(
                        0, y, canvas_width, y,
                        fill=self._apply_appearance_mode(self._select_color),
                        width=2,
                        tags=("dnd_indicator",),
                    )

    def _on_drag_release(self, event):
        if not self._dnd_active:
            return

        if (self._dnd_source and self._dnd_target
                and self._dnd_source != self._dnd_target
                and self._dnd_source in self._nodes
                and self._dnd_target in self._nodes):
            # Prevent dropping a node onto its own descendant
            if not self._is_descendant(self._dnd_target, self._dnd_source):
                self.move(self._dnd_source, self._dnd_target)

        self._dnd_source = None
        self._dnd_target = None
        self._dnd_active = False
        self._redraw_tree()

    def _is_descendant(self, node_id: str, ancestor_id: str) -> bool:
        """Check if node_id is a descendant of ancestor_id."""
        if node_id == ancestor_id:
            return True
        node = self._nodes.get(node_id)
        if node is None:
            return False
        if node.parent_id == "":
            return False
        if node.parent_id == ancestor_id:
            return True
        return self._is_descendant(node.parent_id, ancestor_id)

    # ---------------------------------------------------------------
    # Keyboard navigation
    # ---------------------------------------------------------------

    def _on_key_press(self, event):
        if not self._visible_nodes:
            return

        if self._focus_node is None:
            self._focus_node = self._visible_nodes[0] if self._visible_nodes else None
            self._redraw_tree()
            return

        if self._focus_node not in self._visible_nodes:
            self._focus_node = self._visible_nodes[0] if self._visible_nodes else None

        idx = self._visible_nodes.index(self._focus_node) if self._focus_node in self._visible_nodes else 0

        if event.keysym == "Up":
            if idx > 0:
                self._focus_node = self._visible_nodes[idx - 1]
                self._ensure_visible(self._focus_node)
                self._redraw_tree()

        elif event.keysym == "Down":
            if idx < len(self._visible_nodes) - 1:
                self._focus_node = self._visible_nodes[idx + 1]
                self._ensure_visible(self._focus_node)
                self._redraw_tree()

        elif event.keysym == "Right":
            node = self._nodes.get(self._focus_node)
            if node and node.children:
                if not node.expanded:
                    self.expand(self._focus_node)
                else:
                    # Move focus to first child
                    self._focus_node = node.children[0]
                    self._ensure_visible(self._focus_node)
                    self._redraw_tree()

        elif event.keysym == "Left":
            node = self._nodes.get(self._focus_node)
            if node and node.expanded and node.children:
                self.collapse(self._focus_node)
            elif node and node.parent_id and node.parent_id in self._nodes:
                # Move focus to parent
                self._focus_node = node.parent_id
                self._ensure_visible(self._focus_node)
                self._redraw_tree()

        elif event.keysym == "Return":
            node = self._nodes.get(self._focus_node)
            if node and node.children:
                self.toggle(self._focus_node)

        elif event.keysym == "space":
            if self._select_mode == "single":
                self._selected = [self._focus_node]
                self._redraw_tree()
                self._fire_command()
            elif self._select_mode == "multiple":
                if self._focus_node in self._selected:
                    self._selected.remove(self._focus_node)
                else:
                    self._selected.append(self._focus_node)
                self._redraw_tree()
                self._fire_command()

        elif event.keysym == "Home":
            self._focus_node = self._visible_nodes[0]
            self._ensure_visible(self._focus_node)
            self._redraw_tree()

        elif event.keysym == "End":
            self._focus_node = self._visible_nodes[-1]
            self._ensure_visible(self._focus_node)
            self._redraw_tree()

    # ---------------------------------------------------------------
    # Command callback
    # ---------------------------------------------------------------

    def _fire_command(self):
        if self._command is not None:
            self._command(self._selected.copy())

    # ---------------------------------------------------------------
    # Public API: Node manipulation
    # ---------------------------------------------------------------

    def insert(self, parent_id: str, text: str, icon: Optional[str] = None,
               data: Any = None, badge: Optional[str] = None, index: Optional[int] = None) -> str:
        """
        Insert a new node.

        Args:
            parent_id: ID of the parent node, or "" for root level.
            text: Display text for the node.
            icon: Optional icon character or emoji.
            data: Optional arbitrary data to associate with the node.
            badge: Optional badge text (e.g. a count).
            index: Optional insertion index among siblings. None appends.

        Returns:
            The unique node ID of the new node.
        """
        node_id = str(uuid.uuid4())

        if parent_id == "" or parent_id is None:
            depth = 0
            parent_id = ""
        else:
            if parent_id not in self._nodes:
                raise ValueError(f"Parent node '{parent_id}' does not exist")
            depth = self._nodes[parent_id].depth + 1

        node = _TreeNode(
            node_id=node_id,
            parent_id=parent_id,
            text=text,
            icon=icon,
            data=data,
            badge=badge,
            depth=depth,
        )
        self._nodes[node_id] = node

        if parent_id == "":
            if index is not None:
                self._root_children.insert(index, node_id)
            else:
                self._root_children.append(node_id)
        else:
            parent = self._nodes[parent_id]
            if index is not None:
                parent.children.insert(index, node_id)
            else:
                parent.children.append(node_id)

        self._redraw_tree()
        return node_id

    def delete(self, node_id: str):
        """
        Delete a node and all its descendants.

        Args:
            node_id: The ID of the node to delete.
        """
        if node_id not in self._nodes:
            return

        # Collect all descendants first
        to_remove = []
        self._collect_descendants(node_id, to_remove)

        node = self._nodes[node_id]

        # Remove from parent's children list
        if node.parent_id == "":
            if node_id in self._root_children:
                self._root_children.remove(node_id)
        elif node.parent_id in self._nodes:
            parent = self._nodes[node.parent_id]
            if node_id in parent.children:
                parent.children.remove(node_id)

        # Remove from internal stores
        for nid in to_remove:
            if nid in self._selected:
                self._selected.remove(nid)
            if nid == self._focus_node:
                self._focus_node = None
            self._nodes.pop(nid, None)

        self._redraw_tree()

    def _collect_descendants(self, node_id: str, result: List[str]):
        """Collect node_id and all its descendants into result."""
        result.append(node_id)
        if node_id in self._nodes:
            for child_id in self._nodes[node_id].children:
                self._collect_descendants(child_id, result)

    def move(self, node_id: str, new_parent_id: str, index: Optional[int] = None):
        """
        Move a node to a new parent.

        Args:
            node_id: The node to move.
            new_parent_id: The new parent ID, or "" for root level.
            index: Optional insertion position. None appends.
        """
        if node_id not in self._nodes:
            raise ValueError(f"Node '{node_id}' does not exist")
        if new_parent_id != "" and new_parent_id not in self._nodes:
            raise ValueError(f"New parent '{new_parent_id}' does not exist")
        if self._is_descendant(new_parent_id, node_id):
            raise ValueError("Cannot move a node into its own descendant")

        node = self._nodes[node_id]

        # Remove from current parent
        if node.parent_id == "":
            if node_id in self._root_children:
                self._root_children.remove(node_id)
        elif node.parent_id in self._nodes:
            parent = self._nodes[node.parent_id]
            if node_id in parent.children:
                parent.children.remove(node_id)

        # Set new parent
        node.parent_id = new_parent_id
        if new_parent_id == "":
            new_depth = 0
            if index is not None:
                self._root_children.insert(index, node_id)
            else:
                self._root_children.append(node_id)
        else:
            new_depth = self._nodes[new_parent_id].depth + 1
            if index is not None:
                self._nodes[new_parent_id].children.insert(index, node_id)
            else:
                self._nodes[new_parent_id].children.append(node_id)

        # Update depths recursively
        self._update_depth(node_id, new_depth)
        self._redraw_tree()

    def _update_depth(self, node_id: str, depth: int):
        """Recursively update depth for a node and its descendants."""
        if node_id not in self._nodes:
            return
        self._nodes[node_id].depth = depth
        for child_id in self._nodes[node_id].children:
            self._update_depth(child_id, depth + 1)

    # ---------------------------------------------------------------
    # Public API: Expand / Collapse
    # ---------------------------------------------------------------

    def expand(self, node_id: str):
        """Expand a node to show its children."""
        if node_id in self._nodes:
            self._nodes[node_id].expanded = True
            self._redraw_tree()

    def collapse(self, node_id: str):
        """Collapse a node to hide its children."""
        if node_id in self._nodes:
            self._nodes[node_id].expanded = False
            self._redraw_tree()

    def toggle(self, node_id: str):
        """Toggle a node's expanded/collapsed state."""
        if node_id in self._nodes:
            node = self._nodes[node_id]
            node.expanded = not node.expanded
            self._redraw_tree()

    def expand_all(self):
        """Expand all nodes in the tree."""
        for node in self._nodes.values():
            if node.children:
                node.expanded = True
        self._redraw_tree()

    def collapse_all(self):
        """Collapse all nodes in the tree."""
        for node in self._nodes.values():
            node.expanded = False
        self._redraw_tree()

    def expand_to(self, node_id: str):
        """Expand all ancestor nodes to make the given node visible."""
        if node_id not in self._nodes:
            return
        current = self._nodes[node_id].parent_id
        while current and current in self._nodes:
            self._nodes[current].expanded = True
            current = self._nodes[current].parent_id
        self._redraw_tree()
        self._ensure_visible(node_id)

    # ---------------------------------------------------------------
    # Public API: Selection
    # ---------------------------------------------------------------

    def get_selected(self) -> List[str]:
        """Return a list of currently selected node IDs."""
        return self._selected.copy()

    def select(self, node_id: str):
        """Select the given node, replacing any current selection in single mode."""
        if node_id not in self._nodes:
            return
        if self._select_mode == "single":
            self._selected = [node_id]
        elif self._select_mode == "multiple":
            if node_id not in self._selected:
                self._selected.append(node_id)
        self._focus_node = node_id
        self.expand_to(node_id)
        self._redraw_tree()
        self._fire_command()

    def deselect(self, node_id: str):
        """Deselect the given node."""
        if node_id in self._selected:
            self._selected.remove(node_id)
            self._redraw_tree()
            self._fire_command()

    def deselect_all(self):
        """Clear all selections."""
        self._selected.clear()
        self._redraw_tree()
        self._fire_command()

    # ---------------------------------------------------------------
    # Public API: Query
    # ---------------------------------------------------------------

    def item(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Return a dictionary describing the given node.

        Returns:
            Dict with keys: text, icon, data, badge, children, expanded, depth, parent_id.
            Returns None if the node does not exist.
        """
        if node_id not in self._nodes:
            return None
        node = self._nodes[node_id]
        return {
            "text": node.text,
            "icon": node.icon,
            "data": node.data,
            "badge": node.badge,
            "children": node.children.copy(),
            "expanded": node.expanded,
            "depth": node.depth,
            "parent_id": node.parent_id,
        }

    def item_configure(self, node_id: str, **kwargs):
        """
        Update properties of an existing node.

        Supported kwargs: text, icon, data, badge.
        """
        if node_id not in self._nodes:
            return
        node = self._nodes[node_id]
        if "text" in kwargs:
            node.text = kwargs["text"]
        if "icon" in kwargs:
            node.icon = kwargs["icon"]
        if "data" in kwargs:
            node.data = kwargs["data"]
        if "badge" in kwargs:
            node.badge = kwargs["badge"]
        self._redraw_tree()

    def get_children(self, node_id: str = "") -> List[str]:
        """Return the child node IDs of the given node (or root if node_id is "")."""
        if node_id == "" or node_id is None:
            return self._root_children.copy()
        if node_id in self._nodes:
            return self._nodes[node_id].children.copy()
        return []

    def exists(self, node_id: str) -> bool:
        """Return True if the given node ID exists in the tree."""
        return node_id in self._nodes

    # ---------------------------------------------------------------
    # Public API: Search / Filter
    # ---------------------------------------------------------------

    def search(self, term: str):
        """
        Highlight nodes whose text matches the search term (case-insensitive).
        Pass an empty string to clear the search.
        """
        self._search_term = term.lower()
        self._search_matches.clear()

        if self._search_term:
            for node_id, node in self._nodes.items():
                if self._search_term in node.text.lower():
                    self._search_matches.add(node_id)
                    # Expand ancestors so matches are visible
                    self.expand_to(node_id)

        self._redraw_tree()

    def clear_search(self):
        """Clear any active search highlighting."""
        self._search_term = ""
        self._search_matches.clear()
        self._redraw_tree()

    # ---------------------------------------------------------------
    # Public API: Bulk operations
    # ---------------------------------------------------------------

    def clear(self):
        """Remove all nodes from the tree."""
        self._nodes.clear()
        self._root_children.clear()
        self._selected.clear()
        self._focus_node = None
        self._hover_node = None
        self._visible_nodes.clear()
        self._search_term = ""
        self._search_matches.clear()
        self._redraw_tree()

    # ---------------------------------------------------------------
    # Scaling, appearance mode, dimensions
    # ---------------------------------------------------------------

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)

        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._update_layout()
        self._draw()

    def _set_dimensions(self, width=None, height=None):
        super()._set_dimensions(width, height)

        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height),
        )
        self._update_layout()
        self._draw()

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)

    def _on_font_update(self):
        """Called when the CTkFont object is reconfigured."""
        self._redraw_tree()

    def _update_layout(self):
        """Reposition the inner canvas and scrollbar after size or scaling changes."""
        border_offset = self._corner_radius + self._border_width

        self._inner_canvas.place(
            x=self._apply_widget_scaling(border_offset),
            y=self._apply_widget_scaling(border_offset),
            relwidth=1.0,
            relheight=1.0,
            width=-self._apply_widget_scaling(border_offset * 2 + 16),
            height=-self._apply_widget_scaling(border_offset * 2),
        )

        tkinter.Frame.place(
            self._scrollbar,
            relx=1.0,
            x=-self._apply_widget_scaling(border_offset + 14),
            y=self._apply_widget_scaling(border_offset),
            relheight=1.0,
            height=-self._apply_widget_scaling(border_offset * 2),
            width=self._apply_widget_scaling(14),
        )

    # ---------------------------------------------------------------
    # configure / cget
    # ---------------------------------------------------------------

    def configure(self, require_redraw=False, **kwargs):
        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            self._update_layout()
            require_redraw = True

        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            self._update_layout()
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            require_redraw = True

        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "select_color" in kwargs:
            self._select_color = self._check_color_type(kwargs.pop("select_color"))
            require_redraw = True

        if "select_text_color" in kwargs:
            self._select_text_color = self._check_color_type(kwargs.pop("select_text_color"))
            require_redraw = True

        if "hover_color" in kwargs:
            self._hover_color = self._check_color_type(kwargs.pop("hover_color"))
            require_redraw = True

        if "guide_color" in kwargs:
            self._guide_color = self._check_color_type(kwargs.pop("guide_color"))
            require_redraw = True

        if "arrow_color" in kwargs:
            self._arrow_color = self._check_color_type(kwargs.pop("arrow_color"))
            require_redraw = True

        if "badge_color" in kwargs:
            self._badge_color = self._check_color_type(kwargs.pop("badge_color"))
            require_redraw = True

        if "badge_text_color" in kwargs:
            self._badge_text_color = self._check_color_type(kwargs.pop("badge_text_color"))
            require_redraw = True

        if "highlight_color" in kwargs:
            self._highlight_color = self._check_color_type(kwargs.pop("highlight_color"))
            require_redraw = True

        if "scrollbar_fg_color" in kwargs:
            self._scrollbar.configure(fg_color=kwargs.pop("scrollbar_fg_color"))

        if "scrollbar_button_color" in kwargs:
            self._scrollbar.configure(button_color=kwargs.pop("scrollbar_button_color"))

        if "scrollbar_button_hover_color" in kwargs:
            self._scrollbar.configure(button_hover_color=kwargs.pop("scrollbar_button_hover_color"))

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._on_font_update)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._on_font_update)
            require_redraw = True

        if "row_height" in kwargs:
            self._row_height = kwargs.pop("row_height")
            require_redraw = True

        if "indent_size" in kwargs:
            self._indent_size = kwargs.pop("indent_size")
            require_redraw = True

        if "show_guides" in kwargs:
            self._show_guides = kwargs.pop("show_guides")
            require_redraw = True

        if "select_mode" in kwargs:
            self._select_mode = kwargs.pop("select_mode")
            if self._select_mode == "none":
                self._selected.clear()
            elif self._select_mode == "single" and len(self._selected) > 1:
                self._selected = self._selected[:1]
            require_redraw = True

        if "enable_dnd" in kwargs:
            new_dnd = kwargs.pop("enable_dnd")
            if new_dnd and not self._enable_dnd:
                self._inner_canvas.bind("<B1-Motion>", self._on_drag_motion)
                self._inner_canvas.bind("<ButtonRelease-1>", self._on_drag_release)
            elif not new_dnd and self._enable_dnd:
                self._inner_canvas.unbind("<B1-Motion>")
                self._inner_canvas.unbind("<ButtonRelease-1>")
            self._enable_dnd = new_dnd

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
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
        elif attribute_name == "select_color":
            return self._select_color
        elif attribute_name == "select_text_color":
            return self._select_text_color
        elif attribute_name == "hover_color":
            return self._hover_color
        elif attribute_name == "guide_color":
            return self._guide_color
        elif attribute_name == "arrow_color":
            return self._arrow_color
        elif attribute_name == "badge_color":
            return self._badge_color
        elif attribute_name == "badge_text_color":
            return self._badge_text_color
        elif attribute_name == "highlight_color":
            return self._highlight_color
        elif attribute_name == "scrollbar_fg_color":
            return self._scrollbar.cget("fg_color")
        elif attribute_name == "scrollbar_button_color":
            return self._scrollbar.cget("button_color")
        elif attribute_name == "scrollbar_button_hover_color":
            return self._scrollbar.cget("button_hover_color")
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "row_height":
            return self._row_height
        elif attribute_name == "indent_size":
            return self._indent_size
        elif attribute_name == "show_guides":
            return self._show_guides
        elif attribute_name == "select_mode":
            return self._select_mode
        elif attribute_name == "enable_dnd":
            return self._enable_dnd
        elif attribute_name == "command":
            return self._command
        else:
            return super().cget(attribute_name)

    # ---------------------------------------------------------------
    # bind / unbind / focus
    # ---------------------------------------------------------------

    def bind(self, sequence=None, command=None, add=True):
        """Bindable on the inner canvas."""
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._inner_canvas.bind(sequence, command, add=True)

    def unbind(self, sequence=None, funcid=None):
        """Unbind from the inner canvas."""
        if funcid is not None:
            raise ValueError(
                "'funcid' argument can only be None, because there is a bug in"
                " tkinter and its not clear whether the internal callbacks will be unbinded or not"
            )
        self._inner_canvas.unbind(sequence, None)

    def focus(self):
        return self._inner_canvas.focus()

    def focus_set(self):
        return self._inner_canvas.focus_set()

    def focus_force(self):
        return self._inner_canvas.focus_force()

    # ---------------------------------------------------------------
    # Destroy
    # ---------------------------------------------------------------

    def destroy(self):
        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._on_font_update)
        super().destroy()
