"""
Interactive demo for all CustomTkinter widgets, utilities, and UI enhancements.
"""

import sys
import os
import tkinter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import customtkinter as ctk


class WidgetDemo(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CustomTkinter — Full Widget Demo")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")

        # Scrollable main area
        self._main = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._main.pack(fill="both", expand=True, padx=16, pady=16)

        # ── Original widgets ──
        self._build_rating_section()
        self._build_avatar_section()
        self._build_stepper_section()
        self._build_accordion_section()
        self._build_tooltip_section()
        self._build_status_badge_section()
        self._build_card_section()
        self._build_search_entry_section()
        self._build_circular_progress_section()
        self._build_collapsible_frame_section()
        self._build_rich_textbox_section()
        self._build_context_menu_section()
        self._build_dialog_section()
        self._build_toggle_switch_section()
        self._build_breadcrumb_section()
        self._build_chip_section()
        self._build_number_entry_section()
        self._build_range_slider_section()
        self._build_data_table_section()
        self._build_tree_view_section()
        self._build_notification_banner_section()
        self._build_date_time_section()

        # ── Batch 2 widgets ──
        self._build_spinbox_section()
        self._build_tag_input_section()
        self._build_gauge_section()
        self._build_paginator_section()
        self._build_calendar_view_section()

        # ── Batch 1 widgets (layouts) ──
        self._build_color_picker_section()
        self._build_navigation_rail_section()
        self._build_split_view_section()
        self._build_loading_overlay_section()
        self._build_skeleton_section()

        # ── UI Enhancement widgets ──
        self._build_shadow_frame_section()
        self._build_gradient_frame_section()
        self._build_icon_section()
        self._build_animated_frame_section()
        self._build_frosted_frame_section()

        # ── Utilities ──
        self._build_focus_ring_section()
        self._build_ripple_section()
        self._build_font_scale_section()
        self._build_animation_section()
        self._build_color_utils_section()

    # --- helpers ---
    def _section_label(self, text):
        lbl = ctk.CTkLabel(self._main, text=text, font=ctk.CTkFont(size=18, weight="bold"))
        lbl.pack(anchor="w", pady=(20, 6))
        sep = ctk.CTkFrame(self._main, height=2, fg_color=("#c0c0c0", "#404040"))
        sep.pack(fill="x", pady=(0, 10))

    # ================================================================
    # CTkRating
    # ================================================================
    def _build_rating_section(self):
        self._section_label("CTkRating")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        rating_lbl = ctk.CTkLabel(row, text="Rating: 0.0")
        rating_lbl.pack(side="right", padx=8)

        def on_rate(val):
            rating_lbl.configure(text=f"Rating: {val}")

        r1 = ctk.CTkRating(row, max_stars=5, command=on_rate)
        r1.pack(side="left", padx=8)

        ctk.CTkLabel(row, text="Half-star:").pack(side="left", padx=(16, 4))
        r2 = ctk.CTkRating(row, max_stars=5, allow_half=True, initial_value=3.5,
                            star_color=("#EC4899", "#F472B6"))
        r2.pack(side="left", padx=4)

        ctk.CTkLabel(row, text="Read-only:").pack(side="left", padx=(16, 4))
        r3 = ctk.CTkRating(row, max_stars=5, initial_value=4, state="readonly",
                            star_color=("#22C55E", "#4ADE80"))
        r3.pack(side="left", padx=4)

    # ================================================================
    # CTkAvatar
    # ================================================================
    def _build_avatar_section(self):
        self._section_label("CTkAvatar")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        for name, status in [("John Doe", "online"), ("Alice B", "away"),
                              ("Bob C", "busy"), ("Eve", "offline"), ("?", None)]:
            frame = ctk.CTkFrame(row, fg_color="transparent")
            frame.pack(side="left", padx=12)
            av = ctk.CTkAvatar(frame, text=name, size="large", status=status)
            av.pack()
            ctk.CTkLabel(frame, text=name, font=ctk.CTkFont(size=11)).pack(pady=(4, 0))
            if status:
                ctk.CTkLabel(frame, text=status, font=ctk.CTkFont(size=10),
                             text_color=("gray50", "gray60")).pack()

        ctk.CTkLabel(row, text="  Sizes:").pack(side="left", padx=(24, 4))
        for size in ("small", "medium", "large", "xlarge"):
            ctk.CTkAvatar(row, text="AB", size=size).pack(side="left", padx=4)

    # ================================================================
    # CTkStepper
    # ================================================================
    def _build_stepper_section(self):
        self._section_label("CTkStepper")

        stepper = ctk.CTkStepper(self._main,
                                  steps=["Account", "Profile", "Settings", "Review", "Complete"],
                                  width=700, height=80)
        stepper.pack(fill="x", pady=4)

        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x", pady=4)

        step_lbl = ctk.CTkLabel(row, text="Step: 1/5")
        step_lbl.pack(side="right", padx=8)

        def update_label():
            s = stepper.get_step()
            step_lbl.configure(text=f"Step: {s + 1}/5")

        def go_prev():
            stepper.previous()
            update_label()
        def go_next():
            stepper.next()
            update_label()
        def do_reset():
            stepper.reset()
            update_label()
        def do_complete():
            stepper.complete()
            step_lbl.configure(text="All complete!")

        ctk.CTkButton(row, text="Previous", width=80, command=go_prev).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Next", width=80, command=go_next).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Reset", width=80, command=do_reset).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Complete All", width=100, command=do_complete).pack(side="left", padx=4)

    # ================================================================
    # CTkAccordion
    # ================================================================
    def _build_accordion_section(self):
        self._section_label("CTkAccordion")

        ctk.CTkLabel(self._main, text="Tab to focus headers, arrow keys to navigate between sections",
                      font=ctk.CTkFont(size=11), text_color=("gray50", "gray60")).pack(anchor="w")

        accordion = ctk.CTkAccordion(self._main, exclusive=True)
        accordion.pack(fill="x", pady=4)

        s1 = accordion.add_section("General Settings", collapsed=False)
        ctk.CTkSwitch(s1, text="Enable notifications").pack(padx=16, pady=4, anchor="w")
        ctk.CTkSwitch(s1, text="Auto-save").pack(padx=16, pady=4, anchor="w")
        ctk.CTkEntry(s1, placeholder_text="Username").pack(padx=16, pady=4, fill="x")

        s2 = accordion.add_section("Appearance")
        ctk.CTkLabel(s2, text="Font size:").pack(padx=16, pady=4, anchor="w")
        ctk.CTkSlider(s2, from_=8, to=24, number_of_steps=16).pack(padx=16, pady=4, fill="x")
        ctk.CTkOptionMenu(s2, values=["Light", "Dark", "System"]).pack(padx=16, pady=4)

        s3 = accordion.add_section("Advanced")
        ctk.CTkLabel(s3, text="Thread count:").pack(padx=16, pady=4, anchor="w")
        ctk.CTkSlider(s3, from_=1, to=16, number_of_steps=15).pack(padx=16, pady=4, fill="x")
        ctk.CTkCheckBox(s3, text="Debug mode").pack(padx=16, pady=4, anchor="w")

    # ================================================================
    # CTkToolTip
    # ================================================================
    def _build_tooltip_section(self):
        self._section_label("CTkToolTip")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        btn1 = ctk.CTkButton(row, text="Hover me (basic)")
        btn1.pack(side="left", padx=4)
        ctk.CTkToolTip(btn1, message="Basic tooltip with fade-in animation")

        btn2 = ctk.CTkButton(row, text="Hover me (follow cursor)")
        btn2.pack(side="left", padx=4)
        ctk.CTkToolTip(btn2, message="This tooltip follows your cursor!", follow_cursor=True)

        btn3 = ctk.CTkButton(row, text="Hover me (custom colors)")
        btn3.pack(side="left", padx=4)
        ctk.CTkToolTip(btn3, message="Custom styled tooltip",
                        fg_color=("#2CC985", "#2CC985"), text_color=("#000000", "#000000"))

        btn4 = ctk.CTkButton(row, text="Disabled tooltip")
        btn4.pack(side="left", padx=4)
        tip = ctk.CTkToolTip(btn4, message="You won't see this", enabled=False)

        def toggle_tip():
            if tip._enabled:
                tip.disable()
                btn5.configure(text="Enable tooltip")
            else:
                tip.enable()
                btn5.configure(text="Disable tooltip")
        btn5 = ctk.CTkButton(row, text="Enable tooltip", width=120, command=toggle_tip)
        btn5.pack(side="left", padx=4)

    # ================================================================
    # CTkStatusBadge
    # ================================================================
    def _build_status_badge_section(self):
        self._section_label("CTkStatusBadge")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        for s in ("success", "warning", "error", "info", "muted"):
            ctk.CTkStatusBadge(row, text=s.capitalize(), style=s).pack(side="left", padx=4)

        row2 = ctk.CTkFrame(self._main, fg_color="transparent")
        row2.pack(fill="x", pady=(6, 0))

        for size in ("small", "default", "large"):
            ctk.CTkStatusBadge(row2, text=size, style="info", size=size).pack(side="left", padx=4)

        count_badge = ctk.CTkStatusBadge(row2, text="Notifications", style="error", count=7)
        count_badge.pack(side="left", padx=4)

        def inc_count():
            c = count_badge.cget("count") or 0
            count_badge.set_count(c + 1)
        ctk.CTkButton(row2, text="+1", width=40, command=inc_count).pack(side="left", padx=2)

        pulse_badge = ctk.CTkStatusBadge(row2, text="Loading", style="warning", pulse=True)
        pulse_badge.pack(side="left", padx=4)

        def toggle_pulse():
            if pulse_badge.cget("pulse"):
                pulse_badge.stop_pulse()
            else:
                pulse_badge.start_pulse()
        ctk.CTkButton(row2, text="Toggle Pulse", width=100, command=toggle_pulse).pack(side="left", padx=2)

    # ================================================================
    # CTkCard
    # ================================================================
    def _build_card_section(self):
        self._section_label("CTkCard")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        card1 = ctk.CTkCard(row, width=200, height=120, border_width=2,
                             command=lambda: card1_lbl.configure(text="Clicked!"))
        card1.pack(side="left", padx=8)
        ctk.CTkLabel(card1, text="Clickable Card", font=ctk.CTkFont(weight="bold")).pack(padx=12, pady=(12, 2))
        card1_lbl = ctk.CTkLabel(card1, text="Hover & click me")
        card1_lbl.pack(padx=12, pady=(2, 12))

        card2 = ctk.CTkCard(row, width=200, height=120, border_width=2,
                             command=lambda: card2.toggle_select())
        card2.pack(side="left", padx=8)
        ctk.CTkLabel(card2, text="Selectable Card", font=ctk.CTkFont(weight="bold")).pack(padx=12, pady=(12, 2))
        ctk.CTkLabel(card2, text="Click to toggle select").pack(padx=12, pady=(2, 12))

        card3 = ctk.CTkCard(row, width=200, height=120, border_width=2,
                             command=lambda: None)
        card3.pack(side="left", padx=8)
        card3.disable()
        ctk.CTkLabel(card3, text="Disabled Card", font=ctk.CTkFont(weight="bold")).pack(padx=12, pady=(12, 2))
        ctk.CTkLabel(card3, text="No interaction").pack(padx=12, pady=(2, 12))

        def toggle_card3():
            if card3.cget("state") == "disabled":
                card3.enable()
            else:
                card3.disable()
        ctk.CTkButton(row, text="Toggle Disable", width=120, command=toggle_card3).pack(side="left", padx=8)

    # ================================================================
    # CTkSearchEntry
    # ================================================================
    def _build_search_entry_section(self):
        self._section_label("CTkSearchEntry")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        result_label = ctk.CTkLabel(row, text="Type to search...")
        result_label.pack(side="right", padx=8)

        def on_search(text):
            if text:
                count = sum(text.lower().count(v) for v in "aeiou")
                se.set_result_count(count)
                result_label.configure(text=f"Found {count} vowels in \"{text}\"")
            else:
                se.set_result_count(None)
                result_label.configure(text="Type to search...")

        se = ctk.CTkSearchEntry(row, placeholder_text="Search (try typing, Esc to clear, Enter to submit)...",
                                 width=400, command=on_search, debounce_ms=300)
        se.pack(side="left", padx=4)

    # ================================================================
    # CTkCircularProgress
    # ================================================================
    def _build_circular_progress_section(self):
        self._section_label("CTkCircularProgress")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        cp = ctk.CTkCircularProgress(row, size=100, line_width=8, show_text=True)
        cp.pack(side="left", padx=16)
        cp.set(0.0)

        controls = ctk.CTkFrame(row, fg_color="transparent")
        controls.pack(side="left", padx=8)

        ctk.CTkButton(controls, text="+10%", width=70, command=lambda: cp.step(0.1)).pack(pady=2)
        ctk.CTkButton(controls, text="Reset", width=70, command=lambda: cp.set(0.0)).pack(pady=2)
        ctk.CTkButton(controls, text="100%", width=70, command=lambda: cp.set(1.0)).pack(pady=2)

        spinner = ctk.CTkCircularProgress(row, size=80, line_width=6, mode="indeterminate",
                                           progress_color=("#2CC985", "#2CC985"))
        spinner.pack(side="left", padx=24)
        spinner.start()

        def toggle_spinner():
            if spinner._spinning:
                spinner.stop()
                spin_btn.configure(text="Start Spinner")
            else:
                spinner.start()
                spin_btn.configure(text="Stop Spinner")
        spin_btn = ctk.CTkButton(row, text="Stop Spinner", width=110, command=toggle_spinner)
        spin_btn.pack(side="left", padx=4)

        cp2 = ctk.CTkCircularProgress(row, size=90, line_width=6, show_text=True,
                                        text_callback=lambda v: f"{int(v * 50)}/50")
        cp2.pack(side="left", padx=16)
        cp2.set(0.64)

    # ================================================================
    # CTkCollapsibleFrame
    # ================================================================
    def _build_collapsible_frame_section(self):
        self._section_label("CTkCollapsibleFrame")

        cf1 = ctk.CTkCollapsibleFrame(self._main, title="Settings (click to expand/collapse)")
        cf1.pack(fill="x", pady=4)
        ctk.CTkSwitch(cf1.content, text="Enable notifications").pack(padx=16, pady=4, anchor="w")
        ctk.CTkSwitch(cf1.content, text="Dark mode").pack(padx=16, pady=4, anchor="w")
        ctk.CTkSwitch(cf1.content, text="Auto-update").pack(padx=16, pady=4, anchor="w")

        cf2 = ctk.CTkCollapsibleFrame(self._main, title="Advanced Options", collapsed=True)
        cf2.pack(fill="x", pady=4)
        ctk.CTkLabel(cf2.content, text="Thread count:").pack(padx=16, pady=4, anchor="w")
        ctk.CTkSlider(cf2.content, from_=1, to=16, number_of_steps=15).pack(padx=16, pady=4, fill="x")
        ctk.CTkLabel(cf2.content, text="Buffer size:").pack(padx=16, pady=4, anchor="w")
        ctk.CTkSlider(cf2.content, from_=1, to=64, number_of_steps=63).pack(padx=16, pady=4, fill="x")

        cf3 = ctk.CTkCollapsibleFrame(self._main, title="Locked Section (cannot toggle)", lock=True)
        cf3.pack(fill="x", pady=4)
        ctk.CTkLabel(cf3.content, text="This section is locked open.").pack(padx=16, pady=8, anchor="w")

    # ================================================================
    # CTkRichTextbox
    # ================================================================
    def _build_rich_textbox_section(self):
        self._section_label("CTkRichTextbox")

        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        rtb = ctk.CTkRichTextbox(row, width=500, height=200, show_timestamps=True)
        rtb.pack(side="left", padx=(0, 8))

        rtb.add_text("Application started", style="header")
        rtb.add_text("Loading configuration...", style="info")
        rtb.add_text("Configuration loaded successfully", style="success")
        rtb.add_text("3 deprecated settings found", style="warning")
        rtb.add_text("Failed to connect to backup server", style="error")
        rtb.add_text("Using default fallback configuration", style="muted")
        rtb.add_text("Version: 2.4.4", style="code")
        rtb.add_link("Open documentation", "https://example.com", style="info")
        rtb.add_text("Ready.", style="accent")

        controls = ctk.CTkFrame(row, fg_color="transparent")
        controls.pack(side="left", fill="y", padx=4)

        ctk.CTkButton(controls, text="Add Info", width=100,
                       command=lambda: rtb.add_text("New info message added", style="info")).pack(pady=2)
        ctk.CTkButton(controls, text="Add Error", width=100,
                       command=lambda: rtb.add_text("Something went wrong!", style="error")).pack(pady=2)
        ctk.CTkButton(controls, text="Add Success", width=100,
                       command=lambda: rtb.add_text("Operation completed", style="success")).pack(pady=2)

        search_lbl = ctk.CTkLabel(controls, text="")
        search_lbl.pack(pady=2)

        def do_search():
            count = rtb.search_text("config", nocase=True)
            search_lbl.configure(text=f"{count} matches")
        ctk.CTkButton(controls, text="Search 'config'", width=100, command=do_search).pack(pady=2)
        ctk.CTkButton(controls, text="Next Match", width=100, command=lambda: rtb.search_next()).pack(pady=2)

        def clear_search():
            rtb.clear_search()
            search_lbl.configure(text="")
        ctk.CTkButton(controls, text="Clear Search", width=100, command=clear_search).pack(pady=2)
        ctk.CTkButton(controls, text="Clear All", width=100, fg_color=("#E04545", "#E04545"),
                       command=lambda: rtb.clear()).pack(pady=2)

    # ================================================================
    # CTkContextMenu
    # ================================================================
    def _build_context_menu_section(self):
        self._section_label("CTkContextMenu")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        target = ctk.CTkFrame(row, width=400, height=80, border_width=2,
                               border_color=("#c0c0c0", "#555555"))
        target.pack(side="left", padx=4)
        target.pack_propagate(False)
        ctk.CTkLabel(target, text="Right-click here for context menu").pack(expand=True)

        menu = ctk.CTkContextMenu(target)
        menu.add_header("Edit")
        menu.add_item("Cut", accelerator="Ctrl+X")
        menu.add_item("Copy", accelerator="Ctrl+C")
        menu.add_item("Paste", accelerator="Ctrl+V")
        menu.add_separator()
        menu.add_header("Options")

        bold_var = tkinter.BooleanVar(value=False)
        menu.add_checkbutton("Bold", variable=bold_var)
        italic_var = tkinter.BooleanVar(value=False)
        menu.add_checkbutton("Italic", variable=italic_var)

        menu.add_separator()
        align_var = tkinter.StringVar(value="Left")
        menu.add_radiobutton("Align Left", variable=align_var, value="Left")
        menu.add_radiobutton("Align Center", variable=align_var, value="Center")
        menu.add_radiobutton("Align Right", variable=align_var, value="Right")

        menu.add_separator()
        sub = menu.add_submenu("More options")
        sub.add_item("Option A")
        sub.add_item("Option B")
        menu.bind_context(target)

    # ================================================================
    # CTkDialog
    # ================================================================
    def _build_dialog_section(self):
        self._section_label("CTkDialog")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        result_lbl = ctk.CTkLabel(row, text="")
        result_lbl.pack(side="right", padx=12)

        ctk.CTkButton(row, text="Info", width=80,
                       command=lambda: ctk.CTkDialog.show_info(self, title="Info",
                           message="This is an informational dialog.",
                           detail="Additional detail text goes here.")).pack(side="left", padx=3)
        ctk.CTkButton(row, text="Success", width=80,
                       command=lambda: ctk.CTkDialog.show_success(self, title="Success",
                           message="Operation completed successfully!")).pack(side="left", padx=3)
        ctk.CTkButton(row, text="Warning", width=80,
                       command=lambda: ctk.CTkDialog.show_warning(self, title="Warning",
                           message="This action may have consequences.",
                           detail="Please review before proceeding.")).pack(side="left", padx=3)
        ctk.CTkButton(row, text="Error", width=80,
                       command=lambda: ctk.CTkDialog.show_error(self, title="Error",
                           message="Something went wrong.",
                           detail="Error code: 0xDEADBEEF")).pack(side="left", padx=3)

        def show_confirm():
            result = ctk.CTkDialog.ask_yes_no(self, title="Confirm", message="Are you sure you want to proceed?")
            result_lbl.configure(text=f"Result: {'Yes' if result else 'No'}")
        ctk.CTkButton(row, text="Confirm", width=80, command=show_confirm).pack(side="left", padx=3)

        def show_input():
            result = ctk.CTkDialog.ask_input(self, title="Input", message="Enter your name:",
                                              placeholder="Type here...", default_value="")
            result_lbl.configure(text=f"Input: {result!r}")
        ctk.CTkButton(row, text="Input", width=80, command=show_input).pack(side="left", padx=3)

    # ================================================================
    # CTkToggleSwitch
    # ================================================================
    def _build_toggle_switch_section(self):
        self._section_label("CTkToggleSwitch")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        state_lbl = ctk.CTkLabel(row, text="Off")
        state_lbl.pack(side="right", padx=8)

        sw1 = ctk.CTkToggleSwitch(row, text="Enable feature", size="medium",
                                    command=lambda val: state_lbl.configure(text="On" if val else "Off"))
        sw1.pack(side="left", padx=8)

        ctk.CTkLabel(row, text="Sizes:").pack(side="left", padx=(16, 4))
        for sz in ("small", "medium", "large"):
            ctk.CTkToggleSwitch(row, size=sz).pack(side="left", padx=4)

        ctk.CTkLabel(row, text="Labels:").pack(side="left", padx=(16, 4))
        ctk.CTkToggleSwitch(row, size="large", on_label="ON", off_label="OFF",
                             on_color=("#22C55E", "#16A34A")).pack(side="left", padx=4)

    # ================================================================
    # CTkBreadcrumb
    # ================================================================
    def _build_breadcrumb_section(self):
        self._section_label("CTkBreadcrumb")

        bc_lbl = ctk.CTkLabel(self._main, text="Click a segment above")
        bc = ctk.CTkBreadcrumb(self._main,
                                items=["Home", "Products", "Electronics", "Phones"],
                                command=lambda idx, text: bc_lbl.configure(
                                    text=f"Clicked: {text} (index {idx})"))
        bc.pack(fill="x", pady=4)

        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x", pady=4)

        bc_lbl.pack(in_=row, side="right", padx=8)
        ctk.CTkButton(row, text="Push", width=60, command=lambda: bc.push("Accessories")).pack(side="left", padx=4)

        def pop_safe():
            try:
                bc.pop()
            except IndexError:
                pass
        ctk.CTkButton(row, text="Pop", width=60, command=pop_safe).pack(side="left", padx=4)

    # ================================================================
    # CTkChip
    # ================================================================
    def _build_chip_section(self):
        self._section_label("CTkChip")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        for style in ("default", "primary", "success", "warning", "error"):
            ctk.CTkChip(row, text=style.capitalize(), style=style).pack(side="left", padx=4)

        row2 = ctk.CTkFrame(self._main, fg_color="transparent")
        row2.pack(fill="x", pady=(6, 0))

        ctk.CTkLabel(row2, text="Closeable:").pack(side="left", padx=(0, 4))
        chip_frame = ctk.CTkFrame(row2, fg_color="transparent")
        chip_frame.pack(side="left")
        for tag in ("Python", "JavaScript", "Rust"):
            c = ctk.CTkChip(chip_frame, text=tag, style="primary", closeable=True)
            c.configure(close_command=lambda ch=c: ch.destroy())
            c.pack(side="left", padx=2)

        ctk.CTkLabel(row2, text="Selectable:").pack(side="left", padx=(16, 4))
        sel_chip = ctk.CTkChip(row2, text="Toggle me", style="success")
        sel_chip.pack(side="left", padx=4)
        sel_chip.bind("<Button-1>", lambda e: sel_chip.toggle(), add="+")

    # ================================================================
    # CTkNumberEntry
    # ================================================================
    def _build_number_entry_section(self):
        self._section_label("CTkNumberEntry")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        ctk.CTkLabel(row, text="Integer:").pack(side="left", padx=(0, 4))
        ne1 = ctk.CTkNumberEntry(row, from_=0, to=100, step=1, width=120)
        ne1.pack(side="left", padx=4)
        ne1.set(42)

        ctk.CTkLabel(row, text="Float:").pack(side="left", padx=(16, 4))
        ne2 = ctk.CTkNumberEntry(row, from_=0.0, to=10.0, step=0.1,
                                  number_type=float, width=120)
        ne2.pack(side="left", padx=4)
        ne2.set(3.14)

        ctk.CTkLabel(row, text="With prefix:").pack(side="left", padx=(16, 4))
        ne3 = ctk.CTkNumberEntry(row, from_=0, to=9999, step=10,
                                  prefix="$", width=140)
        ne3.pack(side="left", padx=4)
        ne3.set(250)

    # ================================================================
    # CTkRangeSlider
    # ================================================================
    def _build_range_slider_section(self):
        self._section_label("CTkRangeSlider")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        range_lbl = ctk.CTkLabel(row, text="Range: 25 - 75")
        range_lbl.pack(side="right", padx=8)

        def on_range(low, high):
            range_lbl.configure(text=f"Range: {int(low)} - {int(high)}")

        rs = ctk.CTkRangeSlider(row, from_=0, to=100, command=on_range,
                                 show_value=True, value_format="{:.0f}")
        rs.pack(side="left", fill="x", expand=True, padx=8)
        rs.set(25, 75)

    # ================================================================
    # CTkDataTable
    # ================================================================
    def _build_data_table_section(self):
        self._section_label("CTkDataTable")

        filter_row = ctk.CTkFrame(self._main, fg_color="transparent")
        filter_row.pack(fill="x", pady=(4, 2))
        ctk.CTkLabel(filter_row, text="Filter:").pack(side="left", padx=(0, 4))

        table = ctk.CTkDataTable(self._main, width=700, height=220)

        filter_entry = ctk.CTkEntry(filter_row, placeholder_text="Type to filter rows...", width=250)
        filter_entry.pack(side="left", padx=4)

        match_lbl = ctk.CTkLabel(filter_row, text="")
        match_lbl.pack(side="left", padx=8)

        def on_filter(event=None):
            text = filter_entry.get()
            table.filter(text)
            n = len(table._display_data)
            total = len(table._data)
            match_lbl.configure(text=f"{n}/{total} rows" if text else "")
        filter_entry.bind("<KeyRelease>", on_filter)

        ctk.CTkButton(filter_row, text="Clear", width=60,
                       command=lambda: (filter_entry.delete(0, "end"), table.clear_filter(),
                                         match_lbl.configure(text=""))).pack(side="left", padx=4)
        ctk.CTkLabel(filter_row, text="(Arrow keys navigate, Enter selects)",
                      font=ctk.CTkFont(size=11), text_color=("gray50", "gray60")).pack(side="right", padx=8)

        table.pack(fill="x", pady=4)
        table.set_columns([
            {"key": "name", "title": "Name", "width": 160},
            {"key": "role", "title": "Role", "width": 140},
            {"key": "status", "title": "Status", "width": 100, "type": "badge"},
            {"key": "score", "title": "Score", "width": 80, "type": "number"},
        ])
        table.set_data([
            {"name": "Alice Johnson", "role": "Engineer", "status": "Active", "score": 95},
            {"name": "Bob Smith", "role": "Designer", "status": "Active", "score": 88},
            {"name": "Carol White", "role": "Manager", "status": "Pending", "score": 92},
            {"name": "Dave Brown", "role": "Engineer", "status": "Inactive", "score": 76},
            {"name": "Eve Davis", "role": "QA Lead", "status": "Active", "score": 89},
            {"name": "Frank Lee", "role": "DevOps", "status": "Active", "score": 91},
            {"name": "Grace Kim", "role": "Analyst", "status": "Active", "score": 84},
            {"name": "Hank Wilson", "role": "Engineer", "status": "Pending", "score": 78},
        ])

    # ================================================================
    # CTkTreeView
    # ================================================================
    def _build_tree_view_section(self):
        self._section_label("CTkTreeView")

        tree = ctk.CTkTreeView(self._main, width=500, height=200)
        tree.pack(fill="x", pady=4)

        root1 = tree.insert("", "Project Files")
        src = tree.insert(root1, "src")
        tree.insert(src, "main.py")
        tree.insert(src, "utils.py")
        tree.insert(src, "config.py")
        tests = tree.insert(root1, "tests")
        tree.insert(tests, "test_main.py")
        tree.insert(tests, "test_utils.py")

        root2 = tree.insert("", "Documentation")
        tree.insert(root2, "README.md")
        tree.insert(root2, "CHANGELOG.md")

        tree.expand(root1)
        tree.expand(src)

    # ================================================================
    # CTkNotificationBanner
    # ================================================================
    def _build_notification_banner_section(self):
        self._section_label("CTkNotificationBanner")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        banner_container = ctk.CTkFrame(self._main, fg_color="transparent", height=50)
        banner_container.pack(fill="x", pady=4)
        banner_container.pack_propagate(False)

        def show_banner(style):
            for child in banner_container.winfo_children():
                child.destroy()
            messages = {
                "info": "A new version is available.",
                "success": "Settings saved successfully!",
                "warning": "Your session will expire in 5 minutes.",
                "error": "Failed to connect to server.",
            }
            b = ctk.CTkNotificationBanner(banner_container,
                                           message=messages.get(style, "Notification"),
                                           style=style, dismissible=True)
            b.show()

        for style in ("info", "success", "warning", "error"):
            ctk.CTkButton(row, text=style.capitalize(), width=80,
                           command=lambda s=style: show_banner(s)).pack(side="left", padx=3)

    # ================================================================
    # CTkDatePicker & CTkTimePicker
    # ================================================================
    def _build_date_time_section(self):
        self._section_label("CTkDatePicker & CTkTimePicker")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        ctk.CTkLabel(row, text="Date:").pack(side="left", padx=(0, 4))
        ctk.CTkDatePicker(row, width=180).pack(side="left", padx=4)

        ctk.CTkLabel(row, text="Time (24h):").pack(side="left", padx=(16, 4))
        ctk.CTkTimePicker(row, width=160, time_format="24h").pack(side="left", padx=4)

        ctk.CTkLabel(row, text="Time (12h):").pack(side="left", padx=(16, 4))
        ctk.CTkTimePicker(row, width=160, time_format="12h").pack(side="left", padx=4)

    # ================================================================
    # CTkSpinbox
    # ================================================================
    def _build_spinbox_section(self):
        self._section_label("CTkSpinbox")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        val_lbl = ctk.CTkLabel(row, text="Value: 50")
        val_lbl.pack(side="right", padx=8)

        ctk.CTkLabel(row, text="Integer (0-100):").pack(side="left", padx=(0, 4))
        sb1 = ctk.CTkSpinbox(row, min_value=0, max_value=100, step=1, start_value=50,
                               command=lambda: val_lbl.configure(text=f"Value: {sb1.get()}"))
        sb1.pack(side="left", padx=4)

        ctk.CTkLabel(row, text="Float (0-10):").pack(side="left", padx=(16, 4))
        sb2 = ctk.CTkSpinbox(row, min_value=0.0, max_value=10.0, step=0.5,
                               float_precision=1, start_value=5.0)
        sb2.pack(side="left", padx=4)

        ctk.CTkLabel(row, text="Big step:").pack(side="left", padx=(16, 4))
        sb3 = ctk.CTkSpinbox(row, min_value=0, max_value=1000, step=50, start_value=500)
        sb3.pack(side="left", padx=4)

    # ================================================================
    # CTkTagInput
    # ================================================================
    def _build_tag_input_section(self):
        self._section_label("CTkTagInput")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        tags_lbl = ctk.CTkLabel(row, text="Tags: []")
        tags_lbl.pack(side="right", padx=8)

        def on_tags_changed(tags):
            tags_lbl.configure(text=f"Tags: {tags}")

        ti = ctk.CTkTagInput(row, width=400, placeholder_text="Type and press Enter to add tags...",
                              max_tags=8, command=on_tags_changed)
        ti.pack(side="left", padx=4)

        ctk.CTkButton(row, text="Add 'Demo'", width=100,
                       command=lambda: ti.add_tag("Demo")).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Clear", width=60,
                       command=lambda: ti.clear_tags()).pack(side="left", padx=4)

    # ================================================================
    # CTkGauge
    # ================================================================
    def _build_gauge_section(self):
        self._section_label("CTkGauge")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        # Basic gauge
        g1 = ctk.CTkGauge(row, width=200, height=160, label="Speed",
                            min_value=0, max_value=200, value_format="{:.0f}")
        g1.pack(side="left", padx=16)
        g1.set(0.6)

        # Gauge with color zones
        g2 = ctk.CTkGauge(row, width=200, height=160, label="CPU",
                            min_value=0, max_value=100, value_format="{:.0f}%",
                            zones=[(0, 0.6, "#22C55E"), (0.6, 0.85, "#F59E0B"), (0.85, 1.0, "#EF4444")])
        g2.pack(side="left", padx=16)
        g2.set(0.72)

        controls = ctk.CTkFrame(row, fg_color="transparent")
        controls.pack(side="left", padx=16)

        ctk.CTkLabel(controls, text="Set gauge value:").pack(anchor="w")
        for val, label in [(0.0, "0%"), (0.25, "25%"), (0.5, "50%"), (0.75, "75%"), (1.0, "100%")]:
            ctk.CTkButton(controls, text=label, width=60,
                           command=lambda v=val: (g1.set(v, animate=True), g2.set(v, animate=True))
                           ).pack(side="left", padx=2, pady=2)

    # ================================================================
    # CTkPaginator
    # ================================================================
    def _build_paginator_section(self):
        self._section_label("CTkPaginator")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        page_lbl = ctk.CTkLabel(row, text="Page: 1")
        page_lbl.pack(side="right", padx=8)

        pag = ctk.CTkPaginator(row, total_pages=20, show_info=True, show_first_last=True,
                                command=lambda p: page_lbl.configure(text=f"Page: {p}"))
        pag.pack(side="left", padx=4)

    # ================================================================
    # CTkCalendarView
    # ================================================================
    def _build_calendar_view_section(self):
        self._section_label("CTkCalendarView")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        date_lbl = ctk.CTkLabel(row, text="Selected: (none)")

        cal = ctk.CTkCalendarView(row, width=300, height=320, show_week_numbers=True,
                                   show_today_button=True,
                                   command=lambda d: date_lbl.configure(text=f"Selected: {d}"))
        cal.pack(side="left", padx=8)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=16, fill="y")

        date_lbl.pack(in_=info, anchor="w", pady=4)
        ctk.CTkButton(info, text="Go to Today", width=120,
                       command=lambda: cal.go_to_today()).pack(anchor="w", pady=2)
        ctk.CTkButton(info, text="Clear Selection", width=120,
                       command=lambda: (cal.clear_selection(),
                                         date_lbl.configure(text="Selected: (none)"))).pack(anchor="w", pady=2)

    # ================================================================
    # CTkColorPicker
    # ================================================================
    def _build_color_picker_section(self):
        self._section_label("CTkColorPicker")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        color_lbl = ctk.CTkLabel(row, text="Color: #ff0000")

        def on_color(hex_color):
            color_lbl.configure(text=f"Color: {hex_color}")
            preview.configure(fg_color=hex_color)

        picker = ctk.CTkColorPicker(row, width=300, height=250, command=on_color)
        picker.pack(side="left", padx=8)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=16, fill="y")

        color_lbl.pack(in_=info, anchor="w", pady=4)
        preview = ctk.CTkFrame(info, width=80, height=80, corner_radius=10, fg_color="#ff0000")
        preview.pack(anchor="w", pady=8)

        ctk.CTkButton(info, text="Set Blue", width=100,
                       command=lambda: picker.set("#3B82F6")).pack(anchor="w", pady=2)
        ctk.CTkButton(info, text="Set Green", width=100,
                       command=lambda: picker.set("#22C55E")).pack(anchor="w", pady=2)

    # ================================================================
    # CTkNavigationRail
    # ================================================================
    def _build_navigation_rail_section(self):
        self._section_label("CTkNavigationRail")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        nav_lbl = ctk.CTkLabel(row, text="Selected: home")

        items = [
            {"name": "home", "text": "Home", "icon": "\u2302"},
            {"name": "search", "text": "Search", "icon": "\u2315"},
            {"name": "settings", "text": "Settings", "icon": "\u2699"},
            {"name": "user", "text": "Profile", "icon": "\u263A"},
        ]
        bottom_items = [
            {"name": "help", "text": "Help", "icon": "\u003F"},
        ]

        def on_nav(name):
            nav_lbl.configure(text=f"Selected: {name}")

        rail = ctk.CTkNavigationRail(row, width=180, height=300, items=items,
                                      bottom_items=bottom_items, command=on_nav)
        rail.pack(side="left", padx=8)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=16, fill="y")

        nav_lbl.pack(in_=info, anchor="w", pady=4)

        ctk.CTkButton(info, text="Set badge (search: 5)", width=180,
                       command=lambda: rail.set_badge("search", 5)).pack(anchor="w", pady=2)
        ctk.CTkButton(info, text="Clear badge", width=180,
                       command=lambda: rail.set_badge("search", 0)).pack(anchor="w", pady=2)
        ctk.CTkButton(info, text="Select 'settings'", width=180,
                       command=lambda: rail.set_value("settings")).pack(anchor="w", pady=2)

    # ================================================================
    # CTkSplitView
    # ================================================================
    def _build_split_view_section(self):
        self._section_label("CTkSplitView")

        ratio_lbl = ctk.CTkLabel(self._main, text="Ratio: 0.40")

        split = ctk.CTkSplitView(self._main, width=700, height=200, orientation="horizontal",
                                  ratio=0.4, min_size=80,
                                  command=lambda: ratio_lbl.configure(
                                      text=f"Ratio: {split.get_ratio():.2f}"))
        split.pack(fill="x", pady=4)

        # Panel 1 content
        ctk.CTkLabel(split.panel_1, text="Panel 1", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=8)
        ctk.CTkLabel(split.panel_1, text="Drag the divider\nto resize panels").pack(pady=4)

        # Panel 2 content
        ctk.CTkLabel(split.panel_2, text="Panel 2", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=8)
        ctk.CTkEntry(split.panel_2, placeholder_text="Type here...").pack(padx=12, pady=4, fill="x")
        ctk.CTkButton(split.panel_2, text="Button in Panel 2").pack(padx=12, pady=4)

        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ratio_lbl.pack(in_=row, side="right", padx=8)
        ctk.CTkButton(row, text="50/50", width=60,
                       command=lambda: split.set_ratio(0.5)).pack(side="left", padx=4)
        ctk.CTkButton(row, text="30/70", width=60,
                       command=lambda: split.set_ratio(0.3)).pack(side="left", padx=4)
        ctk.CTkButton(row, text="70/30", width=60,
                       command=lambda: split.set_ratio(0.7)).pack(side="left", padx=4)

    # ================================================================
    # CTkLoadingOverlay
    # ================================================================
    def _build_loading_overlay_section(self):
        self._section_label("CTkLoadingOverlay")

        container = ctk.CTkFrame(self._main, width=500, height=150, border_width=2,
                                  border_color=("#c0c0c0", "#555555"))
        container.pack(fill="x", pady=4)
        container.pack_propagate(False)

        ctk.CTkLabel(container, text="Content behind overlay", font=ctk.CTkFont(size=16)).pack(expand=True)
        ctk.CTkButton(container, text="A button you can't click when loading").pack(pady=(0, 16))

        overlay = ctk.CTkLoadingOverlay(container, message="Loading, please wait...")

        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x", pady=4)

        def show_loading():
            overlay.show()
            self.after(3000, overlay.hide)

        def show_progress():
            overlay.set_message("Downloading...")
            overlay.set_progress(0.0)
            overlay.show()
            step = [0]
            def tick():
                step[0] += 1
                overlay.set_progress(step[0] / 20)
                if step[0] < 20:
                    self.after(150, tick)
                else:
                    self.after(500, overlay.hide)
            tick()

        ctk.CTkButton(row, text="Show (3s)", width=100, command=show_loading).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Show with Progress", width=140, command=show_progress).pack(side="left", padx=4)

    # ================================================================
    # CTkSkeleton
    # ================================================================
    def _build_skeleton_section(self):
        self._section_label("CTkSkeleton")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        # Simulated card skeleton
        card = ctk.CTkFrame(row, width=250, fg_color=("#e8e8e8", "#333333"), corner_radius=8)
        card.pack(side="left", padx=8)

        ctk.CTkSkeleton(card, width=220, height=120, corner_radius=8).pack(padx=12, pady=(12, 8))
        ctk.CTkSkeleton(card, width=180, height=16, corner_radius=4).pack(padx=12, pady=4, anchor="w")
        ctk.CTkSkeleton(card, width=140, height=12, corner_radius=4).pack(padx=12, pady=(2, 12), anchor="w")

        # Different sizes
        sizes = ctk.CTkFrame(row, fg_color="transparent")
        sizes.pack(side="left", padx=16)

        ctk.CTkLabel(sizes, text="Various shapes:").pack(anchor="w", pady=(0, 4))
        ctk.CTkSkeleton(sizes, width=300, height=14, corner_radius=4).pack(pady=3, anchor="w")
        ctk.CTkSkeleton(sizes, width=250, height=14, corner_radius=4).pack(pady=3, anchor="w")
        ctk.CTkSkeleton(sizes, width=200, height=14, corner_radius=4).pack(pady=3, anchor="w")

        circle_row = ctk.CTkFrame(sizes, fg_color="transparent")
        circle_row.pack(anchor="w", pady=4)
        ctk.CTkSkeleton(circle_row, width=40, height=40, corner_radius=20).pack(side="left", padx=4)
        ctk.CTkSkeleton(circle_row, width=40, height=40, corner_radius=20).pack(side="left", padx=4)
        ctk.CTkSkeleton(circle_row, width=40, height=40, corner_radius=20).pack(side="left", padx=4)

    # ================================================================
    # CTkShadowFrame
    # ================================================================
    def _build_shadow_frame_section(self):
        self._section_label("CTkShadowFrame")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        for elev in range(5):
            sf = ctk.CTkShadowFrame(row, width=140, height=100, elevation=elev, corner_radius=10)
            sf.pack(side="left", padx=16, pady=16)
            ctk.CTkLabel(sf, text=f"Elevation {elev}",
                          font=ctk.CTkFont(size=12, weight="bold")).pack(expand=True)

    # ================================================================
    # CTkGradientFrame
    # ================================================================
    def _build_gradient_frame_section(self):
        self._section_label("CTkGradientFrame")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        # Horizontal
        gf1 = ctk.CTkGradientFrame(row, width=200, height=100,
                                     from_color=("#3B82F6", "#2563EB"),
                                     to_color=("#8B5CF6", "#7C3AED"),
                                     orientation="horizontal", corner_radius=10)
        gf1.pack(side="left", padx=8, pady=8)
        ctk.CTkLabel(gf1, text="Horizontal", text_color="white",
                      font=ctk.CTkFont(weight="bold")).pack(expand=True)

        # Vertical
        gf2 = ctk.CTkGradientFrame(row, width=200, height=100,
                                     from_color=("#22C55E", "#16A34A"),
                                     to_color=("#3B82F6", "#2563EB"),
                                     orientation="vertical", corner_radius=10)
        gf2.pack(side="left", padx=8, pady=8)
        ctk.CTkLabel(gf2, text="Vertical", text_color="white",
                      font=ctk.CTkFont(weight="bold")).pack(expand=True)

        # Diagonal
        gf3 = ctk.CTkGradientFrame(row, width=200, height=100,
                                     from_color=("#F59E0B", "#D97706"),
                                     to_color=("#EF4444", "#DC2626"),
                                     orientation="diagonal", corner_radius=10)
        gf3.pack(side="left", padx=8, pady=8)
        ctk.CTkLabel(gf3, text="Diagonal", text_color="white",
                      font=ctk.CTkFont(weight="bold")).pack(expand=True)

    # ================================================================
    # CTkIcon
    # ================================================================
    def _build_icon_section(self):
        self._section_label("CTkIcon")

        from customtkinter.windows.widgets.ctk_icon import ICONS

        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        # Showcase common icons
        icons_to_show = ["home", "search", "settings", "user", "mail", "star",
                          "heart", "check", "edit", "delete", "play", "pause",
                          "sun", "moon", "lock", "bell", "folder", "save"]

        for name in icons_to_show:
            if name in ICONS:
                frame = ctk.CTkFrame(row, fg_color="transparent", width=60)
                frame.pack(side="left", padx=4, pady=4)
                frame.pack_propagate(False)
                ctk.CTkIcon(frame, text=ICONS[name], size=22,
                             text_color=("#333333", "#e0e0e0")).pack()
                ctk.CTkLabel(frame, text=name, font=ctk.CTkFont(size=9),
                              text_color=("gray50", "gray60")).pack()

        # Clickable icon
        row2 = ctk.CTkFrame(self._main, fg_color="transparent")
        row2.pack(fill="x", pady=(8, 0))

        click_lbl = ctk.CTkLabel(row2, text="Click an icon:")
        click_lbl.pack(side="left", padx=(0, 8))

        for name in ("home", "settings", "star", "heart"):
            ctk.CTkIcon(row2, text=ICONS[name], size=28,
                         text_color=("#3B82F6", "#60A5FA"),
                         hover_color=("#2563EB", "#93C5FD"),
                         command=lambda n=name: click_lbl.configure(text=f"Clicked: {n}")
                         ).pack(side="left", padx=6)

    # ================================================================
    # CTkAnimatedFrame
    # ================================================================
    def _build_animated_frame_section(self):
        self._section_label("CTkAnimatedFrame")

        container = ctk.CTkAnimatedFrame(self._main, width=600, height=180,
                                          transition="slide_left", duration=300)
        container.pack(fill="x", pady=4)

        # Create pages
        colors = [("#3B82F6", "Page 1: Blue"), ("#22C55E", "Page 2: Green"),
                  ("#EF4444", "Page 3: Red"), ("#8B5CF6", "Page 4: Purple")]

        for i, (color, label) in enumerate(colors):
            page = container.add_page(f"page{i+1}")
            ctk.CTkLabel(page, text=label, font=ctk.CTkFont(size=20, weight="bold"),
                          text_color="white").pack(expand=True)

        container.show_page("page1", transition="none")

        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x", pady=4)

        page_lbl = ctk.CTkLabel(row, text="Current: page1")
        page_lbl.pack(side="right", padx=8)

        for i in range(4):
            name = f"page{i+1}"
            ctk.CTkButton(row, text=f"Page {i+1}", width=70,
                           command=lambda n=name: (container.show_page(n),
                                                    page_lbl.configure(text=f"Current: {n}"))
                           ).pack(side="left", padx=3)

        ctk.CTkLabel(row, text="Transition:").pack(side="left", padx=(12, 4))
        transitions = ["slide_left", "slide_right", "slide_up", "slide_down", "fade", "none"]
        trans_menu = ctk.CTkOptionMenu(row, values=transitions, width=120,
                                        command=lambda t: container.configure(transition=t))
        trans_menu.pack(side="left", padx=4)

    # ================================================================
    # CTkFrostedFrame
    # ================================================================
    def _build_frosted_frame_section(self):
        self._section_label("CTkFrostedFrame")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        # Background with content
        bg = ctk.CTkFrame(row, width=700, height=180, fg_color=("#6366F1", "#4338CA"),
                           corner_radius=12)
        bg.pack(padx=8, pady=8)
        bg.pack_propagate(False)

        ctk.CTkLabel(bg, text="Background with gradient-like color",
                      text_color="white", font=ctk.CTkFont(size=14)).pack(pady=8)

        # Frosted panels on top
        frost1 = ctk.CTkFrostedFrame(bg, width=200, height=100, tint_opacity=0.12,
                                      border_opacity=0.3, corner_radius=10)
        frost1.place(x=30, y=50)
        ctk.CTkLabel(frost1, text="Frosted Panel",
                      text_color="white", font=ctk.CTkFont(weight="bold")).pack(expand=True)

        frost2 = ctk.CTkFrostedFrame(bg, width=200, height=100, tint_opacity=0.08,
                                      border_opacity=0.2, noise=True, corner_radius=10)
        frost2.place(x=260, y=50)
        ctk.CTkLabel(frost2, text="With Noise",
                      text_color="white", font=ctk.CTkFont(weight="bold")).pack(expand=True)

        frost3 = ctk.CTkFrostedFrame(bg, width=180, height=100,
                                      tint_color=("#FF6B6B", "#FF6B6B"),
                                      tint_opacity=0.15, border_opacity=0.35,
                                      corner_radius=10)
        frost3.place(x=490, y=50)
        ctk.CTkLabel(frost3, text="Tinted Frost",
                      text_color="white", font=ctk.CTkFont(weight="bold")).pack(expand=True)

    # ================================================================
    # CTkFocusRing (Utility)
    # ================================================================
    def _build_focus_ring_section(self):
        self._section_label("CTkFocusRing (Utility)")
        ctk.CTkLabel(self._main, text="Tab through these buttons to see the focus ring appear",
                      font=ctk.CTkFont(size=11), text_color=("gray50", "gray60")).pack(anchor="w")

        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x", pady=4)

        btn1 = ctk.CTkButton(row, text="Button with Focus Ring")
        btn1.pack(side="left", padx=8)
        ctk.CTkFocusRing.attach(btn1)

        btn2 = ctk.CTkButton(row, text="Custom Color Ring")
        btn2.pack(side="left", padx=8)
        ctk.CTkFocusRing.attach(btn2, ring_color=("#22C55E", "#4ADE80"), ring_width=3)

        btn3 = ctk.CTkButton(row, text="Thick Ring")
        btn3.pack(side="left", padx=8)
        ctk.CTkFocusRing.attach(btn3, ring_width=4, ring_pad=3, ring_color=("#EF4444", "#F87171"))

        entry = ctk.CTkEntry(row, placeholder_text="Entry with focus ring", width=200)
        entry.pack(side="left", padx=8)
        ctk.CTkFocusRing.attach(entry)

    # ================================================================
    # CTkRipple (Utility)
    # ================================================================
    def _build_ripple_section(self):
        self._section_label("CTkRipple (Utility)")
        ctk.CTkLabel(self._main, text="Click these buttons to see the ripple effect",
                      font=ctk.CTkFont(size=11), text_color=("gray50", "gray60")).pack(anchor="w")

        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x", pady=4)

        btn1 = ctk.CTkButton(row, text="Default Ripple")
        btn1.pack(side="left", padx=8)
        ctk.CTkRipple.attach(btn1)

        btn2 = ctk.CTkButton(row, text="White Ripple", fg_color=("#3B82F6", "#2563EB"))
        btn2.pack(side="left", padx=8)
        ctk.CTkRipple.attach(btn2, color="#ffffff", opacity=0.2)

        btn3 = ctk.CTkButton(row, text="Slow Ripple")
        btn3.pack(side="left", padx=8)
        ctk.CTkRipple.attach(btn3, duration=600)

        btn4 = ctk.CTkButton(row, text="Strong Ripple", fg_color=("#22C55E", "#16A34A"))
        btn4.pack(side="left", padx=8)
        ctk.CTkRipple.attach(btn4, opacity=0.25)

    # ================================================================
    # CTkFontScale (Utility)
    # ================================================================
    def _build_font_scale_section(self):
        self._section_label("CTkFontScale (Typography)")

        presets = [
            ("display_large", ctk.CTkFontScale.display_large),
            ("display", ctk.CTkFontScale.display),
            ("heading_large", ctk.CTkFontScale.heading_large),
            ("heading", ctk.CTkFontScale.heading),
            ("subheading", ctk.CTkFontScale.subheading),
            ("title", ctk.CTkFontScale.title),
            ("body_large", ctk.CTkFontScale.body_large),
            ("body", ctk.CTkFontScale.body),
            ("body_small", ctk.CTkFontScale.body_small),
            ("label", ctk.CTkFontScale.label),
            ("caption", ctk.CTkFontScale.caption),
            ("overline", ctk.CTkFontScale.overline),
        ]

        for name, factory in presets:
            font = factory()
            spec = ctk.CTkFontScale.get_scale()[name]
            row = ctk.CTkFrame(self._main, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=f"{name}", width=140,
                          font=ctk.CTkFont(size=11), text_color=("gray50", "gray60"),
                          anchor="e").pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text=f"The quick brown fox — size {spec['size']}, {spec['weight']}",
                          font=font).pack(side="left")

    # ================================================================
    # CTkAnimation (Utility)
    # ================================================================
    def _build_animation_section(self):
        self._section_label("CTkAnimation & Easing (Utility)")

        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x", pady=4)

        # Animated button that moves across
        track = ctk.CTkFrame(row, width=600, height=60, fg_color=("#e8e8e8", "#333333"),
                              corner_radius=8)
        track.pack(side="left", padx=8)
        track.pack_propagate(False)

        ball = ctk.CTkFrame(track, width=50, height=50, corner_radius=25,
                             fg_color=("#3B82F6", "#60A5FA"))
        ball.place(x=5, y=5)

        current_anim = [None]

        def animate_ball(easing_name):
            if current_anim[0] is not None:
                current_anim[0].cancel()

            easing_func = getattr(ctk.Easing, easing_name, ctk.Easing.EASE_OUT_CUBIC)

            def update(value):
                x = int(value * 540) + 5
                ball.place(x=x, y=5)

            anim = ctk.CTkAnimation(
                widget=track,
                duration=800,
                from_value=0.0,
                to_value=1.0,
                easing=easing_func,
                callback=update,
            )
            current_anim[0] = anim
            anim.start()

        controls = ctk.CTkFrame(row, fg_color="transparent")
        controls.pack(side="left", padx=8)

        ctk.CTkLabel(controls, text="Easing functions:").pack(anchor="w")
        easings = ["LINEAR", "EASE_IN_QUAD", "EASE_OUT_QUAD", "EASE_IN_OUT_QUAD",
                    "EASE_OUT_CUBIC", "EASE_OUT_BACK", "EASE_OUT_BOUNCE"]
        for e_name in easings:
            ctk.CTkButton(controls, text=e_name.replace("EASE_", "").replace("_", " ").title(),
                           width=130, height=24, font=ctk.CTkFont(size=11),
                           command=lambda n=e_name: animate_ball(n)).pack(pady=1)

    # ================================================================
    # ColorUtils (Utility)
    # ================================================================
    def _build_color_utils_section(self):
        self._section_label("ColorUtils (Utility)")

        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x", pady=4)

        accent = "#3B82F6"
        palette = ctk.ColorUtils.generate_palette(accent)

        ctk.CTkLabel(row, text=f"Generated palette from accent {accent}:",
                      font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 8))

        palette_row = ctk.CTkFrame(self._main, fg_color="transparent")
        palette_row.pack(fill="x", pady=4)

        for name, (light, dark) in palette.items():
            frame = ctk.CTkFrame(palette_row, fg_color="transparent", width=90)
            frame.pack(side="left", padx=4)
            frame.pack_propagate(False)
            swatch = ctk.CTkFrame(frame, width=70, height=40, corner_radius=6,
                                   fg_color=(light, dark))
            swatch.pack()
            ctk.CTkLabel(frame, text=name, font=ctk.CTkFont(size=9),
                          text_color=("gray50", "gray60")).pack(pady=(2, 0))
            ctk.CTkLabel(frame, text=f"{dark}", font=ctk.CTkFont(size=8),
                          text_color=("gray60", "gray50")).pack()

        # Color manipulation demos
        row2 = ctk.CTkFrame(self._main, fg_color="transparent")
        row2.pack(fill="x", pady=(8, 4))

        base = "#3B82F6"
        ops = [
            ("Original", base),
            ("Lighten 20%", ctk.ColorUtils.lighten(base, 0.2)),
            ("Lighten 40%", ctk.ColorUtils.lighten(base, 0.4)),
            ("Darken 20%", ctk.ColorUtils.darken(base, 0.2)),
            ("Darken 40%", ctk.ColorUtils.darken(base, 0.4)),
            ("Desaturate", ctk.ColorUtils.desaturate(base, 0.5)),
            ("Complement", ctk.ColorUtils.complementary(base)),
        ]

        for label, color in ops:
            frame = ctk.CTkFrame(row2, fg_color="transparent", width=90)
            frame.pack(side="left", padx=4)
            frame.pack_propagate(False)
            ctk.CTkFrame(frame, width=70, height=35, corner_radius=6,
                          fg_color=color).pack()
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=9),
                          text_color=("gray50", "gray60")).pack(pady=(2, 0))
            ctk.CTkLabel(frame, text=color, font=ctk.CTkFont(size=8),
                          text_color=("gray60", "gray50")).pack()


if __name__ == "__main__":
    app = WidgetDemo()
    app.mainloop()
