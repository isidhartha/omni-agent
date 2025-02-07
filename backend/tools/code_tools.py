"""Code analysis and transformation utilities."""

from __future__ import annotations

import ast
import re
from typing import Any

from shared.logging import get_logger

log = get_logger("tools.code")


def extract_python_symbols(source: str) -> dict[str, list[str]]:
    """Parse Python source and return classes, functions, and imports."""
    result: dict[str, list[str]] = {"classes": [], "functions": [], "imports": []}
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        log.warning("SyntaxError while parsing source: %s", exc)
        return result

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            result["classes"].append(node.name)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            result["functions"].append(node.name)
        elif isinstance(node, ast.Import):
            result["imports"].extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result["imports"].append(node.module)
    return result


def count_lines(source: str) -> dict[str, int]:
    """Return line statistics for a source string."""
    lines = source.splitlines()
    blank = sum(1 for line in lines if not line.strip())
    comment = sum(1 for line in lines if line.strip().startswith(("#", "//")))
    return {
        "total": len(lines),
        "blank": blank,
        "comment": comment,
        "code": len(lines) - blank - comment,
    }


def detect_language(filename: str, content: str = "") -> str:
    """Heuristic language detection from filename and optional content shebang."""
    ext_map = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".rb": "ruby",
        ".sh": "bash",
    }
    suffix = filename.rsplit(".", 1)
    if len(suffix) == 2:
        lang = ext_map.get(f".{suffix[1].lower()}")
        if lang:
            return lang

    # Shebang detection
    if content.startswith("#!/usr/bin/env python") or content.startswith("#!/usr/bin/python"):
        return "python"
    if content.startswith("#!/bin/bash") or content.startswith("#!/bin/sh"):
        return "bash"

    return "unknown"


def extract_error_info(error_text: str) -> dict[str, Any]:
    """Parse common error patterns from a traceback or error string."""
    info: dict[str, Any] = {"error_type": None, "message": None, "line_number": None}

    # Python traceback patterns
    tb_match = re.search(r"(\w+Error|\w+Exception): (.+)$", error_text, re.MULTILINE)
    if tb_match:
        info["error_type"] = tb_match.group(1)
        info["message"] = tb_match.group(2).strip()

    line_match = re.search(r'line (\d+)', error_text)
    if line_match:
        info["line_number"] = int(line_match.group(1))

    return info


def format_code_block(code: str, language: str = "") -> str:
    """Wrap code in a markdown fenced block."""
    return f"```{language}\n{code.rstrip()}\n```"
