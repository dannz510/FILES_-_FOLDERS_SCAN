import customtkinter as ctk
from config.settings import THEME_REGISTRY, PALETTE_DARK, ACTIVE_THEME_NAME


class ThemeManager:
    """Manages dynamic theme switching between Dark, Light, and Cyberpunk palettes.

    The theme system is *reactive*: registered callbacks are invoked whenever
    the active palette changes so that every UI widget can re-style itself
    without requiring an application restart.
    """

    def __init__(self, initial_theme: str = ACTIVE_THEME_NAME) -> None:
        self._active_theme_name: str = initial_theme
        self._palette: dict[str, str] = THEME_REGISTRY.get(initial_theme, PALETTE_DARK)
        self._callbacks: list[callable] = []

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #
    @property
    def name(self) -> str:
        return self._active_theme_name

    @property
    def palette(self) -> dict[str, str]:
        return self._palette

    @property
    def available_themes(self) -> list[str]:
        return list(THEME_REGISTRY.keys())

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def register_callback(self, callback: callable) -> None:
        """Register a callable that receives the new palette dict on change."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister_callback(self, callback: callable) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    # ------------------------------------------------------------------ #
    # Theme operations
    # ------------------------------------------------------------------ #
    def get_palette(self, theme_name: str | None = None) -> dict[str, str]:
        if theme_name is None:
            return self._palette
        return THEME_REGISTRY.get(theme_name, PALETTE_DARK)

    def switch_to(self, theme_name: str) -> bool:
        """Switch to *theme_name*.  Returns True on success."""
        if theme_name not in THEME_REGISTRY:
            return False
        if self._active_theme_name == theme_name:
            return True

        self._active_theme_name = theme_name
        self._palette = THEME_REGISTRY[theme_name]

        # Update CustomTkinter appearance mode
        if theme_name == "Light":
            ctk.set_appearance_mode("Light")
        else:
            ctk.set_appearance_mode("Dark")

        # Notify all registered widgets
        for cb in list(self._callbacks):
            try:
                cb(self._palette)
            except Exception:
                pass

        return True
