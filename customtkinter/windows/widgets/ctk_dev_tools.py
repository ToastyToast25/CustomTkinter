"""
Developer validation tools for CustomTkinter widgets.

Catches common misconfiguration mistakes at construction time with
clear, actionable error messages. Enable globally or per-widget.

Usage:
    # Enable validation for all widgets in the app
    ctk.CTkDevTools.enable()

    # Now any misconfigured widget raises CTkConfigError with a clear message
    ctk.CTkRating(parent, max_stars=-1)
    # -> CTkConfigError: CTkRating: 'max_stars' must be >= 1, got -1

    # Validate an already-created widget
    issues = ctk.CTkDevTools.validate(widget)
    for issue in issues:
        print(issue)

    # Run a full audit of all widgets in a container
    report = ctk.CTkDevTools.audit(root_window)

    # Disable when shipping to production
    ctk.CTkDevTools.disable()
"""

import tkinter
import warnings
import sys
from typing import Any, Dict, List, Optional, Tuple, Type, Union


class CTkConfigError(ValueError):
    """Raised when a widget is misconfigured."""
    pass


class CTkConfigWarning(UserWarning):
    """Warning for non-fatal misconfigurations."""
    pass


# ── Validation rule definitions ────────────────────────────────────

_WIDGET_RULES: Dict[str, List[dict]] = {}


def _rule(widget_name: str, param: str, check, message: str, level: str = "error"):
    """Register a validation rule for a widget parameter."""
    if widget_name not in _WIDGET_RULES:
        _WIDGET_RULES[widget_name] = []
    _WIDGET_RULES[widget_name].append({
        "param": param,
        "check": check,
        "message": message,
        "level": level,
    })


# ── Type checkers ──────────────────────────────────────────────────

def _is_color(val):
    """Check if value looks like a valid color: hex string, named color, or (light, dark) tuple."""
    if val is None or val == "transparent":
        return True
    if isinstance(val, str):
        return True
    if isinstance(val, (list, tuple)) and len(val) == 2:
        return all(isinstance(c, str) for c in val)
    return False


def _is_positive_int(val):
    return isinstance(val, int) and val > 0


def _is_non_negative_int(val):
    return isinstance(val, int) and val >= 0


def _is_non_negative_num(val):
    return isinstance(val, (int, float)) and val >= 0


def _is_callable_or_none(val):
    return val is None or callable(val)


def _is_string_list(val):
    return isinstance(val, (list, tuple)) and all(isinstance(s, str) for s in val)


# ── Register rules for each widget ────────────────────────────────

# CTkRating
_rule("CTkRating", "max_stars", lambda v: isinstance(v, int) and v >= 1,
      "'max_stars' must be an integer >= 1, got {value!r}")
_rule("CTkRating", "initial_value", lambda v: isinstance(v, (int, float)) and v >= 0,
      "'initial_value' must be a non-negative number, got {value!r}")
_rule("CTkRating", "star_size", lambda v: isinstance(v, int) and v >= 8,
      "'star_size' must be an integer >= 8, got {value!r}")
_rule("CTkRating", "spacing", lambda v: isinstance(v, int) and v >= 0,
      "'spacing' must be a non-negative integer, got {value!r}")
_rule("CTkRating", "state", lambda v: v in ("normal", "readonly", "disabled"),
      "'state' must be 'normal', 'readonly', or 'disabled', got {value!r}")
_rule("CTkRating", "star_color", _is_color,
      "'star_color' must be a color string or (light, dark) tuple, got {value!r}")
_rule("CTkRating", "command", _is_callable_or_none,
      "'command' must be callable or None, got {value!r}")

# CTkAvatar
_rule("CTkAvatar", "size", lambda v: v in ("small", "medium", "large", "xlarge"),
      "'size' must be 'small', 'medium', 'large', or 'xlarge', got {value!r}")
_rule("CTkAvatar", "status", lambda v: v in (None, "online", "offline", "away", "busy"),
      "'status' must be None, 'online', 'offline', 'away', or 'busy', got {value!r}")
_rule("CTkAvatar", "text", lambda v: isinstance(v, str),
      "'text' must be a string, got {value!r}")
_rule("CTkAvatar", "border_width", lambda v: isinstance(v, int) and v >= 0,
      "'border_width' must be a non-negative integer, got {value!r}")

# CTkStepper
_rule("CTkStepper", "steps", _is_string_list,
      "'steps' must be a list of strings, got {value!r}")
_rule("CTkStepper", "steps", lambda v: isinstance(v, (list, tuple)) and len(v) >= 1,
      "'steps' must have at least 1 item, got {length} items", level="error")
