import customtkinter as ctk
from config.settings import PALETTE, FONT_FAMILY


class MetricCard(ctk.CTkFrame):
    """Reusable dashboard stat card with an animated value label."""

    def __init__(self, parent, title: str, initial_value: str = "0",
                 icon: str | None = None, **kwargs) -> None:
        super().__init__(parent, fg_color=PALETTE["card_bg"], corner_radius=10, **kwargs)

        self._icon = icon

        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=12, pady=(8, 0))

        if icon:
            self.lbl_icon = ctk.CTkLabel(
                top_row, text=icon,
                font=ctk.CTkFont(family=FONT_FAMILY, size=14),
                text_color=PALETTE["accent"],
            )
            self.lbl_icon.pack(side="left")
        else:
            self.lbl_icon = None

        self.lbl_title = ctk.CTkLabel(
            top_row, text=title,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=PALETTE["text_sub"],
            anchor="e",
        )
        self.lbl_title.pack(side="right", padx=4)

        self.lbl_val = ctk.CTkLabel(
            self, text=initial_value,
            font=ctk.CTkFont(family=FONT_FAMILY, size=24, weight="bold"),
            text_color=PALETTE["accent"],
        )
        self.lbl_val.pack(pady=(6, 8))

    def update_value(self, text: str, color: str | None = None) -> None:
        self.lbl_val.configure(text=text, text_color=color or PALETTE["accent"])
