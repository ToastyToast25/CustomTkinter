"""
Interactive demo for all 10 polished CustomTkinter widgets.
"""

import sys
import tkinter

sys.path.insert(0, r"C:\Users\Administrator\Pictures\CustomTkinter")
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

        self._build_tooltip_section()
        self._build_status_badge_section()
        self._build_card_section()
        self._build_search_entry_section()
        self._build_circular_progress_section()
        self._build_collapsible_frame_section()
        self._build_rich_textbox_section()
        self._build_context_menu_section()
        self._build_dialog_section()

    # --- helpers ---
    def _section_label(self, text):
        lbl = ctk.CTkLabel(self._main, text=text, font=ctk.CTkFont(size=18, weight="bold"))
        lbl.pack(anchor="w", pady=(20, 6))
        sep = ctk.CTkFrame(self._main, height=2, fg_color=("#c0c0c0", "#404040"))
        sep.pack(fill="x", pady=(0, 10))

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


if __name__ == "__main__":
    app = WidgetDemo()
    app.mainloop()
