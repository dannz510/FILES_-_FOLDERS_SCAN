r"""
PyInstaller Build Script — Pentest Vault & Command Center v2.0
Target Path: D:\Do not open\Obsidian\Dannz\appscan
"""
import os
import sys
import shutil
import stat
import subprocess
import PyInstaller.__main__
from pathlib import Path

# Thư mục gốc dự án
PROJECT_ROOT = Path(r"D:\Do not open\Obsidian\Dannz\appscan")
ENTRY_POINT = PROJECT_ROOT / "main.py"
OUTPUT_NAME = "PentestVaultApp"

ASSETS_DIR = PROJECT_ROOT / "assets"
ICON_PATH = ASSETS_DIR / "app_logo.ico"
UTILS_DIR = PROJECT_ROOT / "utils"


def remove_readonly(func, path, exc_info):
    """Xóa thuộc tính Read-Only nếu file bị lock quyền bởi Windows."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def cleanup_previous_builds():
    """Dọn dẹp tiến trình ngầm và xóa folder dist/build cũ."""
    print("🧹 [BUILD] Terminating running processes & cleaning legacy builds...")
    subprocess.run(
        f"taskkill /F /IM {OUTPUT_NAME}.exe",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for folder in ["build", "dist"]:
        path = PROJECT_ROOT / folder
        if path.exists():
            try:
                shutil.rmtree(path, onerror=remove_readonly)
                print(f"   - Removed: {folder}/")
            except Exception:
                subprocess.run(f'rmdir /s /q "{path}"', shell=True)


def run_pyinstaller():
    print(f"⚡ [BUILD] Compiling '{ENTRY_POINT.name}' -> '{OUTPUT_NAME}.exe'...")

    args = [
        str(ENTRY_POINT),
        f"--name={OUTPUT_NAME}",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
        # Ép PyInstaller nhận diện root directory
        f"--paths={str(PROJECT_ROOT)}",
        # Explicitly declare hidden imports cho utils
        "--hidden-import=utils",
        "--hidden-import=utils.logger",
        f"--add-data={str(UTILS_DIR)};utils",
    ]

    # Nhúng Icon .exe ngoài File Explorer
    if ICON_PATH.exists():
        args.append(f"--icon={str(ICON_PATH)}")
        print(f"   + App Icon: {ICON_PATH}")

    # Nhúng thư mục assets
    if ASSETS_DIR.exists():
        args.append(f"--add-data={str(ASSETS_DIR)};assets")
        print(f"   + Bundled Assets: {ASSETS_DIR}")

    # Nhúng thư viện CustomTkinter assets
    try:
        import customtkinter
        ctk_path = Path(customtkinter.__file__).parent
        args.append(f"--add-data={str(ctk_path)};customtkinter")
        print(f"   + Bundled CTK Assets: {ctk_path}")
    except ImportError:
        print("   ! Warning: CustomTkinter not found in Python environment.")

    # Khởi chạy PyInstaller
    PyInstaller.__main__.run(args)
    print(
        f"\n✅ [BUILD SUCCESS] Executable generated at:\n   {PROJECT_ROOT / 'dist' / OUTPUT_NAME / f'{OUTPUT_NAME}.exe'}"
    )


if __name__ == "__main__":
    cleanup_previous_builds()
    run_pyinstaller()