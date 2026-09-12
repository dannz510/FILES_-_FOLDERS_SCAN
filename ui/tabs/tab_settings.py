"""General settings tab — theme toggle, extensions, exclusions, font scale."""
import json
from pathlib import Path
import customtkinter as ctk

from config.settings import PALETTE, FONT_FAMILY, ALLOWED_EXTENSIONS
from config.theme import ThemeManager
from utils.logger import AppLogger

logger = AppLogger("tab_settings")

CONFIG_FILE = Path("user_settings.json")


class TabSettings(ctk.CTkFrame):
    def __init__(self, master, theme_manager: ThemeManager | None = None,
                 on_theme_change_callback: callable | None = None,
                 on_save_callback: callable | None = None, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.theme_manager = theme_manager
        self.on_theme_change_callback = on_theme_change_callback
        self.on_save_callback = on_save_callback
        self._entries: dict[str, ctk.CTkEntry | ctk.CTkTextbox] = {}
        self._load_settings()
        self._build_ui()

    # ------------------------------------------------------------------ #
    # Settings persistence
    # ------------------------------------------------------------------ #
    def _load_settings(self) -> dict:
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._settings = json.load(f)
            else:
                self._settings = {}
        except Exception:
            self._settings = {}
        return self._settings

    def _save_settings(self) -> bool:
        data = {
            "theme": self.combo_theme.get() if hasattr(self, "combo_theme") else "Dark",
            "extensions": self.entry_ext.get(),
            "exclusions": self.entry_excl.get(),
            "font_scale": self.slider_scale.get() if hasattr(self, "slider_scale") else 1.0,
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info("Settings saved: %s", data)
            if self.on_save_callback:
                self.on_save_callback(data)
            return True
        except Exception as exc:
            logger.error("Failed to save settings: %s", exc)
            return False

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        self._add_section_title(container, "Scanner & Index Configuration")

        frame_ext = ctk.CTkFrame(container, fg_color=PALETTE["card_bg"])
        frame_ext.pack(fill="x", pady=(0, 15), ipadx=10, ipady=10)
        ctk.CTkLabel(
            frame_ext, text="Allowed Index Extensions (comma-separated):",
            font=("Consolas", 12, "bold"), text_color=PALETTE["text_main"],
        ).pack(anchor="w", padx=10, pady=(5, 0))
        self.entry_ext = ctk.CTkEntry(
            frame_ext, fg_color=PALETTE["bg_dark"], border_color=PALETTE["border"],
            text_color=PALETTE["text_main"], font=("Consolas", 11), height=32,
        )
        saved_ext = self._settings.get("extensions", ", ".join(sorted(ALLOWED_EXTENSIONS)))
        self.entry_ext.insert(0, saved_ext)
        self._entries["extensions"] = self.entry_ext

        frame_excl = ctk.CTkFrame(container, fg_color=PALETTE["card_bg"])
        frame_excl.pack(fill="x", pady=(0, 15), ipadx=10, ipady=10)
        ctk.CTkLabel(
            frame_excl, text="Exclusion Patterns (e.g. .git, node_modules, temp_*):",
            font=("Consolas", 12, "bold"), text_color=PALETTE["text_main"],
        ).pack(anchor="w", padx=10, pady=(5, 0))
        self.entry_excl = ctk.CTkEntry(
            frame_excl, fg_color=PALETTE["bg_dark"], border_color=PALETTE["border"],
            text_color=PALETTE["text_main"], font=("Consolas", 11), height=32,
        )
        self.entry_excl.insert(0, self._settings.get("exclusions", ".git, node_modules"))
        self._entries["exclusions"] = self.entry_excl

        self._add_section_title(container, "UI Preferences")

        frame_ui = ctk.CTkFrame(container, fg_color=PALETTE["card_bg"])
        frame_ui.pack(fill="x", pady=(0, 15), ipadx=10, ipady=10)

        ctk.CTkLabel(
            frame_ui, text="Theme:",
            font=("Consolas", 12, "bold"), text_color=PALETTE["text_main"],
        ).pack(anchor="w", padx=10, pady=(5, 0))
        self.combo_theme = ctk.CTkOptionMenu(
            frame_ui,
            values=["Dark", "Light", "Cyberpunk", "System"],
            fg_color=PALETTE["accent"],
            button_color=PALETTE["accent_hover"],
            command=self._change_theme,
            font=("Consolas", 11), height=32,
        )
        saved_theme = self._settings.get("theme", "Dark")
        self.combo_theme.set(saved_theme)
        self.combo_theme.pack(anchor="w", padx=10, pady=(5, 10))

        ctk.CTkLabel(
            frame_ui, text="UI Font Scale:",
            font=("Consolas", 12, "bold"), text_color=PALETTE["text_main"],
        ).pack(anchor="w", padx=10, pady=(10, 0))
        self.slider_scale = ctk.CTkSlider(
            frame_ui, from_=0.8, to=1.5, number_of_steps=14,
        )
        self.slider_scale.set(self._settings.get("font_scale", 1.0))
        self.slider_scale.pack(fill="x", padx=10, pady=(5, 0))
        self.lbl_scale_val = ctk.CTkLabel(
            frame_ui, text=f"Scale: {self.slider_scale.get():.1f}x",
            font=("Consolas", 11), text_color=PALETTE["text_sub"],
        )
        self.lbl_scale_val.pack(anchor="w", padx=10, pady=(5, 5))
        self.slider_scale.configure(command=lambda v: self.lbl_scale_val.configure(
            text=f"Scale: {float(v):.1f}x"
        ))

        # Save button
        btn_save = ctk.CTkButton(
            container, text="Save Configurations",
            fg_color=PALETTE["success"], hover_color="#059669",
            font=("Consolas", 13, "bold"), height=38,
            command=self._on_save,
        )
        btn_save.pack(anchor="e", pady=10)

    def _add_section_title(self, parent, title: str) -> None:
        ctk.CTkLabel(
            parent, text=title,
            font=("Consolas", 14, "bold"),
            text_color=PALETTE["accent"],
        ).pack(anchor="w", pady=(10, 5))

    # ------------------------------------------------------------------ #
    # Callbacks
    # ------------------------------------------------------------------ #
    def _change_theme(self, choice: str) -> None:
        if self.theme_manager:
            if choice == "System":
                import customtkinter as ctk
                # Use system appearance
                ctk.set_appearance_mode("System")
                mode = "Dark"
            else:
                self.theme_manager.switch_to(choice)
                mode = choice
            if self.on_theme_change_callback:
                self.on_theme_change_callback(mode)

    def _on_save(self) -> None:
        if self._save_settings():
            if self.toast:
                self.toast.show("Settings saved successfully!", "Success", "success")
            else:
                print("[SETTINGS] Saved successfully")
        else:
            if self.toast:
                self.toast.show("Failed to save settings!", "Error", "error")
