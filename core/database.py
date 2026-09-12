import sqlite3
import threading
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VaultItem:
    """Lightweight value object representing a single vault entry."""
    path: str
    name: str
    ext: str
    item_type: str  # "folder" | "file"
    parent_path: str = ""
    size: int = 0
    modified: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "ext": self.ext,
            "type": self.item_type,
            "parent_path": self.parent_path,
            "size": self.size,
            "modified": self.modified,
        }


class FTSIndexEngine:
    """In-memory SQLite (FTS5) search engine for the vault index.

    All public methods acquire a re-entrant lock so the engine is safe to
    call from multiple worker threads simultaneously.
    """

    FTS_TABLE = "vault_index"

    def __init__(self) -> None:
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.RLock()
        self._item_count: int = 0
        self.init_db()

    # ------------------------------------------------------------------ #
    # Database lifecycle
    # ------------------------------------------------------------------ #
    def init_db(self) -> None:
        """Create (or recreate) the FTS5 virtual table."""
        with self._lock:
            if self._conn is not None:
                self._conn.close()
            self._conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=MEMORY")
            self._conn.execute("PRAGMA synchronous=OFF")
            self._conn.execute(
                f"""
                CREATE VIRTUAL TABLE {self.FTS_TABLE} USING fts5(
                    path UNINDEXED,
                    name,
                    ext UNINDEXED,
                    type UNINDEXED,
                    parent_path UNINDEXED,
                    size UNINDEXED,
                    modified UNINDEXED,
                    content_snippet UNINDEXED
                )
                """
            )
            self._item_count = 0

    def clear(self) -> None:
        """Delete every row from the index."""
        with self._lock:
            if self._conn is None:
                return
            self._conn.execute(f"DELETE FROM {self.FTS_TABLE}")
            self._conn.commit()
            self._item_count = 0

    @property
    def item_count(self) -> int:
        with self._lock:
            return self._item_count

    # ------------------------------------------------------------------ #
    # Data operations
    # ------------------------------------------------------------------ #
    def bulk_insert(self, items: list[VaultItem]) -> int:
        """Insert *items* in a single transaction.  Returns row count."""
        with self._lock:
            if self._conn is None:
                return 0
            rows = [
                (
                    it.path, it.name, it.ext, it.item_type,
                    it.parent_path, it.size, it.modified,
                    it.name[:200],
                )
                for it in items
            ]
            self._conn.executemany(
                f"""INSERT INTO {self.FTS_TABLE}
                    (path, name, ext, type, parent_path, size, modified, content_snippet)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )
            self._conn.commit()
            self._item_count += len(rows)
            return len(rows)

    def insert_single(self, item: VaultItem) -> None:
        with self._lock:
            if self._conn is None:
                return
            self._conn.execute(
                f"""INSERT INTO {self.FTS_TABLE}
                    (path, name, ext, type, parent_path, size, modified, content_snippet)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    item.path, item.name, item.ext, item.item_type,
                    item.parent_path, item.size, item.modified, item.name[:200],
                ),
            )
            self._conn.commit()
            self._item_count += 1

    def delete_by_path(self, path: str) -> None:
        """Remove a single row identified by its absolute *path*."""
        with self._lock:
            if self._conn is None:
                return
            self._conn.execute(
                f"DELETE FROM {self.FTS_TABLE} WHERE path = ?", (path,)
            )
            self._conn.commit()
            self._item_count = max(0, self._item_count - 1)

    def update_by_path(self, path: str, **kwargs: Any) -> None:
        """Update columns of a row identified by *path*."""
        if not kwargs:
            return
        cols = ", ".join(f"{k} = ?" for k in kwargs)
        params = list(kwargs.values()) + [path]
        with self._lock:
            if self._conn is None:
                return
            self._conn.execute(
                f"UPDATE {self.FTS_TABLE} SET {cols} WHERE path = ?", params
            )
            self._conn.commit()

    # ------------------------------------------------------------------ #
    # Search
    # ------------------------------------------------------------------ #
    def search(self, query_str: str, limit: int = 100) -> list[dict[str, Any]]:
        """Full-text search across file names, extensions and content snippets.

        Supports FTS5 query syntax (tokens, phrases, prefix *, etc.).
        Returns a list of dictionaries.
        """
        if not query_str or self._conn is None:
            return []

        safe_query = query_str.replace('"', "").strip()
        if not safe_query:
            return []

        with self._lock:
            try:
                rows = self._conn.execute(
                    f"""SELECT path, name, ext, type, parent_path, size, modified
                          FROM {self.FTS_TABLE}
                          WHERE {self.FTS_TABLE} MATCH ?
                          ORDER BY rank
                          LIMIT ?""",
                    (safe_query + "*", limit),
                ).fetchall()
            except sqlite3.OperationalError:
                # Fallback to simple LIKE if FTS MATCH fails
                rows = self._conn.execute(
                    f"""SELECT path, name, ext, type, parent_path, size, modified
                          FROM {self.FTS_TABLE}
                          WHERE name LIKE ? OR ext LIKE ?
                          LIMIT ?""",
                    (f"%{safe_query}%", f"%{safe_query}%", limit),
                ).fetchall()

        return [
            {
                "path": r[0], "name": r[1], "ext": r[2], "type": r[3],
                "parent_path": r[4], "size": r[5], "modified": r[6],
            }
            for r in rows
        ]

    def search_like(self, query: str, limit: int = 100) -> list[dict[str, Any]]:
        """LIKE-based fallback search that matches any column partially."""
        if not query or self._conn is None:
            return []
        pattern = f"%{query.lower()}%"
        with self._lock:
            rows = self._conn.execute(
                f"""SELECT path, name, ext, type, parent_path, size, modified
                      FROM {self.FTS_TABLE}
                      WHERE lower(name) LIKE ? OR lower(ext) LIKE ? OR lower(path) LIKE ?
                      ORDER BY name ASC
                      LIMIT ?""",
                (pattern, pattern, pattern, limit),
            ).fetchall()
        return [
            {
                "path": r[0], "name": r[1], "ext": r[2], "type": r[3],
                "parent_path": r[4], "size": r[5], "modified": r[6],
            }
            for r in rows
        ]

    # ------------------------------------------------------------------ #
    # Structural queries
    # ------------------------------------------------------------------ #
    def get_children(self, parent_path: str) -> list[dict[str, Any]]:
        """Return direct children of *parent_path* (sorted dirs-first)."""
        with self._lock:
            if self._conn is None:
                return []
            rows = self._conn.execute(
                f"""SELECT path, name, ext, type, parent_path, size, modified
                      FROM {self.FTS_TABLE}
                      WHERE parent_path = ?
                      ORDER BY CASE WHEN type = 'folder' THEN 0 ELSE 1 END, name ASC""",
                (parent_path,),
            ).fetchall()
        return [
            {
                "path": r[0], "name": r[1], "ext": r[2], "type": r[3],
                "parent_path": r[4], "size": r[5], "modified": r[6],
            }
            for r in rows
        ]

    def get_parent_hierarchy(self, full_path: str) -> list[str]:
        """Walk from root down to *full_path*, returning the chain of ancestor paths."""
        parts = Path(full_path).parts
        hierarchy = []
        for i in range(1, len(parts) + 1):
            hierarchy.append(str(Path(*parts[:i])))
        return hierarchy

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
