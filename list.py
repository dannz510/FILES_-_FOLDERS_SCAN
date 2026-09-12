import os
import sys
import threading
import subprocess
from pathlib import Path
from urllib.parse import quote
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

# Cấu hình giao diện CustomTkinter
ctk.set_appearance_mode("Dark")

# ==========================================
# PALETTE COLOR SYSTEM (TỪ BẢNG MÀU YÊU CẦU)
# ==========================================
PALETTE = {
    "bg_dark": "#0F172A",       # Dark Navy Main Background
    "card_bg": "#1E293B",       # Slate Dark Card Background
    "card_hover": "#334155",    # Lighter Slate Hover
    "accent": "#007BFF",        # Primary Electric Blue
    "accent_hover": "#0056b3",  # Deep Blue
    "neutral": "#64748B",       # Slate Neutral
    "text_main": "#F8FAFC",     # Crisp White
    "text_sub": "#94A3B8",      # Light Slate Gray
    "success": "#10B981",       # Emerald Green
    "terminal_bg": "#0B0F19"    # Deep Charcoal
}

DEFAULT_ROOT_PATH = r'D:\Do not open\Obsidian\Dannz\PENTESTER'
DEFAULT_OUTPUT_FILE = 'Cyber_Library_PENTESTER.md'
ALLOWED_EXTENSIONS = {'.pdf', '.epub', '.txt', '.py', '.bat', '.sh', '.rar', '.7z', '.md'}

FONT_FAMILY = "Segoe UI"
FONT_MONO = "Consolas"

def encode_path_for_obsidian(path_str: str) -> str:
    return quote(path_str.replace('\\', '/'), safe='/:-_')

