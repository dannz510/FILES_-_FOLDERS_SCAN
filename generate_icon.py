import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def draw_cyber_shield_logo(size=512):
    """Vẽ Logo Cyber Command Center chuẩn Vector Style bằng Pillow"""
    # Khởi tạo Canvas RGBA sắc nét (512x512)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center = size / 2
    r = size * 0.44

    # 1. Nền bo góc Dark Slate Cyan (#0F172A)
    draw.rounded_rectangle(
        [size * 0.05, size * 0.05, size * 0.95, size * 0.95],
        radius=int(size * 0.2),
        fill="#0F172A",
        outline="#1E293B",
        width=int(size * 0.015)
    )

    # 2. Khung Khiên Bảo Vệ (Shield Outer - Hexagonal Style)
    shield_points = [
        (center, size * 0.18),                 # Đỉnh trên
        (size * 0.82, size * 0.28),            # Vai phải
        (size * 0.82, size * 0.60),            # Thân phải
        (center, size * 0.84),                 # Đáy nhọn
        (size * 0.18, size * 0.60),            # Thân trái
        (size * 0.18, size * 0.28)             # Vai trái
    ]
    draw.polygon(shield_points, fill="#1E3A8A", outline="#3B82F6", width=int(size * 0.025))

    # 3. Lõi Khiên Trong (Inner Core Glow - Neon Cyan)
    inner_shield = [
        (center, size * 0.26),
        (size * 0.74, size * 0.34),
        (size * 0.74, size * 0.58),
        (center, size * 0.78),
        (size * 0.26, size * 0.58),
        (size * 0.26, size * 0.34)
    ]
    draw.polygon(inner_shield, fill="#0284C7", outline="#38BDF8", width=int(size * 0.015))

    # 4. Biểu tượng Khóa / Lõi Năng Lượng Chữ V (Vault Core)
    core_points = [
        (center - size * 0.12, size * 0.40),
        (center, size * 0.52),
        (center + size * 0.12, size * 0.40),
        (center, size * 0.66)
    ]
    draw.polygon(core_points, fill="#F0F9FF", outline="#06B6D4", width=int(size * 0.01))

    # 5. Đốm sáng phản chiếu (Top-left Highlight)
    draw.ellipse(
        [center - size * 0.04, size * 0.48 - size * 0.04, center + size * 0.04, size * 0.48 + size * 0.04],
        fill="#22D3EE"
    )

    return img

def export_all_icons():
    """Xuất ra toàn bộ các định dạng icon cho App và Inno Setup"""
    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)
    
    print("🎨 Đang tự động vẽ Logo & Icon cho ứng dụng...")
    master_logo = draw_cyber_shield_logo(size=512)

    # 1. Lưu file PNG chất lượng cao (512x512) cho UI App
    png_path = assets_dir / "app_logo.png"
    master_logo.save(png_path, format="PNG")
    print(f"✅ Đã tạo PNG Icon: {png_path}")

    # 2. Lưu file ICO đa kích thước (256, 128, 64, 48, 32, 16) cho Windows & Inno Setup
    ico_path = assets_dir / "app_logo.ico"
    master_logo.save(
        ico_path,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    )
    print(f"✅ Đã tạo ICO Icon: {ico_path}")

if __name__ == "__main__":
    export_all_icons()