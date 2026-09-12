import customtkinter as ctk
from config.settings import PALETTE, FONT_FAMILY


class Sidebar(ctk.CTkFrame):
    """Navigation sidebar with brand header, action buttons, and status badge."""

    def __init__(self, master=None, parent=None, width: int = 230,
                 on_build_index: callable | None = None,
                 on_scan: callable | None = None,
                 on_open_folder: callable | None = None,
                 **kwargs) -> None:
        target = master if master is not None else parent
        kwargs.pop("corner_radius", None)
        kwargs.pop("fg_color", None)

        super().__init__(
            target, width=width, corner_radius=0,
            fg_color=PALETTE["card_bg"], **kwargs,
        )

        self.on_build_index = on_build_index
        self.on_scan = on_scan
        self.on_open_folder = on_open_folder

        self._build_ui()

    def _build_ui(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(24, 18))

        ctk.CTkLabel(
            header, text="⚡ PENTEST VAULT",
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
            text_color=PALETTE["accent"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            header, text="Knowledge Base Command Center",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=PALETTE["text_sub"],
        ).pack(anchor="w", pady=(2, 0))

        btns = [
            ("🔍 Fast Scan Vault", self.on_scan, PALETTE["accent"], PALETTE["accent_hover"]),
            ("📝 Build Full Index", self.on_build_index, PALETTE["neutral"], PALETTE["card_hover"]),
            ("📂 Open Folder", self.on_open_folder, PALETTE["neutral"], PALETTE["card_hover"]),
            ("🔄 Real-time Sync", None, PALETTE["neutral"], PALETTE["card_hover"]),
            ("🗑️ Clear Cache", None, PALETTE["danger"], "#EF4444"),
        ]
        for text, cmd, fg, hover in btns:
            btn = ctk.CTkButton(
                self, text=text, command=cmd,
                fg_color=fg, hover_color=hover,
                text_color=PALETTE["text_main"],
                font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
                height=38, corner_radius=8,
            )
            btn.pack(fill="x", padx=18, pady=4)

        self.lbl_status = ctk.CTkLabel(
            self, text="● SYSTEM READY",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=PALETTE["success"],
        )
        self.lbl_status.pack(side="bottom", pady=(8, 8), padx=18, anchor="w")

        self.lbl_version = ctk.CTkLabel(
            self, text="v2.0.0 | Cyber Center",
            font=ctk.CTkFont(family=FONT_FAMILY, size=9),
            text_color=PALETTE["text_dim"],
        )
        self.lbl_version.pack(side="bottom", pady=2, padx=18, anchor="w")

    def set_status(self, text: str, color: str | None = None) -> None:
        self.lbl_status.configure(
            text=f"● {text}", text_color=color or PALETTE["success"],
        )

    def update_theme(self, palette: dict) -> None:
        self.configure(fg_color=palette["card_bg"])
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkLabel) and child.cget("text") and "SYSTEM" in child.cget("text"):
                child.configure(text_color=palette["success"])
            elif isinstance(child, ctk.CTkLabel):
                child.configure(text_color=palette.get("text_sub", PALETTE["text_sub"]))
