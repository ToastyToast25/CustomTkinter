import tkinter
import copy
import sys
from typing import Union, Tuple, Callable, List, Optional

from ..theme import ThemeManager
from ..font import CTkFont
from ..appearance_mode import CTkAppearanceModeBaseClass
from ..scaling import CTkScalingBaseClass


class DropdownMenu(tkinter.Menu, CTkAppearanceModeBaseClass, CTkScalingBaseClass):
    def __init__(self, *args,
                 min_character_width: int = 18,

                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,

                 font: Optional[Union[tuple, CTkFont]] = None,
                 command: Union[Callable, None] = None,
                 values: Optional[List[str]] = None,
                 max_visible_items: int = 0,
                 **kwargs):

        # call init methods of super classes
        tkinter.Menu.__init__(self, *args, **kwargs)
        CTkAppearanceModeBaseClass.__init__(self)
        CTkScalingBaseClass.__init__(self, scaling_type="widget")

        self._min_character_width = min_character_width
        self._fg_color = ThemeManager.theme["DropdownMenu"]["fg_color"] if fg_color is None else self._check_color_type(fg_color)
        self._hover_color = ThemeManager.theme["DropdownMenu"]["hover_color"] if hover_color is None else self._check_color_type(hover_color)
        self._text_color = ThemeManager.theme["DropdownMenu"]["text_color"] if text_color is None else self._check_color_type(text_color)

        # font
        self._font = CTkFont() if font is None else self._check_font_type(font)
        if isinstance(self._font, CTkFont):
            self._font.add_size_configure_callback(self._update_font)

        self._configure_menu_for_platforms()

        self._values = values
        self._command = command
        self._max_visible_items = max_visible_items  # 0 = unlimited
        self._scroll_offset = 0
        self._last_open_x = 0
        self._last_open_y = 0

        self._add_menu_commands()

    def destroy(self):
        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)

        # call destroy methods of super classes
        tkinter.Menu.destroy(self)
        CTkAppearanceModeBaseClass.destroy(self)
        CTkScalingBaseClass.destroy(self)

    def _update_font(self):
        """ pass font to tkinter widgets with applied font scaling """
        super().configure(font=self._apply_font_scaling(self._font))

    def _configure_menu_for_platforms(self):
        """ apply platform specific appearance attributes, configure all colors """

        if sys.platform == "darwin":
            super().configure(tearoff=False,
                              font=self._apply_font_scaling(self._font))

        elif sys.platform.startswith("win"):
            super().configure(tearoff=False,
                              relief="flat",
                              activebackground=self._apply_appearance_mode(self._hover_color),
                              borderwidth=self._apply_widget_scaling(4),
                              activeborderwidth=self._apply_widget_scaling(4),
                              bg=self._apply_appearance_mode(self._fg_color),
                              fg=self._apply_appearance_mode(self._text_color),
                              activeforeground=self._apply_appearance_mode(self._text_color),
                              font=self._apply_font_scaling(self._font),
                              cursor="hand2")

        else:
            super().configure(tearoff=False,
                              relief="flat",
                              activebackground=self._apply_appearance_mode(self._hover_color),
                              borderwidth=0,
                              activeborderwidth=0,
                              bg=self._apply_appearance_mode(self._fg_color),
                              fg=self._apply_appearance_mode(self._text_color),
                              activeforeground=self._apply_appearance_mode(self._text_color),
                              font=self._apply_font_scaling(self._font))

    def _add_menu_commands(self):
        """ delete existing menu labels and create new labels with command according to values list """

        self.delete(0, "end")  # delete all old commands

        if not self._values:
            return

        needs_scroll = self._max_visible_items > 0 and len(self._values) > self._max_visible_items

        if needs_scroll:
            # clamp scroll offset
            max_offset = len(self._values) - self._max_visible_items
            self._scroll_offset = max(0, min(self._scroll_offset, max_offset))
            visible = self._values[self._scroll_offset:self._scroll_offset + self._max_visible_items]

            # scroll up indicator
            if self._scroll_offset > 0:
                self.add_command(label="\u25B2  Scroll up".ljust(self._min_character_width),
                                 command=self._scroll_up, compound="left")
            else:
                self.add_command(label=" ".ljust(self._min_character_width),
                                 state="disabled", compound="left")
        else:
            visible = self._values

        if sys.platform.startswith("linux"):
            for value in visible:
                self.add_command(label="  " + value.ljust(self._min_character_width) + "  ",
                                 command=lambda v=value: self._button_callback(v),
                                 compound="left")
        else:
            for value in visible:
                self.add_command(label=value.ljust(self._min_character_width),
                                 command=lambda v=value: self._button_callback(v),
                                 compound="left")

        if needs_scroll:
            # scroll down indicator
            if self._scroll_offset + self._max_visible_items < len(self._values):
                self.add_command(label="\u25BC  Scroll down".ljust(self._min_character_width),
                                 command=self._scroll_down, compound="left")
            else:
                self.add_command(label=" ".ljust(self._min_character_width),
                                 state="disabled", compound="left")

    def _scroll_up(self):
        """ Scroll the visible window up by a page """
        self._scroll_offset = max(0, self._scroll_offset - self._max_visible_items)
        self._add_menu_commands()
        self._reopen()

    def _scroll_down(self):
        """ Scroll the visible window down by a page """
        max_offset = len(self._values) - self._max_visible_items
        self._scroll_offset = min(max_offset, self._scroll_offset + self._max_visible_items)
        self._add_menu_commands()
        self._reopen()

    def _reopen(self):
        """ Close and reopen the menu at the same position to reflect scroll changes """
        try:
            self.unpost()
            if sys.platform == "darwin" or sys.platform.startswith("win"):
                self.post(int(self._last_open_x), int(self._last_open_y))
            else:
                self.tk_popup(int(self._last_open_x), int(self._last_open_y))
        except Exception:
            pass

    def _button_callback(self, value):
        if self._command is not None:
            self._command(value)

    def open(self, x: Union[int, float], y: Union[int, float]):

        if sys.platform == "darwin":
            y += self._apply_widget_scaling(8)
        else:
            y += self._apply_widget_scaling(3)

        # flip dropdown above the widget if it would extend past the screen bottom
        try:
            screen_height = self.winfo_screenheight()
            item_count = len(self._values) if self._values else 0
            if self._max_visible_items > 0:
                item_count = min(item_count, self._max_visible_items + 2)  # +2 for scroll arrows
            estimated_item_height = self._apply_widget_scaling(28)
            estimated_height = item_count * estimated_item_height + self._apply_widget_scaling(8)

            if y + estimated_height > screen_height and y > estimated_height:
                y = y - estimated_height - self._apply_widget_scaling(6)
        except Exception:
            pass

        # reset scroll offset on fresh open and rebuild menu
        self._scroll_offset = 0
        self._add_menu_commands()

        self._last_open_x = x
        self._last_open_y = y

        if sys.platform == "darwin" or sys.platform.startswith("win"):
            self.post(int(x), int(y))
        else:  # Linux
            self.tk_popup(int(x), int(y))

    def close(self):
        self.unpost()

    def is_open(self) -> bool:
        return bool(self.winfo_viewable())

    def configure(self, **kwargs):
        if "max_visible_items" in kwargs:
            self._max_visible_items = kwargs.pop("max_visible_items")
            self._scroll_offset = 0
            self._add_menu_commands()

        if "min_character_width" in kwargs:
            self._min_character_width = kwargs.pop("min_character_width")
            self._add_menu_commands()

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"))
            super().configure(bg=self._apply_appearance_mode(self._fg_color))

        if "hover_color" in kwargs:
            self._hover_color = self._check_color_type(kwargs.pop("hover_color"))
            super().configure(activebackground=self._apply_appearance_mode(self._hover_color))

        if "text_color" in kwargs:
            self._text_color = self._check_color_type(kwargs.pop("text_color"))
            super().configure(fg=self._apply_appearance_mode(self._text_color))

        if "font" in kwargs:
            if isinstance(self._font, CTkFont):
                self._font.remove_size_configure_callback(self._update_font)
            self._font = self._check_font_type(kwargs.pop("font"))
            if isinstance(self._font, CTkFont):
                self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "values" in kwargs:
            self._values = kwargs.pop("values")
            self._add_menu_commands()

        super().configure(**kwargs)

    def cget(self, attribute_name: str) -> any:
        if attribute_name == "max_visible_items":
            return self._max_visible_items
        elif attribute_name == "min_character_width":
            return self._min_character_width

        elif attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "hover_color":
            return self._hover_color
        elif attribute_name == "text_color":
            return self._text_color

        elif attribute_name == "font":
            return self._font
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "values":
            return copy.copy(self._values)

        else:
            return super().cget(attribute_name)

    @staticmethod
    def _check_font_type(font: any):
        if isinstance(font, CTkFont):
            return font

        elif type(font) == tuple and len(font) == 1:
            sys.stderr.write(f"Warning: font {font} given without size, will be extended with default text size of current theme\n")
            return font[0], ThemeManager.theme["text"]["size"]

        elif type(font) == tuple and 2 <= len(font) <= 3:
            return font

        else:
            raise ValueError(f"Wrong font type {type(font)} for font '{font}'\n" +
                             f"For consistency, Customtkinter requires the font argument to be a tuple of len 2 or 3 or an instance of CTkFont.\n" +
                             f"\nUsage example:\n" +
                             f"font=customtkinter.CTkFont(family='<name>', size=<size in px>)\n" +
                             f"font=('<name>', <size in px>)\n")

    def _set_scaling(self, new_widget_scaling, new_window_scaling):
        super()._set_scaling(new_widget_scaling, new_window_scaling)
        self._configure_menu_for_platforms()

    def _set_appearance_mode(self, mode_string):
        """ colors won't update on appearance mode change when dropdown is open, because it's not necessary """
        super()._set_appearance_mode(mode_string)
        self._configure_menu_for_platforms()
