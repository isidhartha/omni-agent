"""Tools package — git analysis, code utilities, sandbox, diff analysis."""

from .code_tools import (
    count_lines,
    detect_language,
    extract_error_info,
    extract_python_symbols,
    format_code_block,
)
from .diff_analyzer import FileDiff, HunkLine, detect_issues, parse_diff, summarize_diff
from .git_tools import analyze_repo, get_diff, list_changed_files
from .sandbox import run_code, run_command

__all__ = [
    "count_lines",
    "detect_language",
    "extract_error_info",
    "extract_python_symbols",
    "format_code_block",
    "FileDiff",
    "HunkLine",
    "detect_issues",
    "parse_diff",
    "summarize_diff",
    "analyze_repo",
    "get_diff",
    "list_changed_files",
    "run_code",
    "run_command",
]
