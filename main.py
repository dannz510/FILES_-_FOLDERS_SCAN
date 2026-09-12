"""Compatibility wrapper — delegates to the v2.0 application in app.py.

The full v2.0 architecture lives in app.py (clean entry point).
This file is kept for backward compatibility with existing launch scripts.
"""
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import PentestIndexerApp

if __name__ == "__main__":
    app = PentestIndexerApp()
    app.mainloop()