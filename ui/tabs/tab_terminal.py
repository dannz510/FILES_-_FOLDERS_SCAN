"""Integrated terminal tab — multi-tab PTY console using pywinpty."""
import customtkinter as ctk
from config.settings import (
    PALETTE, FONT_MONO, DEFAULT_TERM_FONT_SIZE, TERMINAL_PROFILES,
)
from core.pty_terminal import PtyTerminalBridge
from ui.components.toast import ToastNotification


class InteractiveTerminalTab(ctk.CTkFrame):
    """A single terminal console embedded in a CTkTabview tab."""

    def __init__(self, parent, profile_name: str = "PowerShell",
                 is_admin: bool = False, toast: ToastNotification | None = None,
                 **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self.profile_name = profile_name
        profile = TERMINAL_PROFILES.get(profile_name, dict(list(TERMINAL_PROFILES.values())[0]))
        self.profile = profile
        self.is_admin = is_admin
        self.toast = toast

        bg = profile.get("color_bg", PALETTE["terminal_bg"])
        fg = profile.get("color_fg", PALETTE["text_main"])
        self.configure(fg_color=bg)

        self.textbox = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family=FONT_MONO, size=DEFAULT_TERM_FONT_SIZE),
            fg_color=bg, text_color=fg, wrap="none",
        )
        self.textbox.pack(fill="both", expand=True, padx=3, pady=3)
        self.textbox.configure(state="normal")

        cmd = profile.get("cmd", ["cmd.exe"])
        self.engine = PtyTerminalBridge(cmd, is_admin=is_admin)
        self.engine.start()

        # Enable VT processing for native Windows consoles
        PtyTerminalBridge.enable_vt_mode()

        self._poll_id: str | None = None
        self._start_polling()

        # Forward keyboard input
        self.textbox.bind("<Key>", self._on_key)
        self.textbox.bind("<Return>", self._on_enter)

    def _start_polling(self) -> None:
        if self._poll_id is not None:
            self.after_cancel(self._poll_id)
        self._poll_id = self.after(50, self._poll_output)

    def _poll_output(self) -> None:
        while not self.engine.output_queue.empty():
            data = self.engine.output_queue.get()
            self.textbox.insert("end", data)
            self.textbox.see("end")
        self._poll_id = self.after(50, self._poll_output)

    def _on_key(self, event) -> None:
        """Forward key presses to the PTY."""
        if event.keysym == "BackSpace":
            self.engine.write_input("\x7f")
        elif event.keysym == "Tab":
            self.engine.write_input("\t")
        elif event.keysym == "Escape":
            self.engine.write_input("\x1b")
        elif event.keysym == "Up":
            self.engine.write_input("\x1b[A")
        elif event.keysym == "Down":
            self.engine.write_input("\x1b[B")
        elif event.keysym == "Right":
            self.engine.write_input("\x1b[C")
        elif event.keysym == "Left":
            self.engine.write_input("\x1b[D")
        elif event.keysym == "Home":
            self.engine.write_input("\x1b[H")
        elif event.keysym == "End":
            self.engine.write_input("\x1b[F")
        elif event.keysym == "Delete":
            self.engine.write_input("\x1b[3~")
        elif event.keysym == "Return":
            pass  # handled in _on_enter
        elif event.char:
            self.engine.write_input(event.char)

    def _on_enter(self, event) -> None:
        self.engine.write_input("\r")
        self.textbox.configure(state="normal")
        return "break"

    def write_text(self, text: str) -> None:
        self.textbox.insert("end", text)
        self.textbox.see("end")

    def destroy(self) -> None:
        if self._poll_id is not None:
            self.after_cancel(self._poll_id)
        self.engine.terminate()
        super().destroy()


class TabTerminal(ctk.CTkFrame):
    """Multi-profile embedded terminal container."""

    def __init__(self, parent, toast: ToastNotification | None = None, **kwargs) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.toast = toast
        self.term_tabs: dict[str, InteractiveTerminalTab] = {}

        # Toolbar for adding/removing terminal tabs
        toolbar = ctk.CTkFrame(self, fg_color="transparent", height=42)
        toolbar.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkLabel(
            toolbar, text="Terminal Profiles:",
            font=("Consolas", 11), text_color=PALETTE["text_sub"],
        ).pack(side="left", padx=(8, 4))

        profile_values = list(TERMINAL_PROFILES.keys())
        self.combo_profile = ctk.CTkComboBox(
            toolbar, values=profile_values, width=140,
            fg_color=PALETTE["bg_dark"], border_color=PALETTE["neutral"],
            button_color=PALETTE["accent"],
        )
        self.combo_profile.set(profile_values[0])
        self.combo_profile.pack(side="left", padx=6)

        btn_add = ctk.CTkButton(
            toolbar, text="\U00002795 Add Session", width=120,
            command=self._add_terminal_tab,
        )
        btn_add.pack(side="left", padx=6)

        self.tabs_close_btn_holder: dict[str, ctk.CTkButton] = {}

        self.term_tabview = ctk.CTkTabview(self)
        self.term_tabview.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._add_terminal_tab(profile_name=self.combo_profile.get())

    def _add_terminal_tab(self, profile_name: str | None = None) -> None:
        profile_name = profile_name or self.combo_profile.get()
        p_info = TERMINAL_PROFILES.get(profile_name, TERMINAL_PROFILES["PowerShell"])
        tab_title = f"{p_info.get('icon', '💻')} {profile_name}"
        tab_frame = self.term_tabview.add(tab_title)
        term = InteractiveTerminalTab(
            tab_frame, profile_name, toast=self.toast,
        )
        term.pack(fill="both", expand=True)
        self.term_tabs[tab_title] = term

    def destroy(self) -> None:
        for tab in self.term_tabs.values():
            try:
                tab.engine.terminate()
            except Exception:
                pass
        super().destroy()