_rule("CTkStepper", "current_step", lambda v: isinstance(v, int) and v >= 0,
      "'current_step' must be a non-negative integer, got {value!r}")
_rule("CTkStepper", "step_size", lambda v: isinstance(v, int) and v >= 12,
      "'step_size' must be an integer >= 12, got {value!r}")
_rule("CTkStepper", "line_width", lambda v: isinstance(v, int) and v >= 1,
      "'line_width' must be an integer >= 1, got {value!r}")

# CTkAccordion
_rule("CTkAccordion", "exclusive", lambda v: isinstance(v, bool),
      "'exclusive' must be a boolean, got {value!r}")
_rule("CTkAccordion", "animate", lambda v: isinstance(v, bool),
      "'animate' must be a boolean, got {value!r}")
_rule("CTkAccordion", "animation_duration", lambda v: isinstance(v, int) and v >= 0,
      "'animation_duration' must be a non-negative integer, got {value!r}")
_rule("CTkAccordion", "section_spacing", lambda v: isinstance(v, int) and v >= 0,
      "'section_spacing' must be a non-negative integer, got {value!r}")

# CTkCard
_rule("CTkCard", "border_width", lambda v: isinstance(v, int) and v >= 0,
      "'border_width' must be a non-negative integer, got {value!r}")
_rule("CTkCard", "hover_duration", lambda v: isinstance(v, int) and v >= 50,
      "'hover_duration' must be >= 50ms, got {value!r}")
_rule("CTkCard", "state", lambda v: v in ("normal", "disabled"),
      "'state' must be 'normal' or 'disabled', got {value!r}")
_rule("CTkCard", "selected", lambda v: isinstance(v, bool),
      "'selected' must be a boolean, got {value!r}")

# CTkToggleSwitch
_rule("CTkToggleSwitch", "size", lambda v: v in ("small", "medium", "large"),
      "'size' must be 'small', 'medium', or 'large', got {value!r}")
_rule("CTkToggleSwitch", "state", lambda v: v in ("normal", "disabled"),
      "'state' must be 'normal' or 'disabled', got {value!r}")
_rule("CTkToggleSwitch", "animation_duration", lambda v: isinstance(v, int) and v >= 50,
      "'animation_duration' must be >= 50ms, got {value!r}")

# CTkDataTable
_rule("CTkDataTable", "width", lambda v: isinstance(v, int) and v >= 50,
      "'width' must be an integer >= 50, got {value!r}")
_rule("CTkDataTable", "height", lambda v: isinstance(v, int) and v >= 50,
      "'height' must be an integer >= 50, got {value!r}")

# CTkTreeView
_rule("CTkTreeView", "width", lambda v: isinstance(v, int) and v >= 50,
      "'width' must be an integer >= 50, got {value!r}")
_rule("CTkTreeView", "height", lambda v: isinstance(v, int) and v >= 50,
      "'height' must be an integer >= 50, got {value!r}")

# CTkNumberEntry
_rule("CTkNumberEntry", "step", lambda v: isinstance(v, (int, float)) and v > 0,
      "'step' must be a positive number, got {value!r}")

# CTkRangeSlider
_rule("CTkRangeSlider", "orientation", lambda v: v in ("horizontal", "vertical"),
      "'orientation' must be 'horizontal' or 'vertical', got {value!r}")

# CTkNotificationBanner
_rule("CTkNotificationBanner", "style", lambda v: v in ("info", "success", "warning", "error"),
      "'style' must be 'info', 'success', 'warning', or 'error', got {value!r}")

# CTkChip
_rule("CTkChip", "style", lambda v: v in ("default", "primary", "success", "warning", "error"),
      "'style' must be 'default', 'primary', 'success', 'warning', or 'error', got {value!r}")

# CTkDatePicker
_rule("CTkDatePicker", "date_format", lambda v: isinstance(v, str) and len(v) > 0,
      "'date_format' must be a non-empty format string, got {value!r}")

# CTkTimePicker
_rule("CTkTimePicker", "time_format", lambda v: v in ("12h", "24h"),
      "'time_format' must be '12h' or '24h', got {value!r}")

# CTkBreadcrumb
_rule("CTkBreadcrumb", "items", lambda v: v is None or _is_string_list(v),
      "'items' must be None or a list of strings, got {value!r}")
_rule("CTkBreadcrumb", "max_items", lambda v: isinstance(v, int) and v >= 0,
      "'max_items' must be a non-negative integer, got {value!r}")

# CTkStatusBadge
_rule("CTkStatusBadge", "style", lambda v: v in ("success", "warning", "error", "info", "muted"),
      "'style' must be 'success', 'warning', 'error', 'info', or 'muted', got {value!r}")
