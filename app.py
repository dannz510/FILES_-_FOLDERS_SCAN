"""Application entry point — High-Performance Pentest Vault & Command Center v2.0

Architecture
------------
• GUI thread  → renders widgets, polls ``ui_queue`` for worker updates
• Engine threads → scanning, indexing, terminal I/O (daemon threads)
• IPC layer → ``queue.Queue`` channels carry messages from workers → GUI

Run::
    python app.py
"""
import sys
import os
import threading
import traceback
import queue
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def get_resource_path(relative_path: str) -> Path:
    
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / relative_path
    return PROJECT_ROOT / relative_path

# Flush stdout/stderr immediately for real-time console logs
from utils.logger import flush_streams, AppLogger
flush_streams()
logger = AppLogger("app")

import customtkinter as ctk

from config.settings import (
    PALETTE, PALETTE_DARK, PALETTE_LIGHT, PALETTE_CYBERPUNK,
    FONT_FAMILY, FONT_MONO, ALLOWED_EXTENSIONS,
    DEFAULT_OUTPUT_FILE, TERMINAL_PROFILES, THEME_REGISTRY,
)
from config.theme import ThemeManager

from core.database import FTSIndexEngine
from core.scanner import FastVaultScanner
from core.watcher import VaultWatcher
from core.exporter import MarkdownExporter, JSONExporter
from core.pty_terminal import PtyTerminalBridge

from ui.styles import apply_treeview_style, apply_all_styles
from ui.components.sidebar import Sidebar
from ui.components.path_bar import PathBar
from ui.components.metric_card import MetricCard
from ui.components.status_bar import SystemStatusBar
from ui.components.toast import ToastNotification

from ui.tabs.tab_explorer import TabExplorer
from ui.tabs.tab_search import TabSearch
from ui.tabs.tab_extract import TabExtract
from ui.tabs.tab_terminal import TabTerminal
from ui.tabs.tab_settings import TabSettings


