import json
import os
import time
from difflib import SequenceMatcher
from pathlib import Path


FOLDER_INDEX_FILE = Path(
    "data/file_index/folder_index.json"
)


SKIP_FOLDER_NAMES = {
    "appdata",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    ".idea",
    ".vscode",
    "cache",
    "temp",
    "tmp",
    "$recycle.bin",
    "system volume information"
}


class FileControl:

    def normalize(
        self,
        text: str
    ) -> str:
        return (
            str(text)
            .lower()
            .strip()
            .replace("_", " ")
            .replace("-", " ")
        )

    def get_search_roots(self) -> list[Path]:
        roots = []
        home = Path.home()

        common_folders = [
            home / "Desktop",
            home / "Downloads",
            home / "Documents",
            home / "Pictures",
            home / "Videos",
            home / "Music"
        ]

        for folder in common_folders:
            if folder.exists():
                roots.append(folder)

        cwd = Path.cwd()

        roots.append(cwd)

        for parent in list(cwd.parents)[:3]:
            if parent.exists():
                roots.append(parent)

        unique_roots = []
        seen = set()

        for root in roots:
            resolved = str(root.resolve()).lower()

            if resolved not in seen:
                seen.add(resolved)
                unique_roots.append(root)

        return unique_roots

    def should_skip_folder(
        self,
        folder: Path
    ) -> bool:
        name = folder.name.lower().strip()

        if name in SKIP_FOLDER_NAMES:
            return True

        if name.startswith("$"):
            return True

        return False

    def scan_folders(
        self,
        max_depth: int = 5,
        max_folders: int = 15000
    ) -> list[str]:
        folders = []
        seen = set()

        roots = self.get_search_roots()

        for root in roots:
            stack = [
                (
                    root,
                    0
                )
            ]

            while stack:
                current_folder, depth = stack.pop()

                if len(folders) >= max_folders:
                    break

                try:
                    resolved = str(
                        current_folder.resolve()
                    )

                    resolved_key = resolved.lower()

                    if resolved_key in seen:
                        continue

                    seen.add(
                        resolved_key
                    )

                    folders.append(
                        resolved
                    )

                    if depth >= max_depth:
                        continue

                    with os.scandir(
                        current_folder
                    ) as entries:
                        for entry in entries:
                            try:
                                if not entry.is_dir(
                                    follow_symlinks=False
                                ):
                                    continue

                                child = Path(
                                    entry.path
                                )

                                if self.should_skip_folder(
                                    child
                                ):
                                    continue

                                stack.append(
                                    (
                                        child,
                                        depth + 1
                                    )
                                )

                            except Exception:
                                continue

                except Exception:
                    continue

        return sorted(
            folders,
            key=lambda value: value.lower()
        )

    def save_index(
        self,
        folders: list[str]
    ):
        FOLDER_INDEX_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        data = {
            "created_at": time.time(),
            "folder_count": len(folders),
            "folders": folders
        }

        with open(
            FOLDER_INDEX_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                data,
                f,
                indent=4
            )

    def load_index(
        self
    ) -> list[str]:
        if not FOLDER_INDEX_FILE.exists():
            return []

        try:
            with open(
                FOLDER_INDEX_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

            folders = data.get(
                "folders",
                []
            )

            if isinstance(
                folders,
                list
            ):
                return [
                    str(folder)
                    for folder in folders
                    if str(folder).strip()
                ]

        except Exception:
            return []

        return []

    def refresh_folder_index(
        self
    ) -> str:
        folders = self.scan_folders()
        self.save_index(
            folders
        )

        return (
            "Folder scan complete. "
            f"Indexed {len(folders)} folders."
        )

    def ensure_index(
        self
    ) -> list[str]:
        folders = self.load_index()

        if not folders:
            folders = self.scan_folders()
            self.save_index(
                folders
            )

        return folders

    def score_folder(
        self,
        query: str,
        folder_path: str
    ) -> float:
        query_norm = self.normalize(
            query
        )

        path = Path(
            folder_path
        )

        name_norm = self.normalize(
            path.name
        )

        full_norm = self.normalize(
            str(path)
        )

        if query_norm == name_norm:
            return 100

        if name_norm.startswith(
            query_norm
        ):
            return 90

        if query_norm in name_norm:
            return 82

        if query_norm in full_norm:
            return 72

        name_ratio = SequenceMatcher(
            None,
            query_norm,
            name_norm
        ).ratio()

        full_ratio = SequenceMatcher(
            None,
            query_norm,
            full_norm
        ).ratio()

        return max(
            name_ratio * 80,
            full_ratio * 60
        )

    def find_folder_matches(
        self,
        query: str,
        limit: int = 8
    ) -> list[tuple[str, float]]:
        folders = self.ensure_index()

        scored = []

        for folder in folders:
            score = self.score_folder(
                query,
                folder
            )

            if score >= 45:
                scored.append(
                    (
                        folder,
                        score
                    )
                )

        scored.sort(
            key=lambda item: item[1],
            reverse=True
        )

        return scored[:limit]

    def resolve_folder(
        self,
        query: str
    ) -> Path | None:
        query = str(query).strip()

        if not query:
            return None

        direct_path = Path(
            os.path.expandvars(
                os.path.expanduser(
                    query
                )
            )
        )

        if direct_path.exists() and direct_path.is_dir():
            return direct_path

        matches = self.find_folder_matches(
            query,
            limit=1
        )

        if not matches:
            self.refresh_folder_index()

            matches = self.find_folder_matches(
                query,
                limit=1
            )

        if not matches:
            return None

        folder_path, score = matches[0]

        if score < 55:
            return None

        folder = Path(
            folder_path
        )

        if folder.exists() and folder.is_dir():
            return folder

        return None

    def open_folder(
        self,
        query: str
    ) -> str:
        folder = self.resolve_folder(
            query
        )

        if folder is None:
            return f"Folder '{query}' was not found."

        try:
            os.startfile(
                str(folder)
            )

            return f"Opening {folder.name} folder."

        except Exception as e:
            return f"Failed to open folder: {e}"

    def find_folder(
        self,
        query: str
    ) -> str:
        matches = self.find_folder_matches(
            query
        )

        if not matches:
            return f"No folders found for '{query}'."

        lines = []

        for folder_path, score in matches:
            folder = Path(
                folder_path
            )

            lines.append(
                f"{folder.name} - {folder_path}"
            )

        return "\n".join(
            lines
        )

    def open_path(
        self,
        path: str
    ) -> str:
        target = Path(
            os.path.expandvars(
                os.path.expanduser(
                    path
                )
            )
        )

        if not target.exists():
            return f"Path does not exist: {path}"

        try:
            os.startfile(
                str(target)
            )

            return f"Opening {target.name}."

        except Exception as e:
            return f"Failed to open path: {e}"