_rule("CTkStatusBadge", "size", lambda v: v in ("small", "default", "large"),
      "'size' must be 'small', 'default', or 'large', got {value!r}")

# CTkCircularProgress
_rule("CTkCircularProgress", "mode", lambda v: v in ("determinate", "indeterminate"),
      "'mode' must be 'determinate' or 'indeterminate', got {value!r}")
_rule("CTkCircularProgress", "line_width", lambda v: isinstance(v, int) and v >= 1,
      "'line_width' must be an integer >= 1, got {value!r}")

# CTkSplitView
_rule("CTkSplitView", "orientation", lambda v: v in ("horizontal", "vertical"),
      "'orientation' must be 'horizontal' or 'vertical', got {value!r}")
_rule("CTkSplitView", "ratio", lambda v: isinstance(v, (int, float)) and 0.0 <= v <= 1.0,
      "'ratio' must be a number between 0.0 and 1.0, got {value!r}")
_rule("CTkSplitView", "min_size", lambda v: isinstance(v, int) and v >= 0,
      "'min_size' must be a non-negative integer, got {value!r}")


# ── Validation engine ──────────────────────────────────────────────

def _format_msg(template: str, param: str, value: Any) -> str:
    """Format a rule message, injecting value and length."""
    length = len(value) if hasattr(value, '__len__') else 0
    return template.format(value=value, length=length, param=param)


def _validate_kwargs(widget_class_name: str, kwargs: dict) -> List[str]:
    """
    Validate kwargs against registered rules for a widget class.
    Returns a list of error/warning message strings.
    """
    rules = _WIDGET_RULES.get(widget_class_name, [])
    issues = []

    for rule in rules:
        param = rule["param"]
        if param not in kwargs:
            continue

        value = kwargs[param]
        try:
            ok = rule["check"](value)
        except Exception:
            ok = False

        if not ok:
            msg = _format_msg(rule["message"], param, value)
            full_msg = f"{widget_class_name}: {msg}"
            issues.append((rule["level"], full_msg))

    return issues


# ── Public API ─────────────────────────────────────────────────────

