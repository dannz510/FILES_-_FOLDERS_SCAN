"""Dynamic SVG/Pillow-based icon and logo generator.

All icons are rendered at runtime using Pillow (PIL.ImageDraw) — no external
image assets required.  Icons are cached as PhotoImage instances.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

# Icon cache — maps logical name -> CTkImage / PIL Image
_cache: dict[str, Any] = {}


def _default_font(size: int = 14) -> ImageFont.FreeTypeFont:
    """Return a usable default font, falling back to PIL default if needed."""
    candidates = [
        "Segoe UI",
        "Arial",
        "DejaVu Sans",
        "Calibri",
    ]
    for fam in candidates:
        try:
            return ImageFont.truetype(fam, size=size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _make_canvas(size: int = 48, bg: tuple | None = None) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (size, size), bg or (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    return img, draw


def _to_ctk_image(img: Image.Image, size: tuple[int, int] = (24, 24)):
    from customtkinter import CTkImage
    return CTkImage(light_image=img, dark_image=img, size=size)


# ---------------------------------------------------------------------------
# Icon renderers
# ---------------------------------------------------------------------------
def render_app_logo(size: int = 96) -> Image.Image:
    """Render the application logo: a shield with P3C3 text."""
    if "app_logo" in _cache:
        return _cache["app_logo"]

    img, draw = _make_canvas(size)
    margin = size // 16
    cx, cy, r = size // 2, size // 2, size // 2 - margin

    # Shield shape (rounded polygon)
    points = [
        (cx, margin),
        (cx + r, cx - r // 4),
        (cx, cy + r),
        (cx - r, cx - r // 4),
    ]
    draw.polygon(points, fill="#3B82F6")
    # Inner highlight
    inner = [(p[0], p[1]) for p in points]
    draw.polygon(inner, fill="#2563EB")

    # Shield border
    draw.line([points[0], points[1], points[2], points[3], points[0]],
              fill="#FFFFFF", width=max(1, size // 24))

    # Crosshair
    cross_color = (255, 255, 255, 220)
    draw.line([cx - r // 3, cy, cx + r // 3, cy], fill=cross_color, width=max(1, size // 32))
    draw.line([cx, cy - r // 3, cx, cy + r // 3], fill=cross_color, width=max(1, size // 32))

    _cache["app_logo"] = img
    return img


def render_icon(name: str, size: int = 24, color: tuple = (255, 255, 255)) -> Image.Image:
    """Render a named icon by drawing primitive shapes."""
    key = f"icon_{name}_{size}_{color}"
    if key in _cache:
        return _cache[key]

    img, draw = _make_canvas(size)
    s = size
    m = s // 10  # margin
    c = color
    fc = (c[0], c[1], c[2], 255)  # full alpha

    if name == "alarm":
        # Digital alarm clock
        draw.ellipse([m, m, s - m, s - m], outline=fc, width=2)
        draw.line([s // 2, m + 2], [s // 2, s // 2], fill=fc, width=2)
        draw.ellipse([s // 2 - 3, s // 2 - 3, s // 2 + 3, s // 2 + 3], fill=fc)
        # Bell
        draw.polygon([(s // 2 - 6, s // 2 + 4), (s // 2 + 6, s // 2 + 4), (s // 2, s // 2 + 12)], fill=fc)

    elif name == "passgen":
        # Key
        draw.ellipse([m, m, s - m, s - m], outline=fc, width=2)
        draw.arc([m + 4, m + 4, s // 2 + 2, s // 2 + 2], 200, 340, fill=fc, width=2)
        draw.line([s // 2 + 2, s // 2 + 2, s - m - 2, s - m - 2], fill=fc, width=2)

    elif name == "3d":
        # Cube wireframe
        pts = [(m, m), (s - m, m), (s - m, s - m), (m, s - m)]
        offset = 6
        pts2 = [(p[0] + offset, p[1] + offset) for p in pts]
        draw.line([pts[0], pts[1], pts[2], pts[3], pts[0]], fill=fc, width=2)
        for i in range(4):
            draw.line([pts[i], pts2[i]], fill=fc, width=2)
        draw.line([pts2[0], pts2[1], pts2[2], pts2[3], pts2[0]], fill=fc, width=2)

    elif name == "converter":
        # Exchange arrows
        draw.line([m, s // 2, s // 2 - 4, s // 2 - 6], fill=fc, width=2)
        draw.line([s // 2 - 4, s // 2 - 6, s // 2 - 4, s // 2 + 6], fill=fc, width=2)
        draw.line([s // 2 + 4, s // 2 + 6, s - m, s // 2], fill=fc, width=2)
        draw.line([s // 2 + 4, s // 2 + 6, s // 2 + 4, s // 2 - 6], fill=fc, width=2)
        # Swap arrows
        draw.line([s // 2 - 2, m, s // 2 - 2, s - m], fill=fc, width=2)

    elif name == "downloader":
        # Download arrow
        draw.line([s // 2, m + 2, s // 2, s // 2 - 2], fill=fc, width=2)
        draw.polygon([(s // 2 - 5, s // 2 - 2), (s // 2 + 5, s // 2 - 2), (s // 2, s // 2 + 4)], fill=fc)
        # Drive
        draw.rectangle([m + 4, s // 2 + 8, s - m - 4, s - m - 4], outline=fc, width=2)

    elif name == "paint":
        # Paintbrush
        draw.line([m, s - m, s // 2, m + 4], fill=fc, width=2)
        draw.ellipse([s // 2 - 4, m, s // 2 + 4, m + 8], outline=fc, width=2)
        # Palette dots
        for i, (dx, dy) in enumerate([(-6, -6), (6, -6), (-4, 4), (4, 4)]):
            draw.ellipse([s // 2 + dx - 2, m + 8 + dy - 2, s // 2 + dx + 2, m + 8 + dy + 2], fill=fc)

    elif name == "vault":
        # Folder
        draw.rectangle([m, m + 4, s - m, s - m], outline=fc, width=2)
        draw.rectangle([m + 2, m, s // 2 + 4, m + 6], outline=fc, width=2)

    elif name == "search":
        # Magnifier
        draw.arc([m, m, s - m, s - m], 200, 340, fill=fc, width=2)
        draw.arc([m, m, s - m, s - m], 340, 360, fill=fc, width=2)
        draw.line([s // 2 + 4, s // 2 + 4, s - m - 2, s - m - 2], fill=fc, width=2)

    elif name == "terminal":
        # Terminal window
        draw.rectangle([m, m, s - m, s - m], outline=fc, width=2)
        draw.line([m + 2, m + 6, s - m - 2, m + 6], fill=fc, width=1)

    elif name == "dashboard":
        # Speedometer / gauge
        draw.arc([m, m, s - m, s - m], 200, 340, fill=fc, width=2)
        draw.arc([m, m, s - m, s - m], 220, 320, outline=fc, width=1)
        draw.line([s // 2, s // 2, s // 2 + (s // 2 - m) * 0.7, s // 2], fill=fc, width=2)
        draw.ellipse([s // 2 - 1, s // 2 - 1, s // 2 + 1, s // 2 + 1], fill=fc)

    elif name == "copy":
        # Clipboard
        draw.rectangle([m + 4, m + 4, s - m - 4, s - m - 2], outline=fc, width=2)
        draw.arc([m + 2, m - 2, s - m + 2, m + 6], 180, 0, fill=fc, width=2)

    elif name == "save":
        # Disk / floppy
        draw.rectangle([m, m + 6, s - m, s - m], outline=fc, width=2)
        draw.rectangle([m + 2, m, s // 2, m + 6], outline=fc, width=2, fill=fc)

    elif name == "settings":
        # Gear
        import math
        cx, cy, r = s // 2, s // 2, s // 2 - m
        for i in range(6):
            angle = i * 60
            ax = cx + r * 0.7 * math.cos(math.radians(angle))
            ay = cy + r * 0.7 * math.sin(math.radians(angle))
            bx = cx + r * math.cos(math.radians(angle))
            by = cy + r * math.sin(math.radians(angle))
            draw.line([ax, ay, bx, by], fill=fc, width=2)
        draw.ellipse([cx - r * 0.4, cy - r * 0.4, cx + r * 0.4, cy + r * 0.4], outline=fc, width=2)

    else:
        # Default: question mark in circle
        draw.ellipse([m, m, s - m, s - m], outline=fc, width=2)
        draw.line([s // 2, m + 6, s // 2, s // 2 - 6], fill=fc, width=2)
        draw.ellipse([s // 2 - 2, s // 2 - 6, s // 2 + 2, s // 2 + 2], outline=fc, width=2)

    _cache[key] = img
    return img


def get_ctk_icon(name: str, size: int = 20, color: tuple = (255, 255, 255)) -> Any:
    """Return a CTkImage for use in CustomTkinter widgets."""
    img = render_icon(name, size=size, color=color)
    return _to_ctk_image(img, (size, size))


def get_pil_icon(name: str, size: int = 24) -> Image.Image:
    """Return a raw PIL Image for direct drawing contexts."""
    return render_icon(name, size=size)


def render_text_logo(text: str, size: int = 48,
                     font_path: str | None = None) -> Image.Image:
    """Render text-based logo with gradient fill."""
    img = Image.new("RGBA", (size * len(text) // 2 + size, size + 8), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _default_font(size=size)
    x = 8
    for i, ch in enumerate(text):
        toned = tuple(int(c * (0.7 + 0.3 * i / len(text))) for c in (59, 130, 246))
        draw.text((x, 2), ch, font=font, fill=toned + (255,))
        bbox = draw.textbbox((x, 2), ch, font=font)
        x = bbox[2] + 2
    return img
