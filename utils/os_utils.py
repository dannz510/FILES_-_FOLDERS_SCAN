import os
import sys
import shutil
import subprocess
from pathlib import Path
from urllib.parse import quote
from typing import Union


def encode_path_for_obsidian(path_str: str) -> str:
    """Convert a Windows path into an Obsidian-compatible file:// URI."""
    return quote(str(path_str).replace("\\", "/"), safe="/:-_")


def open_local_path(path_obj: Union[str, Path]) -> bool:
    """Open a file or folder using the OS-default application."""
    try:
        path_obj = Path(path_obj)
        if not path_obj.exists():
            return False
        if sys.platform == "win32":
            os.startfile(str(path_obj))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path_obj)])
        else:
            subprocess.Popen(["xdg-open", str(path_obj)])
        return True
    except Exception:
        return False


def get_formatted_size(size_bytes: int) -> str:
    """Human-readable byte size (B / KB / MB / GB / TB / PB)."""
    if size_bytes <= 0:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def get_directory_size(path_obj: Path) -> int:
    """Recursively compute the total byte size of every file under *path_obj*."""
    total = 0
    try:
        for root, _dirs, files in os.walk(path_obj):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
    except PermissionError:
        pass
    return total


def safe_remove(path_obj: Union[str, Path]) -> bool:
    """Attempt to delete a file or directory, returning True on success."""
    try:
        path_obj = Path(path_obj)
        if path_obj.is_dir():
            shutil.rmtree(path_obj)
        else:
            path_obj.unlink()
        return True
    except Exception:
        return False


def is_hidden(path_obj: Union[str, Path]) -> bool:
    """Return True when *path_obj* is a hidden file/folder (platform-aware)."""
    name = Path(path_obj).name
    if name.startswith("."):
        return True
    if sys.platform == "win32":
        try:
            import ctypes
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path_obj))
            if attrs == -1:
                return False
            return bool(attrs & 0x02)  # FILE_ATTRIBUTE_HIDDEN
        except Exception:
            return False
    return False


def ensure_dir(path_obj: Union[str, Path]) -> Path:
    """Create *path_obj* (and parents) if it does not exist, then return it."""
    path_obj = Path(path_obj)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj
