"""Live search tab — FTS5-powered instant search results."""
import customtkinter as ctk
from pathlib import Path
from typing import Callable

from core.database import FTSIndexEngine
from config.settings import PALETTE, FONT_FAMILY, FONT_MONO
from utils.os_utils import open_local_path, encode_path_for_obsidian, get_formatted_size


class TabSearch(ctk.CTkFrame):
    def __init__(self, parent, db_engine: FTSIndexEngine | None = None,
                 on_search_trigger: Callable | None = None,
                 on_log_callback: Callable | None = None, **kwargs) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.db_engine = db_engine
        self.on_search_trigger = on_search_trigger
        self.on_log_callback = on_log_callback
        self.search_timer: str | None = None
        self._max_results = 100
        self._build_ui()

    def _build_ui(self) -> None:
        search_top = ctk.CTkFrame(self, fg_color="transparent")
        search_top.pack(fill="x", padx=10, pady=(10, 5))

        self.entry_search = ctk.CTkEntry(
            search_top,
            placeholder_text="T\u00ed\u006d ch\u00e1 \u0066 file, extension (.pdf, .py), \u0111\u01b0\u1eddng d\u1ea5n\u2026",
            fg_color=PALETTE["bg_dark"], border_color=PALETTE["neutral"],
            text_color=PALETTE["text_main"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=12), height=34,
        )
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_search.bind("<KeyRelease>", self._on_key_release)
        self.entry_search.bind("<Control-a>", lambda e: "break")
        self.entry_search.focus()

        btn_clear = ctk.CTkButton(
            search_top, text="\U0001f6d4 Clear", width=80, command=self.clear_search,
            fg_color=PALETTE["neutral"], hover_color=PALETTE["card_hover"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        btn_clear.pack(side="right")

        stats_bar = ctk.CTkFrame(self, fg_color="transparent")
        stats_bar.pack(fill="x", padx=10, pady=(0, 4))
        self.lbl_stats = ctk.CTkLabel(
            stats_bar, text="Nhap tu khoa de tim kiem...",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=PALETTE["text_dim"], anchor="w",
        )
        self.lbl_stats.pack(side="left")

        self.scroll_results = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_results.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _on_key_release(self, event=None) -> None:
        if self.search_timer is not None:
            self.after_cancel(self.search_timer)
        query = self.entry_search.get().strip().lower()
        if not query:
            self._clear_results()
            return
        self.search_timer = self.after(250, lambda: self._execute_search(query))

    def _execute_search(self, query: str) -> None:
        self.search_timer = None
        if not query:
            return

        if self.on_log_callback:
            self.on_log_callback(f"Searching: {query}")

        if self.db_engine and self.db_engine.item_count > 0:
            matches = self.db_engine.search(query, limit=self._max_results)
        else:
            matches = []

        self._render_results(matches, query)

        if self.on_log_callback:
            self.on_log_callback(f"Found {len(matches)} results for '{query}'")

    def set_db_engine(self, db_engine: FTSIndexEngine) -> None:
        self.db_engine = db_engine

    def render_results(self, matches: list[dict], query: str = "") -> None:
        self._render_results(matches, query)

    def _render_results(self, matches: list[dict], query: str = "") -> None:
        for w in self.scroll_results.winfo_children():
            w.destroy()

        if not matches:
            ctk.CTkLabel(
                self.scroll_results, text="No results found.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                text_color=PALETTE["text_dim"],
            ).pack(pady=20)
            return

        self.lbl_stats.configure(
            text=f"Found {len(matches)} results for '{query}'",
            text_color=PALETTE["accent"],
        )

        for item in matches[:self._max_results]:
            self._render_item(item)

    def _render_item(self, item: dict) -> None:
        icon = "📂" if item["type"] == "folder" else "📄"

        card = ctk.CTkFrame(self.scroll_results, fg_color=PALETTE["card_bg"], corner_radius=6)
        card.pack(fill="x", pady=2)

        ctk.CTkLabel(
            card, text=icon, font=ctk.CTkFont(size=14),
        ).pack(side="left", padx=(8, 4))

        name_label = ctk.CTkLabel(
            card, text=item["name"],
            font=ctk.CTkFont(family=FONT_FAMILY, weight="bold"),
            text_color=PALETTE["text_main"],
            anchor="w",
        )
        name_label.pack(side="left", padx=4, fill="x", expand=True)

        ext = item.get("ext", "")
        if ext:
            ext_label = ctk.CTkLabel(
                card, text=ext.upper(),
                font=ctk.CTkFont(family=FONT_MONO, size=10),
                text_color=PALETTE["accent"],
            )
            ext_label.pack(side="right", padx=(0, 4))

        size_val = item.get("size", 0)
        if size_val:
            size_label = ctk.CTkLabel(
                card, text=get_formatted_size(size_val),
                font=ctk.CTkFont(family=FONT_MONO, size=10),
                text_color=PALETTE["text_sub"],
            )
            size_label.pack(side="right", padx=(0, 4))

        def _open(p=item["path"]):
            open_local_path(Path(p))

        def _copy(p=item["path"], n=item["name"]):
            md_link = f"[{n}]({encode_path_for_obsidian(str(Path(p).resolve()))})"
            self.clipboard_clear()
            self.clipboard_append(md_link)
            if self.on_log_callback:
                self.on_log_callback(f"Copied Obsidian link: {md_link}")

        btn_open = ctk.CTkButton(
            card, text="Open", width=60, height=24,
            fg_color=PALETTE["neutral"], hover_color=PALETTE["card_hover"],
            font=ctk.CTkFont(size=10), command=_open,
        )
        btn_open.pack(side="right", padx=(0, 4), pady=4)

        btn_copy = ctk.CTkButton(
            card, text="Copy Link", width=70, height=24,
            fg_color=PALETTE["accent"], hover_color=PALETTE["accent_hover"],
            font=ctk.CTkFont(size=10), command=_copy,
        )
        btn_copy.pack(side="right", padx=(0, 8), pady=4)

    def _clear_results(self) -> None:
        for w in self.scroll_results.winfo_children():
            w.destroy()
        self.lbl_stats.configure(text="Enter search keywords...")

    def clear_search(self) -> None:
        self.entry_search.delete(0, "end")
        self._clear_results()
