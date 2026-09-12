import os
from pathlib import Path
from typing import Any

# ==============================================================================
# App Metadata
# ==============================================================================
APP_NAME: str = "Pentest Ecosystem"
APP_SUBTITLE: str = "Command Center & Productivity Suite"
APP_VERSION: str = "3.0.0"
APP_LOGO_TEXT: str = "P3C3"

# ==============================================================================
# Font Configurations
# ==============================================================================
FONT_FAMILY: str = "Segoe UI"
FONT_MONO: str = "Consolas"
DEFAULT_TERM_FONT_SIZE: int = 12
DEFAULT_UI_FONT_SIZE: int = 12
DEFAULT_TITLE_FONT_SIZE: int = 22
DEFAULT_CAPTION_FONT_SIZE: int = 11

# ==============================================================================
# Path & Exporter Settings
# ==============================================================================
DEFAULT_ROOT_PATH: str = str(Path.cwd())
DEFAULT_OUTPUT_FILE: str = "INDEX_FULL.md"
ALLOWED_EXTENSIONS: set[str] = {
    ".md", ".txt", ".py", ".cpp", ".json", ".yaml", ".yml",
    ".sh", ".ps1", ".pdf", ".epub", ".bat", ".rar", ".7z",
}

# ==============================================================================
# Terminal Profiles
# ==============================================================================
TERMINAL_PROFILES: dict[str, dict[str, Any]] = {
    "PowerShell": {
        "cmd": ["powershell.exe", "-NoExit"],
        "icon": "PowerShell",
        "color_bg": "#012456",
        "color_fg": "#CCCCCC",
    },
    "CMD": {
        "cmd": ["cmd.exe"],
        "icon": "CMD",
        "color_bg": "#0C0C0C",
        "color_fg": "#CCCCCC",
    },
    "Git Bash": {
        "cmd": [r"C:\Program Files\Git\bin\bash.exe", "--login", "-i"],
        "icon": "Bash",
        "color_bg": "#1E1E1E",
        "color_fg": "#CCCCCC",
    },
}

# ==============================================================================
# Web-like Design System: Glassmorphism / Fluent UI Palettes
# ==============================================================================
PALETTE_DARK: dict[str, str] = {
    "bg_dark": "#0F172A",
    "bg_panel": "#111827",
    "card_bg": "#1E293B",
    "card_hover": "#334155",
    "card_border": "#334155",
    "accent": "#3B82F6",
    "accent_hover": "#2563EB",
    "accent_soft": "#3B82F633",
    "neutral": "#475569",
    "neutral_soft": "#334155",
    "text_main": "#F8FAFC",
    "text_sub": "#94A3B8",
    "text_dim": "#64748B",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "heading_bg": "#020617",
    "terminal_bg": "#0B0F19",
    "border": "#334155",
    "glass_bg": "#FFFFFF1A",
    "glass_border": "#FFFFFF33",
}

PALETTE_LIGHT: dict[str, str] = {
    "bg_dark": "#F1F5F9",
    "bg_panel": "#E2E8F0",
    "card_bg": "#FFFFFF",
    "card_hover": "#F1F5F9",
    "card_border": "#E2E8F0",
    "accent": "#2563EB",
    "accent_hover": "#1D4ED8",
    "accent_soft": "#2563EB33",
    "neutral": "#CBD5E1",
    "neutral_soft": "#CBD5E1",
    "text_main": "#0F172A",
    "text_sub": "#64748B",
    "text_dim": "#94A3B8",
    "success": "#059669",
    "warning": "#D97706",
    "danger": "#DC2626",
    "heading_bg": "#E2E8F0",
    "terminal_bg": "#F5F5F5",
    "border": "#CBD5E1",
    "glass_bg": "#FFFFFFAA",
    "glass_border": "#FFFFFF88",
}

PALETTE_CYBERPUNK: dict[str, str] = {
    "bg_dark": "#00000A",
    "bg_panel": "#050514",
    "card_bg": "#0A0A1A",
    "card_hover": "#1A1A2E",
    "card_border": "#0F0F3D",
    "accent": "#00F3FF",
    "accent_hover": "#00CED1",
    "accent_soft": "#00F3FF33",
    "neutral": "#1A1A3E",
    "neutral_soft": "#1A1A2E",
    "text_main": "#E0E0FF",
    "text_sub": "#AAABB6",
    "text_dim": "#6666AA",
    "success": "#00FF88",
    "warning": "#FF8800",
    "danger": "#FF0066",
    "heading_bg": "#000011",
    "terminal_bg": "#00000A",
    "border": "#0A0A2A",
    "glass_bg": "#00F3FF11",
    "glass_border": "#00F3FF44",
}

THEME_REGISTRY: dict[str, dict[str, str]] = {
    "Dark": PALETTE_DARK,
    "Light": PALETTE_LIGHT,
    "Cyberpunk": PALETTE_CYBERPUNK,
}

ACTIVE_THEME_NAME: str = "Dark"
PALETTE: dict[str, str] = PALETTE_DARK


def get_palette(name: str | None = None) -> dict[str, str]:
    if name is None:
        return PALETTE
    return THEME_REGISTRY.get(name, PALETTE_DARK)


# ==============================================================================
# Layout constants
# ==============================================================================
SIDEBAR_WIDTH: int = 240
TOPBAR_HEIGHT: int = 48
CARD_CORNER_RADIUS: int = 12
CONTENT_PADDING: int = 16

# ==============================================================================
# Scanner / Concurrency settings
# ==============================================================================
SCANNER_MAX_WORKERS: int = min(16, (os.cpu_count() or 4) * 2)
SCANNER_BATCH_SIZE: int = 500
WATCHER_DEBOUNCE_MS: int = 300

# ==============================================================================
# Ecosystem tool registry
# ==============================================================================
TOOLS: dict[str, dict[str, str]] = {
    "alarm": {"name": "Alarm Clock", "icon": "⏰", "desc": "Multi-timer & alarm scheduler"},
    "passgen": {"name": "Password Generator", "icon": "🔐", "desc": "Crypto-safe password generator"},
    "3dbuilder": {"name": "3D Builder", "icon": "🧊", "desc": "3D wireframe viewer & editor"},
    "converter": {"name": "File Converter", "icon": "🔄", "desc": "Multi-format converter"},
    "downloader": {"name": "Downloader", "icon": "📥", "desc": "Multi-threaded downloader"},
    "paint": {"name": "Paint", "icon": "🎨", "desc": "Digital canvas painting"},
}

VIEWS: dict[str, dict[str, str]] = {
    "home": {"name": "Dashboard", "icon": "🏠"},
    "vault": {"name": "Vault", "icon": "🌲"},
    "utilities": {"name": "Utilities", "icon": "🔧"},
}

# ==============================================================================
# Export formats
# ==============================================================================
EXPORT_FORMATS: dict[str, str] = {
    "Markdown": "*.md",
    "JSON": "*.json",
}
