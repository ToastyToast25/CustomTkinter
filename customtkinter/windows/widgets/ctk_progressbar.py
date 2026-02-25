import tkinter
import math
from typing import Union, Tuple, Optional, Callable, Any
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass


class CTkProgressBar(CTkBaseClass):
    """
    Progressbar with rounded corners, border, variable support,
    indeterminate mode, vertical orientation.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: Any,
                 width: Optional[int] = None,
                 height: Optional[int] = None,
                 corner_radius: Optional[int] = None,
                 border_width: Optional[int] = None,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 progress_color: Optional[Union[str, Tuple[str, str]]] = None,

                 variable: Union[tkinter.Variable, None] = None,
                 orientation: str = "horizontal",
                 mode: Literal["determinate", "indeterminate"] = "determinate",
                 determinate_speed: float = 1,
                 indeterminate_speed: float = 1,
                 **kwargs):

        # set default dimensions according to orientation
        if width is None:
            if orientation.lower() == "vertical":
                width = 8
            else:
                width = 200
        if height is None:
            if orientation.lower() == "vertical":
                height = 200
            else:
                height = 8

        # transfer basic functionality (_bg_color, size, __appearance_mode, scaling) to CTkBaseClass
        super().__init__(master=master, bg_color=bg_color, width=width, height=height, **kwargs)

        # color
        self._border_color = ThemeManager.theme["CTkProgressBar"]["border_color"] if border_color is None else self._check_color_type(border_color)
        self._fg_color = ThemeManager.theme["CTkProgressBar"]["fg_color"] if fg_color is None else self._check_color_type(fg_color)
        self._progress_color = ThemeManager.theme["CTkProgressBar"]["progress_color"] if progress_color is None else self._check_color_type(progress_color)

        # control variable
        self._variable = variable
        self._variable_callback_blocked = False
        self._variable_callback_name = None
        self._loop_after_id = None

        # shape
        self._corner_radius = ThemeManager.theme["CTkProgressBar"]["corner_radius"] if corner_radius is None else corner_radius
        self._border_width = ThemeManager.theme["CTkProgressBar"]["border_width"] if border_width is None else border_width
        self._determinate_value: float = 0.5  # range 0-1
        self._determinate_speed = determinate_speed  # range 0-1
        self._indeterminate_value: float = 0  # range 0-inf
        self._indeterminate_width: float = 0.4  # range 0-1
        self._indeterminate_speed = indeterminate_speed  # range 0-1 to travel in 50ms
        self._loop_running: bool = False
        self._orientation = orientation
        self._mode = mode  # "determinate" or "indeterminate"

        # pulse animation state
        self._pulse_running: bool = False
        self._pulse_after_id = None
        self._pulse_color_2 = None
        self._pulse_speed: int = 800  # full cycle in ms
        self._pulse_phase: float = 0.0

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, rowspan=1, columnspan=1, sticky="nswe")
        self._draw_engine = DrawEngine(self._canvas)

        self._draw()  # initial draw

        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._variable_callback_blocked = True
            self.set(self._variable.get(), from_variable_callback=True)
            self._variable_callback_blocked = False

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

    def destroy(self):
        if self._loop_after_id is not None:
            self.after_cancel(self._loop_after_id)
            self._loop_after_id = None
        self._loop_running = False

        if self._pulse_after_id is not None:
            self.after_cancel(self._pulse_after_id)
            self._pulse_after_id = None
        self._pulse_running = False

        if self._variable is not None:
            self._variable.trace_remove("write", self._variable_callback_name)

        super().destroy()

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        if self._orientation.lower() == "horizontal":
            orientation = "w"
        elif self._orientation.lower() == "vertical":
            orientation = "s"
        else:
            orientation = "w"

        if self._mode == "determinate":
            requires_recoloring = self._draw_engine.draw_rounded_progress_bar_with_border(self._apply_widget_scaling(self._current_width),
                                                                                          self._apply_widget_scaling(self._current_height),
                                                                                          self._apply_widget_scaling(self._corner_radius),
                                                                                          self._apply_widget_scaling(self._border_width),
                                                                                          0,
                                                                                          self._determinate_value,
                                                                                          orientation)
        else:  # indeterminate mode
            progress_value = (math.sin(self._indeterminate_value * math.pi / 40) + 1) / 2
            progress_value_1 = min(1.0, progress_value + (self._indeterminate_width / 2))
            progress_value_2 = max(0.0, progress_value - (self._indeterminate_width / 2))

            requires_recoloring = self._draw_engine.draw_rounded_progress_bar_with_border(self._apply_widget_scaling(self._current_width),
                                                                                          self._apply_widget_scaling(self._current_height),
                                                                                          self._apply_widget_scaling(self._corner_radius),
                                                                                          self._apply_widget_scaling(self._border_width),
                                                                                          progress_value_1,
                                                                                          progress_value_2,
                                                                                          orientation)

        if no_color_updates is False or requires_recoloring:
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._canvas.itemconfig("border_parts",
                                    fill=self._apply_appearance_mode(self._border_color),
                                    outline=self._apply_appearance_mode(self._border_color))
            self._canvas.itemconfig("inner_parts",
                                    fill=self._apply_appearance_mode(self._fg_color),
                                    outline=self._apply_appearance_mode(self._fg_color))
            self._canvas.itemconfig("progress_parts",
                                    fill=self._apply_appearance_mode(self._progress_color),
                                    outline=self._apply_appearance_mode(self._progress_color))

    def configure(self, require_redraw=False, **kwargs):
        if "corner_radius" in kwargs:
            self._corner_radius = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._border_width = kwargs.pop("border_width")
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True

        if "border_color" in kwargs:
            self._border_color = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "progress_color" in kwargs:
            self._progress_color = self._check_color_type(kwargs.pop("progress_color"))
            require_redraw = True

        if "variable" in kwargs:
            if self._variable is not None:
                self._variable.trace_remove("write", self._variable_callback_name)
            self._variable = kwargs.pop("variable")
            if self._variable is not None and self._variable != "":
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
                self.set(self._variable.get(), from_variable_callback=True)

        if "mode" in kwargs:
            self._mode = kwargs.pop("mode")
            require_redraw = True

        if "determinate_speed" in kwargs:
            self._determinate_speed = kwargs.pop("determinate_speed")

        if "indeterminate_speed" in kwargs:
            self._indeterminate_speed = kwargs.pop("indeterminate_speed")

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
        elif attribute_name == "progress_color":
            return self._progress_color

        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "orientation":
            return self._orientation
        elif attribute_name == "mode":
            return self._mode
        elif attribute_name == "determinate_speed":
            return self._determinate_speed
        elif attribute_name == "indeterminate_speed":
            return self._indeterminate_speed

        else:
            return super().cget(attribute_name)

    def _variable_callback(self, var_name, index, mode):
        if not self._variable_callback_blocked:
            self.set(self._variable.get(), from_variable_callback=True)

    def set(self, value, from_variable_callback=False):
        """ set determinate value """
        self._determinate_value = value

        if self._determinate_value > 1:
            self._determinate_value = 1
        elif self._determinate_value < 0:
            self._determinate_value = 0

        self._draw(no_color_updates=True)

        if self._variable is not None and not from_variable_callback:
            self._variable_callback_blocked = True
            self._variable.set(round(self._determinate_value) if isinstance(self._variable, tkinter.IntVar) else self._determinate_value)
            self._variable_callback_blocked = False

    def get(self) -> float:
        """ get determinate value """
        return self._determinate_value

    def start(self):
        """ start automatic mode """
        if not self._loop_running:
            self._loop_running = True
            self._internal_loop()

    def stop(self):
        """ stop automatic mode """
        if self._loop_after_id is not None:
            self.after_cancel(self._loop_after_id)
        self._loop_running = False

    def _internal_loop(self):
        if self._loop_running:
            if self._mode == "determinate":
                self._determinate_value += self._determinate_speed / 50
                if self._determinate_value > 1:
                    self._determinate_value -= 1
                self._draw()
                self._loop_after_id = self.after(20, self._internal_loop)
            else:
                self._indeterminate_value += self._indeterminate_speed
                self._draw()
                self._loop_after_id = self.after(20, self._internal_loop)

    def step(self):
        """ increase progress """
        if self._mode == "determinate":
            self._determinate_value += self._determinate_speed / 50
            if self._determinate_value > 1:
                self._determinate_value -= 1
            self._draw()
        else:
            self._indeterminate_value += self._indeterminate_speed
            self._draw()

    @staticmethod
    def _lerp_hex(color1: str, color2: str, t: float) -> str:
        """ linearly interpolate between two hex colors, t in [0, 1] """
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def reset(self):
        """ reset progress bar: stop all animations and set value to 0 """
        self.stop()
        self.stop_pulse()
        self._determinate_value = 0
        self._indeterminate_value = 0
        self._draw()

    def start_pulse(self, pulse_color: Optional[str] = None, speed: int = 800):
        """ start pulsing progress_color between current color and pulse_color.
            speed: full cycle duration in milliseconds. """
        base = self._apply_appearance_mode(self._progress_color)
        if pulse_color is None:
            # auto-generate a brighter version of progress_color
            r, g, b = int(base[1:3], 16), int(base[3:5], 16), int(base[5:7], 16)
            r = min(255, r + 40)
            g = min(255, g + 40)
            b = min(255, b + 40)
            pulse_color = f"#{r:02x}{g:02x}{b:02x}"
        self._pulse_color_2 = pulse_color
        self._pulse_speed = max(100, speed)
        self._pulse_phase = 0.0
        if not self._pulse_running:
            self._pulse_running = True
            self._pulse_tick()

    def stop_pulse(self):
        """ stop pulse animation and restore original progress_color """
        self._pulse_running = False
        if self._pulse_after_id is not None:
            self.after_cancel(self._pulse_after_id)
            self._pulse_after_id = None
        # restore original color
        self._canvas.itemconfig("progress_parts",
                                fill=self._apply_appearance_mode(self._progress_color),
                                outline=self._apply_appearance_mode(self._progress_color))

    def _pulse_tick(self):
        if not self._pulse_running:
            return
        # sine easing: smooth 0->1->0 over one cycle
        t = (math.sin(self._pulse_phase * math.pi * 2) + 1) / 2
        base = self._apply_appearance_mode(self._progress_color)
        color = self._lerp_hex(base, self._pulse_color_2, t)
        self._canvas.itemconfig("progress_parts", fill=color, outline=color)
        # advance phase
        interval = 16  # ~60fps
        self._pulse_phase += interval / self._pulse_speed
        if self._pulse_phase >= 1.0:
            self._pulse_phase -= 1.0
        self._pulse_after_id = self.after(interval, self._pulse_tick)

    def bind(self, sequence: str = None, command: Callable = None, add: Union[str, bool] = True):
        """ called on the tkinter.Canvas """
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, command, add=True)

    def unbind(self, sequence: str = None, funcid: str = None):
        """ called on the tkinter.Label and tkinter.Canvas """
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in" +
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._canvas.unbind(sequence, None)

    def focus(self):
        return self._canvas.focus()

    def focus_set(self):
        return self._canvas.focus_set()

    def focus_force(self):
        return self._canvas.focus_force()
