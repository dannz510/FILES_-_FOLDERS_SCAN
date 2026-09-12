import customtkinter as ctk
from config.settings import PALETTE, FONT_FAMILY, CARD_CORNER_RADIUS


class GlassCard(ctk.CTkFrame):
    """Web-like glassmorphism card with subtle border and rounded corners."""

    def __init__(self, parent, title: str | None = None, icon: str = None,
                 width: int | None = None, height: int | None = None,
                 **kwargs) -> None:
        super().__init__(
            parent,
            fg_color=PALETTE.get("card_bg", "#1E293B"),
            corner_radius=CARD_CORNER_RADIUS,
            border_width=1,
            border_color=PALETTE.get("card_border", "#334155"),
            width=width,
            height=height,
            **kwargs,
        )

        self._title_label = None
        if title:
            header = ctk.CTkFrame(self, fg_color="transparent")
            header.pack(fill="x", padx=12, pady=(10, 4))

            if icon:
                self._icon_label = ctk.CTkLabel(
                    header, text=icon,
                    font=ctk.CTkFont(family=FONT_FAMILY, size=14),
                    text_color=PALETTE["accent"],
                )
                self._icon_label.pack(side="left")
            else:
                self._icon_label = None

            self._title_label = ctk.CTkLabel(
                header, text=title,
                font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                text_color=PALETTE["text_main"],
                anchor="w",
            )
            self._title_label.pack(side="left", padx=(8, 0))

    def set_title(self, title: str) -> None:
        if self._title_label:
            self._title_label.configure(text=title)

    def update_theme(self, palette: dict) -> None:
        self.configure(
            fg_color=palette.get("card_bg", "#1E293B"),
            border_color=palette.get("card_border", "#334155"),
        )
        if self._title_label:
            self._title_label.configure(text_color=palette["text_main"])
        if self._icon_label:
            self._icon_label.configure(text_color=palette["accent"])
