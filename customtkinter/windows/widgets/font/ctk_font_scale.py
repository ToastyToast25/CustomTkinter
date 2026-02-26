"""
CTkFontScale — Predefined typography scale for consistent text hierarchy.

Provides named font presets (display, heading, subheading, body, caption, etc.)
that return CTkFont instances with consistent sizing, weight, and spacing.

Usage:
    from customtkinter import CTkFontScale

    title = CTkFontScale.heading()      # CTkFont(size=22, weight="bold")
    body  = CTkFontScale.body()         # CTkFont(size=14)
    small = CTkFontScale.caption()      # CTkFont(size=11)

    # Or get all presets as a dict for programmatic use:
    scale = CTkFontScale.get_scale()
"""

from typing import Dict, Optional
from .ctk_font import CTkFont


# Default scale (Material Design 3 inspired, pixel sizes)
_DEFAULT_SCALE = {
    "display_large":   {"size": 40, "weight": "bold"},
    "display":         {"size": 32, "weight": "bold"},
    "heading_large":   {"size": 26, "weight": "bold"},
    "heading":         {"size": 22, "weight": "bold"},
    "subheading":      {"size": 18, "weight": "bold"},
    "title":           {"size": 16, "weight": "bold"},
    "body_large":      {"size": 16, "weight": "normal"},
    "body":            {"size": 14, "weight": "normal"},
    "body_small":      {"size": 13, "weight": "normal"},
    "label":           {"size": 13, "weight": "bold"},
    "caption":         {"size": 11, "weight": "normal"},
    "overline":        {"size": 10, "weight": "bold"},
}


class CTkFontScale:
    """Provides named font presets for a consistent type hierarchy."""

    _custom_scale: Optional[Dict] = None

    @classmethod
    def _get_spec(cls, name: str) -> dict:
        scale = cls._custom_scale if cls._custom_scale is not None else _DEFAULT_SCALE
        return scale[name]

    # -- Named presets (each returns a new CTkFont instance) ----------------

    @classmethod
    def display_large(cls, **overrides) -> CTkFont:
        spec = {**cls._get_spec("display_large"), **overrides}
        return CTkFont(**spec)

    @classmethod
    def display(cls, **overrides) -> CTkFont:
        spec = {**cls._get_spec("display"), **overrides}
        return CTkFont(**spec)

    @classmethod
    def heading_large(cls, **overrides) -> CTkFont:
        spec = {**cls._get_spec("heading_large"), **overrides}
        return CTkFont(**spec)

    @classmethod
    def heading(cls, **overrides) -> CTkFont:
        spec = {**cls._get_spec("heading"), **overrides}
        return CTkFont(**spec)

    @classmethod
    def subheading(cls, **overrides) -> CTkFont:
        spec = {**cls._get_spec("subheading"), **overrides}
        return CTkFont(**spec)

    @classmethod
    def title(cls, **overrides) -> CTkFont:
        spec = {**cls._get_spec("title"), **overrides}
        return CTkFont(**spec)

    @classmethod
    def body_large(cls, **overrides) -> CTkFont:
        spec = {**cls._get_spec("body_large"), **overrides}
        return CTkFont(**spec)

    @classmethod
    def body(cls, **overrides) -> CTkFont:
        spec = {**cls._get_spec("body"), **overrides}
        return CTkFont(**spec)

    @classmethod
    def body_small(cls, **overrides) -> CTkFont:
        spec = {**cls._get_spec("body_small"), **overrides}
        return CTkFont(**spec)

    @classmethod
    def label(cls, **overrides) -> CTkFont:
        spec = {**cls._get_spec("label"), **overrides}
        return CTkFont(**spec)

    @classmethod
    def caption(cls, **overrides) -> CTkFont:
        spec = {**cls._get_spec("caption"), **overrides}
        return CTkFont(**spec)

    @classmethod
    def overline(cls, **overrides) -> CTkFont:
        spec = {**cls._get_spec("overline"), **overrides}
        return CTkFont(**spec)

    # -- Scale management ---------------------------------------------------

    @classmethod
    def get_scale(cls) -> Dict[str, dict]:
        """Return the current type scale as a dict of {name: {size, weight, ...}}."""
        return dict(cls._custom_scale if cls._custom_scale is not None else _DEFAULT_SCALE)

    @classmethod
    def set_scale(cls, scale: Dict[str, dict]) -> None:
        """
        Override the default type scale.  Keys should match the preset names
        (display_large, display, heading_large, heading, subheading, title,
        body_large, body, body_small, label, caption, overline).
        Missing keys fall back to defaults.
        """
        merged = dict(_DEFAULT_SCALE)
        merged.update(scale)
        cls._custom_scale = merged

    @classmethod
    def reset_scale(cls) -> None:
        """Reset to the built-in default type scale."""
        cls._custom_scale = None
