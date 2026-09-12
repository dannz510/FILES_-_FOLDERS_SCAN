import customtkinter as ctk
from config.settings import PALETTE, FONT_FAMILY


class ToastNotification:
    """Transient toast popup (auto-dismiss, click-to-dismiss)."""

    def __init__(self, parent, duration: int = 2500, corner_radius: int = 8) -> None:
        self.parent = parent
        self.duration = duration
        self.corner_radius = corner_radius
        self._active: list[ctk.CTkToplevel] = []

    def show(self, message: str, title: str = "Notification",
             severity: str = "info") -> None:
        toast = ctk.CTkToplevel(self.parent)
        toast.overrideredirect(True)
        toast.configure(fg_color=self._severity_color(severity))
        toast.attributes("-topmost", True)
        toast.transient(self.parent)

        toast_width = min(340, max(220, len(message) * 9 + 60))
        toast_height = 75
        toast.geometry(f"{toast_width}x{toast_height}+0+0")

        x = self.parent.winfo_rootx() + 20
        y = self.parent.winfo_rooty() + 40
        toast.geometry(f"+{x}+{y}")

        title_label = ctk.CTkLabel(
            toast, text=title,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color="#FFFFFF",
        )
        title_label.pack(anchor="w", padx=12, pady=(12, 2))

        msg_label = ctk.CTkLabel(
            toast, text=message,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color="#E0E0E0",
            wraplength=toast_width - 24,
            justify="left",
        )
        msg_label.pack(anchor="w", padx=12, pady=(0, 12))

        self._active.append(toast)

        def _dismiss() -> None:
            if toast in self._active:
                self._active.remove(toast)
            toast.after(0, toast.destroy)

        toast.after(self.duration, _dismiss)
        toast.bind("<Button-1>", lambda e: _dismiss())

    @staticmethod
    def _severity_color(severity: str) -> str:
        mapping = {
            "info": "#1E293B",
            "success": "#10B981",
            "warning": "#F59E0B",
            "error": "#EF4444",
        }
        return mapping.get(severity, mapping["info"])


class StatusBar(ctk.CTkFrame):
    """Thin status bar that can show a message + optional spinner indicator."""

    def __init__(self, parent, **kwargs) -> None:
        super().__init__(parent, fg_color=PALETTE["card_bg"], height=32, **kwargs)
        self.pack_propagate(False)

        self.lbl_status = ctk.CTkLabel(
            self, text="Ready",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=PALETTE["text_sub"],
            anchor="w",
        )
        self.lbl_status.pack(side="left", padx=12, pady=2)

        self.lbl_spinner = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=PALETTE["accent"],
            anchor="e",
        )
        self.lbl_spinner.pack(side="right", padx=12, pady=2)

        self._spin_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._spin_idx = 0
        self._spinning = False

    def set_status(self, text: str, color: str | None = None) -> None:
        self.lbl_status.configure(text=text, text_color=color or PALETTE["text_sub"])
        if self.parent:
            self.parent.update_idletasks()

    def set_spinner(self, active: bool, label: str = "") -> None:
        self._spinning = active
        if active:
            self._spin_step()
        else:
            self.lbl_spinner.configure(text=label)

    def _spin_step(self) -> None:
        if not self._spinning:
            return
        self.lbl_spinner.configure(text=f"{self._spin_chars[self._spin_idx]} Processing…")
        self._spin_idx = (self._spin_idx + 1) % len(self._spin_chars)
        self.after(80, self._spin_step)
