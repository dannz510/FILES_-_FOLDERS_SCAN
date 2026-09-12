import os
import json
import datetime
from pathlib import Path
from typing import Optional, Any

from utils.logger import AppLogger
from utils.os_utils import encode_path_for_obsidian
from config.settings import ALLOWED_EXTENSIONS

logger = AppLogger("exporter")


class StreamExporter:
    """Base class for streaming exporters.

    Exports are performed in a *streaming* fashion — the file is written
    incrementally rather than building a giant string in memory, which keeps
    memory usage O(1) regardless of vault size.
    """

    def __init__(self, allowed_extensions: Optional[set[str]] = None) -> None:
        self.allowed_extensions = allowed_extensions or ALLOWED_EXTENSIONS

    def _iter_vault(self, root_path: Path):
        """Yield ``(dir_path, rel_level)`` tuples for directories and
        ``(file_path, rel_level)`` for files in a single os.walk pass."""
        for root, dirs, files in os.walk(root_path):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            current = Path(root)
            try:
                level = 0 if current == root_path else len(current.relative_to(root_path).parts)
            except ValueError:
                level = 0
            yield current, dirs, files, level


class MarkdownExporter(StreamExporter):
    """Stream-write a Markdown knowledge-base index from the vault."""

    def generate_full_index(self, root_path: Path, output_file: str) -> bool:
        try:
            output = Path(output_file)
            with open(output, "w", encoding="utf-8") as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write("# 🛡️ PENTESTER KNOWLEDGE BASE INDEX\n\n")
                f.write(f"> **Root Directory:** `{root_path}`\n")
                f.write(f"> **Generated:** `{timestamp}`\n\n")
                f.write("---\n")

                for current, dirs, files, level in self._iter_vault(root_path):
                    if level > 0:
                        indent = "  " * (level - 1)
                        f.write(f"{indent}- 📂 **{current.name}**\n")

                    for file_name in sorted(files):
                        fp = current / file_name
                        if fp.suffix.lower() in self.allowed_extensions:
                            indent = "  " * level
                            link = encode_path_for_obsidian(str(fp.resolve()))
                            f.write(f"{indent}- [📄 {file_name}](file:///{link})\n")

            logger.info("Markdown index written to %s", output)
            return True
        except Exception as exc:
            logger.error("Markdown export failed: %s", exc)
            return False

    def generate_subfolder_index(self, root_path: Path, subfolder: str,
                                  output_file: str) -> bool:
        base_root = Path(root_path).resolve()

        if Path(subfolder).is_absolute():
            target_path = Path(subfolder).resolve()
        else:
            target_path = (base_root / subfolder).resolve()

        if not target_path.exists():
            logger.error("Subfolder does not exist: %s", target_path)
            return False

        try:
            output = Path(output_file)
            with open(output, "w", encoding="utf-8") as f:
                folder_name = target_path.name
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                try:
                    rel_parts = target_path.relative_to(base_root).parts
                    tags = ["#pentest", "#cybersecurity"] + \
                           [f"#{p.lower().replace(' ', '_')}" for p in rel_parts if p]
                except ValueError:
                    tags = ["#pentest", "#cybersecurity"]

                f.write("---\n")
                f.write(f"tags: {', '.join(tags)}\n")
                f.write(f"generated: {timestamp}\n")
                f.write("---\n\n")
                f.write(f"# 📂 Chi tiết Folder: {folder_name}\n\n")
                f.write(f"> **Đường dẫn:** `{target_path}`\n\n")
                f.write("[[INDEX_FULL.md|← Back to Root Index]]\n\n---\n\n")

                for current, dirs, files, level in self._iter_vault(target_path):
                    if level > 0:
                        indent = "  " * (level - 1)
                        rel_dir = current.relative_to(target_path).as_posix()
                        encoded = encode_path_for_obsidian(rel_dir)
                        f.write(f"{indent}- 📂 [{current.name}]({encoded}/)\n")

                    for file_name in sorted(files):
                        fp = current / file_name
                        if fp.suffix.lower() in self.allowed_extensions:
                            indent = "  " * level
                            rel_file = fp.relative_to(target_path).as_posix()
                            encoded = encode_path_for_obsidian(rel_file)
                            f.write(f"{indent}- [📄 {file_name}]({encoded})\n")

            logger.info("Subfolder index written to %s", output)
            return True
        except Exception as exc:
            logger.error("Subfolder export failed: %s", exc)
            return False


class JSONExporter(StreamExporter):
    """Export vault index as structured JSON."""

    def generate_json_index(self, root_path: Path, output_file: str) -> bool:
        try:
            output = Path(output_file)
            data: list[dict[str, Any]] = []

            for current, dirs, files, level in self._iter_vault(root_path):
                dir_entry: dict[str, Any] = {
                    "type": "folder",
                    "name": current.name if current != root_path else str(current.name),
                    "path": str(current.resolve()),
                    "level": level,
                    "children": [],
                }
                for file_name in sorted(files):
                    fp = current / file_name
                    if fp.suffix.lower() in self.allowed_extensions:
                        dir_entry["children"].append({
                            "type": "file",
                            "name": file_name,
                            "path": str(fp.resolve()),
                            "extension": fp.suffix.lower(),
                        })
                data.append(dir_entry)

            with open(output, "w", encoding="utf-8") as f:
                json.dump({"root": str(root_path.resolve()), "items": data}, f, indent=2)

            logger.info("JSON index written to %s", output)
            return True
        except Exception as exc:
            logger.error("JSON export failed: %s", exc)
            return False