class ModernPentesterIndexer(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🛡️ Obsidian Pentester Knowledge Base Pro")
        self.geometry("1180x750")
        self.minsize(1024, 680)
        self.configure(fg_color=PALETTE["bg_dark"])

        self.cached_items = []
        self.search_timer = None

        self._apply_custom_treeview_style()
        self._build_sidebar()
        self._build_main_panel()

    def _apply_custom_treeview_style(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Custom.Treeview",
            background=PALETTE["card_bg"],
            foreground=PALETTE["text_main"],
            fieldbackground=PALETTE["card_bg"],
            borderwidth=0,
            font=(FONT_FAMILY, 10),
            rowheight=28
        )
        style.configure("Custom.Treeview.Heading", background=PALETTE["neutral"], foreground=PALETTE["text_main"], font=(FONT_FAMILY, 10, "bold"))
        style.map("Custom.Treeview", background=[("selected", PALETTE["accent"])])

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, fg_color=PALETTE["card_bg"], corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # App Logo & Branding
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(25, 20))

        lbl_logo = ctk.CTkLabel(
            logo_frame, text="🛡️ PENTEST", 
            font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"), 
            text_color=PALETTE["accent"]
        )
        lbl_logo.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(
            logo_frame, text="Obsidian Base Engine", 
            font=ctk.CTkFont(family=FONT_FAMILY, size=12), 
            text_color=PALETTE["neutral"]
        )
        lbl_sub.pack(anchor="w")

        # Action Buttons
        btn_config = [
            ("⚡ Build Full Index", self.start_generate_index_thread, PALETTE["accent"], PALETTE["accent_hover"]),
            ("📊 Scan & Sync Vault", self.start_quick_scan_thread, PALETTE["card_hover"], PALETTE["neutral"]),
            ("📂 Open Vault Directory", self.open_vault_folder, PALETTE["card_hover"], PALETTE["neutral"])
        ]

        for text, cmd, fg, hover in btn_config:
            btn = ctk.CTkButton(
                self.sidebar, text=text, command=cmd, 
                fg_color=fg, hover_color=hover, text_color=PALETTE["text_main"],
                font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                height=40, corner_radius=8
            )
            btn.pack(fill="x", padx=20, pady=8)

        # Status Badge
        self.lbl_system_status = ctk.CTkLabel(
            self.sidebar, text="● SYSTEM READY", 
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=PALETTE["success"]
        )
        self.lbl_system_status.pack(side="bottom", pady=20)

    def _build_main_panel(self):
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # 1. Path Selector Bar
        path_card = ctk.CTkFrame(main_container, fg_color=PALETTE["card_bg"], corner_radius=10)
        path_card.pack(fill="x", pady=(0, 15))

        lbl_path = ctk.CTkLabel(
            path_card, text="Vault Root:", 
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=PALETTE["text_sub"]
        )
        lbl_path.pack(side="left", padx=(15, 10), pady=12)

        self.entry_path = ctk.CTkEntry(
            path_card, fg_color=PALETTE["bg_dark"], text_color=PALETTE["text_main"],
            border_color=PALETTE["neutral"], border_width=1, corner_radius=6,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12)
        )
        self.entry_path.insert(0, DEFAULT_ROOT_PATH)
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=12)

        btn_browse = ctk.CTkButton(
            path_card, text="Browse", width=80, command=self.browse_folder,
            fg_color=PALETTE["neutral"], hover_color=PALETTE["card_hover"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=12)
        )
        btn_browse.pack(side="right", padx=(0, 15), pady=12)

        # 2. Metric Dashboard
        metrics_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        metrics_frame.pack(fill="x", pady=(0, 15))
        metrics_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.card_dirs = self._create_metric_card(metrics_frame, "0", "Folders Detected", 0)
        self.card_files = self._create_metric_card(metrics_frame, "0", "Valid Files", 1)
        self.card_cache = self._create_metric_card(metrics_frame, "Unsynced", "Search Index Status", 2)

        # 3. Multi-Tab Section
        self.tabview = ctk.CTkTabview(
            main_container, fg_color=PALETTE["card_bg"], 
            segmented_button_fg_color=PALETTE["bg_dark"],
            segmented_button_selected_color=PALETTE["accent"],
            segmented_button_selected_hover_color=PALETTE["accent_hover"],
            segmented_button_unselected_color=PALETTE["card_bg"],
            segmented_button_unselected_hover_color=PALETTE["card_hover"]
        )
        self.tabview.pack(fill="both", expand=True)

        self.tab_tree = self.tabview.add("🌲 Vault Explorer")
        self.tab_search = self.tabview.add("🔍 Live Search")
        self.tab_extract = self.tabview.add("📂 Subfolder Exporter")
        self.tab_log = self.tabview.add("🖥️ Terminal Log")

        self._build_tree_tab()
        self._build_search_tab()
        self._build_extract_tab()
        self._build_log_tab()

    def _create_metric_card(self, parent, value: str, title: str, col: int):
        card = ctk.CTkFrame(parent, fg_color=PALETTE["card_bg"], corner_radius=10)
        card.grid(row=0, column=col, padx=6, sticky="ew")

        lbl_val = ctk.CTkLabel(
            card, text=value, 
            font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"),
            text_color=PALETTE["accent"]
        )
        lbl_val.pack(pady=(12, 2))

        lbl_title = ctk.CTkLabel(
            card, text=title, 
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=PALETTE["text_sub"]
        )
        lbl_title.pack(pady=(0, 12))
        return lbl_val

    # --- TAB 1: TREEVIEW ---
    def _build_tree_tab(self):
        frame = ctk.CTkFrame(self.tab_tree, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(frame, columns=("path"), show="tree", style="Custom.Treeview")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self.on_tree_double_click)

    # --- TAB 2: LIVE SEARCH ---
    def _build_search_tab(self):
        search_top = ctk.CTkFrame(self.tab_search, fg_color="transparent")
        search_top.pack(fill="x", padx=10, pady=(10, 5))

        self.entry_search = ctk.CTkEntry(
            search_top, placeholder_text="Gõ tên file, extension (.pdf, .py)...",
            fg_color=PALETTE["bg_dark"], border_color=PALETTE["neutral"],
            text_color=PALETTE["text_main"], font=ctk.CTkFont(family=FONT_FAMILY, size=12)
        )
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_search.bind("<KeyRelease>", self.on_search_key_debounce)

        btn_clear = ctk.CTkButton(
            search_top, text="Clear", width=70, command=self.clear_search,
            fg_color=PALETTE["neutral"], hover_color=PALETTE["card_hover"]
        )
        btn_clear.pack(side="right")

        self.scroll_search = ctk.CTkScrollableFrame(self.tab_search, fg_color="transparent")
        self.scroll_search.pack(fill="both", expand=True, padx=10, pady=5)

    # --- TAB 3: EXTRACTOR ---
    def _build_extract_tab(self):
        frame = ctk.CTkFrame(self.tab_extract, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        lbl_desc = ctk.CTkLabel(
            frame, text="Trích xuất cấu trúc chi tiết của một thư mục con thành file .md độc lập.",
            text_color=PALETTE["text_sub"], font=ctk.CTkFont(family=FONT_FAMILY, size=12)
        )
        lbl_desc.pack(anchor="w", pady=(0, 15))

        self.entry_subfolder = ctk.CTkEntry(
            frame, placeholder_text="Nhập đường dẫn tương đối (Ví dụ: 02_Network_Security)...",
            fg_color=PALETTE["bg_dark"], border_color=PALETTE["neutral"],
            text_color=PALETTE["text_main"], font=ctk.CTkFont(family=FONT_FAMILY, size=12), height=40
        )
        self.entry_subfolder.pack(fill="x", pady=(0, 15))

        btn_run_extract = ctk.CTkButton(
            frame, text="🚀 Extract Details File", command=self.start_extract_folder_thread,
            fg_color=PALETTE["accent"], hover_color=PALETTE["accent_hover"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"), height=42
        )
        btn_run_extract.pack(anchor="w")

    # --- TAB 4: TERMINAL LOG ---
    def _build_log_tab(self):
        self.textbox_log = ctk.CTkTextbox(
            self.tab_log, font=ctk.CTkFont(family=FONT_MONO, size=12),
            fg_color=PALETTE["terminal_bg"], text_color=PALETTE["success"]
        )
        self.textbox_log.pack(fill="both", expand=True, padx=10, pady=10)

    # ==========================================
    # LOGIC HỆ THỐNG & CÁC THUẬT TOÁN TỐI ƯU
    # ==========================================
    def log(self, message: str):
        self.textbox_log.insert("end", f"> {message}\n")
        self.textbox_log.see("end")

    def browse_folder(self):
        selected = ctk.filedialog.askdirectory(initialdir=self.entry_path.get())
        if selected:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, selected)

    def open_vault_folder(self):
        p = Path(self.entry_path.get().strip())
        if p.exists():
            self.open_local_path(p)

    def open_local_path(self, path_obj: Path):
        try:
            if sys.platform == 'win32':
                os.startfile(path_obj)
            else:
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.call([opener, str(path_obj)])
        except Exception as e:
            self.log(f"ERROR: Không thể mở file/folder -> {str(e)}")

    def on_tree_double_click(self, event):
        item_id = self.tree.focus()
        if item_id:
            values = self.tree.item(item_id, "values")
            if values:
                self.open_local_path(Path(values[0]))

    def start_quick_scan_thread(self):
        threading.Thread(target=self.run_quick_scan, daemon=True).start()

    def start_generate_index_thread(self):
        threading.Thread(target=self.run_generate_index, daemon=True).start()

    def start_extract_folder_thread(self):
        threading.Thread(target=self.run_extract_folder, daemon=True).start()

    # Thuật toán duyệt siêu nhanh sử dụng os.scandir
    def run_quick_scan(self):
        root_path = Path(self.entry_path.get().strip())
        if not root_path.exists():
            self.log("ERROR: Đường dẫn Vault không tồn tại!")
            return

        self.lbl_system_status.configure(text="● SCANNING...", text_color=PALETTE["accent"])
        self.log(f"Bắt đầu Fast Scan: {root_path}")
        
        self.cached_items.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

        total_dirs, total_files = self._fast_scan_dir(root_path, "")

        self.card_dirs.configure(text=str(total_dirs))
        self.card_files.configure(text=str(total_files))
        self.card_cache.configure(text="Synced", text_color=PALETTE["success"])
        self.lbl_system_status.configure(text="● SYSTEM READY", text_color=PALETTE["success"])
        self.log(f"Scan hoàn tất: {total_dirs} Folders | {total_files} Files")

    def _fast_scan_dir(self, current_path: Path, parent_tree_node: str):
        dirs_count, files_count = 0, 0
        try:
            entries = sorted(list(os.scandir(current_path)), key=lambda e: (not e.is_dir(), e.name.lower()))
            for entry in entries:
                if entry.name.startswith('.'):
                    continue
                
                entry_path = Path(entry.path)
                if entry.is_dir():
                    dirs_count += 1
                    node_id = self.tree.insert(parent_tree_node, "end", text=f"📂 {entry.name}", values=(str(entry_path),))
                    self.cached_items.append({'name': entry.name, 'type': 'folder', 'ext': '', 'path': entry_path})
                    
                    sub_d, sub_f = self._fast_scan_dir(entry_path, node_id)
                    dirs_count += sub_d
                    files_count += sub_f
                else:
                    ext = entry_path.suffix.lower()
                    if ext in ALLOWED_EXTENSIONS:
                        files_count += 1
                        self.tree.insert(parent_tree_node, "end", text=f"📄 {entry.name}", values=(str(entry_path),))
                        self.cached_items.append({'name': entry.name, 'type': 'file', 'ext': ext, 'path': entry_path})
        except PermissionError:
            pass
        return dirs_count, files_count

    # Thuật toán Debounce giảm độ trễ khi tìm kiếm
    def on_search_key_debounce(self, event=None):
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(250, self.execute_search)

    def execute_search(self):
        query = self.entry_search.get().strip().lower()
        for w in self.scroll_search.winfo_children():
            w.destroy()

        if not query:
            return

        if not self.cached_items:
            self.run_quick_scan()

        matches = [
            item for item in self.cached_items 
            if query in item['name'].lower() or query in item['ext'].lower()
        ]

        for item in matches[:40]:
            card = ctk.CTkFrame(self.scroll_search, fg_color=PALETTE["card_bg"], corner_radius=6)
            card.pack(fill="x", pady=3)

            lbl_icon = ctk.CTkLabel(card, text="📂" if item['type'] == 'folder' else "📄", font=ctk.CTkFont(size=14))
            lbl_icon.pack(side="left", padx=10)

            lbl_title = ctk.CTkLabel(card, text=item['name'], font=ctk.CTkFont(family=FONT_FAMILY, weight="bold"))
            lbl_title.pack(side="left", padx=5)

            btn_copy = ctk.CTkButton(
                card, text="Copy Link", width=70, height=26, fg_color=PALETTE["accent"],
                command=lambda p=item['path'], n=item['name']: self.copy_link(p, n)
            )
            btn_copy.pack(side="right", padx=10, pady=6)

            btn_open = ctk.CTkButton(
                card, text="Open", width=60, height=26, fg_color=PALETTE["neutral"],
                command=lambda p=item['path']: self.open_local_path(p)
            )
            btn_open.pack(side="right", padx=0, pady=6)

    def clear_search(self):
        self.entry_search.delete(0, "end")
        for w in self.scroll_search.winfo_children():
            w.destroy()

    def copy_link(self, path_obj: Path, name: str):
        encoded = encode_path_for_obsidian(str(path_obj.resolve()))
        md_link = f"[{name}](file:///{encoded})"
        self.clipboard_clear()
        self.clipboard_append(md_link)
        self.log(f"Copied Obsidian Link: {md_link}")

    def run_generate_index(self):
        root_path = Path(self.entry_path.get().strip())
        if not root_path.exists():
            self.log("ERROR: Đường dẫn không tồn tại!")
            return

        self.log("Đang tạo Full Index Vault...")
        output_file = DEFAULT_OUTPUT_FILE

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# 🛡️ PENTESTER KNOWLEDGE BASE INDEX\n\n")
                f.write(f"> **Root Directory:** `{root_path}`\n\n---\n")

                for root, dirs, files in os.walk(root_path):
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    current_dir = Path(root)
                    
                    level = 0 if current_dir == root_path else len(current_dir.relative_to(root_path).parts)
                    if level > 0:
                        f.write(f"{'  ' * (level - 1)}- 📂 **{current_dir.name}**\n")

                    for file in sorted(files):
                        file_path = current_dir / file
                        if file_path.suffix.lower() in ALLOWED_EXTENSIONS:
                            encoded_link = encode_path_for_obsidian(str(file_path.resolve()))
                            f.write(f"{'  ' * level}- [📄 {file}](file:///{encoded_link})\n")

            self.log(f"SUCCESS: Đã xuất Index -> {output_file}")
        except Exception as e:
            self.log(f"CRITICAL ERROR: {str(e)}")

    def run_extract_folder(self):
        base_root = Path(self.entry_path.get().strip()).resolve()
        subfolder_input = self.entry_subfolder.get().strip()

        if not subfolder_input:
            self.log("WARNING: Chưa nhập subfolder!")
            return

        target_path = (base_root / subfolder_input).resolve() if not Path(subfolder_input).is_absolute() else Path(subfolder_input)
        if not target_path.exists():
            self.log(f"ERROR: Thư mục không tồn tại -> {target_path}")
            return

        folder_name = target_path.name
        output_file = f"{folder_name}_details.md"

        try:
            relative_parts = target_path.relative_to(base_root).parts if target_path.is_relative_to(base_root) else target_path.parts
            tags = ['#pentest', '#cybersecurity'] + [f"#{part.lower().replace(' ', '_')}" for part in relative_parts if part]

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"---\ntags: {', '.join(tags)}\n---\n\n")
                f.write(f"# 📂 Chi tiết Folder: {folder_name}\n\n")
                f.write(f"> **Đường dẫn:** `{target_path}`\n\n[[Cyber_Library_PENTESTER|← Back to Root Index]]\n\n---\n")

                for root, dirs, files in os.walk(target_path):
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    current_dir = Path(root)

                    level = 0 if current_dir == target_path else len(current_dir.relative_to(target_path).parts)
                    if level > 0:
                        rel_dir_path = current_dir.relative_to(target_path).as_posix()
                        encoded_dir = encode_path_for_obsidian(rel_dir_path)
                        f.write(f"{'  ' * (level - 1)}- 📂 [{current_dir.name}]({encoded_dir}/)\n")

                    valid_files = [f for f in sorted(files) if Path(f).suffix.lower() in ALLOWED_EXTENSIONS]
                    for file in valid_files:
                        file_full_path = current_dir / file
                        rel_file_path = file_full_path.relative_to(target_path).as_posix()
                        encoded_file = encode_path_for_obsidian(rel_file_path)
                        f.write(f"{'  ' * level}- [📄 {file}]({encoded_file})\n")

            self.log(f"SUCCESS: Đã xuất file chi tiết -> {output_file}")
        except Exception as e:
            self.log(f"ERROR: {str(e)}")

if __name__ == "__main__":
    app = ModernPentesterIndexer()
    app.mainloop()