import tkinter
import math
from typing import Union, Tuple, Optional, Callable, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_rendering import DrawEngine
from .core_widget_classes import CTkBaseClass
from .ctk_frame import CTkFrame


class CTkCard(CTkFrame):
    """
    Interactive card/panel with animated border glow on hover.
    Extends CTkFrame with hover animation, click handling, and
    optional header/footer sections.

    Supports disabled state (suppresses interaction, muted border),
    selected state (persistent distinct border), click feedback
    (brief flash), and keyboard focus ring (Tab/Enter/Space).

    Usage:
        card = CTkCard(parent, border_width=2, hover_effect=True)
        ctk.CTkLabel(card, text="Title").pack(padx=16, pady=(16, 4))
        ctk.CTkLabel(card, text="Content here").pack(padx=16, pady=(4, 16))
    """

    # Default focus ring colors (light, dark)
    _DEFAULT_FOCUS_COLOR = ("#1f6feb", "#58a6ff")
    # Default disabled border colors (light, dark) -- muted appearance
    _DEFAULT_DISABLED_BORDER_COLOR = ("#c0c0c0", "#2a2a2a")
    # Default click flash color (light, dark)
    _DEFAULT_CLICK_FLASH_COLOR = ("#ffffff", "#ffffff")

    def __init__(self,
                 master: Any,
                 width: int = 300,
                 height: int = 200,
                 corner_radius: Optional[int] = None,
                 border_width: int = 2,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 hover_border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 selected_border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 disabled_border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 focus_border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 click_flash_color: Optional[Union[str, Tuple[str, str]]] = None,

                 hover_effect: bool = True,
                 hover_duration: int = 200,
                 command: Optional[Callable] = None,
                 state: str = "normal",
                 selected: bool = False,
                 **kwargs):

        # default border color
        if border_color is None:
            border_color = ("#d4d4d4", "#404040")

        super().__init__(master=master, width=width, height=height,
                         corner_radius=corner_radius, border_width=border_width,
                         bg_color=bg_color, fg_color=fg_color,
                         border_color=border_color, **kwargs)

        self._hover_border_color = hover_border_color or ("#3B8ED0", "#3B8ED0")
        self._base_border_color = border_color
        self._hover_effect = hover_effect
        self._hover_duration = max(50, hover_duration)
        self._command = command

        # selected state
        self._selected = selected
        self._selected_border_color = selected_border_color or self._hover_border_color

        # disabled state
        self._state = state
        self._disabled_border_color = disabled_border_color or self._DEFAULT_DISABLED_BORDER_COLOR

        # focus ring
        self._focus_border_color = focus_border_color or self._DEFAULT_FOCUS_COLOR
        self._focused = False

        # click flash
        self._click_flash_color = click_flash_color or self._DEFAULT_CLICK_FLASH_COLOR

        # animation state
        self._hover_phase = 0.0  # 0.0 = base, 1.0 = full hover
        self._hover_direction = 0  # 1 = hovering in, -1 = hovering out
        self._hover_after_id = None
        self._click_after_id = None

        # bindings
        if self._hover_effect or self._command:
            self.bind("<Enter>", self._on_enter, add="+")
            self.bind("<Leave>", self._on_leave, add="+")
        if self._command:
            self.bind("<Button-1>", self._on_click, add="+")
            if hasattr(self, '_cursor_manipulation_enabled') and self._cursor_manipulation_enabled:
                self.configure(cursor="hand2")

        # keyboard focus support — bypass CTkFrame.configure which rejects takefocus
        tkinter.Frame.configure(self, takefocus=True)
        self.bind("<FocusIn>", self._on_focus_in, add="+")
        self.bind("<FocusOut>", self._on_focus_out, add="+")
        self.bind("<Return>", self._on_key_activate, add="+")
        self.bind("<space>", self._on_key_activate, add="+")

        # Apply initial visual state if selected or disabled at construction time
        if self._state == "disabled" or self._selected:
            self.after(10, self._apply_static_border)

    # ------------------------------------------------------------------
    #  Effective "rest" border: accounts for disabled > selected > base
    # ------------------------------------------------------------------

    def _effective_rest_border_color(self) -> str:
        """Return the resolved hex color for the current rest state.

        Priority: disabled > selected > base.
        """
        if self._state == "disabled":
            return self._color_to_hex(
                self._apply_appearance_mode(self._disabled_border_color))
        if self._selected:
            return self._color_to_hex(
                self._apply_appearance_mode(self._selected_border_color))
        return self._color_to_hex(
            self._apply_appearance_mode(self._base_border_color))

    def _apply_static_border(self):
        """Set border to the current effective rest color without animation."""
        color = self._effective_rest_border_color()
        try:
            self._canvas.itemconfig("border_parts", fill=color, outline=color)
        except Exception:
            pass

    # ------------------------------------------------------------------
    #  Hover
    # ------------------------------------------------------------------

    def _on_enter(self, event=None):
        if self._state == "disabled":
            return
        if self._hover_effect:
            self._hover_direction = 1
            self._animate_hover()

    def _on_leave(self, event=None):
        if self._state == "disabled":
            return
        if self._hover_effect:
            self._hover_direction = -1
            self._animate_hover()

    # ------------------------------------------------------------------
    #  Click
    # ------------------------------------------------------------------

    def _on_click(self, event=None):
        if self._state == "disabled":
            return
        self._do_click_flash()
        if self._command is not None:
            self._command()

    def _on_key_activate(self, event=None):
        """Handle Return / Space when the card has keyboard focus."""
        if self._state == "disabled":
            return
        self._do_click_flash()
        if self._command is not None:
            self._command()

    def _do_click_flash(self):
        """Flash the border to the click color, then ease back over 100ms."""
        # Cancel any pending click-flash recovery
        if self._click_after_id is not None:
            self.after_cancel(self._click_after_id)
            self._click_after_id = None

        flash = self._color_to_hex(
            self._apply_appearance_mode(self._click_flash_color))
        try:
            self._canvas.itemconfig("border_parts", fill=flash, outline=flash)
        except Exception:
            return

        # After 100ms, restore to the correct visual state
        self._click_after_id = self.after(100, self._click_flash_recover)

    def _click_flash_recover(self):
        """Restore border after a click flash."""
        self._click_after_id = None

        # If hover is active, let the hover animation recalculate
        if self._hover_phase > 0.0:
            self._animate_hover_frame()
        else:
            self._apply_static_border()

        # If focused, overlay the focus ring
        if self._focused:
            self._apply_focus_ring()

    # ------------------------------------------------------------------
    #  Hover animation
    # ------------------------------------------------------------------

    def _animate_hover(self):
        """Animate border color transition."""
        if self._hover_after_id is not None:
            self.after_cancel(self._hover_after_id)
            self._hover_after_id = None

        interval = 16  # ~60fps
        step = interval / self._hover_duration

        self._hover_phase += step * self._hover_direction
        self._hover_phase = max(0.0, min(1.0, self._hover_phase))

        self._animate_hover_frame()

        # continue animation if not at target
        if (self._hover_direction > 0 and self._hover_phase < 1.0) or \
           (self._hover_direction < 0 and self._hover_phase > 0.0):
            self._hover_after_id = self.after(interval, self._animate_hover)

    def _animate_hover_frame(self):
        """Apply a single frame of the hover animation at the current phase."""
        # The "base" for interpolation is the effective rest color
        base = self._effective_rest_border_color()
        target = self._color_to_hex(
            self._apply_appearance_mode(self._hover_border_color))
        current = self._lerp_hex(base, target, self._ease_out_cubic(self._hover_phase))

        try:
            self._canvas.itemconfig("border_parts", fill=current, outline=current)
        except Exception:
            return

    # ------------------------------------------------------------------
    #  Focus ring
    # ------------------------------------------------------------------

    def _on_focus_in(self, event=None):
        self._focused = True
        if self._state == "disabled":
            return
        self._apply_focus_ring()

    def _on_focus_out(self, event=None):
        self._focused = False
        if self._state == "disabled":
            return
        self._revert_focus_ring()

    def _apply_focus_ring(self):
        """Show the focus ring by setting border to the focus color."""
        color = self._color_to_hex(
            self._apply_appearance_mode(self._focus_border_color))
        try:
            self._canvas.itemconfig("border_parts", fill=color, outline=color)
        except Exception:
            pass

    def _revert_focus_ring(self):
        """Revert border after focus is lost."""
        if self._hover_phase > 0.0:
            # Mid-hover: let the animation paint the correct interpolated frame
            self._animate_hover_frame()
        else:
            self._apply_static_border()

    # ------------------------------------------------------------------
    #  Disabled state
    # ------------------------------------------------------------------

    def enable(self):
        """Enable the card, restoring hover animation and click events."""
        if self._state == "normal":
            return
        self._state = "normal"
        self._apply_static_border()

    def disable(self):
        """Disable the card, suppressing hover/click and showing a muted border."""
        if self._state == "disabled":
            return
        self._state = "disabled"
        # Reset hover
        self._hover_phase = 0.0
        self._hover_direction = 0
        if self._hover_after_id is not None:
            self.after_cancel(self._hover_after_id)
            self._hover_after_id = None
        if self._click_after_id is not None:
            self.after_cancel(self._click_after_id)
            self._click_after_id = None
        self._apply_static_border()

    # ------------------------------------------------------------------
    #  Selected state
    # ------------------------------------------------------------------

    def select(self):
        """Mark the card as selected, showing the selected border color."""
        if self._selected:
            return
        self._selected = True
        # Only update visuals when not disabled (disabled border takes priority)
        if self._state != "disabled" and self._hover_phase == 0.0 and not self._focused:
            self._apply_static_border()

    def deselect(self):
        """Remove the selected state, reverting to the base border color."""
        if not self._selected:
            return
        self._selected = False
        if self._state != "disabled" and self._hover_phase == 0.0 and not self._focused:
            self._apply_static_border()

    def toggle_select(self):
        """Toggle the selected state."""
        if self._selected:
            self.deselect()
        else:
            self.select()

    # ------------------------------------------------------------------
    #  Utility (unchanged)
    # ------------------------------------------------------------------

    def _color_to_hex(self, color: str) -> str:
        """Convert any tkinter color to #RRGGBB."""
        if color.startswith("#") and len(color) == 7:
            return color
        try:
            r, g, b = self._canvas.winfo_rgb(color)
            return f"#{r >> 8:02x}{g >> 8:02x}{b >> 8:02x}"
        except Exception:
            return "#333333"

    @staticmethod
    def _lerp_hex(c1: str, c2: str, t: float) -> str:
        """Linearly interpolate between two hex colors."""
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        return f"#{int(r1+(r2-r1)*t):02x}{int(g1+(g2-g1)*t):02x}{int(b1+(b2-b1)*t):02x}"

    @staticmethod
    def _ease_out_cubic(t: float) -> float:
        """Cubic ease-out for smooth deceleration."""
        return 1 - (1 - t) ** 3

    # ------------------------------------------------------------------
    #  Lifecycle
    # ------------------------------------------------------------------

    def destroy(self):
        if self._hover_after_id is not None:
            self.after_cancel(self._hover_after_id)
            self._hover_after_id = None
        if self._click_after_id is not None:
            self.after_cancel(self._click_after_id)
            self._click_after_id = None
        super().destroy()

    # ------------------------------------------------------------------
    #  configure / cget
    # ------------------------------------------------------------------

    def configure(self, **kwargs):
        if "hover_border_color" in kwargs:
            self._hover_border_color = kwargs.pop("hover_border_color")
        if "hover_effect" in kwargs:
            self._hover_effect = kwargs.pop("hover_effect")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "border_color" in kwargs:
            self._base_border_color = kwargs["border_color"]
        if "selected_border_color" in kwargs:
            self._selected_border_color = kwargs.pop("selected_border_color")
        if "disabled_border_color" in kwargs:
            self._disabled_border_color = kwargs.pop("disabled_border_color")
        if "focus_border_color" in kwargs:
            self._focus_border_color = kwargs.pop("focus_border_color")
        if "click_flash_color" in kwargs:
            self._click_flash_color = kwargs.pop("click_flash_color")
        if "state" in kwargs:
            new_state = kwargs.pop("state")
            if new_state == "disabled":
                self.disable()
            else:
                self.enable()
        if "selected" in kwargs:
            sel = kwargs.pop("selected")
            if sel:
                self.select()
            else:
                self.deselect()
        super().configure(**kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "hover_border_color":
            return self._hover_border_color
        elif attribute_name == "hover_effect":
            return self._hover_effect
        elif attribute_name == "hover_duration":
            return self._hover_duration
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "selected":
            return self._selected
        elif attribute_name == "selected_border_color":
            return self._selected_border_color
        elif attribute_name == "disabled_border_color":
            return self._disabled_border_color
        elif attribute_name == "focus_border_color":
            return self._focus_border_color
        elif attribute_name == "click_flash_color":
            return self._click_flash_color
        else:
            return super().cget(attribute_name)
