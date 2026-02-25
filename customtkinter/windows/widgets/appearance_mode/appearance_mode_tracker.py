import tkinter
from typing import Callable
import darkdetect


def _is_tk_alive(widget) -> bool:
    """Check if a tkinter widget still exists and has a valid Tcl interpreter."""
    try:
        return widget.winfo_exists()
    except Exception:
        return False


class AppearanceModeTracker:

    callback_set: set = set()
    app_list = []
    update_loop_running = False
    update_loop_interval = 500  # milliseconds (increased from 30ms — theme changes are rare user events)

    appearance_mode_set_by = "system"
    appearance_mode = 0  # Light (standard)

    @classmethod
    def init_appearance_mode(cls):
        if cls.appearance_mode_set_by == "system":
            new_appearance_mode = cls.detect_appearance_mode()

            if new_appearance_mode != cls.appearance_mode:
                cls.appearance_mode = new_appearance_mode
                cls.update_callbacks()

    @classmethod
    def add(cls, callback: Callable, widget=None):
        cls.callback_set.add(callback)

        if widget is not None:
            app = cls.get_tk_root_of_widget(widget)
            if app not in cls.app_list:
                cls.app_list.append(app)

                if not cls.update_loop_running:
                    app.after(cls.update_loop_interval, cls.update)
                    cls.update_loop_running = True

    @classmethod
    def remove(cls, callback: Callable):
        cls.callback_set.discard(callback)

    @classmethod
    def remove_app(cls, app):
        try:
            cls.app_list.remove(app)
        except ValueError:
            return

    @staticmethod
    def detect_appearance_mode() -> int:
        try:
            if darkdetect.theme() == "Dark":
                return 1  # Dark
            else:
                return 0  # Light
        except NameError:
            return 0  # Light

    @classmethod
    def get_tk_root_of_widget(cls, widget):
        current_widget = widget

        while isinstance(current_widget, tkinter.Tk) is False:
            current_widget = current_widget.master

        return current_widget

    @classmethod
    def update_callbacks(cls):
        mode_string = "Light" if cls.appearance_mode == 0 else "Dark"
        for callback in list(cls.callback_set):
            try:
                callback(mode_string)
            except Exception:
                continue

    @classmethod
    def update(cls):
        if cls.appearance_mode_set_by == "system":
            new_appearance_mode = cls.detect_appearance_mode()

            if new_appearance_mode != cls.appearance_mode:
                cls.appearance_mode = new_appearance_mode
                cls.update_callbacks()

        # prune destroyed windows and find a live one for the next .after() call
        cls.app_list = [app for app in cls.app_list if _is_tk_alive(app)]
        for app in cls.app_list:
            try:
                app.after(cls.update_loop_interval, cls.update)
                return
            except Exception:
                continue

        cls.update_loop_running = False

    @classmethod
    def get_mode(cls) -> int:
        return cls.appearance_mode

    @classmethod
    def set_appearance_mode(cls, mode_string: str):
        if mode_string.lower() == "dark":
            cls.appearance_mode_set_by = "user"
            new_appearance_mode = 1

            if new_appearance_mode != cls.appearance_mode:
                cls.appearance_mode = new_appearance_mode
                cls.update_callbacks()

        elif mode_string.lower() == "light":
            cls.appearance_mode_set_by = "user"
            new_appearance_mode = 0

            if new_appearance_mode != cls.appearance_mode:
                cls.appearance_mode = new_appearance_mode
                cls.update_callbacks()

        elif mode_string.lower() == "system":
            cls.appearance_mode_set_by = "system"
