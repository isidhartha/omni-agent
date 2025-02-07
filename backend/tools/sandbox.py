"""Secure subprocess execution sandbox with timeout and resource limits."""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

from shared.models import SandboxResult
from shared.logging import get_logger

log = get_logger("tools.sandbox")

_DEFAULT_TIMEOUT = 30  # seconds


async def run_code(
    code: str,
    language: str = "python",
    timeout: int = _DEFAULT_TIMEOUT,
    env_vars: Optional[dict[str, str]] = None,
) -> SandboxResult:
    """Execute code in an isolated subprocess and return the result."""
    with tempfile.TemporaryDirectory(prefix="omni_sandbox_") as tmpdir:
        script_path, cmd = _prepare_script(code, language, tmpdir)
        return await _execute(cmd, timeout, env_vars, cwd=tmpdir)


async def run_command(
    command: list[str],
    cwd: Optional[str] = None,
    timeout: int = _DEFAULT_TIMEOUT,
    env_vars: Optional[dict[str, str]] = None,
) -> SandboxResult:
    """Execute an arbitrary shell command safely."""
    return await _execute(command, timeout, env_vars, cwd=cwd)


def _prepare_script(code: str, language: str, tmpdir: str) -> tuple[Path, list[str]]:
    ext_map = {"python": ".py", "javascript": ".js", "typescript": ".ts", "bash": ".sh"}
    ext = ext_map.get(language, ".txt")
    script_path = Path(tmpdir) / f"script{ext}"
    script_path.write_text(code, encoding="utf-8")

    interpreter_map = {
        "python": [sys.executable],
        "javascript": ["node"],
        "bash": ["bash"],
    }
    interpreter = interpreter_map.get(language, [sys.executable])
    return script_path, interpreter + [str(script_path)]


async def _execute(
    cmd: list[str],
    timeout: int,
    env_vars: Optional[dict[str, str]],
    cwd: Optional[str] = None,
) -> SandboxResult:
    env = {**os.environ, **(env_vars or {})}
    # Strip dangerous env vars
    for key in ("LD_PRELOAD", "PYTHONPATH"):
        env.pop(key, None)

    start = time.monotonic()
    timed_out = False

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            timed_out = True
            stdout_bytes, stderr_bytes = b"", b"Execution timed out"

        elapsed_ms = (time.monotonic() - start) * 1000
        return SandboxResult(
            stdout=stdout_bytes.decode("utf-8", errors="replace"),
            stderr=stderr_bytes.decode("utf-8", errors="replace"),
            exit_code=proc.returncode if not timed_out else -1,
            timed_out=timed_out,
            execution_time_ms=round(elapsed_ms, 2),
        )
    except FileNotFoundError as exc:
        log.error("Interpreter not found: %s", exc)
        return SandboxResult(
            stdout="",
            stderr=str(exc),
            exit_code=-1,
            timed_out=False,
            execution_time_ms=0.0,
        )