class CTkDevTools:
    """
    Developer validation tools for catching widget misconfiguration.

    Call CTkDevTools.enable() during development to automatically validate
    all widget constructors and configure() calls. Disable for production.
    """

    _enabled = False
    _strict = False  # if True, raise on errors; if False, warn
    _patched_classes = {}
    _original_inits = {}
    _original_configures = {}

    @classmethod
    def enable(cls, strict: bool = True):
        """
        Enable developer validation on all registered widget classes.

        Args:
            strict: If True (default), raises CTkConfigError on invalid config.
                    If False, prints warnings instead.
        """
        if cls._enabled:
            return

        cls._strict = strict
        cls._enabled = True

        # Patch __init__ and configure on all widgets with registered rules
        from . import (
            CTkRating, CTkAvatar, CTkStepper, CTkAccordion, CTkCard,
            CTkToggleSwitch, CTkDataTable, CTkTreeView, CTkNumberEntry,
            CTkRangeSlider, CTkNotificationBanner, CTkChip, CTkDatePicker,
            CTkTimePicker, CTkBreadcrumb, CTkStatusBadge, CTkCircularProgress,
            CTkSplitView,
        )

        widget_map = {
            "CTkRating": CTkRating,
            "CTkAvatar": CTkAvatar,
            "CTkStepper": CTkStepper,
            "CTkAccordion": CTkAccordion,
            "CTkCard": CTkCard,
            "CTkToggleSwitch": CTkToggleSwitch,
            "CTkDataTable": CTkDataTable,
            "CTkTreeView": CTkTreeView,
            "CTkNumberEntry": CTkNumberEntry,
            "CTkRangeSlider": CTkRangeSlider,
            "CTkNotificationBanner": CTkNotificationBanner,
            "CTkChip": CTkChip,
            "CTkDatePicker": CTkDatePicker,
            "CTkTimePicker": CTkTimePicker,
            "CTkBreadcrumb": CTkBreadcrumb,
            "CTkStatusBadge": CTkStatusBadge,
            "CTkCircularProgress": CTkCircularProgress,
            "CTkSplitView": CTkSplitView,
        }

        for name, widget_cls in widget_map.items():
            if name not in _WIDGET_RULES:
                continue
            cls._patch_class(name, widget_cls)

        print(f"[CTkDevTools] Validation enabled (strict={strict}) "
              f"— {len(cls._patched_classes)} widget types monitored")

    @classmethod
    def disable(cls):
        """Disable developer validation and restore original methods."""
        if not cls._enabled:
            return

        for name, widget_cls in cls._patched_classes.items():
            if name in cls._original_inits:
                widget_cls.__init__ = cls._original_inits[name]
            if name in cls._original_configures:
                widget_cls.configure = cls._original_configures[name]

        cls._patched_classes.clear()
        cls._original_inits.clear()
        cls._original_configures.clear()
        cls._enabled = False
        print("[CTkDevTools] Validation disabled")

    @classmethod
    def _patch_class(cls, name: str, widget_cls):
        """Monkey-patch __init__ and configure to add validation."""
        cls._patched_classes[name] = widget_cls

        # Patch __init__
        original_init = widget_cls.__init__
        cls._original_inits[name] = original_init

        def patched_init(_self, *args, _orig=original_init, _name=name, **kwargs):
            cls._check_kwargs(_name, kwargs)
            return _orig(_self, *args, **kwargs)

        widget_cls.__init__ = patched_init

        # Patch configure
        original_configure = widget_cls.configure
        cls._original_configures[name] = original_configure

        def patched_configure(_self, _orig=original_configure, _name=name, **kwargs):
            cls._check_kwargs(_name, kwargs)
            return _orig(_self, **kwargs)

        widget_cls.configure = patched_configure

    @classmethod
    def _check_kwargs(cls, widget_name: str, kwargs: dict):
        """Run validation rules and raise/warn as appropriate."""
        issues = _validate_kwargs(widget_name, kwargs)
        for level, msg in issues:
            if level == "error":
                if cls._strict:
                    raise CTkConfigError(msg)
                else:
                    warnings.warn(msg, CTkConfigWarning, stacklevel=4)
            else:
                warnings.warn(msg, CTkConfigWarning, stacklevel=4)

    @classmethod
    def validate(cls, widget) -> List[str]:
        """
        Validate an already-created widget's current configuration.

        Returns a list of issue description strings (empty if all good).
        """
        widget_name = type(widget).__name__
        rules = _WIDGET_RULES.get(widget_name, [])
        issues = []

        for rule in rules:
            param = rule["param"]
            try:
                value = widget.cget(param)
            except Exception:
                continue

            try:
                ok = rule["check"](value)
            except Exception:
                ok = False

            if not ok:
                msg = _format_msg(rule["message"], param, value)
                issues.append(f"{widget_name}: {msg}")

        return issues

    @classmethod
    def audit(cls, root) -> dict:
        """
        Recursively audit all widgets under a root container.

        Returns a dict:
            {
                "total_widgets": int,
                "widgets_checked": int,
                "issues": [{"widget": str, "message": str}, ...],
                "summary": str,
            }
        """
        all_widgets = []
        cls._collect_widgets(root, all_widgets)

        total = len(all_widgets)
        checked = 0
        issues = []

        for widget in all_widgets:
            widget_name = type(widget).__name__
            if widget_name in _WIDGET_RULES:
                checked += 1
                widget_issues = cls.validate(widget)
                for msg in widget_issues:
                    issues.append({
                        "widget": f"{widget_name} ({id(widget):#x})",
                        "message": msg,
                    })

        if issues:
            summary = f"FAIL: {len(issues)} issue(s) found in {checked}/{total} widgets"
        else:
            summary = f"PASS: {checked}/{total} widgets checked, no issues found"

        return {
            "total_widgets": total,
            "widgets_checked": checked,
            "issues": issues,
            "summary": summary,
        }

    @classmethod
    def _collect_widgets(cls, widget, result: list):
        """Recursively collect all child widgets."""
        result.append(widget)
        try:
            for child in widget.winfo_children():
                cls._collect_widgets(child, result)
        except Exception:
            pass

    @classmethod
    def print_audit(cls, root):
        """Run audit and print a formatted report."""
        report = cls.audit(root)
        print(f"\n{'='*60}")
        print(f"  CTkDevTools Audit Report")
        print(f"{'='*60}")
        print(f"  Total widgets:   {report['total_widgets']}")
        print(f"  Widgets checked: {report['widgets_checked']}")
        print(f"  Issues found:    {len(report['issues'])}")
        print(f"{'='*60}")

        if report["issues"]:
            for i, issue in enumerate(report["issues"], 1):
                print(f"\n  [{i}] {issue['widget']}")
                print(f"      {issue['message']}")
        else:
            print("\n  All widgets configured correctly!")

        print(f"\n  {report['summary']}")
        print(f"{'='*60}\n")
        return report

    @classmethod
    def is_enabled(cls) -> bool:
        """Return True if validation is currently enabled."""
        return cls._enabled
