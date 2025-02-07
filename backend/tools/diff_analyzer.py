"""Diff analysis utilities for PR review."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from shared.logging import get_logger

log = get_logger("tools.diff")


@dataclass
class HunkLine:
    kind: str  # "context", "added", "removed"
    number_old: Optional[int]
    number_new: Optional[int]
    content: str


@dataclass
class FileDiff:
    path: str
    old_path: Optional[str]
    hunks: list[list[HunkLine]] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0

    @property
    def is_new(self) -> bool:
        return self.old_path == "/dev/null"

    @property
    def is_deleted(self) -> bool:
        return self.path == "/dev/null"


def parse_diff(unified_diff: str) -> list[FileDiff]:
    """Parse a unified diff string into structured FileDiff objects."""
    files: list[FileDiff] = []
    current: Optional[FileDiff] = None
    current_hunk: list[HunkLine] = []
    old_line = new_line = 0

    for raw_line in unified_diff.splitlines():
        if raw_line.startswith("diff --git"):
            if current_hunk and current:
                current.hunks.append(current_hunk)
            current_hunk = []
            current = FileDiff(path="", old_path=None)
            files.append(current)
            continue

        if current is None:
            continue

        if raw_line.startswith("--- "):
            current.old_path = _strip_prefix(raw_line[4:])
        elif raw_line.startswith("+++ "):
            current.path = _strip_prefix(raw_line[4:])
        elif raw_line.startswith("@@"):
            if current_hunk:
                current.hunks.append(current_hunk)
            current_hunk = []
            old_line, new_line = _parse_hunk_header(raw_line)
        elif raw_line.startswith("+"):
            current_hunk.append(HunkLine("added", None, new_line, raw_line[1:]))
            current.additions += 1
            new_line += 1
        elif raw_line.startswith("-"):
            current_hunk.append(HunkLine("removed", old_line, None, raw_line[1:]))
            current.deletions += 1
            old_line += 1
        else:
            current_hunk.append(HunkLine("context", old_line, new_line, raw_line[1:]))
            old_line += 1
            new_line += 1

    if current_hunk and current:
        current.hunks.append(current_hunk)

    return files


def summarize_diff(files: list[FileDiff]) -> dict[str, object]:
    """Produce a high-level summary dict from parsed file diffs."""
    total_add = sum(f.additions for f in files)
    total_del = sum(f.deletions for f in files)
    return {
        "files_changed": len(files),
        "total_additions": total_add,
        "total_deletions": total_del,
        "net_change": total_add - total_del,
        "files": [
            {
                "path": f.path,
                "additions": f.additions,
                "deletions": f.deletions,
                "is_new": f.is_new,
                "is_deleted": f.is_deleted,
            }
            for f in files
        ],
    }


def detect_issues(files: list[FileDiff]) -> list[dict[str, object]]:
    """Heuristic checks for common diff issues."""
    issues: list[dict[str, object]] = []
    for file_diff in files:
        for hunk in file_diff.hunks:
            for line in hunk:
                if line.kind == "added":
                    _check_line_issues(file_diff.path, line, issues)
    return issues


def _check_line_issues(
    path: str, line: HunkLine, issues: list[dict[str, object]]
) -> None:
    content = line.content
    if re.search(r"\bTODO\b|\bFIXME\b|\bHACK\b", content, re.I):
        issues.append({"path": path, "line": line.number_new, "type": "todo", "detail": content.strip()})
    if re.search(r"(password|secret|api_key)\s*=\s*['\"][^'\"]{4,}", content, re.I):
        issues.append({"path": path, "line": line.number_new, "type": "secret", "detail": "Possible hardcoded secret"})
    if len(content) > 120:
        issues.append({"path": path, "line": line.number_new, "type": "long_line", "detail": f"Line length {len(content)}"})


def _strip_prefix(path: str) -> str:
    for prefix in ("a/", "b/"):
        if path.startswith(prefix):
            return path[2:]
    return path


def _parse_hunk_header(header: str) -> tuple[int, int]:
    m = re.search(r"@@ -(\d+)(?:,\d+)? \+(\d+)", header)
    if m:
        return int(m.group(1)), int(m.group(2))
    return 1, 1
