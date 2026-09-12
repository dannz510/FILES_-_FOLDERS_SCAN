import os
import sys
import subprocess
from pathlib import Path
from urllib.parse import quote

def encode_path_for_obsidian(path_str: str) -> str:
    return quote(path_str.replace('\\', '/'), safe='/:-_')

def open_local_path(path_obj: Path) -> bool:
    try:
        if sys.platform == 'win32':
            os.startfile(path_obj)
        else:
            opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
            subprocess.call([opener, str(path_obj)])
        return True
    except Exception:
        return False