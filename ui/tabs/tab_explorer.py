"""Virtualized TreeView tab with lazy-loading of directory nodes.

Only the top-level and currently-expanded nodes are rendered, so the tree
can handle vaults with tens of thousands of files without UI lag.
"""
import os
import tkinter as tk
from pathlib import Path
from datetime import datetime
from tkinter import ttk
import customtkinter as ctk

from core.database import FTSIndexEngine, VaultItem
from config.settings import PALETTE, FONT_FAMILY, PALETTE_DARK, PALETTE_LIGHT, PALETTE_CYBERPUNK
from utils.os_utils import open_local_path, get_formatted_size
from ui.styles import apply_treeview_style
from config.theme import ThemeManager


class TabExplorer(ctk.CTkFrame):
    def __init__(self, master, db_engine: FTSIndexEngine | None = None,
                 theme_manager: ThemeManager | None = None, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db_engine = db_engine
        self.theme_manager = theme_manager or apply_treeview_style()
        self._expanded_dirs: set[str] = set()
        self._build_ui()

    def _build_ui(self) -> None:
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            top_bar, text="🗂️ Vault Structure (Lazy-Loaded)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=PALETTE["text_sub"],
        ).pack(side="left")

        btn_refresh = ctk.CTkButton(
            top_bar, text="🔄 Refresh", width=90,
            fg_color=PALETTE["neutral"], hover_color=PALETTE["card_hover"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            command=self._on_refresh,
        )
        btn_refresh.pack(side="right")

        tree_container = ctk.CTkFrame(self, fg_color="transparent")
        tree_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(
            tree_container,
            columns=("size", "modified"),
            show="tree headings",
            selectmode="browse",
        )
        self.tree.heading("#0", text="Name / Directory", anchor="w")
        self.tree.heading("size", text="Size", anchor="e")
        self.tree.heading("modified", text="Date Modified", anchor="center")
        self.tree.column("#0", width=420, minwidth=200, stretch=True)
        self.tree.column("size", width=120, minwidth=80, anchor="e", stretch=False)
        self.tree.column("modified", width=180, minwidth=140, anchor="center", stretch=False)

        self.vsb = ctk.CTkScrollbar(tree_container)
        self.tree.configure(yscrollcommand=self.vsb.set)
        self.vsb.configure(command=self.tree.yview)

        self.tree.pack(side="left", fill="both", expand=True)
        self.vsb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<<TreeviewOpen>>", self._on_node_expand)

    # ------------------------------------------------------------------ #
    # Data population (virtualized / lazy)
    # ------------------------------------------------------------------ #
    def clear(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self._expanded_dirs.clear()

    def get_node_id(self, path: str) -> str:
        """Return the tree item ID for *path*, or empty string if not found."""
        return self._find_node_by_path("", path)

    def _find_node_by_path(self, parent_id: str, target_path: str) -> str:
        for child_id in self.tree.get_children(parent_id):
            val = self.tree.item(child_id, "values")
            if len(val) >= 3 and val[2] == target_path:
                return child_id
            result = self._find_node_by_path(child_id, target_path)
            if result:
                return result
        return ""

    def populate_root(self, root_path: Path) -> None:
        """Load top-level children of *root_path* into the tree."""
        self.clear()

        root_str = str(root_path)
        try:
            stat = root_path.stat()
            mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        except OSError:
            mod_time = "--"

        root_id = self.tree.insert(
            "", 0, text=f"📂 {root_path.name}",
            values=(get_formatted_size(root_path.stat().st_size if root_path.exists() else 0),
                    mod_time, root_str),
        )

        self._load_children(root_id, root_path)
        self.tree.item(root_id, open=True)

    def _load_children(self, parent_id: str, dir_path: Path) -> None:
        """Lazy-load children of *dir_path* from the filesystem or DB."""
        self.tree.delete(*self.tree.get_children(parent_id))

        parent_str = str(dir_path)

        # If DB is available, use it; otherwise fall back to os.scandir
        if self.db_engine and self.db_engine.item_count > 0:
            children = self.db_engine.get_children(parent_str)
            for child in children:
                self._insert_item(parent_id, child)
        else:
            self._scan_and_insert(parent_id, dir_path)

        # Add a dummy "loading" child for directories so the expand arrow shows
        for child_id in self.tree.get_children(parent_id):
            vals = self.tree.item(child_id, "values")
            if len(vals) >= 4 and vals[3] == "folder":
                # Add placeholder to show expand arrow
                self.tree.insert(child_id, "end", iid=f"__placeholder_{child_id}")

    def _scan_and_insert(self, parent_id: str, dir_path: Path) -> None:
        try:
            entries = sorted(os.scandir(dir_path), key=self._sort_key)
        except (PermissionError, OSError):
            return

        for entry in entries:
            if entry.name.startswith("."):
                continue
            entry_path = Path(entry.path)
            try:
                stat = entry_path.stat()
            except OSError:
                stat = None

            is_dir = entry.is_dir(follow_symlinks=False)
            if is_dir:
                text = f"📂 {entry.name}"
                size = "--"
                self.tree.insert(
                    parent_id, "end", text=f" {text}",
                    values=(
                        size,
                        datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S") if stat else "--",
                        str(entry_path), "folder",
                    ),
                )
            else:
                ext = entry_path.suffix.lower()
                if ext in {".md", ".txt", ".py", ".cpp", ".json", ".yaml", ".yml",
                           ".sh", ".ps1", ".pdf", ".epub", ".bat", ".rar", ".7z"}:
                    self.tree.insert(
                        parent_id, "end", text=f"📄 {entry.name}",
                        values=(
                            get_formatted_size(stat.st_size) if stat else "--",
                            datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S") if stat else "--",
                            str(entry_path), "file",
                        ),
                    )

    def _insert_item(self, parent_id: str, item: dict) -> None:
        icon = "📂" if item["type"] == "folder" else "📄"
        is_folder = item["type"] == "folder"

        # Format modified time
        mod_val = item.get("modified", 0)
        try:
            mod_str = datetime.fromtimestamp(mod_val).strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, OSError):
            mod_str = "--"

        size_str = "--"
        if not is_folder:
            size_str = get_formatted_size(item.get("size", 0))

        iid = f"item_{item['path'].__hash__()}" if not hasattr(item, 'path') else item['path'][:100]
        self.tree.insert(
            parent_id, "end",
            text=f" {icon} {item['name']}",
            values=(size_str, mod_str, item["path"], item["type"]),
        )

    @staticmethod
    def _sort_key(entry) -> tuple:
        try:
            is_dir = entry.is_dir(follow_symlinks=False)
        except OSError:
            is_dir = False
        return (not is_dir, entry.name.lower())

    # ------------------------------------------------------------------ #
    # Event handlers
    # ------------------------------------------------------------------ #
    def _on_node_expand(self, event: tk.Event) -> None:
        """Lazy-load children when a node is expanded."""
        node_id = self.tree.focus()
        if not node_id:
            return
        vals = self.tree.item(node_id, "values")
        if len(vals) < 4:
            return
        path_str = vals[2]
        item_type = vals[3]

        # Remove placeholder children
        for child in list(self.tree.get_children(node_id)):
            if child.startswith("__placeholder_"):
                self.tree.delete(child)

        # If not yet expanded, load real children
        if path_str not in self._expanded_dirs and item_type == "folder":
            self._load_children(node_id, Path(path_str))
            self._expanded_dirs.add(path_str)

    def _on_refresh(self) -> None:
        root_path_str = self.tree.item(self.tree.get_children()[0], "values")[2] if self.tree.get_children() else ""
        if root_path_str:
            self.populate_root(Path(root_path_str))

    def _on_double_click(self, event: tk.Event) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        vals = self.tree.item(selected[0], "values")
        if len(vals) >= 3:
            target = Path(vals[2])
            if target.exists():
                open_local_path(target)

    # ------------------------------------------------------------------ #
    # Theme
    # ------------------------------------------------------------------ #
    def update_theme_style(self, mode: str) -> None:
        palette = PALETTE_LIGHT if mode == "Light" else PALETTE_DARK
        style = ttk.Style()
        style.configure(
            "Treeview",
            background=palette["card_bg"],
            foreground=palette["text_main"],
            fieldbackground=palette["card_bg"],
            rowheight=28,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=palette.get("heading_bg", palette["bg_dark"]),
            foreground=palette.get("text_sub", palette["text_main"]),
            font=(FONT_FAMILY, 10, "bold"),
        )
        style.map("Treeview", background=[("selected", palette["accent"])],
                  foreground=[("selected", "#FFFFFF")])
