"""Git repository analysis tools."""

from __future__ import annotations

import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Optional

from shared.logging import get_logger

log = get_logger("tools.git")

# Language detection by extension
_EXT_LANG: dict[str, str] = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".md": "Markdown",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".html": "HTML",
    ".css": "CSS",
}

_IGNORE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "coverage",
}


def analyze_repo(repo_path: str) -> dict[str, Any]:
    """Walk a local repository and return structure + language breakdown."""
    root = Path(repo_path)
    if not root.is_dir():
        raise ValueError(f"Path does not exist or is not a directory: {repo_path}")

    structure: dict[str, Any] = {}
    lang_counter: Counter[str] = Counter()
    file_count = 0

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored directories in-place
        dirnames[:] = [d for d in dirnames if d not in _IGNORE_DIRS]
        rel_dir = Path(dirpath).relative_to(root)
        node = _get_nested(structure, rel_dir.parts)

        for fname in sorted(filenames):
            ext = Path(fname).suffix.lower()
            lang = _EXT_LANG.get(ext, "Other")
            lang_counter[lang] += 1
            file_count += 1
            node[fname] = lang

    languages = [lang for lang, _ in lang_counter.most_common() if lang != "Other"]
    summary = _build_summary(repo_path, file_count, lang_counter)

    return {
        "repo_path": str(root.resolve()),
        "structure": structure,
        "summary": summary,
        "file_count": file_count,
        "languages": languages,
    }


def get_diff(repo_path: str, base: str = "HEAD~1", head: str = "HEAD") -> str:
    """Return unified diff between two refs using gitpython if available."""
    try:
        import git  # type: ignore[import]

        repo = git.Repo(repo_path)
        diff = repo.git.diff(base, head, unified=3)
        return diff
    except Exception as exc:
        log.warning("gitpython unavailable or diff failed: %s", exc)
        return ""


def list_changed_files(repo_path: str) -> list[str]:
    """List files changed vs HEAD."""
    try:
        import git  # type: ignore[import]

        repo = git.Repo(repo_path)
        changed = [item.a_path for item in repo.index.diff(None)]
        changed += repo.untracked_files
        return changed
    except Exception as exc:
        log.warning("Could not list changed files: %s", exc)
        return []


def _get_nested(d: dict[str, Any], parts: tuple[str, ...]) -> dict[str, Any]:
    node = d
    for part in parts:
        if part:
            node = node.setdefault(part, {})
    return node


def _build_summary(repo_path: str, file_count: int, lang_counter: Counter[str]) -> str:
    name = Path(repo_path).name
    top = ", ".join(f"{lang} ({cnt})" for lang, cnt in lang_counter.most_common(5))
    return (
        f"Repository '{name}' contains {file_count} files. "
        f"Primary languages: {top or 'unknown'}."
    )
