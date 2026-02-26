"""
CTkColorUtils — Color manipulation and palette generation for CustomTkinter.

Provides functions to lighten, darken, adjust saturation/opacity, mix colors,
and auto-generate a full widget palette from a single accent color.

Usage:
    from .utility.ctk_color_utils import ColorUtils

    palette = ColorUtils.generate_palette("#3B8ED0")
    darker  = ColorUtils.darken("#3B8ED0", 0.15)
    lighter = ColorUtils.lighten("#3B8ED0", 0.20)
    mixed   = ColorUtils.mix("#ff0000", "#0000ff", 0.5)
    shadow  = ColorUtils.with_alpha("#000000", 0.12)  # -> hex approximation on bg
"""

import colorsys
from typing import Tuple, Dict


class ColorUtils:
    """Static utility class for color manipulation."""

    # -- Parsing / conversion -----------------------------------------------

    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert #RRGGBB or #RGB to (r, g, b) ints 0-255."""
        h = hex_color.lstrip("#")
        if len(h) == 3:
            h = h[0]*2 + h[1]*2 + h[2]*2
        if len(h) != 6:
            raise ValueError(f"Invalid hex color '{hex_color}': expected #RRGGBB or #RGB")
        try:
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        except ValueError:
            raise ValueError(f"Invalid hex color '{hex_color}': contains non-hex characters")

    @staticmethod
    def rgb_to_hex(r: int, g: int, b: int) -> str:
        """Convert (r, g, b) ints 0-255 to #rrggbb."""
        return f"#{max(0,min(255,r)):02x}{max(0,min(255,g)):02x}{max(0,min(255,b)):02x}"

    @staticmethod
    def hex_to_hsl(hex_color: str) -> Tuple[float, float, float]:
        """Convert #RRGGBB to (h, s, l) floats 0-1."""
        r, g, b = ColorUtils.hex_to_rgb(hex_color)
        r_f, g_f, b_f = r / 255.0, g / 255.0, b / 255.0
        h, l, s = colorsys.rgb_to_hls(r_f, g_f, b_f)
        return h, s, l

    @staticmethod
    def hsl_to_hex(h: float, s: float, l: float) -> str:
        """Convert (h, s, l) floats 0-1 to #rrggbb."""
        r_f, g_f, b_f = colorsys.hls_to_rgb(h, l, s)
        return ColorUtils.rgb_to_hex(int(r_f * 255), int(g_f * 255), int(b_f * 255))

    # -- Basic operations ---------------------------------------------------

    @staticmethod
    def lighten(hex_color: str, amount: float = 0.15) -> str:
        """Make a color lighter by `amount` (0-1). 0.15 = 15% lighter."""
        h, s, l = ColorUtils.hex_to_hsl(hex_color)
        l = min(1.0, l + amount)
        return ColorUtils.hsl_to_hex(h, s, l)

    @staticmethod
    def darken(hex_color: str, amount: float = 0.15) -> str:
        """Make a color darker by `amount` (0-1). 0.15 = 15% darker."""
        h, s, l = ColorUtils.hex_to_hsl(hex_color)
        l = max(0.0, l - amount)
        return ColorUtils.hsl_to_hex(h, s, l)

    @staticmethod
    def saturate(hex_color: str, amount: float = 0.15) -> str:
        """Increase saturation by `amount`."""
        h, s, l = ColorUtils.hex_to_hsl(hex_color)
        s = min(1.0, s + amount)
        return ColorUtils.hsl_to_hex(h, s, l)

    @staticmethod
    def desaturate(hex_color: str, amount: float = 0.15) -> str:
        """Decrease saturation by `amount`."""
        h, s, l = ColorUtils.hex_to_hsl(hex_color)
        s = max(0.0, s - amount)
        return ColorUtils.hsl_to_hex(h, s, l)

    @staticmethod
    def set_lightness(hex_color: str, lightness: float) -> str:
        """Set absolute lightness (0-1)."""
        h, s, _ = ColorUtils.hex_to_hsl(hex_color)
        return ColorUtils.hsl_to_hex(h, s, max(0.0, min(1.0, lightness)))

    @staticmethod
    def set_saturation(hex_color: str, saturation: float) -> str:
        """Set absolute saturation (0-1)."""
        h, _, l = ColorUtils.hex_to_hsl(hex_color)
        return ColorUtils.hsl_to_hex(h, max(0.0, min(1.0, saturation)), l)

    @staticmethod
    def mix(hex1: str, hex2: str, weight: float = 0.5) -> str:
        """Mix two colors. weight=0 returns hex1, weight=1 returns hex2."""
        r1, g1, b1 = ColorUtils.hex_to_rgb(hex1)
        r2, g2, b2 = ColorUtils.hex_to_rgb(hex2)
        w = max(0.0, min(1.0, weight))
        return ColorUtils.rgb_to_hex(
            int(r1 + (r2 - r1) * w),
            int(g1 + (g2 - g1) * w),
            int(b1 + (b2 - b1) * w),
        )

    @staticmethod
    def with_alpha(hex_color: str, alpha: float, bg_hex: str = "#ffffff") -> str:
        """
        Simulate alpha transparency by blending `hex_color` at `alpha`
        onto `bg_hex`. Since tkinter has no real alpha, this produces
        the equivalent flat color.
        """
        return ColorUtils.mix(bg_hex, hex_color, alpha)

    @staticmethod
    def contrast_text(hex_bg: str) -> str:
        """Return '#ffffff' or '#1a1a1a' depending on which has better contrast."""
        r, g, b = ColorUtils.hex_to_rgb(hex_bg)
        # Relative luminance (ITU-R BT.709)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
        return "#1a1a1a" if luminance > 0.5 else "#ffffff"

    @staticmethod
    def complementary(hex_color: str) -> str:
        """Return the complementary (opposite hue) color."""
        h, s, l = ColorUtils.hex_to_hsl(hex_color)
        return ColorUtils.hsl_to_hex((h + 0.5) % 1.0, s, l)

    # -- Palette generation -------------------------------------------------

    @staticmethod
    def generate_palette(accent: str) -> Dict[str, Tuple[str, str]]:
        """
        Auto-generate a complete widget color palette from a single accent
        hex color.  Returns a dict of ``{name: (light_mode, dark_mode)}``.

        Generated roles:
            accent           — the accent color itself
            accent_hover     — 12% darker (light), 10% lighter (dark)
            accent_disabled  — desaturated 40%, lightened 20% (light) / darkened 10% (dark)
            surface_tint     — accent at 8% opacity on white (light) / on #1a1a1a (dark)
            on_accent        — contrast text for accent
            border           — accent at 30% opacity
            shadow           — #000 at 12% (light), #000 at 25% (dark)
            success          — green variant
            warning          — amber variant
            error            — red variant
        """
        h, s, l = ColorUtils.hex_to_hsl(accent)

        # Light & dark variants of the accent
        accent_light = accent
        accent_dark = ColorUtils.set_lightness(accent, max(0.3, l - 0.08))

        hover_light = ColorUtils.darken(accent, 0.12)
        hover_dark = ColorUtils.lighten(accent_dark, 0.10)

        disabled_light = ColorUtils.lighten(ColorUtils.desaturate(accent, 0.40), 0.20)
        disabled_dark = ColorUtils.darken(ColorUtils.desaturate(accent_dark, 0.30), 0.10)

        tint_light = ColorUtils.with_alpha(accent, 0.08, "#ffffff")
        tint_dark = ColorUtils.with_alpha(accent_dark, 0.10, "#1a1a1a")

        border_light = ColorUtils.with_alpha(accent, 0.30, "#ffffff")
        border_dark = ColorUtils.with_alpha(accent_dark, 0.30, "#1a1a1a")

        on_accent = ColorUtils.contrast_text(accent)

        # Semantic colors — shift hue but keep similar saturation/lightness
        success_light = ColorUtils.hsl_to_hex(0.38, min(s, 0.65), min(l, 0.45))
        success_dark = ColorUtils.hsl_to_hex(0.38, min(s, 0.55), 0.40)

        warning_light = ColorUtils.hsl_to_hex(0.10, min(s + 0.1, 0.8), min(l, 0.50))
        warning_dark = ColorUtils.hsl_to_hex(0.10, min(s + 0.1, 0.7), 0.45)

        error_light = ColorUtils.hsl_to_hex(0.0, min(s + 0.1, 0.75), min(l, 0.48))
        error_dark = ColorUtils.hsl_to_hex(0.0, min(s + 0.1, 0.65), 0.42)

        shadow_light = ColorUtils.with_alpha("#000000", 0.12, "#ffffff")
        shadow_dark = ColorUtils.with_alpha("#000000", 0.25, "#141414")

        return {
            "accent":           (accent_light, accent_dark),
            "accent_hover":     (hover_light, hover_dark),
            "accent_disabled":  (disabled_light, disabled_dark),
            "surface_tint":     (tint_light, tint_dark),
            "on_accent":        (on_accent, on_accent),
            "border":           (border_light, border_dark),
            "shadow":           (shadow_light, shadow_dark),
            "success":          (success_light, success_dark),
            "warning":          (warning_light, warning_dark),
            "error":            (error_light, error_dark),
        }
