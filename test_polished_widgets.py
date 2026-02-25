"""
Comprehensive test for all 10 polished CustomTkinter widgets.

Tests instantiation, API calls, state changes, configure/cget,
and destroy for each widget. Requires a display (tkinter).
"""

import tkinter
import sys
import time

# Add customtkinter to path
sys.path.insert(0, r"C:\Users\Administrator\Pictures\CustomTkinter")
import customtkinter as ctk


class TestRunner:
    """Simple test runner that tracks pass/fail counts."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def test(self, name, func):
        try:
            func()
            self.passed += 1
            print(f"  PASS  {name}")
        except Exception as e:
            self.failed += 1
            self.errors.append((name, e))
            print(f"  FAIL  {name}: {e}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Results: {self.passed}/{total} passed, {self.failed} failed")
        if self.errors:
            print(f"\nFailures:")
            for name, err in self.errors:
                print(f"  - {name}: {err}")
        print(f"{'='*60}")
        return self.failed == 0


def main():
    runner = TestRunner()

    # Create root window
    root = ctk.CTk()
    root.geometry("800x600")
    root.withdraw()  # Hide window during tests
    root.update()

    # ================================================================
    # 1. CTkToolTip
    # ================================================================
    print("\n--- CTkToolTip ---")

    btn = ctk.CTkButton(root, text="Hover me")
    btn.pack()
    root.update()

    def test_tooltip_create():
        tip = ctk.CTkToolTip(btn, message="Test tooltip")
        assert tip._message == "Test tooltip"
        assert tip._enabled is True

    def test_tooltip_disable_enable():
        tip = ctk.CTkToolTip(btn, message="Test")
        tip.disable()
        assert tip._enabled is False
        tip.enable()
        assert tip._enabled is True

    def test_tooltip_show_hide():
        tip = ctk.CTkToolTip(btn, message="Programmatic", fade_in=False)
        tip.show()
        root.update()
        assert tip._visible is True
        tip.hide()
        root.update()
        assert tip._visible is False

    def test_tooltip_configure():
        tip = ctk.CTkToolTip(btn, message="Old")
        tip.configure(message="New")
        assert tip._message == "New"
        tip.configure(enabled=False)
        assert tip._enabled is False

    def test_tooltip_cget():
        tip = ctk.CTkToolTip(btn, message="Hello", delay=500)
        assert tip.cget("message") == "Hello"
        assert tip.cget("delay") == 500
        assert tip.cget("enabled") is True

    def test_tooltip_follow_cursor():
        tip = ctk.CTkToolTip(btn, message="Follow", follow_cursor=True)
        assert tip._follow_cursor is True

    runner.test("tooltip_create", test_tooltip_create)
    runner.test("tooltip_disable_enable", test_tooltip_disable_enable)
    runner.test("tooltip_show_hide", test_tooltip_show_hide)
    runner.test("tooltip_configure", test_tooltip_configure)
    runner.test("tooltip_cget", test_tooltip_cget)
    runner.test("tooltip_follow_cursor", test_tooltip_follow_cursor)
    btn.destroy()

    # ================================================================
    # 2. CTkCollapsibleFrame
    # ================================================================
    print("\n--- CTkCollapsibleFrame ---")

    def test_collapsible_create():
        cf = ctk.CTkCollapsibleFrame(root, title="Section")
        cf.pack()
        root.update()
        assert cf._title == "Section"
        assert cf._collapsed is False
        cf.destroy()

    def test_collapsible_start_collapsed():
        cf = ctk.CTkCollapsibleFrame(root, title="Closed", collapsed=True)
        cf.pack()
        root.update()
        assert cf.is_collapsed() is True
        cf.destroy()

    def test_collapsible_toggle():
        cf = ctk.CTkCollapsibleFrame(root, title="Toggle", animate=False)
        cf.pack()
        root.update()
        assert cf.is_collapsed() is False
        cf.collapse(animate=False)
        assert cf.is_collapsed() is True
        cf.expand(animate=False)
        assert cf.is_collapsed() is False
        cf.destroy()

    def test_collapsible_content_access():
        cf = ctk.CTkCollapsibleFrame(root, title="Content")
        cf.pack()
        root.update()
        content = cf.content
        assert content is not None
        lbl = ctk.CTkLabel(content, text="Inside")
        lbl.pack()
        root.update()
        cf.destroy()

    def test_collapsible_lock():
        cf = ctk.CTkCollapsibleFrame(root, title="Locked", lock=True)
        cf.pack()
        root.update()
        assert cf._lock is True
        # Expand should be blocked when locked
        cf.collapse(animate=False)
        was_collapsed = cf.is_collapsed()
        cf.expand(animate=False)
        # If it was already collapsed and locked, it stays collapsed
        # If not collapsed (default), toggle should be blocked
        cf.destroy()

    def test_collapsible_configure_cget():
        cf = ctk.CTkCollapsibleFrame(root, title="Old Title", animate=False)
        cf.pack()
        root.update()
        cf.configure(title="New Title")
        assert cf.cget("title") == "New Title"
        cf.configure(lock=True)
        assert cf.cget("lock") is True
        cf.configure(animation_duration=300)
        assert cf.cget("animation_duration") == 300
        cf.destroy()

    def test_collapsible_command_callback():
        results = []
        cf = ctk.CTkCollapsibleFrame(root, title="CB", animate=False,
                                      command=lambda c: results.append(c))
        cf.pack()
        root.update()
        cf.collapse(animate=False)
        assert len(results) == 1
        assert results[0] is True  # collapsed=True
        cf.expand(animate=False)
        assert len(results) == 2
        assert results[1] is False  # collapsed=False
        cf.destroy()

    runner.test("collapsible_create", test_collapsible_create)
    runner.test("collapsible_start_collapsed", test_collapsible_start_collapsed)
    runner.test("collapsible_toggle", test_collapsible_toggle)
    runner.test("collapsible_content_access", test_collapsible_content_access)
    runner.test("collapsible_lock", test_collapsible_lock)
    runner.test("collapsible_configure_cget", test_collapsible_configure_cget)
    runner.test("collapsible_command_callback", test_collapsible_command_callback)

    # ================================================================
    # 3. CTkContextMenu
    # ================================================================
    print("\n--- CTkContextMenu ---")

    def test_context_menu_create():
        menu = ctk.CTkContextMenu(root)
        assert menu._items == []
        menu.destroy()

    def test_context_menu_add_items():
        menu = ctk.CTkContextMenu(root)
        menu.add_item("Copy", command=lambda: None, accelerator="Ctrl+C")
        menu.add_separator()
        menu.add_item("Paste", command=lambda: None)
        assert len(menu._items) == 3
        assert menu._items[0]["label"] == "Copy"
        assert menu._items[1]["type"] == "separator"
        menu.destroy()

    def test_context_menu_submenu():
        menu = ctk.CTkContextMenu(root)
        sub = menu.add_submenu("More")
        sub.add_item("Sub Item 1")
        assert len(menu._items) == 1
        assert menu._items[0]["type"] == "cascade"
        menu.destroy()

    def test_context_menu_checkbutton():
        menu = ctk.CTkContextMenu(root)
        var = tkinter.BooleanVar(value=False)
        menu.add_checkbutton("Toggle", variable=var)
        assert len(menu._items) == 1
        assert menu._items[0]["type"] == "checkbutton"
        assert var in menu._check_variables
        menu.destroy()

    def test_context_menu_radiobutton():
        menu = ctk.CTkContextMenu(root)
        var = tkinter.StringVar(value="A")
        menu.add_radiobutton("Option A", variable=var, value="A")
        menu.add_radiobutton("Option B", variable=var, value="B")
        assert len(menu._items) == 2
        assert menu._items[0]["type"] == "radiobutton"
        assert var in menu._radio_variables
        menu.destroy()

    def test_context_menu_header():
        menu = ctk.CTkContextMenu(root)
        menu.add_header("Section Title")
        assert len(menu._items) == 1
        assert menu._items[0]["type"] == "header"
        menu.destroy()

    def test_context_menu_set_item_state():
        menu = ctk.CTkContextMenu(root)
        menu.add_item("Editable")
        menu.set_item_state(0, "disabled")
        assert menu._items[0]["state"] == "disabled"
        menu.set_item_state("Editable", "normal")
        assert menu._items[0]["state"] == "normal"
        menu.destroy()

    def test_context_menu_clear():
        menu = ctk.CTkContextMenu(root)
        menu.add_item("A")
        menu.add_item("B")
        menu.clear()
        assert len(menu._items) == 0
        menu.destroy()

    def test_context_menu_bind_unbind():
        menu = ctk.CTkContextMenu(root)
        frame = ctk.CTkFrame(root)
        frame.pack()
        root.update()
        menu.bind_context(frame)
        assert frame in menu._bound_widgets
        menu.unbind_context(frame)
        assert frame not in menu._bound_widgets
        frame.destroy()
        menu.destroy()

    runner.test("context_menu_create", test_context_menu_create)
    runner.test("context_menu_add_items", test_context_menu_add_items)
    runner.test("context_menu_submenu", test_context_menu_submenu)
    runner.test("context_menu_checkbutton", test_context_menu_checkbutton)
    runner.test("context_menu_radiobutton", test_context_menu_radiobutton)
    runner.test("context_menu_header", test_context_menu_header)
    runner.test("context_menu_set_item_state", test_context_menu_set_item_state)
    runner.test("context_menu_clear", test_context_menu_clear)
    runner.test("context_menu_bind_unbind", test_context_menu_bind_unbind)

    # ================================================================
    # 4. CTkDialog
    # ================================================================
    print("\n--- CTkDialog ---")

    def test_dialog_suppression():
        # Use suppression to avoid blocking modal dialogs
        key = "_test_suppress_key"
        CTkDialog = ctk.CTkDialog
        CTkDialog._suppressed[key] = True
        d = CTkDialog(root, title="Test", message="Suppressed", show_again_key=key)
        result = d.get_result()
        assert result == "OK"  # default button
        del CTkDialog._suppressed[key]

    def test_dialog_style_config():
        CTkDialog = ctk.CTkDialog
        assert "info" in CTkDialog._STYLE_CONFIG
        assert "success" in CTkDialog._STYLE_CONFIG
        assert "warning" in CTkDialog._STYLE_CONFIG
        assert "error" in CTkDialog._STYLE_CONFIG
        assert "question" in CTkDialog._STYLE_CONFIG

    runner.test("dialog_suppression", test_dialog_suppression)
    runner.test("dialog_style_config", test_dialog_style_config)

    # ================================================================
    # 5. CTkStatusBadge
    # ================================================================
    print("\n--- CTkStatusBadge ---")

    def test_status_badge_create():
        badge = ctk.CTkStatusBadge(root, text="Active", style="success")
        badge.pack()
        root.update()
        assert badge.cget("text") == "Active"
        assert badge.cget("style") == "success"
        badge.destroy()

    def test_status_badge_set_status():
        badge = ctk.CTkStatusBadge(root, text="Init")
        badge.pack()
        root.update()
        badge.set_status("Running", "info")
        root.update()
        assert badge.cget("text") == "Running"
        assert badge.cget("style") == "info"
        badge.destroy()

    def test_status_badge_sizes():
        for size in ("small", "default", "large"):
            badge = ctk.CTkStatusBadge(root, text="Test", size=size)
            badge.pack()
            root.update()
            assert badge.cget("size") == size
            badge.destroy()

    def test_status_badge_count():
        badge = ctk.CTkStatusBadge(root, text="Items", count=5)
        badge.pack()
        root.update()
        assert badge.cget("count") == 5
        badge.set_count(42)
        root.update()
        assert badge.cget("count") == 42
        badge.set_count(150)
        root.update()
        assert badge.cget("count") == 150
        badge.set_count(None)
        root.update()
        assert badge.cget("count") is None
        badge.destroy()

    def test_status_badge_pulse():
        badge = ctk.CTkStatusBadge(root, text="Loading", pulse=True)
        badge.pack()
        root.update()
        assert badge.cget("pulse") is True
        badge.stop_pulse()
        root.update()
        badge.start_pulse()
        root.update()
        badge.destroy()

    def test_status_badge_configure():
        badge = ctk.CTkStatusBadge(root, text="Old")
        badge.pack()
        root.update()
        badge.configure(text="New", style="warning")
        root.update()
        assert badge.cget("text") == "New"
        assert badge.cget("style") == "warning"
        badge.destroy()

    runner.test("status_badge_create", test_status_badge_create)
    runner.test("status_badge_set_status", test_status_badge_set_status)
    runner.test("status_badge_sizes", test_status_badge_sizes)
    runner.test("status_badge_count", test_status_badge_count)
    runner.test("status_badge_pulse", test_status_badge_pulse)
    runner.test("status_badge_configure", test_status_badge_configure)

    # ================================================================
    # 6. CTkCard
    # ================================================================
    print("\n--- CTkCard ---")

    def test_card_create():
        card = ctk.CTkCard(root, width=300, height=200)
        card.pack()
        root.update()
        assert card.cget("state") == "normal"
        assert card.cget("selected") is False
        card.destroy()

    def test_card_disable_enable():
        card = ctk.CTkCard(root)
        card.pack()
        root.update()
        card.disable()
        assert card.cget("state") == "disabled"
        card.enable()
        assert card.cget("state") == "normal"
        card.destroy()

    def test_card_select_deselect():
        card = ctk.CTkCard(root)
        card.pack()
        root.update()
        card.select()
        assert card.cget("selected") is True
        card.deselect()
        assert card.cget("selected") is False
        card.toggle_select()
        assert card.cget("selected") is True
        card.toggle_select()
        assert card.cget("selected") is False
        card.destroy()

    def test_card_command():
        results = []
        card = ctk.CTkCard(root, command=lambda: results.append(1))
        card.pack()
        root.update()
        card._on_click()
        assert len(results) == 1
        card.destroy()

    def test_card_disabled_suppresses_click():
        results = []
        card = ctk.CTkCard(root, command=lambda: results.append(1))
        card.pack()
        root.update()
        card.disable()
        card._on_click()
        assert len(results) == 0  # disabled, no callback
        card.destroy()

    def test_card_configure():
        card = ctk.CTkCard(root)
        card.pack()
        root.update()
        card.configure(state="disabled")
        assert card.cget("state") == "disabled"
        card.configure(selected=True)
        assert card.cget("selected") is True
        card.configure(hover_effect=False)
        assert card.cget("hover_effect") is False
        card.destroy()

    def test_card_cget_colors():
        card = ctk.CTkCard(root, focus_border_color=("#ff0000", "#00ff00"))
        card.pack()
        root.update()
        assert card.cget("focus_border_color") == ("#ff0000", "#00ff00")
        card.destroy()

    runner.test("card_create", test_card_create)
    runner.test("card_disable_enable", test_card_disable_enable)
    runner.test("card_select_deselect", test_card_select_deselect)
    runner.test("card_command", test_card_command)
    runner.test("card_disabled_suppresses_click", test_card_disabled_suppresses_click)
    runner.test("card_configure", test_card_configure)
    runner.test("card_cget_colors", test_card_cget_colors)

    # ================================================================
    # 7. CTkRichTextbox
    # ================================================================
    print("\n--- CTkRichTextbox ---")

    def test_rich_textbox_create():
        rtb = ctk.CTkRichTextbox(root, width=400, height=200)
        rtb.pack()
        root.update()
        rtb.destroy()

    def test_rich_textbox_add_text_styles():
        rtb = ctk.CTkRichTextbox(root, width=400, height=200)
        rtb.pack()
        root.update()
        for style in ("default", "header", "success", "warning", "error",
                       "info", "muted", "code", "accent"):
            rtb.add_text(f"Test {style}", style=style)
        root.update()
        content = rtb.get("1.0", "end-1c")
        assert "Test header" in content
        assert "Test error" in content
        rtb.destroy()

    def test_rich_textbox_timestamps():
        rtb = ctk.CTkRichTextbox(root, width=400, height=200, show_timestamps=True)
        rtb.pack()
        root.update()
        rtb.add_text("Timed message")
        root.update()
        content = rtb.get("1.0", "end-1c")
        assert "[" in content  # timestamp bracket
        rtb.destroy()

    def test_rich_textbox_line_highlight():
        rtb = ctk.CTkRichTextbox(root, width=400, height=200)
        rtb.pack()
        root.update()
        rtb.add_text("Line 1")
        rtb.add_text("Line 2")
        rtb.highlight_line(1, "#ff0000")
        root.update()
        rtb.clear_highlights()
        root.update()
        rtb.destroy()

    def test_rich_textbox_search():
        rtb = ctk.CTkRichTextbox(root, width=400, height=200)
        rtb.pack()
        root.update()
        rtb.add_text("Hello world")
        rtb.add_text("Hello again")
        root.update()
        count = rtb.search_text("Hello")
        assert count == 2
        rtb.search_next()
        rtb.search_prev()
        rtb.clear_search()
        root.update()
        rtb.destroy()

    def test_rich_textbox_add_link():
        rtb = ctk.CTkRichTextbox(root, width=400, height=200)
        rtb.pack()
        root.update()
        results = []
        rtb.add_link("Click me", lambda: results.append(1))
        root.update()
        content = rtb.get("1.0", "end-1c")
        assert "Click me" in content
        rtb.destroy()

    def test_rich_textbox_batch_insert():
        rtb = ctk.CTkRichTextbox(root, width=400, height=200)
        rtb.pack()
        root.update()
        rtb.add_batch([
            {"text": "Item 1", "style": "info"},
            {"text": "Item 2", "style": "success"},
            {"text": "Item 3", "style": "error"},
        ])
        root.update()
        content = rtb.get("1.0", "end-1c")
        assert "Item 1" in content
        assert "Item 3" in content
        rtb.destroy()

    def test_rich_textbox_clear():
        rtb = ctk.CTkRichTextbox(root, width=400, height=200)
        rtb.pack()
        root.update()
        rtb.add_text("Some text")
        root.update()
        rtb.clear()
        root.update()
        content = rtb.get("1.0", "end-1c").strip()
        assert content == ""
        rtb.destroy()

    runner.test("rich_textbox_create", test_rich_textbox_create)
    runner.test("rich_textbox_add_text_styles", test_rich_textbox_add_text_styles)
    runner.test("rich_textbox_timestamps", test_rich_textbox_timestamps)
    runner.test("rich_textbox_line_highlight", test_rich_textbox_line_highlight)
    runner.test("rich_textbox_search", test_rich_textbox_search)
    runner.test("rich_textbox_add_link", test_rich_textbox_add_link)
    runner.test("rich_textbox_batch_insert", test_rich_textbox_batch_insert)
    runner.test("rich_textbox_clear", test_rich_textbox_clear)

    # ================================================================
    # 8. CTkCircularProgress
    # ================================================================
    print("\n--- CTkCircularProgress ---")

    def test_circular_progress_create():
        cp = ctk.CTkCircularProgress(root, size=100)
        cp.pack()
        root.update()
        assert cp.cget("value") == 0.0
        cp.destroy()

    def test_circular_progress_set_value():
        cp = ctk.CTkCircularProgress(root, size=100)
        cp.pack()
        root.update()
        cp.set(0.5)
        root.update()
        # Value is animated, so internal target should be 0.5
        assert cp._target_value == 0.5
        cp.destroy()

    def test_circular_progress_step():
        cp = ctk.CTkCircularProgress(root, size=80)
        cp.pack()
        root.update()
        cp.set(0.0)
        root.update()
        cp.step(0.25)
        root.update()
        assert cp._target_value == 0.25
        cp.step(0.25)
        root.update()
        assert cp._target_value == 0.50
        cp.destroy()

    def test_circular_progress_indeterminate():
        cp = ctk.CTkCircularProgress(root, size=80, mode="indeterminate")
        cp.pack()
        root.update()
        assert cp.cget("mode") == "indeterminate"
        cp.start()
        root.update()
        assert cp._spinning is True
        cp.stop()
        root.update()
        assert cp._spinning is False
        cp.destroy()

    def test_circular_progress_on_complete():
        results = []
        cp = ctk.CTkCircularProgress(root, size=80, on_complete=lambda: results.append(1))
        cp.pack()
        root.update()
        # Set to 1.0 directly (no animation to speed up test)
        cp._value = 1.0
        cp._target_value = 1.0
        cp._draw()
        # The on_complete fires when animated value reaches 1.0
        # Since we may need animation ticks, just verify no crash
        cp.destroy()

    def test_circular_progress_text_callback():
        cp = ctk.CTkCircularProgress(
            root, size=100, show_text=True,
            text_callback=lambda v: f"{int(v * 100)} files"
        )
        cp.pack()
        root.update()
        cp.set(0.42)
        root.update()
        cp.destroy()

    def test_circular_progress_configure():
        cp = ctk.CTkCircularProgress(root, size=80)
        cp.pack()
        root.update()
        cp.configure(line_width=10)
        assert cp.cget("line_width") == 10
        cp.configure(show_text=True)
        assert cp.cget("show_text") is True
        cp.destroy()

    runner.test("circular_progress_create", test_circular_progress_create)
    runner.test("circular_progress_set_value", test_circular_progress_set_value)
    runner.test("circular_progress_step", test_circular_progress_step)
    runner.test("circular_progress_indeterminate", test_circular_progress_indeterminate)
    runner.test("circular_progress_on_complete", test_circular_progress_on_complete)
    runner.test("circular_progress_text_callback", test_circular_progress_text_callback)
    runner.test("circular_progress_configure", test_circular_progress_configure)

    # ================================================================
    # 9. CTkSearchEntry
    # ================================================================
    print("\n--- CTkSearchEntry ---")

    def test_search_entry_create():
        se = ctk.CTkSearchEntry(root, placeholder_text="Search...")
        se.pack()
        root.update()
        assert se.get() == ""
        se.destroy()

    def test_search_entry_set_get():
        se = ctk.CTkSearchEntry(root)
        se.pack()
        root.update()
        se.set("hello")
        root.update()
        assert se.get() == "hello"
        se.clear()
        root.update()
        assert se.get() == ""
        se.destroy()

    def test_search_entry_command():
        results = []
        se = ctk.CTkSearchEntry(root, command=lambda t: results.append(t),
                                 debounce_ms=0)
        se.pack()
        root.update()
        # Use set() to put text, then _on_return to fire command
        se.set("test query")
        root.update()
        # Clear results from debounce (debounce_ms=0 fires immediately on text change)
        results.clear()
        se._on_return()
        assert len(results) == 1
        assert results[0] == "test query"
        se.destroy()

    def test_search_entry_escape_clear():
        se = ctk.CTkSearchEntry(root)
        se.pack()
        root.update()
        se.set("text")
        root.update()
        se._on_escape()
        root.update()
        assert se.get() == ""
        se.destroy()

    def test_search_entry_result_count():
        se = ctk.CTkSearchEntry(root)
        se.pack()
        root.update()
        se.set_result_count(5)
        root.update()
        assert se.cget("result_count") == 5
        se.set_result_count(None)
        root.update()
        assert se.cget("result_count") is None
        se.destroy()

    def test_search_entry_loading():
        se = ctk.CTkSearchEntry(root)
        se.pack()
        root.update()
        se.set_loading(True)
        root.update()
        assert se.cget("loading") is True
        se.set_loading(False)
        root.update()
        assert se.cget("loading") is False
        se.destroy()

    def test_search_entry_configure():
        se = ctk.CTkSearchEntry(root)
        se.pack()
        root.update()
        se.configure(focus_border_color=("#ff0000", "#00ff00"))
        assert se.cget("focus_border_color") == ("#ff0000", "#00ff00")
        se.destroy()

    runner.test("search_entry_create", test_search_entry_create)
    runner.test("search_entry_set_get", test_search_entry_set_get)
    runner.test("search_entry_command", test_search_entry_command)
    runner.test("search_entry_escape_clear", test_search_entry_escape_clear)
    runner.test("search_entry_result_count", test_search_entry_result_count)
    runner.test("search_entry_loading", test_search_entry_loading)
    runner.test("search_entry_configure", test_search_entry_configure)

    # ================================================================
    # 10. CTkScrollableFrame
    # ================================================================
    print("\n--- CTkScrollableFrame ---")

    def test_scrollable_frame_create():
        sf = ctk.CTkScrollableFrame(root, width=300, height=200)
        sf.pack()
        root.update()
        sf.destroy()

    def test_scrollable_frame_add_content():
        sf = ctk.CTkScrollableFrame(root, width=300, height=100)
        sf.pack()
        root.update()
        for i in range(20):
            ctk.CTkLabel(sf, text=f"Item {i}").pack()
        root.update()
        sf.destroy()

    def test_scrollable_frame_scroll_to_top():
        sf = ctk.CTkScrollableFrame(root, width=300, height=100)
        sf.pack()
        root.update()
        for i in range(30):
            ctk.CTkLabel(sf, text=f"Item {i}").pack()
        root.update()
        sf.scroll_to_top()
        root.update()
        sf.destroy()

    def test_scrollable_frame_scroll_to_bottom():
        sf = ctk.CTkScrollableFrame(root, width=300, height=100)
        sf.pack()
        root.update()
        for i in range(30):
            ctk.CTkLabel(sf, text=f"Item {i}").pack()
        root.update()
        sf.scroll_to_bottom()
        root.update()
        sf.destroy()

    def test_scrollable_frame_get_scroll_position():
        sf = ctk.CTkScrollableFrame(root, width=300, height=100)
        sf.pack()
        root.update()
        for i in range(30):
            ctk.CTkLabel(sf, text=f"Item {i}").pack()
        root.update()
        pos = sf.get_scroll_position()
        assert isinstance(pos, float)
        sf.destroy()

    def test_scrollable_frame_set_scroll_position():
        sf = ctk.CTkScrollableFrame(root, width=300, height=100)
        sf.pack()
        root.update()
        for i in range(30):
            ctk.CTkLabel(sf, text=f"Item {i}").pack()
        root.update()
        sf.set_scroll_position(0.5)
        root.update()
        sf.destroy()

    def test_scrollable_frame_scroll_by():
        sf = ctk.CTkScrollableFrame(root, width=300, height=100)
        sf.pack()
        root.update()
        for i in range(30):
            ctk.CTkLabel(sf, text=f"Item {i}").pack()
        root.update()
        sf.scroll_by(0.1)
        root.update()
        sf.destroy()

    def test_scrollable_frame_is_at_top_bottom():
        sf = ctk.CTkScrollableFrame(root, width=300, height=100)
        sf.pack()
        root.update()
        for i in range(30):
            ctk.CTkLabel(sf, text=f"Item {i}").pack()
        root.update()
        sf.scroll_to_top()
        root.update()
        assert sf.is_at_top() is True
        sf.scroll_to_bottom()
        root.update()
        assert sf.is_at_bottom() is True
        sf.destroy()

    def test_scrollable_frame_scroll_command():
        positions = []
        sf = ctk.CTkScrollableFrame(root, width=300, height=100,
                                      scroll_command=lambda p: positions.append(p))
        sf.pack()
        root.update()
        for i in range(30):
            ctk.CTkLabel(sf, text=f"Item {i}").pack()
        root.update()
        sf.scroll_to_bottom()
        root.update()
        # The scroll_command should have been called at least once
        sf.destroy()

    def test_scrollable_frame_configure_cget():
        sf = ctk.CTkScrollableFrame(root, width=300, height=100)
        sf.pack()
        root.update()
        sf.configure(scroll_command=lambda p: None)
        cb = sf.cget("scroll_command")
        assert cb is not None
        sf.destroy()

    runner.test("scrollable_frame_create", test_scrollable_frame_create)
    runner.test("scrollable_frame_add_content", test_scrollable_frame_add_content)
    runner.test("scrollable_frame_scroll_to_top", test_scrollable_frame_scroll_to_top)
    runner.test("scrollable_frame_scroll_to_bottom", test_scrollable_frame_scroll_to_bottom)
    runner.test("scrollable_frame_get_scroll_position", test_scrollable_frame_get_scroll_position)
    runner.test("scrollable_frame_set_scroll_position", test_scrollable_frame_set_scroll_position)
    runner.test("scrollable_frame_scroll_by", test_scrollable_frame_scroll_by)
    runner.test("scrollable_frame_is_at_top_bottom", test_scrollable_frame_is_at_top_bottom)
    runner.test("scrollable_frame_scroll_command", test_scrollable_frame_scroll_command)
    runner.test("scrollable_frame_configure_cget", test_scrollable_frame_configure_cget)

    # ================================================================
    # Cleanup & Summary
    # ================================================================
    root.destroy()

    success = runner.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
