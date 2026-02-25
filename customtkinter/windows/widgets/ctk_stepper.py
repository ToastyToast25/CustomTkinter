import tkinter
import math
from typing import Union, Tuple, Optional, Callable, List, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .font import CTkFont


class CTkStepper(CTkBaseClass):
    """
    Step progress indicator for wizard-style workflows.

    Displays numbered steps with labels, showing completed, active,
    and upcoming states with smooth color transitions.

    Usage:
        stepper = CTkStepper(parent, steps=["Account", "Profile", "Confirm"])
        stepper.next()
        stepper.set_step(2)
        stepper.previous()
    """

    def __init__(self,
                 master: Any,
                 steps: Optional[List[str]] = None,
                 current_step: int = 0,
                 width: int = 500,
                 height: int = 80,

                 completed_color: Optional[Union[str, Tuple[str, str]]] = None,
                 active_color: Optional[Union[str, Tuple[str, str]]] = None,
                 upcoming_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 completed_text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 line_color: Optional[Union[str, Tuple[str, str]]] = None,
                 completed_line_color: Optional[Union[str, Tuple[str, str]]] = None,

                 step_size: int = 32,
                 line_width: int = 3,
                 font: Optional[Union[tuple, CTkFont]] = None,
                 command: Optional[Callable] = None,
                 **kwargs):

        super().__init__(master=master, width=width, height=height,
                         bg_color="transparent", **kwargs)

        self._steps = steps or ["Step 1", "Step 2", "Step 3"]
        self._current_step = max(0, min(current_step, len(self._steps) - 1))
        self._step_size = step_size
        self._line_width = line_width
        self._command = command

        # colors
        self._completed_color = completed_color or ("#3B8ED0", "#1F6AA5")
        self._active_color = active_color or ("#3B8ED0", "#1F6AA5")
        self._upcoming_color = upcoming_color or ("#D1D5DB", "#4B5563")
        self._text_color = text_color or ThemeManager.theme["CTkLabel"]["text_color"]
        self._completed_text_color = completed_text_color or ("#FFFFFF", "#FFFFFF")
        self._line_color = line_color or ("#D1D5DB", "#4B5563")
        self._completed_line_color = completed_line_color or ("#3B8ED0", "#1F6AA5")

        # font
        self._font = font or CTkFont(size=11)
        self._number_font = CTkFont(size=12, weight="bold")

        # canvas
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, sticky="nswe")
        self._draw_engine = DrawEngine(self._canvas)

        # animation state for active circle pulse
        self._pulse_after_id = None
        self._pulse_t = 0.0
        self._pulse_dir = 1
        # animated line fill progress
        self._line_anim_after_id = None
        self._line_anim_step = 0
        self._line_anim_index = 0

        self._draw()
        self._start_active_pulse()

    # ── Drawing ───────────────────────────────────────────────────

    def _draw(self, no_color_updates=False):
        super()._draw(no_color_updates)

        self._canvas.delete("all")

        s = self._apply_widget_scaling
        w = self._current_width
        h = self._current_height

        bg = self._apply_appearance_mode(self._bg_color)
        self._canvas.configure(bg=bg)

        n = len(self._steps)
        if n == 0:
            return

        circle_r = s(self._step_size / 2)
        cy = s(h / 2 - 8)  # leave room for labels below

        # calculate positions: evenly distribute circles
        padding = s(30)
        available = s(w) - 2 * padding
        if n > 1:
            step_spacing = available / (n - 1)
        else:
            step_spacing = 0

        positions = []
        for i in range(n):
            cx = padding + i * step_spacing
            positions.append(cx)

        # draw connecting lines
        for i in range(n - 1):
            x1 = positions[i] + circle_r
            x2 = positions[i + 1] - circle_r

            if i < self._current_step:
                line_c = self._apply_appearance_mode(self._completed_line_color)
            else:
                line_c = self._apply_appearance_mode(self._line_color)

            self._canvas.create_line(
                x1, cy, x2, cy,
                fill=line_c, width=s(self._line_width),
                tags=f"line_{i}"
            )

        # draw step circles and labels
        for i in range(n):
            cx = positions[i]

            if i < self._current_step:
                # completed
                circle_c = self._apply_appearance_mode(self._completed_color)
                num_c = self._apply_appearance_mode(self._completed_text_color)
                display_text = "\u2713"  # checkmark
            elif i == self._current_step:
                # active
                circle_c = self._apply_appearance_mode(self._active_color)
                num_c = self._apply_appearance_mode(self._completed_text_color)
                display_text = str(i + 1)
            else:
                # upcoming
                circle_c = self._apply_appearance_mode(self._upcoming_color)
                num_c = self._apply_appearance_mode(self._text_color)
                display_text = str(i + 1)

            # circle
            self._canvas.create_oval(
                cx - circle_r, cy - circle_r,
                cx + circle_r, cy + circle_r,
                fill=circle_c, outline=circle_c,
                tags=f"circle_{i}"
            )

            # number/checkmark inside circle
            num_font = self._number_font if isinstance(self._number_font, tuple) else (
                self._number_font.cget("family"), self._number_font.cget("size"),
                self._number_font.cget("weight"))
            self._canvas.create_text(
                cx, cy,
                text=display_text, fill=num_c, font=num_font,
                tags=f"num_{i}"
            )

            # label below circle
            label_y = cy + circle_r + s(12)
            label_c = self._apply_appearance_mode(self._text_color)
            label_font = self._font if isinstance(self._font, tuple) else (
                self._font.cget("family"), self._font.cget("size"),
                self._font.cget("weight"))

            # bold label for active step
            if i == self._current_step:
                label_font = self._number_font if isinstance(self._number_font, tuple) else (
                    self._number_font.cget("family"), self._number_font.cget("size"),
                    self._number_font.cget("weight"))

            self._canvas.create_text(
                cx, label_y,
                text=self._steps[i], fill=label_c, font=label_font,
                tags=f"label_{i}"
            )

    # ── Public API ────────────────────────────────────────────────

    def get_step(self) -> int:
        """Return the current step index (0-based)."""
        return self._current_step

    def set_step(self, step: int):
        """Set the current step (0-based index)."""
        old = self._current_step
        self._current_step = max(0, min(step, len(self._steps) - 1))
        if old != self._current_step:
            self._draw()
            self._start_active_pulse()
            # animate the connecting line fill
            if old < self._current_step and old < len(self._steps) - 1:
                self._animate_line_fill(old)
            if self._command is not None:
                self._command(self._current_step)

    def next(self):
        """Advance to the next step."""
        self.set_step(self._current_step + 1)

    def previous(self):
        """Go back to the previous step."""
        self.set_step(self._current_step - 1)

    def reset(self):
        """Reset to the first step."""
        self.set_step(0)

    def complete(self):
        """Mark all steps as completed (sets step beyond last)."""
        self._current_step = len(self._steps)
        self._draw()
        if self._command is not None:
            self._command(self._current_step)

    def is_complete(self) -> bool:
        """Return True if all steps are completed."""
        return self._current_step >= len(self._steps)

    def is_first(self) -> bool:
        """Return True if at the first step."""
        return self._current_step == 0

    def is_last(self) -> bool:
        """Return True if at the last step."""
        return self._current_step >= len(self._steps) - 1

    # ── Active step pulse animation ──────────────────────────────

    def _start_active_pulse(self):
        """Pulse the active step circle with a subtle glow."""
        self._stop_active_pulse()
        self._pulse_t = 0.0
        self._pulse_dir = 1
        self._active_pulse_tick()

    def _stop_active_pulse(self):
        if self._pulse_after_id is not None:
            self.after_cancel(self._pulse_after_id)
            self._pulse_after_id = None

    def _active_pulse_tick(self):
        """Animate active circle between normal and slightly larger size."""
        dt = 16.0 / 600.0
        self._pulse_t += dt * self._pulse_dir
        if self._pulse_t >= 1.0:
            self._pulse_t = 1.0
            self._pulse_dir = -1
        elif self._pulse_t <= 0.0:
            self._pulse_t = 0.0
            self._pulse_dir = 1

        # smooth ease
        t = self._pulse_t
        eased = t * t * (3.0 - 2.0 * t)

        s = self._apply_widget_scaling
        n = len(self._steps)
        idx = self._current_step
        if idx >= n:
            self._pulse_after_id = None
            return

        circle_r = s(self._step_size / 2)
        pulse_r = circle_r * (1.0 + 0.12 * eased)

        cy = s(self._current_height / 2 - 8)
        padding = s(30)
        available = s(self._current_width) - 2 * padding
        step_spacing = available / (n - 1) if n > 1 else 0
        cx = padding + idx * step_spacing

        tag = f"circle_{idx}"
        try:
            self._canvas.coords(tag, cx - pulse_r, cy - pulse_r, cx + pulse_r, cy + pulse_r)
        except Exception:
            self._pulse_after_id = None
            return

        self._pulse_after_id = self.after(16, self._active_pulse_tick)

    # ── Line fill animation ───────────────────────────────────────

    def _animate_line_fill(self, line_index: int):
        """Animate a connecting line filling from left to right."""
        if self._line_anim_after_id is not None:
            self.after_cancel(self._line_anim_after_id)
        self._line_anim_step = 0
        self._line_anim_index = line_index
        self._line_fill_tick()

    def _line_fill_tick(self):
        total = 10
        step = self._line_anim_step
        if step > total:
            self._line_anim_after_id = None
            return

        t = step / total
        idx = self._line_anim_index
        s = self._apply_widget_scaling
        n = len(self._steps)
        circle_r = s(self._step_size / 2)
        cy = s(self._current_height / 2 - 8)
        padding = s(30)
        available = s(self._current_width) - 2 * padding
        step_spacing = available / (n - 1) if n > 1 else 0

        x1 = padding + idx * step_spacing + circle_r
        x2 = padding + (idx + 1) * step_spacing - circle_r
        x_current = x1 + (x2 - x1) * t

        line_c = self._apply_appearance_mode(self._completed_line_color)

        # draw partial fill overlay
        tag = f"line_fill_{idx}"
        self._canvas.delete(tag)
        self._canvas.create_line(
            x1, cy, x_current, cy,
            fill=line_c, width=s(self._line_width),
            tags=tag
        )

        self._line_anim_step += 1
        self._line_anim_after_id = self.after(16, self._line_fill_tick)

    def destroy(self):
        self._stop_active_pulse()
        if self._line_anim_after_id is not None:
            self.after_cancel(self._line_anim_after_id)
        super().destroy()

    # ── Scaling ───────────────────────────────────────────────────

    def _set_scaling(self, *args, **kwargs):
        super()._set_scaling(*args, **kwargs)
        self._canvas.configure(
            width=self._apply_widget_scaling(self._desired_width),
            height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    # ── Configure / cget ──────────────────────────────────────────

    def configure(self, **kwargs):
        require_redraw = False
        if "steps" in kwargs:
            self._steps = kwargs.pop("steps")
            self._current_step = min(self._current_step, len(self._steps) - 1)
            require_redraw = True
        if "current_step" in kwargs:
            self.set_step(kwargs.pop("current_step"))
        if "completed_color" in kwargs:
            self._completed_color = kwargs.pop("completed_color")
            require_redraw = True
        if "active_color" in kwargs:
            self._active_color = kwargs.pop("active_color")
            require_redraw = True
        if "upcoming_color" in kwargs:
            self._upcoming_color = kwargs.pop("upcoming_color")
            require_redraw = True
        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            require_redraw = True
        if "completed_text_color" in kwargs:
            self._completed_text_color = kwargs.pop("completed_text_color")
            require_redraw = True
        if "line_color" in kwargs:
            self._line_color = kwargs.pop("line_color")
            require_redraw = True
        if "completed_line_color" in kwargs:
            self._completed_line_color = kwargs.pop("completed_line_color")
            require_redraw = True
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if require_redraw:
            self._draw()
        super().configure(**kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "steps":
            return self._steps
        elif attribute_name == "current_step":
            return self._current_step
        elif attribute_name == "completed_color":
            return self._completed_color
        elif attribute_name == "active_color":
            return self._active_color
        elif attribute_name == "upcoming_color":
            return self._upcoming_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "completed_text_color":
            return self._completed_text_color
        elif attribute_name == "line_color":
            return self._line_color
        elif attribute_name == "completed_line_color":
            return self._completed_line_color
        elif attribute_name == "command":
            return self._command
        else:
            return super().cget(attribute_name)
