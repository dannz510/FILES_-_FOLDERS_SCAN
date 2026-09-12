from tkinter import ttk
from config.settings import PALETTE, FONT_FAMILY
from config.theme import ThemeManager


def apply_treeview_style(palette: dict | None = None) -> ThemeManager:
    """Apply TTK Treeview styles matching the given (or active) palette.

    Returns a :class:`ThemeManager` pre-loaded with a callback that re-applies
    the treeview style whenever the active palette changes.
    """
    if palette is None:
        from config.settings import PALETTE as palette
    tm = ThemeManager()

    def _apply(p: dict) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=p["card_bg"],
            foreground=p["text_main"],
            fieldbackground=p["card_bg"],
            borderwidth=0,
            font=(FONT_FAMILY, 10),
            rowheight=28,
        )
        style.configure(
            "Treeview.Heading",
            background=p.get("heading_bg", p["bg_dark"]),
            foreground=p.get("text_sub", p["text_main"]),
            font=(FONT_FAMILY, 10, "bold"),
            borderwidth=0,
        )
        style.map(
            "Treeview",
            background=[("selected", p["accent"])],
            foreground=[("selected", "#FFFFFF")],
        )
        style.map(
            "Treeview.Heading",
            background=[("active", p.get("card_hover", p["card_bg"]))],
        )

    _apply(palette)
    tm.register_callback(_apply)
    return tm


def apply_all_styles(theme_manager: ThemeManager) -> None:
    """Register style callbacks for every TTK widget type used in the app."""
    def _style(p: dict) -> None:
        style = ttk.Style()
        style.configure(
            "TScrollbar",
            background=p.get("card_bg", "#1E293B"),
            troughcolor=p.get("bg_dark", "#0F172A"),
            bordercolor=p.get("border", "#334155"),
            arrowcolor=p.get("text_main", "#F8FAFC"),
        )

    theme_manager.register_callback(_style)
    _style(theme_manager.palette)
