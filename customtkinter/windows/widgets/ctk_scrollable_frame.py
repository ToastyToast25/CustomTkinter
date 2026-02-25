from typing import Union, Tuple, Optional, Any, Callable
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
import tkinter
import sys

from .ctk_frame import CTkFrame
from .ctk_scrollbar import CTkScrollbar
from .appearance_mode import CTkAppearanceModeBaseClass
from .scaling import CTkScalingBaseClass
from .core_widget_classes import CTkBaseClass
from .ctk_label import CTkLabel
from .font import CTkFont
from .theme import ThemeManager


class CTkScrollableFrame(tkinter.Frame, CTkAppearanceModeBaseClass, CTkScalingBaseClass):
    # class-level registry for mouse wheel isolation
    _instances: list = []
    _global_bindings_set: bool = False

    @classmethod
    def _ensure_global_bindings(cls, widget):
        """Set up global mouse wheel binding once, shared by all instances."""
        if not cls._global_bindings_set:
            if "linux" in sys.platform:
                widget.bind_all("<Button-4>", cls._dispatch_mouse_wheel, add=True)
                widget.bind_all("<Button-5>", cls._dispatch_mouse_wheel, add=True)
            else:
                widget.bind_all("<MouseWheel>", cls._dispatch_mouse_wheel, add=True)
            widget.bind_all("<KeyPress-Shift_L>", cls._dispatch_shift_press, add=True)
            widget.bind_all("<KeyPress-Shift_R>", cls._dispatch_shift_press, add=True)
            widget.bind_all("<KeyRelease-Shift_L>", cls._dispatch_shift_release, add=True)
            widget.bind_all("<KeyRelease-Shift_R>", cls._dispatch_shift_release, add=True)
            cls._global_bindings_set = True

    @classmethod
    def _remove_global_bindings(cls, widget):
        """Remove global bindings when the last instance is destroyed."""
        if cls._global_bindings_set and not cls._instances:
            try:
                if "linux" in sys.platform:
                    widget.unbind_all("<Button-4>")
                    widget.unbind_all("<Button-5>")
                else:
                    widget.unbind_all("<MouseWheel>")
                widget.unbind_all("<KeyPress-Shift_L>")
                widget.unbind_all("<KeyPress-Shift_R>")
                widget.unbind_all("<KeyRelease-Shift_L>")
                widget.unbind_all("<KeyRelease-Shift_R>")
            except Exception:
                pass
            cls._global_bindings_set = False

    @classmethod
    def _dispatch_mouse_wheel(cls, event):
        """Route mouse wheel event to the correct instance under the cursor."""
        for instance in cls._instances:
            try:
                if instance.check_if_master_is_canvas(event.widget):
                    instance._mouse_wheel_all(event)
                    return
            except Exception:
                continue

    @classmethod
    def _dispatch_shift_press(cls, event):
        for instance in cls._instances:
            instance._shift_pressed = True

    @classmethod
    def _dispatch_shift_release(cls, event):
        for instance in cls._instances:
            instance._shift_pressed = False

    def __init__(self,
                 master: Any,
                 width: int = 200,
                 height: int = 200,
                 corner_radius: Optional[Union[int, str]] = None,
                 border_width: Optional[Union[int, str]] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 scrollbar_fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 scrollbar_button_color: Optional[Union[str, Tuple[str, str]]] = None,
                 scrollbar_button_hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 label_fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 label_text_color: Optional[Union[str, Tuple[str, str]]] = None,

                 label_text: str = "",
                 label_font: Optional[Union[tuple, CTkFont]] = None,
                 label_anchor: str = "center",
                 orientation: Literal["vertical", "horizontal"] = "vertical",
                 scroll_command: Optional[Callable] = None):

        self._orientation = orientation

        # dimensions independent of scaling
        self._desired_width = width  # _desired_width and _desired_height, represent desired size set by width and height
        self._desired_height = height
        self._border_width = border_width if border_width else 0

        self._parent_frame = CTkFrame(master=master, width=0, height=0, corner_radius=corner_radius,
                                      border_width=border_width, bg_color=bg_color, fg_color=fg_color, border_color=border_color)
        self._parent_canvas = tkinter.Canvas(master=self._parent_frame, highlightthickness=0)
        self._set_scroll_increments()

        if self._orientation == "horizontal":
            self._scrollbar = CTkScrollbar(master=self._parent_frame, orientation="horizontal", command=self._parent_canvas.xview,
                                           fg_color=scrollbar_fg_color, button_color=scrollbar_button_color, button_hover_color=scrollbar_button_hover_color)
            self._parent_canvas.configure(xscrollcommand=self._scroll_command_wrapper)
        elif self._orientation == "vertical":
            self._scrollbar = CTkScrollbar(master=self._parent_frame, orientation="vertical", command=self._parent_canvas.yview,
                                           fg_color=scrollbar_fg_color, button_color=scrollbar_button_color, button_hover_color=scrollbar_button_hover_color)
            self._parent_canvas.configure(yscrollcommand=self._scroll_command_wrapper)

        self._label_text = label_text
        self._label = CTkLabel(self._parent_frame, text=label_text, anchor=label_anchor, font=label_font,
                               corner_radius=self._parent_frame.cget("corner_radius"), text_color=label_text_color,
                               fg_color=ThemeManager.theme["CTkScrollableFrame"]["label_fg_color"] if label_fg_color is None else label_fg_color)

        tkinter.Frame.__init__(self, master=self._parent_canvas, highlightthickness=0)
        CTkAppearanceModeBaseClass.__init__(self)
        CTkScalingBaseClass.__init__(self, scaling_type="widget")

        self._create_grid()

        self._parent_canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                                      height=self._apply_widget_scaling(self._desired_height))

        self.bind("<Configure>", lambda e: self._parent_canvas.configure(scrollregion=self._parent_canvas.bbox("all")))
        self._parent_canvas.bind("<Configure>", self._fit_frame_dimensions_to_canvas)

        # register instance and set up shared global bindings
        self._instances.append(self)
        self._ensure_global_bindings(self)
        self._create_window_id = self._parent_canvas.create_window(0, 0, window=self, anchor="nw")

        if self._parent_frame.cget("fg_color") == "transparent":
            tkinter.Frame.configure(self, bg=self._apply_appearance_mode(self._parent_frame.cget("bg_color")))
            self._parent_canvas.configure(bg=self._apply_appearance_mode(self._parent_frame.cget("bg_color")))
        else:
            tkinter.Frame.configure(self, bg=self._apply_appearance_mode(self._parent_frame.cget("fg_color")))
            self._parent_canvas.configure(bg=self._apply_appearance_mode(self._parent_frame.cget("fg_color")))

        self._scroll_anim_id = None
        self._on_scroll_callback = scroll_command
        self._shift_pressed = False

    def _scroll_command_wrapper(self, *args):
        """Wrapper for yscrollcommand/xscrollcommand that updates scrollbar and fires callback."""
        self._scrollbar.set(*args)
        if self._on_scroll_callback is not None:
            try:
                # args is (first_fraction, last_fraction) from the canvas
                self._on_scroll_callback(float(args[0]))
            except Exception:
                pass

    def destroy(self):
        # cancel any running scroll animation
        if self._scroll_anim_id is not None:
            self.after_cancel(self._scroll_anim_id)
            self._scroll_anim_id = None

        # unregister instance
        try:
            self._instances.remove(self)
        except ValueError:
            pass

        # remove global bindings if this was the last instance
        self._remove_global_bindings(self)

        tkinter.Frame.destroy(self)
        self._parent_frame.destroy()
        CTkAppearanceModeBaseClass.destroy(self)
        CTkScalingBaseClass.destroy(self)

    def _create_grid(self):
        border_spacing = self._apply_widget_scaling(self._parent_frame.cget("corner_radius") + self._parent_frame.cget("border_width"))

        if self._orientation == "horizontal":
            border_padding = (0, self._border_width +1)
            self._parent_frame.grid_columnconfigure(0, weight=1)
            self._parent_frame.grid_rowconfigure(1, weight=1)
            self._parent_canvas.grid(row=1, column=0, sticky="nsew", padx=border_spacing, pady=(border_spacing, 0))
            self._scrollbar.grid(row=2, column=0, sticky="nsew", padx=border_spacing, pady=border_padding)

            if self._label_text is not None and self._label_text != "":
                self._label.grid(row=0, column=0, sticky="ew", padx=border_spacing, pady=border_spacing)
            else:
                self._label.grid_forget()

        elif self._orientation == "vertical":
            border_padding = (0, self._border_width +1)
            self._parent_frame.grid_columnconfigure(0, weight=1)
            self._parent_frame.grid_rowconfigure(1, weight=1)
            self._parent_canvas.grid(row=1, column=0, sticky="nsew", padx=(border_spacing, 0), pady=border_spacing)
            self._scrollbar.grid(row=1, column=1, sticky="nsew", padx=border_padding, pady=border_spacing)

            if self._label_text is not None and self._label_text != "":
                self._label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=border_spacing, pady=border_spacing)
            else:
                self._label.grid_forget()

    def _set_appearance_mode(self, mode_string):
        super()._set_appearance_mode(mode_string)

        if self._parent_frame.cget("fg_color") == "transparent":
            tkinter.Frame.configure(self, bg=self._apply_appearance_mode(self._parent_frame.cget("bg_color")))
            self._parent_canvas.configure(bg=self._apply_appearance_mode(self._parent_frame.cget("bg_color")))
        else:
            tkinter.Frame.configure(self, bg=self._apply_appearance_mode(self._parent_frame.cget("fg_color")))
            self._parent_canvas.configure(bg=self._apply_appearance_mode(self._parent_frame.cget("fg_color")))

    def _set_scaling(self, new_widget_scaling, new_window_scaling):
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._parent_canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                                      height=self._apply_widget_scaling(self._desired_height))

    def _set_dimensions(self, width=None, height=None):
        if width is not None:
            self._desired_width = width
        if height is not None:
            self._desired_height = height

        self._parent_canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                                      height=self._apply_widget_scaling(self._desired_height))

    def configure(self, **kwargs):
        if "width" in kwargs:
            self._set_dimensions(width=kwargs.pop("width"))

        if "height" in kwargs:
            self._set_dimensions(height=kwargs.pop("height"))

        if "corner_radius" in kwargs:
            new_corner_radius = kwargs.pop("corner_radius")
            self._parent_frame.configure(corner_radius=new_corner_radius)
            if self._label is not None:
                self._label.configure(corner_radius=new_corner_radius)
            self._create_grid()

        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            self._parent_frame.configure(border_width=self._border_width)
            self._create_grid()

        if "fg_color" in kwargs:
            self._parent_frame.configure(fg_color=kwargs.pop("fg_color"))

            if self._parent_frame.cget("fg_color") == "transparent":
                tkinter.Frame.configure(self, bg=self._apply_appearance_mode(self._parent_frame.cget("bg_color")))
                self._parent_canvas.configure(bg=self._apply_appearance_mode(self._parent_frame.cget("bg_color")))
            else:
                tkinter.Frame.configure(self, bg=self._apply_appearance_mode(self._parent_frame.cget("fg_color")))
                self._parent_canvas.configure(bg=self._apply_appearance_mode(self._parent_frame.cget("fg_color")))

            for child in self.winfo_children():
                if isinstance(child, CTkBaseClass):
                    child.configure(bg_color=self._parent_frame.cget("fg_color"))

        if "scrollbar_fg_color" in kwargs:
            self._scrollbar.configure(fg_color=kwargs.pop("scrollbar_fg_color"))

        if "scrollbar_button_color" in kwargs:
            self._scrollbar.configure(button_color=kwargs.pop("scrollbar_button_color"))

        if "scrollbar_button_hover_color" in kwargs:
            self._scrollbar.configure(button_hover_color=kwargs.pop("scrollbar_button_hover_color"))

        if "label_fg_color" in kwargs:
            self._label.configure(fg_color=kwargs.pop("label_fg_color"))

        if "label_text_color" in kwargs:
            self._label.configure(text_color=kwargs.pop("label_text_color"))

        if "label_text" in kwargs:
            self._label_text = kwargs.pop("label_text")
            self._label.configure(text=self._label_text)
            self._create_grid()

        if "label_font" in kwargs:
            self._label.configure(font=kwargs.pop("label_font"))

        if "label_anchor" in kwargs:
            self._label.configure(anchor=kwargs.pop("label_anchor"))

        if "scroll_command" in kwargs:
            self._on_scroll_callback = kwargs.pop("scroll_command")

        self._parent_frame.configure(**kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "width":
            return self._desired_width
        elif attribute_name == "height":
            return self._desired_height

        elif attribute_name.startswith("scrollbar_fg_color"):
            return self._scrollbar.cget("fg_color")
        elif attribute_name.startswith("scrollbar_button_color"):
            return self._scrollbar.cget("button_color")
        elif attribute_name.startswith("scrollbar_button_hover_color"):
            return self._scrollbar.cget("button_hover_color")
        elif attribute_name == "label_fg_color":
            return self._label.cget("fg_color")
        elif attribute_name == "label_text_color":
            return self._label.cget("_text_color")

        elif attribute_name == "label_text":
            return self._label_text
        elif attribute_name == "label_font":
            return self._label.cget("font")
        elif attribute_name == "label_anchor":
            return self._label.cget("anchor")
        elif attribute_name == "orientation":
            return self._orientation
        elif attribute_name == "scroll_command":
            return self._on_scroll_callback

        else:
            return self._parent_frame.cget(attribute_name)

    def _fit_frame_dimensions_to_canvas(self, event):
        if self._orientation == "horizontal":
            self._parent_canvas.itemconfigure(self._create_window_id, height=self._parent_canvas.winfo_height())
        elif self._orientation == "vertical":
            self._parent_canvas.itemconfigure(self._create_window_id, width=self._parent_canvas.winfo_width())

    def _set_scroll_increments(self):
        if sys.platform.startswith("win"):
            self._parent_canvas.configure(xscrollincrement=1, yscrollincrement=1)
        elif sys.platform == "darwin":
            self._parent_canvas.configure(xscrollincrement=4, yscrollincrement=8)
        else:
            self._parent_canvas.configure(xscrollincrement=30, yscrollincrement=30)

    def _mouse_wheel_all(self, event):
        if self.check_if_master_is_canvas(event.widget):
            if sys.platform.startswith("win"):
                if self._shift_pressed:
                    if self._parent_canvas.xview() != (0.0, 1.0):
                        self._parent_canvas.xview("scroll", -int(event.delta / 6), "units")
                else:
                    if self._parent_canvas.yview() != (0.0, 1.0):
                        self._parent_canvas.yview("scroll", -int(event.delta / 6), "units")
            elif sys.platform == "darwin":
                if self._shift_pressed:
                    if self._parent_canvas.xview() != (0.0, 1.0):
                        self._parent_canvas.xview("scroll", -event.delta, "units")
                else:
                    if self._parent_canvas.yview() != (0.0, 1.0):
                        self._parent_canvas.yview("scroll", -event.delta, "units")
            else:
                if self._shift_pressed:
                    if self._parent_canvas.xview() != (0.0, 1.0):
                        self._parent_canvas.xview_scroll(-1 if event.num == 4 else 1, "units")
                else:
                    if self._parent_canvas.yview() != (0.0, 1.0):
                        self._parent_canvas.yview_scroll(-1 if event.num == 4 else 1, "units")


    def _keyboard_shift_press_all(self, event):
        self._shift_pressed = True

    def _keyboard_shift_release_all(self, event):
        self._shift_pressed = False

    def check_if_master_is_canvas(self, widget):
        if widget == self._parent_canvas:
            return True
        elif widget.master is not None:
            return self.check_if_master_is_canvas(widget.master)
        else:
            return False

    def _animate_scroll(self, start_pos: float, end_pos: float, duration: int):
        """Animate scroll from start_pos to end_pos fraction using ease-out-cubic."""
        if self._scroll_anim_id is not None:
            self.after_cancel(self._scroll_anim_id)
            self._scroll_anim_id = None

        elapsed = [0]
        interval = 16  # ~60fps

        def tick():
            elapsed[0] += interval
            t = min(1.0, elapsed[0] / duration)
            t_eased = 1 - (1 - t) ** 3  # ease-out-cubic
            pos = start_pos + (end_pos - start_pos) * t_eased
            if self._orientation == "vertical":
                self._parent_canvas.yview_moveto(pos)
            else:
                self._parent_canvas.xview_moveto(pos)
            if t < 1.0:
                self._scroll_anim_id = self.after(interval, tick)
            else:
                self._scroll_anim_id = None
                if self._on_scroll_callback:
                    self._on_scroll_callback(pos)

        tick()

    def scroll_to_top(self, animate: bool = False, duration: int = 300):
        """Scroll to the top (vertical) or left (horizontal)."""
        self._parent_canvas.update_idletasks()
        if animate:
            start = self.get_scroll_position()
            self._animate_scroll(start, 0.0, duration)
        else:
            if self._orientation == "vertical":
                self._parent_canvas.yview_moveto(0.0)
            else:
                self._parent_canvas.xview_moveto(0.0)

    def scroll_to_bottom(self, animate: bool = False, duration: int = 300):
        """Scroll to the bottom (vertical) or right (horizontal)."""
        self._parent_canvas.update_idletasks()
        if animate:
            start = self.get_scroll_position()
            self._animate_scroll(start, 1.0, duration)
        else:
            if self._orientation == "vertical":
                self._parent_canvas.yview_moveto(1.0)
            else:
                self._parent_canvas.xview_moveto(1.0)

    def scroll_to_widget(self, widget, animate: bool = False, duration: int = 300):
        """Scroll so that the given child widget is visible."""
        self._parent_canvas.update_idletasks()

        # get canvas scroll region
        bbox = self._parent_canvas.bbox("all")
        if not bbox:
            return

        if self._orientation == "vertical":
            total_height = bbox[3] - bbox[1]
            if total_height <= 0:
                return
            canvas_height = self._parent_canvas.winfo_height()
            # widget position relative to the scrollable frame
            try:
                widget_y = widget.winfo_y()
                widget_h = widget.winfo_height()
            except Exception:
                return
            # calculate fraction to center the widget
            target = max(0, widget_y - (canvas_height - widget_h) // 2)
            fraction = max(0.0, min(1.0, target / total_height))
        else:
            total_width = bbox[2] - bbox[0]
            if total_width <= 0:
                return
            canvas_width = self._parent_canvas.winfo_width()
            try:
                widget_x = widget.winfo_x()
                widget_w = widget.winfo_width()
            except Exception:
                return
            target = max(0, widget_x - (canvas_width - widget_w) // 2)
            fraction = max(0.0, min(1.0, target / total_width))

        if animate:
            start = self.get_scroll_position()
            self._animate_scroll(start, fraction, duration)
        else:
            if self._orientation == "vertical":
                self._parent_canvas.yview_moveto(fraction)
            else:
                self._parent_canvas.xview_moveto(fraction)

    def get_scroll_position(self) -> float:
        """Get current scroll position as a fraction (0.0 to 1.0)."""
        if self._orientation == "vertical":
            return self._parent_canvas.yview()[0]
        else:
            return self._parent_canvas.xview()[0]

    def set_scroll_position(self, fraction: float, animate: bool = False, duration: int = 300):
        """Set scroll position as a fraction (0.0 to 1.0)."""
        fraction = max(0.0, min(1.0, fraction))
        self._parent_canvas.update_idletasks()
        if animate:
            start = self.get_scroll_position()
            self._animate_scroll(start, fraction, duration)
        else:
            if self._orientation == "vertical":
                self._parent_canvas.yview_moveto(fraction)
            else:
                self._parent_canvas.xview_moveto(fraction)

    def scroll_by(self, amount: float, animate: bool = False, duration: int = 300):
        """Scroll by a relative fraction amount (positive = down/right, negative = up/left)."""
        self._parent_canvas.update_idletasks()
        current = self.get_scroll_position()
        target = max(0.0, min(1.0, current + amount))
        if animate:
            self._animate_scroll(current, target, duration)
        else:
            if self._orientation == "vertical":
                self._parent_canvas.yview_moveto(target)
            else:
                self._parent_canvas.xview_moveto(target)

    def is_at_top(self) -> bool:
        """Return True if scrolled to the very top (vertical) or left (horizontal)."""
        if self._orientation == "vertical":
            return self._parent_canvas.yview()[0] <= 0.0
        else:
            return self._parent_canvas.xview()[0] <= 0.0

    def is_at_bottom(self) -> bool:
        """Return True if scrolled to the very bottom (vertical) or right (horizontal)."""
        if self._orientation == "vertical":
            return self._parent_canvas.yview()[1] >= 1.0
        else:
            return self._parent_canvas.xview()[1] >= 1.0

    def pack(self, **kwargs):
        self._parent_frame.pack(**kwargs)

    def place(self, **kwargs):
        self._parent_frame.place(**kwargs)

    def grid(self, **kwargs):
        self._parent_frame.grid(**kwargs)

    def pack_forget(self):
        self._parent_frame.pack_forget()

    def place_forget(self, **kwargs):
        self._parent_frame.place_forget()

    def grid_forget(self, **kwargs):
        self._parent_frame.grid_forget()

    def grid_remove(self, **kwargs):
        self._parent_frame.grid_remove()

    def grid_propagate(self, **kwargs):
        self._parent_frame.grid_propagate()

    def grid_info(self, **kwargs):
        return self._parent_frame.grid_info()

    def lift(self, aboveThis=None):
        self._parent_frame.lift(aboveThis)

    def lower(self, belowThis=None):
        self._parent_frame.lower(belowThis)
