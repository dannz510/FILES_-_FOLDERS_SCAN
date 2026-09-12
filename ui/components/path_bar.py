import customtkinter as ctk
from pathlib import Path
from config.settings import PALETTE, FONT_FAMILY
from utils.os_utils import open_local_path
from utils.logger import AppLogger

logger = AppLogger("path_bar")


class PathBar(ctk.CTkFrame):
    """Dynamic Vault Root path selector with entry field and file-dialog trigger."""

    def __init__(self, master, on_path_change: callable | None = None, **kwargs) -> None:
        kwargs.pop("fg_color", None)
        kwargs.pop("corner_radius", None)
        super().__init__(
            master,
            fg_color=PALETTE["card_bg"],
            corner_radius=10,
            **kwargs,
        )
        self.on_path_change = on_path_change

        lbl = ctk.CTkLabel(
            self, text="Vault Root:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=PALETTE["text_sub"],
        )
        lbl.pack(side="left", padx=(15, 10), pady=10)

        self.entry_path = ctk.CTkEntry(
            self,
            fg_color=PALETTE["bg_dark"],
            text_color=PALETTE["text_main"],
            border_color=PALETTE["neutral"],
            border_width=1,
            corner_radius=6,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            height=32,
        )
        default_path = str(Path.cwd())
        self.entry_path.insert(0, default_path)
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=10)

        self.btn_browse = ctk.CTkButton(
            self, text="Browse", width=80,
            fg_color=PALETTE["neutral"], hover_color=PALETTE["card_hover"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            command=self._handle_browse,
        )
        self.btn_browse.pack(side="right", padx=(0, 15), pady=10)

    def _handle_browse(self) -> None:
        selected = ctk.filedialog.askdirectory(initialdir=self.get_path())
        if selected:
            self.set_path(selected)
            if self.on_path_change:
                self.on_path_change(selected)

    def get_path(self) -> str:
        return self.entry_path.get().strip()

    def set_path(self, path_str: str) -> None:
        self.entry_path.delete(0, "end")
        self.entry_path.insert(0, str(path_str))

    def open_vault_folder(self) -> None:
        """Open the currently-typed vault path in the OS file explorer."""
        p = Path(self.get_path())
        open_local_path(p)

    def validate_path(self) -> Path | None:
        """Return a resolved Path if valid, else None."""
        raw = self.get_path()
        if not raw:
            return None
        p = Path(raw)
        return p if p.exists() else None
