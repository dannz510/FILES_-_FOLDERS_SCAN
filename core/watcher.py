import os
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileModifiedEvent, FileMovedEvent

from core.database import FTSIndexEngine, VaultItem
from config.settings import WATCHER_DEBOUNCE_MS
from utils.logger import AppLogger

logger = AppLogger("watcher")


class VaultEventHandler(FileSystemEventHandler):
    """Watchdog event handler that forwards file-system changes to the index engine.

    Events are debounced to avoid duplicate updates when an editor saves a
    file (create + modify + move can fire in quick succession).
    """

    def __init__(self, db_engine: FTSIndexEngine, allowed_extensions: set[str],
                 root_path: Path, on_change: Optional[Callable] = None) -> None:
        super().__init__()
        self.db_engine = db_engine
        self.allowed_extensions = allowed_extensions
        self.root_path = str(root_path)
        self.on_change = on_change
        self._pending: dict[str, str] = {}  # path -> action
        self._lock = threading.Lock()

    def _is_valid_path(self, path: str) -> bool:
        """Ignore paths outside the vault root or hidden files."""
        try:
            resolved = Path(path).resolve()
            if not str(resolved).startswith(self.root_path):
                return False
            if Path(path).name.startswith("."):
                return False
            return True
        except Exception:
            return False

    def _debounce_dispatch(self) -> None:
        """Process all pending events as a batch."""
        with self._lock:
            pending = list(self._pending.items())
            self._pending.clear()

        for path_str, action in pending:
            try:
                if not self._is_valid_path(path_str):
                    continue
                self._handle_action(path_str, action)
            except Exception as exc:
                logger.debug("Watcher event error for %s: %s", path_str, exc)

        if pending and self.on_change:
            self.on_change()

    def _handle_action(self, path_str: str, action: str) -> None:
        path = Path(path_str)

        if action in ("created", "modified"):
            if path.is_dir():
                self._index_directory(path)
            elif path.is_file():
                ext = path.suffix.lower()
                if ext in self.allowed_extensions:
                    try:
                        stat = path.stat()
                        item = VaultItem(
                            path=str(path),
                            name=path.name,
                            ext=ext,
                            item_type="file",
                            parent_path=str(path.parent),
                            size=stat.st_size,
                            modified=stat.st_mtime,
                        )
                        self.db_engine.insert_single(item)
                    except OSError:
                        pass

        elif action == "deleted":
            self.db_engine.delete_by_path(str(path))

    def _index_directory(self, dir_path: Path) -> None:
        """Walk a newly-created directory and index all valid files."""
        try:
            for root, dirs, files in os.walk(dir_path):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for f in files:
                    fp = Path(root) / f
                    ext = fp.suffix.lower()
                    if ext in self.allowed_extensions:
                        try:
                            stat = fp.stat()
                            item = VaultItem(
                                path=str(fp),
                                name=f,
                                ext=ext,
                                item_type="file",
                                parent_path=str(fp.parent),
                                size=stat.st_size,
                                modified=stat.st_mtime,
                            )
                            self.db_engine.insert_single(item)
                        except OSError:
                            pass
        except PermissionError:
            logger.warning("Permission denied in watcher: %s", dir_path)

    def on_created(self, event: FileSystemEvent) -> None:
        self._schedule(str(event.src_path), "created")

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._schedule(str(event.src_path), "deleted")

    def on_modified(self, event: FileSystemEvent) -> None:
        self._schedule(str(event.src_path), "modified")

    def on_moved(self, event: FileMovedEvent) -> None:
        self._schedule(str(event.src_path), "deleted")
        self._schedule(str(event.dest_path), "created")

    def _schedule(self, path: str, action: str) -> None:
        with self._lock:
            self._pending[path] = action
        threading.Thread(
            target=self._debounce_and_process, daemon=True
        ).start()

    def _debounce_and_process(self) -> None:
        time.sleep(WATCHER_DEBOUNCE_MS / 1000.0)
        self._debounce_dispatch()


class VaultWatcher:
    """Wraps watchdog's ``Observer`` to monitor a vault directory.

    Usage::

        watcher = VaultWatcher(db_engine, allowed_exts, root_path)
        watcher.start(on_change=lambda: print("index updated"))
        ...
        watcher.stop()
    """

    def __init__(self, db_engine: FTSIndexEngine, allowed_extensions: set[str],
                 root_path: Path) -> None:
        self.db_engine = db_engine
        self.root_path = Path(root_path)
        self.allowed_extensions = allowed_extensions
        self.observer: Optional[Observer] = None
        self.handler: Optional[VaultEventHandler] = None
        self._running = False

    def start(self, on_change: Optional[Callable] = None) -> bool:
        """Begin watching the vault root.  Returns True on success."""
        if self._running or not self.root_path.exists():
            return False
        try:
            self.handler = VaultEventHandler(
                self.db_engine, self.allowed_extensions,
                self.root_path, on_change,
            )
            self.observer = Observer()
            self.observer.schedule(
                self.handler, str(self.root_path), recursive=True
            )
            self.observer.start()
            self._running = True
            logger.info("Vault watcher started on %s", self.root_path)
            return True
        except Exception as exc:
            logger.error("Failed to start watcher: %s", exc)
            return False

    def stop(self) -> None:
        """Stop the observer thread."""
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=3.0)
        self._running = False
        logger.info("Vault watcher stopped")

    @property
    def is_running(self) -> bool:
        return self._running
