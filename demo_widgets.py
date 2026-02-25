"""
Interactive demo for all 10 polished CustomTkinter widgets.
"""

import sys
import os
import tkinter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import customtkinter as ctk


class WidgetDemo(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Polished Widgets Demo")
        self.geometry("1100x750")
        ctk.set_appearance_mode("dark")

        # Scrollable main area
        self._main = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._main.pack(fill="both", expand=True, padx=16, pady=16)

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

    # --- helpers ---
    def _section_label(self, text):
        lbl = ctk.CTkLabel(self._main, text=text, font=ctk.CTkFont(size=18, weight="bold"))
        lbl.pack(anchor="w", pady=(20, 6))
        sep = ctk.CTkFrame(self._main, height=2, fg_color=("#c0c0c0", "#404040"))
        sep.pack(fill="x", pady=(0, 10))

    # ================================================================
    # NEW: CTkRating
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
    # NEW: CTkAvatar
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

        # Size variants
        ctk.CTkLabel(row, text="  Sizes:").pack(side="left", padx=(24, 4))
        for size in ("small", "medium", "large", "xlarge"):
            ctk.CTkAvatar(row, text="AB", size=size).pack(side="left", padx=4)

    # ================================================================
    # NEW: CTkStepper
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
    # NEW: CTkAccordion
    # ================================================================
    def _build_accordion_section(self):
        self._section_label("CTkAccordion")

        ctk.CTkLabel(self._main, text="Tab to focus headers, arrow keys to navigate between sections",
                      font=ctk.CTkFont(size=11), text_color=("gray50", "gray60")).pack(anchor="w")

        accordion = ctk.CTkAccordion(self._main, exclusive=True)
        accordion.pack(fill="x", pady=4)

        # Section 1
        s1 = accordion.add_section("General Settings", collapsed=False)
        ctk.CTkSwitch(s1, text="Enable notifications").pack(padx=16, pady=4, anchor="w")
        ctk.CTkSwitch(s1, text="Auto-save").pack(padx=16, pady=4, anchor="w")
        ctk.CTkEntry(s1, placeholder_text="Username").pack(padx=16, pady=4, fill="x")

        # Section 2
        s2 = accordion.add_section("Appearance")
        ctk.CTkLabel(s2, text="Font size:").pack(padx=16, pady=4, anchor="w")
        ctk.CTkSlider(s2, from_=8, to=24, number_of_steps=16).pack(padx=16, pady=4, fill="x")
        ctk.CTkOptionMenu(s2, values=["Light", "Dark", "System"]).pack(padx=16, pady=4)

        # Section 3
        s3 = accordion.add_section("Advanced")
        ctk.CTkLabel(s3, text="Thread count:").pack(padx=16, pady=4, anchor="w")
        ctk.CTkSlider(s3, from_=1, to=16, number_of_steps=15).pack(padx=16, pady=4, fill="x")
        ctk.CTkCheckBox(s3, text="Debug mode").pack(padx=16, pady=4, anchor="w")

    # ================================================================
    # 1. CTkToolTip
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
    # 2. CTkStatusBadge
    # ================================================================
    def _build_status_badge_section(self):
        self._section_label("CTkStatusBadge")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        styles = ["success", "warning", "error", "info", "muted"]
        badges = []
        for s in styles:
            b = ctk.CTkStatusBadge(row, text=s.capitalize(), style=s)
            b.pack(side="left", padx=4)
            badges.append(b)

        row2 = ctk.CTkFrame(self._main, fg_color="transparent")
        row2.pack(fill="x", pady=(6, 0))

        # Size variants
        for size in ("small", "default", "large"):
            b = ctk.CTkStatusBadge(row2, text=size, style="info", size=size)
            b.pack(side="left", padx=4)

        # Count badge
        count_badge = ctk.CTkStatusBadge(row2, text="Notifications", style="error", count=7)
        count_badge.pack(side="left", padx=4)

        def inc_count():
            c = count_badge.cget("count") or 0
            count_badge.set_count(c + 1)
        ctk.CTkButton(row2, text="+1", width=40, command=inc_count).pack(side="left", padx=2)

        # Pulse badge
        pulse_badge = ctk.CTkStatusBadge(row2, text="Loading", style="warning", pulse=True)
        pulse_badge.pack(side="left", padx=4)

        def toggle_pulse():
            if pulse_badge.cget("pulse"):
                pulse_badge.stop_pulse()
            else:
                pulse_badge.start_pulse()
        ctk.CTkButton(row2, text="Toggle Pulse", width=100, command=toggle_pulse).pack(side="left", padx=2)

    # ================================================================
    # 3. CTkCard
    # ================================================================
    def _build_card_section(self):
        self._section_label("CTkCard")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        # Interactive card
        card1 = ctk.CTkCard(row, width=200, height=120, border_width=2,
                             command=lambda: card1_lbl.configure(text="Clicked!"))
        card1.pack(side="left", padx=8)
        ctk.CTkLabel(card1, text="Clickable Card", font=ctk.CTkFont(weight="bold")).pack(padx=12, pady=(12, 2))
        card1_lbl = ctk.CTkLabel(card1, text="Hover & click me")
        card1_lbl.pack(padx=12, pady=(2, 12))

        # Selectable card
        card2 = ctk.CTkCard(row, width=200, height=120, border_width=2,
                             command=lambda: card2.toggle_select())
        card2.pack(side="left", padx=8)
        ctk.CTkLabel(card2, text="Selectable Card", font=ctk.CTkFont(weight="bold")).pack(padx=12, pady=(12, 2))
        ctk.CTkLabel(card2, text="Click to toggle select").pack(padx=12, pady=(2, 12))

        # Disabled card
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
    # 4. CTkSearchEntry
    # ================================================================
    def _build_search_entry_section(self):
        self._section_label("CTkSearchEntry")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        result_label = ctk.CTkLabel(row, text="Type to search...")
        result_label.pack(side="right", padx=8)

        def on_search(text):
            if text:
                # Simulate a search
                count = text.count("a") + text.count("e") + text.count("i") + text.count("o") + text.count("u")
                se.set_result_count(count)
                result_label.configure(text=f"Found {count} vowels in \"{text}\"")
            else:
                se.set_result_count(None)
                result_label.configure(text="Type to search...")

        se = ctk.CTkSearchEntry(row, placeholder_text="Search (try typing, Esc to clear, Enter to submit)...",
                                 width=400, command=on_search, debounce_ms=300)
        se.pack(side="left", padx=4)

    # ================================================================
    # 5. CTkCircularProgress
    # ================================================================
    def _build_circular_progress_section(self):
        self._section_label("CTkCircularProgress")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        # Determinate
        cp = ctk.CTkCircularProgress(row, size=100, line_width=8, show_text=True)
        cp.pack(side="left", padx=16)
        cp.set(0.0)

        controls = ctk.CTkFrame(row, fg_color="transparent")
        controls.pack(side="left", padx=8)

        def step_progress():
            cp.step(0.1)
        ctk.CTkButton(controls, text="+10%", width=70, command=step_progress).pack(pady=2)

        def reset_progress():
            cp.set(0.0)
        ctk.CTkButton(controls, text="Reset", width=70, command=reset_progress).pack(pady=2)

        def set_full():
            cp.set(1.0)
        ctk.CTkButton(controls, text="100%", width=70, command=set_full).pack(pady=2)

        # Indeterminate spinner
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

        # Custom text callback
        cp2 = ctk.CTkCircularProgress(row, size=90, line_width=6, show_text=True,
                                        text_callback=lambda v: f"{int(v * 50)}/50")
        cp2.pack(side="left", padx=16)
        cp2.set(0.64)

    # ================================================================
    # 6. CTkCollapsibleFrame
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
    # 7. CTkRichTextbox
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

        def add_info():
            rtb.add_text("New info message added", style="info")
        ctk.CTkButton(controls, text="Add Info", width=100, command=add_info).pack(pady=2)

        def add_error():
            rtb.add_text("Something went wrong!", style="error")
        ctk.CTkButton(controls, text="Add Error", width=100, command=add_error).pack(pady=2)

        def add_success():
            rtb.add_text("Operation completed", style="success")
        ctk.CTkButton(controls, text="Add Success", width=100, command=add_success).pack(pady=2)

        def do_search():
            count = rtb.search_text("config", nocase=True)
            search_lbl.configure(text=f"{count} matches")
        ctk.CTkButton(controls, text="Search 'config'", width=100, command=do_search).pack(pady=2)

        def next_match():
            rtb.search_next()
        ctk.CTkButton(controls, text="Next Match", width=100, command=next_match).pack(pady=2)

        def clear_search():
            rtb.clear_search()
            search_lbl.configure(text="")
        ctk.CTkButton(controls, text="Clear Search", width=100, command=clear_search).pack(pady=2)

        search_lbl = ctk.CTkLabel(controls, text="")
        search_lbl.pack(pady=2)

        def clear_all():
            rtb.clear()
        ctk.CTkButton(controls, text="Clear All", width=100, fg_color=("#E04545", "#E04545"),
                       command=clear_all).pack(pady=2)

    # ================================================================
    # 8. CTkContextMenu
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
    # 9. CTkDialog
    # ================================================================
    def _build_dialog_section(self):
        self._section_label("CTkDialog")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        def show_info():
            ctk.CTkDialog.show_info(self, title="Info", message="This is an informational dialog.",
                                     detail="Additional detail text goes here.")

        def show_success():
            ctk.CTkDialog.show_success(self, title="Success", message="Operation completed successfully!")

        def show_warning():
            ctk.CTkDialog.show_warning(self, title="Warning", message="This action may have consequences.",
                                        detail="Please review before proceeding.")

        def show_error():
            ctk.CTkDialog.show_error(self, title="Error", message="Something went wrong.",
                                      detail="Error code: 0xDEADBEEF")

        def show_confirm():
            result = ctk.CTkDialog.ask_yes_no(self, title="Confirm", message="Are you sure you want to proceed?")
            result_lbl.configure(text=f"Result: {'Yes' if result else 'No'}")

        def show_input():
            result = ctk.CTkDialog.ask_input(self, title="Input", message="Enter your name:",
                                              placeholder="Type here...", default_value="")
            result_lbl.configure(text=f"Input: {result!r}")

        ctk.CTkButton(row, text="Info", width=80, command=show_info).pack(side="left", padx=3)
        ctk.CTkButton(row, text="Success", width=80, command=show_success).pack(side="left", padx=3)
        ctk.CTkButton(row, text="Warning", width=80, command=show_warning).pack(side="left", padx=3)
        ctk.CTkButton(row, text="Error", width=80, command=show_error).pack(side="left", padx=3)
        ctk.CTkButton(row, text="Confirm", width=80, command=show_confirm).pack(side="left", padx=3)
        ctk.CTkButton(row, text="Input", width=80, command=show_input).pack(side="left", padx=3)

        result_lbl = ctk.CTkLabel(row, text="")
        result_lbl.pack(side="left", padx=12)

    # ================================================================
    # 10. CTkToggleSwitch
    # ================================================================
    def _build_toggle_switch_section(self):
        self._section_label("CTkToggleSwitch")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        state_lbl = ctk.CTkLabel(row, text="Off")
        state_lbl.pack(side="right", padx=8)

        def on_toggle(val):
            state_lbl.configure(text="On" if val else "Off")

        sw1 = ctk.CTkToggleSwitch(row, text="Enable feature", size="medium",
                                    command=on_toggle)
        sw1.pack(side="left", padx=8)

        ctk.CTkLabel(row, text="Sizes:").pack(side="left", padx=(16, 4))
        for sz in ("small", "medium", "large"):
            ctk.CTkToggleSwitch(row, size=sz).pack(side="left", padx=4)

        ctk.CTkLabel(row, text="Labels:").pack(side="left", padx=(16, 4))
        ctk.CTkToggleSwitch(row, size="large", on_label="ON", off_label="OFF",
                             on_color=("#22C55E", "#16A34A")).pack(side="left", padx=4)

    # ================================================================
    # 11. CTkBreadcrumb
    # ================================================================
    def _build_breadcrumb_section(self):
        self._section_label("CTkBreadcrumb")

        bc = ctk.CTkBreadcrumb(self._main,
                                items=["Home", "Products", "Electronics", "Phones"],
                                command=lambda idx, text: bc_lbl.configure(
                                    text=f"Clicked: {text} (index {idx})"))
        bc.pack(fill="x", pady=4)

        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x", pady=4)

        bc_lbl = ctk.CTkLabel(row, text="Click a segment above")
        bc_lbl.pack(side="right", padx=8)

        def push_item():
            bc.push("Accessories")
        def pop_item():
            try:
                bc.pop()
            except IndexError:
                pass

        ctk.CTkButton(row, text="Push", width=60, command=push_item).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Pop", width=60, command=pop_item).pack(side="left", padx=4)

    # ================================================================
    # 12. CTkChip
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
    # 13. CTkNumberEntry
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
    # 14. CTkRangeSlider
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
    # 15. CTkDataTable (with filter + keyboard navigation)
    # ================================================================
    def _build_data_table_section(self):
        self._section_label("CTkDataTable")

        # Filter bar
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
            if text:
                match_lbl.configure(text=f"{n}/{total} rows")
            else:
                match_lbl.configure(text="")

        filter_entry.bind("<KeyRelease>", on_filter)

        def clear_filter():
            filter_entry.delete(0, "end")
            table.clear_filter()
            match_lbl.configure(text="")

        ctk.CTkButton(filter_row, text="Clear", width=60, command=clear_filter).pack(side="left", padx=4)
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
    # 16. CTkTreeView
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
    # 17. CTkNotificationBanner
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
            b = ctk.CTkNotificationBanner(
                banner_container,
                message=messages.get(style, "Notification"),
                style=style,
                dismissible=True,
            )
            b.show()

        for style in ("info", "success", "warning", "error"):
            ctk.CTkButton(row, text=style.capitalize(), width=80,
                           command=lambda s=style: show_banner(s)).pack(side="left", padx=3)

    # ================================================================
    # 18. CTkDatePicker & CTkTimePicker
    # ================================================================
    def _build_date_time_section(self):
        self._section_label("CTkDatePicker & CTkTimePicker")
        row = ctk.CTkFrame(self._main, fg_color="transparent")
        row.pack(fill="x")

        ctk.CTkLabel(row, text="Date:").pack(side="left", padx=(0, 4))
        dp = ctk.CTkDatePicker(row, width=180)
        dp.pack(side="left", padx=4)

        ctk.CTkLabel(row, text="Time (24h):").pack(side="left", padx=(16, 4))
        tp = ctk.CTkTimePicker(row, width=160, time_format="24h")
        tp.pack(side="left", padx=4)

        ctk.CTkLabel(row, text="Time (12h):").pack(side="left", padx=(16, 4))
        tp2 = ctk.CTkTimePicker(row, width=160, time_format="12h")
        tp2.pack(side="left", padx=4)


if __name__ == "__main__":
    app = WidgetDemo()
    app.mainloop()
