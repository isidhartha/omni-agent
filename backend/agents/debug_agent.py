"""Debug agent — analyses errors and suggests or produces fixes."""

from __future__ import annotations

from typing import Any

from shared.models import AgentType
from tools.code_tools import detect_language, extract_error_info, format_code_block
from tools.sandbox import run_code
from shared.config import get_settings
from .base_agent import BaseAgent

_SYSTEM = """You are an expert debugger. When given code and an error:
1. Identify the root cause precisely.
2. Explain the fix in plain English.
3. Return the corrected code (complete, not just the diff).

Structure your response exactly as:
ANALYSIS: <brief analysis>
ROOT_CAUSE: <one sentence>
FIX: <explanation of the fix>
FIXED_CODE:
```<language>
<corrected code here>
```"""


class DebugAgent(BaseAgent):
    agent_type = AgentType.DEBUG
    name = "DebugAgent"
    description = "Analyses runtime errors and produces corrected code."
    capabilities = [
        "error_analysis",
        "root_cause_identification",
        "automated_fix",
        "test_execution",
        "traceback_parsing",
    ]

    async def run(self, task: str, context: dict[str, Any]) -> str:
        code = context.get("code", "")
        error = context.get("error", task)
        language = context.get("language", "python")

        if not language and code:
            language = detect_language("script.py", code)

        error_info = extract_error_info(error)
        self._log.info(
            "Debugging %s error: %s",
            error_info.get("error_type", "unknown"),
            error_info.get("message", "")[:80],
        )

        prompt = self._build_prompt(code, error, language, error_info)
        raw = await self._call_llm(prompt, system=_SYSTEM)

        # Optionally verify the fix by running it
        fixed_code = self._extract_fixed_code(raw)
        if fixed_code and language == "python":
            result = await run_code(
                fixed_code,
                language="python",
                timeout=get_settings().sandbox_timeout,
            )
            if result.exit_code == 0 and not result.timed_out:
                self._log.info("Fixed code verified via sandbox execution.")
            else:
                self._log.warning("Fixed code still has issues: %s", result.stderr[:200])

        return raw

    def _build_prompt(
        self,
        code: str,
        error: str,
        language: str,
        error_info: dict[str, Any],
    ) -> str:
        parts = [f"Language: {language}"]
        if error_info.get("error_type"):
            parts.append(f"Error type: {error_info['error_type']}")
        if error_info.get("line_number"):
            parts.append(f"Error line: {error_info['line_number']}")
        if code:
            parts.append(f"Code:\n{format_code_block(code, language)}")
        parts.append(f"Error:\n```\n{error}\n```")
        return "\n\n".join(parts)

    def _extract_fixed_code(self, raw: str) -> str:
        """Pull the fixed code block from the LLM response."""
        import re
        m = re.search(r"```(?:\w+)?\n([\s\S]+?)\n```", raw)
        return m.group(1) if m else ""