class PentestIndexerApp(ctk.CTk):
    """Main application class — orchestrates all subsystems."""

    def __init__(self) -> None:
        super().__init__()

        logger.info("=" * 60)
        logger.info("Starting Pentest Vault & Command Center v2.0")
        logger.info("=" * 60)

        # ---- Async event loop infra -----------------------------------
        self.ui_queue: queue.Queue = queue.Queue()
        self._resize_timer: str | None = None

        # ---- Theme & style --------------------------------------------
        self.theme_manager = ThemeManager("Dark")
        self.apply_theme_palette(self.theme_manager.palette)
        self.tree_style_tm = apply_treeview_style(self.theme_manager.palette)
        apply_all_styles(self.tree_style_tm)

        # ---- Core engines --------------------------------------------
        self.db_engine = FTSIndexEngine()
        self.scanner = FastVaultScanner(ALLOWED_EXTENSIONS, self.db_engine)
        self.exporter = MarkdownExporter(ALLOWED_EXTENSIONS)
        self.json_exporter = JSONExporter(ALLOWED_EXTENSIONS)
        self.watcher: VaultWatcher | None = None

        # ---- Window config -------------------------------------------
        self.title("🛡️ Pentest Vault — Knowledge Base & Command Center")
        self.geometry("1366x820")
        self.minsize(1024, 700)
        self._apply_palette_bg()

        # ---- App Icon ------------------------------------------------
        icon_ico = get_resource_path("assets/app_logo.ico")
        if icon_ico.exists():
            self.iconbitmap(str(icon_ico))

        # Toast notifier
        self.toast = ToastNotification(self)

        # ---- Build layout --------------------------------------------
        self._build_layout()
        self._build_menu()

        # Bind events
        self.bind("<Configure>", self._on_window_resize)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Start UI queue processor
        self._process_ui_queue()
        self._start_watcher_if_needed()
        self.after(100, self.status_bar.start_monitoring)

        logger.info("Application UI initialised successfully")

    # ==================================================================
    # Theme management
    # ==================================================================
    def apply_theme_palette(self, palette: dict) -> None:
        self._palette = palette

    def _apply_palette_bg(self) -> None:
        bg = self._palette["bg_dark"]
        self.configure(fg_color=bg)

    def _on_theme_changed(self, mode: str) -> None:
        """Callback fired by TabSettings when the user picks a new theme."""
        if mode in THEME_REGISTRY:
            self.theme_manager.switch_to(mode)
        self.apply_theme_palette(self.theme_manager.palette)
        self._apply_palette_bg()
        ctk.set_appearance_mode("Light" if mode == "Light" else "Dark")

        # Update all UI components
        self.status_bar.update_theme(self.theme_manager.palette)
        self.sidebar.update_theme(self.theme_manager.palette)
        self.tab_explorer.update_theme_style(mode)
        self.tab_terminal.configure(fg_color=self.theme_manager.palette["bg_dark"])

    # ==================================================================
    # Layout
    # ==================================================================
    def _build_menu(self) -> None:
        import tkinter as tk
        menubar = tk.Menu(self, tearoff=0)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Vault Folder", command=self._open_browse)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        scan_menu = tk.Menu(menubar, tearoff=0)
        scan_menu.add_command(label="Fast Scan",
                              command=lambda: self._run_async("Fast Scan", self.run_scan))
        scan_menu.add_command(label="Re-index",
                              command=lambda: self._run_async("Re-index", self.run_scan))
        scan_menu.add_separator()
        scan_menu.add_command(label="Export Markdown",
                              command=lambda: self._run_async("Export MD", self._export_md))
        scan_menu.add_command(label="Export JSON",
                              command=lambda: self._run_async("Export JSON", self._export_json))
        menubar.add_cascade(label="Actions", menu=scan_menu)

        self.config(menu=menubar)

    def _build_layout(self) -> None:
        # Top System Status Bar
        self.status_bar = SystemStatusBar(self)
        self.status_bar.pack(fill="x", padx=10, pady=(10, 0))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, pady=(10, 0))

        # Sidebar
        self.sidebar = Sidebar(
            content,
            on_build_index=lambda: self._run_async("Build Index", self.run_generate_index),
            on_scan=lambda: self._run_async("Fast Scan", self.run_scan),
            on_open_folder=lambda: self._run_async("Open Folder", self.path_bar.open_vault_folder),
        )
        self.sidebar.pack(side="left", fill="y")

        # Main panel
        main_panel = ctk.CTkFrame(content, fg_color="transparent")
        main_panel.pack(side="right", fill="both", expand=True, padx=(10, 20), pady=0)

        # Path Bar
        self.path_bar = PathBar(
            main_panel,
            on_path_change=lambda p: self._on_path_changed(p),
        )
        self.path_bar.pack(fill="x", pady=(0, 10))

        # Metric cards
        metrics = ctk.CTkFrame(main_panel, fg_color="transparent")
        metrics.pack(fill="x", pady=(0, 10))
        metrics.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_dirs = MetricCard(metrics, "Folders Detected", "0", "📁")
        self.card_dirs.grid(row=0, column=0, padx=4, sticky="ew")

        self.card_files = MetricCard(metrics, "Valid Files", "0", "📄")
        self.card_files.grid(row=0, column=1, padx=4, sticky="ew")

        self.card_cache = MetricCard(metrics, "Search Index", "Empty", "🧠")
        self.card_cache.grid(row=0, column=2, padx=4, sticky="ew")

        self.card_watcher = MetricCard(metrics, "Real-time Sync", "Paused", "🔄")
        self.card_watcher.grid(row=0, column=3, padx=4, sticky="ew")

        # Tabview
        self.tabview = ctk.CTkTabview(
            main_panel,
            fg_color=self._palette["card_bg"],
            segmented_button_fg_color=self._palette["bg_dark"],
            segmented_button_selected_color=self._palette["accent"],
            segmented_button_selected_hover_color=self._palette["accent_hover"],
            segmented_button_unselected_color=self._palette["card_bg"],
            segmented_button_unselected_hover_color=self._palette["card_hover"],
        )
        self.tabview.pack(fill="both", expand=True)

        # Explorer tab
        self.tab_explorer = TabExplorer(
            self.tabview.add("🌲 Vault Explorer"),
            db_engine=self.db_engine,
            theme_manager=self.theme_manager,
        )
        self.tab_explorer.pack(fill="both", expand=True)

        # Search tab
        self.tab_search = TabSearch(
            self.tabview.add("🔍 Live Search"),
            db_engine=self.db_engine,
            on_search_trigger=self.handle_search,
            on_log_callback=self._toast_log,
        )
        self.tab_search.pack(fill="both", expand=True)

        # Extract tab
        self.tab_extract = TabExtract(
            self.tabview.add("📂 Subfolder Exporter"),
            on_extract_callback=lambda sub: self._run_async(
                "Extract Subfolder", lambda: self.run_extract(sub)
            ),
            exporter=self.exporter,
        )
        self.tab_extract.pack(fill="both", expand=True)

        # Terminal tab
        self.tab_terminal = TabTerminal(
            self.tabview.add("💻 Command Terminal"),
            toast=self.toast,
        )
        self.tab_terminal.pack(fill="both", expand=True)

        # Settings tab
        self.tab_settings = TabSettings(
            self.tabview.add("⚙️ General Settings"),
            theme_manager=self.theme_manager,
            on_theme_change_callback=self._on_theme_changed,
            on_save_callback=self._on_settings_saved,
        )
        self.tab_settings.pack(fill="both", expand=True)

    # ==================================================================
    # Async execution helpers
    # ==================================================================
    def _run_async(self, action_name: str, task_func: callable,
                   on_done: callable | None = None) -> None:
        """Run *task_func* in a daemon thread, catching + reporting errors."""
        def _wrapper() -> None:
            try:
                logger.info("Executing async task: %s", action_name)
                result = task_func()
                self._enqueue(lambda: self._on_task_done(action_name, result, on_done))
            except Exception:
                tb = traceback.format_exc()
                logger.error("Task failed: %s\n%s", action_name, tb)
                self._enqueue(lambda: self._on_task_error(action_name, tb))

        threading.Thread(target=_wrapper, daemon=True).start()

    def _enqueue(self, callback: callable) -> None:
        """Safely schedule *callback* on the GUI thread."""
        self.ui_queue.put(callback)

    def _process_ui_queue(self) -> None:
        """Drain the UI queue every 50ms — keeps the GUI responsive."""
        try:
            while True:
                callback = self.ui_queue.get_nowait()
                callback()
        except queue.Empty:
            pass
        self.after(50, self._process_ui_queue)

    # ==================================================================
    # Task completion handlers (run on GUI thread)
    # ==================================================================
    def _on_task_done(self, action: str, result, on_done: callable | None = None) -> None:
        logger.info("Task completed: %s — %s", action, result)
        self.sidebar.set_status("SYSTEM READY", PALETTE["success"])
        self.toast.show(f"'{action}' completed", "Done", "success")

    def _on_task_error(self, action: str, tb: str) -> None:
        logger.error("Task error: %s", action)
        self.sidebar.set_status(f"ERROR: {action}", PALETTE["danger"])
        self.toast.show(f"Task '{action}' failed — see console", "Error", "error")

    def _toast_log(self, msg: str) -> None:
        logger.info(msg)

    # ==================================================================
    # Window events
    # ==================================================================
    def _on_window_resize(self, event) -> None:
        if event.widget == self:
            if self._resize_timer:
                self.after_cancel(self._resize_timer)
            self._resize_timer = self.after(60, self._handle_post_resize)

    def _handle_post_resize(self) -> None:
        self._resize_timer = None
        self.update_idletasks()

    def _open_browse(self) -> None:
        selected = ctk.filedialog.askdirectory(initialdir=self.path_bar.get_path())
        if selected:
            self.path_bar.set_path(selected)
            self._on_path_changed(selected)

    def _on_path_changed(self, new_path: str) -> None:
        logger.info("Vault path changed: %s", new_path)
        self._start_watcher_if_needed()

    def _start_watcher_if_needed(self) -> None:
        path = Path(self.path_bar.get_path())
        if not path.exists():
            return
        if self.watcher and self.watcher.is_running:
            return
        try:
            self.watcher = VaultWatcher(
                self.db_engine, ALLOWED_EXTENSIONS, path,
            )
            started = self.watcher.start(on_change=lambda: self._on_vault_changed())
            if started:
                self.card_watcher.update_value("Live", PALETTE["success"])
                logger.info("Real-time watcher enabled")
        except Exception as exc:
            logger.warning("Watcher could not start: %s", exc)
            self.card_watcher.update_value("Disabled", PALETTE["danger"])

    def _on_vault_changed(self) -> None:
        self._enqueue(lambda: self.card_watcher.update_value("Updated", PALETTE["warning"]))
        self._enqueue(lambda: self.after(2000, lambda: self.card_watcher.update_value("Live", PALETTE["success"])) if self.winfo_exists() else None)

    def _on_settings_saved(self, data: dict) -> None:
        logger.info("Settings saved")
        self.toast.show("Settings saved!", "Success", "success")

    def _on_close(self) -> None:
        logger.info("Shutting down...")
        try:
            if self.watcher:
                self.watcher.stop()
        except Exception:
            pass
        try:
            self.db_engine.close()
        except Exception:
            pass
        self.destroy()

    # ==================================================================
    # Core operations (run in worker threads)
    # ==================================================================
    def run_scan(self) -> dict:
        from utils.os_utils import open_local_path
        root_path = Path(self.path_bar.get_path())
        if not root_path.exists():
            self._enqueue(lambda: self.sidebar.set_status("INVALID PATH!", PALETTE["danger"]))
            logger.error("Scan root does not exist: %s", root_path)
            return {"dirs": 0, "files": 0}

        self._enqueue(lambda: self.sidebar.set_status("SCANNING...", PALETTE["accent"]))
        self._enqueue(lambda: self.card_cache.set_spinner(True))

        dirs, files, items = self.scanner.fast_scan(
            root_path,
            progress_callback=lambda f, t: self._enqueue(
                lambda: self._on_scan_progress(f, t)
            ),
        )

        # Build tree structure on UI thread
        self._enqueue(lambda: self._on_scan_complete(root_path, dirs, files, items))
        return {"dirs": dirs, "files": files, "items": len(items)}

    def _on_scan_progress(self, files_scanned: int, total: int) -> None:
        self.card_files.update_value(str(files_scanned))

    def _on_scan_complete(self, root_path: Path, dirs: int, files: int,
                          items: list) -> None:
        self.tab_explorer.clear()
        self.tab_explorer.populate_root(root_path)

        self.card_dirs.update_value(str(dirs))
        self.card_files.update_value(str(files))
        self.card_cache.update_value("Synced", PALETTE["success"])
        self.card_cache.set_spinner(False)
        self.sidebar.set_status("SYSTEM READY", PALETTE["success"])
        logger.info("Scan complete: %d dirs, %d files", dirs, files)

    def run_generate_index(self) -> bool:
        root_path = Path(self.path_bar.get_path())
        if not root_path.exists():
            self._enqueue(lambda: self.sidebar.set_status("INVALID PATH!", PALETTE["danger"]))
            return False

        self._enqueue(lambda: self.sidebar.set_status("BUILDING INDEX...", PALETTE["accent"]))
        logger.info("Generating full index for: %s", root_path)

        # Scan first if index is empty
        if self.db_engine.item_count == 0:
            self.scanner.fast_scan(root_path)

        output_file = DEFAULT_OUTPUT_FILE
        ok = self.exporter.generate_full_index(root_path, output_file)
        if ok:
            self._enqueue(lambda: self.sidebar.set_status("INDEX CREATED", PALETTE["success"]))
            logger.info("Index file created: %s", output_file)
        else:
            self._enqueue(lambda: self.sidebar.set_status("BUILD ERROR", PALETTE["danger"]))
            logger.error("Failed to generate index file")

        return ok

    def run_extract(self, subfolder: str) -> bool:
        from utils.os_utils import open_local_path
        root_path = Path(self.path_bar.get_path())
        self._enqueue(lambda: self.sidebar.set_status("EXTRACTING...", PALETTE["accent"]))
        logger.info("Extracting subfolder: %s", subfolder)

        output_name = subfolder.replace("/", "_").replace("\\", "_").strip("_") + "_details.md"
        ok = self.exporter.generate_subfolder_index(root_path, subfolder, output_name)
        if ok:
            self._enqueue(lambda: self.sidebar.set_status("EXTRACT COMPLETE", PALETTE["success"]))
            logger.info("Extracted to: %s", output_name)
        else:
            self._enqueue(lambda: self.sidebar.set_status("EXTRACT ERROR", PALETTE["danger"]))
            logger.error("Extraction failed")

        return ok

    def _export_md(self) -> bool:
        root_path = Path(self.path_bar.get_path())
        return self.exporter.generate_full_index(root_path, DEFAULT_OUTPUT_FILE)

    def _export_json(self) -> bool:
        root_path = Path(self.path_bar.get_path())
        return self.json_exporter.generate_json_index(root_path, "vault_index.json")

    def handle_search(self, query: str) -> None:
        if not query:
            self.tab_search._clear_results()
            return
        logger.info("Search query: %s", query)
        matches = self.db_engine.search(query, limit=100)
        self._enqueue(lambda: self.tab_search.render_results(matches, query))


if __name__ == "__main__":
    try:
        app = PentestIndexerApp()
        app.mainloop()
    except Exception:
        print("\n" + "=" * 60)
        print("FATAL UNHANDLED EXCEPTION:")
        traceback.print_exc()
        print("=" * 60)
        input("Press Enter to exit...")
