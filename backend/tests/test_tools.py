"""Tests for tools package."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from tools.code_tools import (
    count_lines,
    detect_language,
    extract_error_info,
    extract_python_symbols,
    format_code_block,
)
from tools.diff_analyzer import detect_issues, parse_diff, summarize_diff


# --- code_tools ---

def test_count_lines_basic():
    source = "x = 1\n\n# comment\ny = 2"
    result = count_lines(source)
    assert result["total"] == 4
    assert result["blank"] == 1
    assert result["comment"] == 1
    assert result["code"] == 2


def test_detect_language_by_extension():
    assert detect_language("main.py") == "python"
    assert detect_language("App.tsx") == "typescript"
    assert detect_language("index.js") == "javascript"
    assert detect_language("unknown.xyz") == "unknown"


def test_detect_language_shebang():
    assert detect_language("script", "#!/usr/bin/env python\nprint('hi')") == "python"
    assert detect_language("run", "#!/bin/bash\necho hi") == "bash"


def test_extract_python_symbols():
    source = "import os\nfrom pathlib import Path\nclass Foo:\n    pass\ndef bar(): pass"
    result = extract_python_symbols(source)
    assert "Foo" in result["classes"]
    assert "bar" in result["functions"]
    assert "os" in result["imports"]
    assert "pathlib" in result["imports"]


def test_extract_python_symbols_invalid():
    result = extract_python_symbols("def not valid python ::::")
    assert result["classes"] == []
    assert result["functions"] == []


def test_extract_error_info():
    tb = "Traceback (most recent call last):\n  File 'x.py', line 5, in foo\nValueError: bad input"
    info = extract_error_info(tb)
    assert info["error_type"] == "ValueError"
    assert info["message"] == "bad input"
    assert info["line_number"] == 5


def test_format_code_block():
    block = format_code_block("print('hi')", "python")
    assert block.startswith("```python")
    assert "print('hi')" in block
    assert block.endswith("```")


# --- diff_analyzer ---

SAMPLE_DIFF = """\
diff --git a/main.py b/main.py
--- a/main.py
+++ b/main.py
@@ -1,3 +1,5 @@
 def foo():
-    pass
+    # TODO fix this
+    password = 'hardcoded'
+    return True
"""


def test_parse_diff_counts():
    files = parse_diff(SAMPLE_DIFF)
    assert len(files) == 1
    assert files[0].additions == 3
    assert files[0].deletions == 1


def test_summarize_diff():
    files = parse_diff(SAMPLE_DIFF)
    summary = summarize_diff(files)
    assert summary["files_changed"] == 1
    assert summary["total_additions"] == 3
    assert summary["total_deletions"] == 1


def test_detect_issues_todo_and_secret():
    files = parse_diff(SAMPLE_DIFF)
    issues = detect_issues(files)
    types = [i["type"] for i in issues]
    assert "todo" in types
    assert "secret" in types
