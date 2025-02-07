"""Coding agent — writes, refactors, and tests code."""

from __future__ import annotations

from typing import Any

from shared.models import AgentType
from tools.code_tools import detect_language, extract_python_symbols, format_code_block
from .base_agent import BaseAgent

_SYSTEM = """You are an expert software engineer. You write clean, typed, well-tested code.
Follow SOLID principles. Keep functions under 20 lines. Add docstrings and type hints.
When asked to refactor, improve readability and structure without changing behaviour.
When asked to write tests, use pytest with descriptive test names."""


class CodingAgent(BaseAgent):
    agent_type = AgentType.CODING
    name = "CodingAgent"
    description = "Writes, refactors, and tests code across multiple languages."
    capabilities = [
        "code_generation",
        "refactoring",
        "test_generation",
        "code_review",
        "documentation",
    ]

    async def run(self, task: str, context: dict[str, Any]) -> str:
        existing_code = context.get("code", "")
        language = context.get("language") or (
            detect_language("file.py", existing_code) if existing_code else "python"
        )

        prompt = self._build_prompt(task, existing_code, language)
        self._log.info("Running coding task: %s", task[:80])
        result = await self._call_llm(prompt, system=_SYSTEM)
        return self._post_process(result, language)

    def _build_prompt(self, task: str, code: str, language: str) -> str:
        parts = [f"Task: {task}", f"Language: {language}"]
        if code:
            symbols = extract_python_symbols(code) if language == "python" else {}
            parts.append(f"Existing code:\n{format_code_block(code, language)}")
            if symbols.get("functions"):
                parts.append(f"Detected functions: {', '.join(symbols['functions'])}")
        parts.append("Provide complete, working code with explanations.")
        return "\n\n".join(parts)

    def _post_process(self, result: str, language: str) -> str:
        # Strip markdown fences if the model returned raw code
        if result.startswith("```"):
            lines = result.splitlines()
            # Remove first and last fence lines
            inner = [l for l in lines if not l.startswith("```")]
            return "\n".join(inner)
        return result
