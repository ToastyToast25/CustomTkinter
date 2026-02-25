import sys
import os
import shutil
from typing import Union


class FontManager:

    linux_font_path = "~/.fonts/"

    @classmethod
    def init_font_manager(cls):
        # Linux
        if sys.platform.startswith("linux"):
            try:
                if not os.path.isdir(os.path.expanduser(cls.linux_font_path)):
                    os.mkdir(os.path.expanduser(cls.linux_font_path))
                return True
            except Exception as err:
                sys.stderr.write("FontManager error: " + str(err) + "\n")
                return False

        # other platforms
        else:
            return True

    @classmethod
    def windows_load_font(cls, font_path: Union[str, bytes], private: bool = True, enumerable: bool = False) -> bool:
        """ Function taken from: https://stackoverflow.com/questions/11993290/truly-custom-font-in-tkinter/30631309#30631309 """

        from ctypes import windll, byref, create_unicode_buffer, create_string_buffer

        FR_PRIVATE = 0x10
        FR_NOT_ENUM = 0x20

        if isinstance(font_path, bytes):
            path_buffer = create_string_buffer(font_path)
            add_font_resource_ex = windll.gdi32.AddFontResourceExA
        elif isinstance(font_path, str):
            path_buffer = create_unicode_buffer(font_path)
            add_font_resource_ex = windll.gdi32.AddFontResourceExW
        else:
            raise TypeError('font_path must be of type bytes or str')

        flags = (FR_PRIVATE if private else 0) | (FR_NOT_ENUM if not enumerable else 0)
        num_fonts_added = add_font_resource_ex(byref(path_buffer), flags, 0)
        return bool(min(num_fonts_added, 1))

    _VALID_FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2"}

    @classmethod
    def load_font(cls, font_path: str) -> bool:
        # Validate font file extension
        _, ext = os.path.splitext(font_path)
        if ext.lower() not in cls._VALID_FONT_EXTENSIONS:
            sys.stderr.write(f"FontManager error: invalid font extension '{ext}'. Expected one of {cls._VALID_FONT_EXTENSIONS}\n")
            return False

        # Resolve symlinks to prevent symlink attacks
        resolved_path = os.path.realpath(font_path)

        # Windows
        if sys.platform.startswith("win"):
            return cls.windows_load_font(resolved_path, private=True, enumerable=False)

        # Linux
        elif sys.platform.startswith("linux"):
            try:
                shutil.copy(resolved_path, os.path.expanduser(cls.linux_font_path))
                return True
            except Exception as err:
                sys.stderr.write("FontManager error: " + str(err) + "\n")
                return False

        # macOS and others
        else:
            return False
