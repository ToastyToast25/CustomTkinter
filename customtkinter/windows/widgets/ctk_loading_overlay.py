import tkinter
from typing import Union, Tuple, Optional, Callable, Any

from .core_rendering import CTkCanvas
from .theme import ThemeManager
from .core_widget_classes import CTkBaseClass
from .font import CTkFont
from .appearance_mode import AppearanceModeTracker


class CTkLoadingOverlay(CTkBaseClass):
    """
    Loading overlay that dims the parent container and shows a centered
    spinner with an optional message and progress indicator.

    The overlay covers the entire parent using place(relwidth=1, relheight=1),
    blocks interaction with underlying widgets, and provides a smooth
    fade-in/fade-out transition via stipple-based dimming.

    Supports two display modes:
        - Indeterminate (default): A spinning arc animates continuously.
        - Progress: When set_progress() is called, a determinate arc fills
          proportionally and percentage text is shown.

    Usage:
        overlay = CTkLoadingOverlay(parent,
            message="Loading data...",
            spinner_size=40,
            fg_color=("#3a3a3a", "#1a1a1a"),
        )
        overlay.show()
        overlay.set_message("Processing...")
        overlay.set_progress(0.5)  # switches to progress mode
        overlay.hide()
    """

    # Stipple patterns ordered from least opaque to most opaque, used for
    # the fade-in/fade-out animation steps.
    _STIPPLE_STEPS = ["gray12", "gray25", "gray50", "gray50"]

    def __init__(self,
                 master: Any,
                 message: str = "",
                 spinner_size: int = 40,
                 spinner_line_width: int = 4,
                 fade_duration: int = 200,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 spinner_color: Optional[Union[str, Tuple[str, str]]] = None,
                 spinner_track_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 progress_text_color: Optional[Union[str, Tuple[str, str]]] = None,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 progress_font: Optional[Union[tuple, CTkFont]] = None,
                 on_show: Optional[Callable] = None,
                 on_hide: Optional[Callable] = None,
                 cancel_command: Optional[Callable] = None,
                 cancel_text: str = "Cancel",
                 **kwargs):

        # The overlay starts at 0x0; it will be resized via place(relwidth=1, relheight=1).
        super().__init__(master=master, bg_color=bg_color, width=0, height=0, **kwargs)

        # ---- configuration ----
        self._message = message
        self._spinner_size = spinner_size
        self._spinner_line_width = spinner_line_width
        self._fade_duration = max(50, fade_duration)

        # colors
        self._fg_color = fg_color or ("#3a3a3a", "#1a1a1a")
        self._spinner_color = spinner_color or ThemeManager.theme["CTkProgressBar"]["progress_color"]
        self._spinner_track_color = spinner_track_color or ("#555555", "#444444")
        self._text_color = text_color or ("#e0e0e0", "#e0e0e0")
        self._progress_text_color = progress_text_color or ("#ffffff", "#ffffff")

        # fonts
        self._font = font or CTkFont(size=14)
        self._progress_font = progress_font or CTkFont(size=max(10, spinner_size // 4))

        # callbacks
        self._on_show_callback = on_show
        self._on_hide_callback = on_hide
        self._cancel_command = cancel_command
        self._cancel_text = cancel_text

        # ---- internal state ----
        self._visible = False
        self._progress: Optional[float] = None  # None = indeterminate, 0.0-1.0 = determinate
        self._spin_angle = 0.0
        self._spin_after_id = None
        self._fade_after_id = None
        self._fade_phase = 0  # index into _STIPPLE_STEPS during fade
        self._fading_in = False
        self._fading_out = False

        # ---- canvas (drawn on top of dim layer) ----
        # The dim overlay and the canvas are both managed within this frame.
        # The dim rectangle is a canvas item covering the full area.
        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=0, height=0)

        # Canvas item IDs (created lazily in _draw_spinner)
        self._dim_rect_id = None
        self._track_arc_id = None
        self._spinner_arc_id = None
        self._message_text_id = None
        self._progress_text_id = None
        self._cancel_text_id = None

        # Bind canvas resize to redraw
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Block all mouse interaction from passing through
        self._canvas.bind("<Button-1>", self._consume_event)
        self._canvas.bind("<Button-2>", self._consume_event)
        self._canvas.bind("<Button-3>", self._consume_event)
        self._canvas.bind("<ButtonRelease-1>", self._consume_event)
        self._canvas.bind("<ButtonRelease-2>", self._consume_event)
        self._canvas.bind("<ButtonRelease-3>", self._consume_event)
        self._canvas.bind("<Motion>", self._consume_event)
        self._canvas.bind("<MouseWheel>", self._consume_event)
        self._canvas.bind("<Double-Button-1>", self._consume_event)

        # Do NOT place/show yet -- wait for show() call
        # Remove from view immediately
        tkinter.Frame.place_forget(self)

    # ------------------------------------------------------------------
    #  Event blocking
    # ------------------------------------------------------------------

    @staticmethod
    def _consume_event(event=None):
        """Consume the event so it does not propagate to widgets below."""
        return "break"

    # ------------------------------------------------------------------
    #  Show / Hide
    # ------------------------------------------------------------------

    def show(self):
        """Display the overlay with a fade-in transition."""
        if self._visible and not self._fading_out:
            return

        # Cancel any pending fade-out
        if self._fade_after_id is not None:
            self.after_cancel(self._fade_after_id)
            self._fade_after_id = None
        self._fading_out = False

        self._visible = True

        # Place ourselves over the parent, filling the entire area.
        # Use tkinter.Frame.place directly to bypass CTkBaseClass scaling logic
        # which rejects width/height in place().
        tkinter.Frame.place(self, relx=0, rely=0, relwidth=1, relheight=1)

        # Place canvas to fill this frame
        self._canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Lift above all siblings so we cover everything
        self.lift()

        # Start fade in
        self._fade_phase = 0
        self._fading_in = True
        self._apply_dim_stipple()
        self._fade_in_step()

        # Start spinner animation
        self._start_spin()

        if self._on_show_callback is not None:
            self._on_show_callback()

    def hide(self):
        """Hide the overlay with a fade-out transition."""
        if not self._visible:
            return

        # Cancel fade-in if in progress
        if self._fading_in:
            self._fading_in = False

        # Cancel any previous fade timer
        if self._fade_after_id is not None:
            self.after_cancel(self._fade_after_id)
            self._fade_after_id = None

        self._fading_out = True
        self._fade_phase = len(self._STIPPLE_STEPS) - 1
        self._fade_out_step()

    def _finish_hide(self):
        """Complete the hide after fade-out finishes."""
        self._fading_out = False
        self._visible = False

        # Stop spinner
        self._stop_spin()

        # Remove from layout
        self._canvas.place_forget()
        tkinter.Frame.place_forget(self)

        if self._on_hide_callback is not None:
            self._on_hide_callback()

    # ------------------------------------------------------------------
    #  Fade animation
    # ------------------------------------------------------------------

    def _fade_in_step(self):
        """Advance one step of the fade-in animation."""
        if not self._fading_in:
            return

        self._apply_dim_stipple()
        self._draw_spinner()

        self._fade_phase += 1
        if self._fade_phase < len(self._STIPPLE_STEPS):
            interval = self._fade_duration // len(self._STIPPLE_STEPS)
            self._fade_after_id = self.after(max(16, interval), self._fade_in_step)
        else:
            # Fade-in complete
            self._fading_in = False
            self._fade_after_id = None
            # Final draw at full opacity
            self._fade_phase = len(self._STIPPLE_STEPS) - 1
            self._apply_dim_stipple()
            self._draw_spinner()

    def _fade_out_step(self):
        """Advance one step of the fade-out animation."""
        if not self._fading_out:
            return

        self._apply_dim_stipple()

        self._fade_phase -= 1
        if self._fade_phase >= 0:
            interval = self._fade_duration // len(self._STIPPLE_STEPS)
            self._fade_after_id = self.after(max(16, interval), self._fade_out_step)
        else:
            self._fade_after_id = None
            self._finish_hide()

    def _apply_dim_stipple(self):
        """Apply the current stipple pattern to the dim rectangle."""
        phase = max(0, min(self._fade_phase, len(self._STIPPLE_STEPS) - 1))
        stipple = self._STIPPLE_STEPS[phase]
        fg = self._resolve_color(self._fg_color)

        if self._dim_rect_id is not None:
            try:
                self._canvas.itemconfigure(self._dim_rect_id,
                                           fill=fg,
                                           stipple=stipple)
            except Exception:
                pass

    # ------------------------------------------------------------------
    #  Spinner drawing
    # ------------------------------------------------------------------

    def _draw_spinner(self):
        """Redraw the spinner, message text, and progress text on the canvas."""
        try:
            cw = self._canvas.winfo_width()
            ch = self._canvas.winfo_height()
        except Exception:
            return

        if cw < 2 or ch < 2:
            return

        fg = self._resolve_color(self._fg_color)
        spinner_c = self._resolve_color(self._spinner_color)
        track_c = self._resolve_color(self._spinner_track_color)
        text_c = self._resolve_color(self._text_color)
        progress_text_c = self._resolve_color(self._progress_text_color)

        # ---- dim rectangle ----
        phase = max(0, min(self._fade_phase, len(self._STIPPLE_STEPS) - 1))
        stipple = self._STIPPLE_STEPS[phase]

        if self._dim_rect_id is None:
            self._dim_rect_id = self._canvas.create_rectangle(
                0, 0, cw, ch,
                fill=fg, outline="",
                stipple=stipple,
                tags="dim"
            )
        else:
            self._canvas.coords(self._dim_rect_id, 0, 0, cw, ch)
            self._canvas.itemconfigure(self._dim_rect_id, fill=fg, stipple=stipple)

        # Center coordinates
        cx = cw / 2
        cy = ch / 2

        # If there is a message, shift spinner up a bit
        has_message = bool(self._message)
        has_cancel = self._cancel_command is not None
        vertical_offset = 0
        if has_message:
            vertical_offset = -14
        if has_cancel:
            vertical_offset -= 8

        spinner_cx = cx
        spinner_cy = cy + vertical_offset

        # Spinner dimensions
        s = self._spinner_size
        lw = max(1, self._spinner_line_width)
        pad = lw / 2 + 2
        x1 = spinner_cx - s / 2
        y1 = spinner_cy - s / 2
        x2 = spinner_cx + s / 2
        y2 = spinner_cy + s / 2

        # ---- track arc (background ring) ----
        if self._track_arc_id is None:
            self._track_arc_id = self._canvas.create_arc(
                x1 + pad, y1 + pad, x2 - pad, y2 - pad,
                start=0, extent=359.99,
                style="arc", width=lw,
                outline=track_c,
                tags="track"
            )
        else:
            self._canvas.coords(self._track_arc_id,
                                x1 + pad, y1 + pad, x2 - pad, y2 - pad)
            self._canvas.itemconfigure(self._track_arc_id, outline=track_c, width=lw)

        # ---- spinner arc ----
        if self._progress is not None:
            # Determinate: arc fills proportionally
            arc_start = 90
            arc_extent = -self._progress * 360
        else:
            # Indeterminate: spinning partial arc
            arc_start = self._spin_angle
            arc_extent = -90  # 90-degree arc segment

        if self._spinner_arc_id is None:
            self._spinner_arc_id = self._canvas.create_arc(
                x1 + pad, y1 + pad, x2 - pad, y2 - pad,
                start=arc_start, extent=arc_extent,
                style="arc", width=lw,
                outline=spinner_c,
                tags="spinner"
            )
        else:
            self._canvas.coords(self._spinner_arc_id,
                                x1 + pad, y1 + pad, x2 - pad, y2 - pad)
            self._canvas.itemconfigure(self._spinner_arc_id,
                                       outline=spinner_c, width=lw)
            self._canvas.itemconfigure(self._spinner_arc_id,
                                       start=arc_start, extent=arc_extent)

        # ---- progress percentage text (inside spinner) ----
        if self._progress is not None:
            pct_text = f"{int(self._progress * 100)}%"
            p_font = self._resolve_font(self._progress_font)
            if self._progress_text_id is None:
                self._progress_text_id = self._canvas.create_text(
                    spinner_cx, spinner_cy,
                    text=pct_text, fill=progress_text_c,
                    font=p_font, anchor="center",
                    tags="progress_text"
                )
            else:
                self._canvas.coords(self._progress_text_id, spinner_cx, spinner_cy)
                self._canvas.itemconfigure(self._progress_text_id,
                                           text=pct_text, fill=progress_text_c,
                                           font=p_font)
        else:
            # Remove progress text if we are in indeterminate mode
            if self._progress_text_id is not None:
                self._canvas.delete(self._progress_text_id)
                self._progress_text_id = None

        # ---- message text ----
        msg_y = spinner_cy + s / 2 + 16
        if has_message:
            m_font = self._resolve_font(self._font)
            if self._message_text_id is None:
                self._message_text_id = self._canvas.create_text(
                    cx, msg_y,
                    text=self._message, fill=text_c,
                    font=m_font, anchor="center",
                    tags="message"
                )
            else:
                self._canvas.coords(self._message_text_id, cx, msg_y)
                self._canvas.itemconfigure(self._message_text_id,
                                           text=self._message, fill=text_c,
                                           font=m_font)
        else:
            if self._message_text_id is not None:
                self._canvas.delete(self._message_text_id)
                self._message_text_id = None

        # ---- cancel text (clickable) ----
        cancel_y = msg_y + (22 if has_message else s / 2 + 16)
        if has_cancel:
            c_font = self._resolve_font(self._font)
            if self._cancel_text_id is None:
                self._cancel_text_id = self._canvas.create_text(
                    cx, cancel_y,
                    text=self._cancel_text, fill=self._resolve_color(self._spinner_color),
                    font=c_font, anchor="center",
                    tags="cancel"
                )
                self._canvas.tag_bind("cancel", "<Button-1>", self._on_cancel_click)
                self._canvas.tag_bind("cancel", "<Enter>",
                                      lambda e: self._canvas.configure(cursor="hand2"))
                self._canvas.tag_bind("cancel", "<Leave>",
                                      lambda e: self._canvas.configure(cursor=""))
            else:
                self._canvas.coords(self._cancel_text_id, cx, cancel_y)
                self._canvas.itemconfigure(self._cancel_text_id,
                                           text=self._cancel_text,
                                           fill=self._resolve_color(self._spinner_color),
                                           font=c_font)
        else:
            if self._cancel_text_id is not None:
                self._canvas.delete(self._cancel_text_id)
                self._cancel_text_id = None

        # Ensure proper stacking: dim on bottom, then track, spinner, texts on top
        self._canvas.tag_raise("track", "dim")
        self._canvas.tag_raise("spinner", "track")
        self._canvas.tag_raise("progress_text", "spinner")
        self._canvas.tag_raise("message", "spinner")
        self._canvas.tag_raise("cancel", "message")

    def _on_cancel_click(self, event=None):
        """Handle click on the cancel text."""
        if self._cancel_command is not None:
            self._cancel_command()
        return "break"

    # ------------------------------------------------------------------
    #  Spinner animation
    # ------------------------------------------------------------------

    def _start_spin(self):
        """Start the spinner rotation animation."""
        self._spin_tick()

    def _stop_spin(self):
        """Stop the spinner rotation animation."""
        if self._spin_after_id is not None:
            self.after_cancel(self._spin_after_id)
            self._spin_after_id = None

    def _spin_tick(self):
        """Advance the spinner by one frame (~60fps, ~1 revolution per second)."""
        if not self._visible:
            return

        if self._progress is None:
            # Indeterminate: rotate the arc
            self._spin_angle = (self._spin_angle + 6) % 360  # 6 deg * 60fps ~ 360 deg/sec

        # Update only the spinner arc (not the full redraw) for performance
        if self._spinner_arc_id is not None:
            try:
                if self._progress is not None:
                    arc_start = 90
                    arc_extent = -self._progress * 360
                else:
                    arc_start = self._spin_angle
                    arc_extent = -90
                self._canvas.itemconfigure(self._spinner_arc_id,
                                           start=arc_start, extent=arc_extent)
            except Exception:
                pass

        self._spin_after_id = self.after(16, self._spin_tick)

    # ------------------------------------------------------------------
    #  Canvas resize handler
    # ------------------------------------------------------------------

    def _on_canvas_configure(self, event=None):
        """Redraw when the canvas is resized."""
        if self._visible:
            # Delete all items and recreate to avoid coordinate drift
            self._clear_canvas_items()
            self._draw_spinner()

    def _clear_canvas_items(self):
        """Delete all canvas item references so they get recreated."""
        self._canvas.delete("all")
        self._dim_rect_id = None
        self._track_arc_id = None
        self._spinner_arc_id = None
        self._message_text_id = None
        self._progress_text_id = None
        self._cancel_text_id = None

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def set_message(self, message: str):
        """Update the message text displayed below the spinner."""
        self._message = message
        if self._visible:
            self._draw_spinner()

    def set_progress(self, value: Optional[float]):
        """Set progress value (0.0 to 1.0) or None for indeterminate mode.

        When a float is provided, the spinner switches to determinate mode
        showing a proportional arc and percentage text. Pass None to revert
        to the indeterminate spinning animation.
        """
        if value is not None:
            value = max(0.0, min(1.0, float(value)))
        self._progress = value
        if self._visible:
            self._draw_spinner()

    def get_progress(self) -> Optional[float]:
        """Return the current progress value, or None if indeterminate."""
        return self._progress

    def is_visible(self) -> bool:
        """Return True if the overlay is currently shown."""
        return self._visible

    # ------------------------------------------------------------------
    #  Color / font resolution helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_color(color):
        """Resolve a (light, dark) color tuple to a single hex color string."""
        if isinstance(color, (list, tuple)) and len(color) >= 2:
            mode = AppearanceModeTracker.appearance_mode
            return color[mode] if mode < len(color) else color[0]
        return color

    @staticmethod
    def _resolve_font(font):
        """Resolve a CTkFont or tuple to a tkinter-compatible font tuple."""
        if isinstance(font, CTkFont):
            return (font.cget("family"), font.cget("size"), font.cget("weight"))
        return font

    # ------------------------------------------------------------------
    #  Lifecycle
    # ------------------------------------------------------------------

    def destroy(self):
        """Clean up all animation timers and destroy the widget."""
        # Stop all animations
        if self._spin_after_id is not None:
            self.after_cancel(self._spin_after_id)
            self._spin_after_id = None
        if self._fade_after_id is not None:
            self.after_cancel(self._fade_after_id)
            self._fade_after_id = None

        self._visible = False
        self._fading_in = False
        self._fading_out = False

        super().destroy()

    def _draw(self, no_color_updates=False):
        """Override CTkBaseClass._draw. Redraw spinner if visible."""
        super()._draw(no_color_updates)
        if self._visible:
            self._draw_spinner()

    # ------------------------------------------------------------------
    #  configure / cget
    # ------------------------------------------------------------------

    def configure(self, **kwargs):
        require_redraw = False

        if "message" in kwargs:
            self._message = kwargs.pop("message")
            require_redraw = True

        if "spinner_size" in kwargs:
            self._spinner_size = kwargs.pop("spinner_size")
            require_redraw = True

        if "spinner_line_width" in kwargs:
            self._spinner_line_width = kwargs.pop("spinner_line_width")
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = kwargs.pop("fg_color")
            require_redraw = True

        if "spinner_color" in kwargs:
            self._spinner_color = kwargs.pop("spinner_color")
            require_redraw = True

        if "spinner_track_color" in kwargs:
            self._spinner_track_color = kwargs.pop("spinner_track_color")
            require_redraw = True

        if "text_color" in kwargs:
            self._text_color = kwargs.pop("text_color")
            require_redraw = True

        if "progress_text_color" in kwargs:
            self._progress_text_color = kwargs.pop("progress_text_color")
            require_redraw = True

        if "font" in kwargs:
            self._font = kwargs.pop("font")
            require_redraw = True

        if "progress_font" in kwargs:
            self._progress_font = kwargs.pop("progress_font")
            require_redraw = True

        if "fade_duration" in kwargs:
            self._fade_duration = max(50, kwargs.pop("fade_duration"))

        if "on_show" in kwargs:
            self._on_show_callback = kwargs.pop("on_show")

        if "on_hide" in kwargs:
            self._on_hide_callback = kwargs.pop("on_hide")

        if "cancel_command" in kwargs:
            self._cancel_command = kwargs.pop("cancel_command")
            require_redraw = True

        if "cancel_text" in kwargs:
            self._cancel_text = kwargs.pop("cancel_text")
            require_redraw = True

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str):
        if attribute_name == "message":
            return self._message
        elif attribute_name == "spinner_size":
            return self._spinner_size
        elif attribute_name == "spinner_line_width":
            return self._spinner_line_width
        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "spinner_color":
            return self._spinner_color
        elif attribute_name == "spinner_track_color":
            return self._spinner_track_color
        elif attribute_name == "text_color":
            return self._text_color
        elif attribute_name == "progress_text_color":
            return self._progress_text_color
        elif attribute_name == "font":
            return self._font
        elif attribute_name == "progress_font":
            return self._progress_font
        elif attribute_name == "fade_duration":
            return self._fade_duration
        elif attribute_name == "on_show":
            return self._on_show_callback
        elif attribute_name == "on_hide":
            return self._on_hide_callback
        elif attribute_name == "cancel_command":
            return self._cancel_command
        elif attribute_name == "cancel_text":
            return self._cancel_text
        elif attribute_name == "progress":
            return self._progress
        elif attribute_name == "visible":
            return self._visible
        else:
            return super().cget(attribute_name)

    # ------------------------------------------------------------------
    #  bind / unbind — override CTkBaseClass to allow internal bindings
    # ------------------------------------------------------------------

    def bind(self, sequence=None, command=None, add=None):
        """Bind on the internal canvas."""
        if not (add == "+" or add is True):
            raise ValueError(
                "'add' argument can only be '+' or True to preserve internal callbacks"
            )
        self._canvas.bind(sequence, command, add=True)

    def unbind(self, sequence=None, funcid=None):
        """Unbind from the internal canvas."""
        if funcid is not None:
            raise ValueError(
                "'funcid' argument can only be None, because there is a bug in "
                "tkinter and it's not clear whether internal callbacks will be unbound"
            )
        self._canvas.unbind(sequence, None)
