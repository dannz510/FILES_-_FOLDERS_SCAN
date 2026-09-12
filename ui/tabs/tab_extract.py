"""Subfolder extraction tab — export a directory subtree to Markdown / JSON."""
import customtkinter as ctk
from typing import Callable

from config.settings import PALETTE, FONT_FAMILY, DEFAULT_OUTPUT_FILE
from core.exporter import MarkdownExporter


class TabExtract(ctk.CTkFrame):
    def __init__(self, parent, on_extract_callback: Callable | None = None,
                 exporter: MarkdownExporter | None = None, **kwargs) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.on_extract_callback = on_extract_callback
        self.exporter = exporter or MarkdownExporter()

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            container,
            text="📦 Trích xuất cấu trúc thư mục con thành file Markdown độc lập.",
            text_color=PALETTE["text_sub"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        ).pack(anchor="w", pady=(0, 15))

        self.entry_subfolder = ctk.CTkEntry(
            container,
            placeholder_text="Nhập đường dẫn tương đối (ví dụ: 02_Network_Security)…",
            fg_color=PALETTE["bg_dark"], border_color=PALETTE["neutral"],
            text_color=PALETTE["text_main"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=12), height=38,
        )
        self.entry_subfolder.pack(fill="x", pady=(0, 15))

        btn_run = ctk.CTkButton(
            container, text="🚀 Extract Details File",
            command=self._handle_run,
            fg_color=PALETTE["accent"], hover_color=PALETTE["accent_hover"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"), height=40,
        )
        btn_run.pack(anchor="w")

    def _handle_run(self) -> None:
        folder_input = self.entry_subfolder.get().strip()
        if folder_input and self.on_extract_callback:
            self.on_extract_callback(folder_input)
