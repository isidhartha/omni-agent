"""Tests for the sandbox execution module."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from tools.sandbox import run_code, run_command


@pytest.mark.asyncio
async def test_run_python_success():
    result = await run_code("print('hello world')", language="python", timeout=10)
    assert result.exit_code == 0
    assert "hello world" in result.stdout
    assert not result.timed_out


@pytest.mark.asyncio
async def test_run_python_error():
    result = await run_code("raise ValueError('oops')", language="python", timeout=10)
    assert result.exit_code != 0
    assert "ValueError" in result.stderr


@pytest.mark.asyncio
async def test_run_command_echo():
    result = await run_command(
        [sys.executable, "-c", "import sys; print('ok'); sys.exit(0)"],
        timeout=10,
    )
    assert result.exit_code == 0
    assert "ok" in result.stdout


@pytest.mark.asyncio
async def test_timeout_enforced():
    result = await run_code(
        "import time; time.sleep(60)", language="python", timeout=2
    )
    assert result.timed_out
    assert result.exit_code == -1


@pytest.mark.asyncio
async def test_invalid_interpreter():
    result = await run_command(["definitely_not_a_real_program", "arg"], timeout=5)
    assert result.exit_code == -1
    assert result.stderr != ""
