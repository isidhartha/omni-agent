"""Architect agent — generates project scaffolds and architecture documentation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shared.models import AgentType
from .base_agent import BaseAgent

_SYSTEM = """You are a software architect. Given a project description, produce:
1. A recommended directory structure (as a nested JSON object where leaf values are file descriptions).
2. Technology choices with reasoning.
3. Architecture decisions (ADRs) in brief.
4. A Mermaid C4 or component diagram.

Return JSON with keys: structure, tech_stack, decisions, mermaid_diagram."""


class ArchitectAgent(BaseAgent):
    agent_type = AgentType.ARCHITECT
    name = "ArchitectAgent"
    description = "Generates project scaffolds, architecture docs, and tech-stack recommendations."
    capabilities = [
        "scaffold_generation",
        "architecture_design",
        "tech_stack_recommendation",
        "adr_generation",
        "diagram_generation",
    ]

    async def run(self, task: str, context: dict[str, Any]) -> str:
        language = context.get("language", "python")
        framework = context.get("framework", "")
        scale = context.get("scale", "medium")

        prompt = self._build_prompt(task, language, framework, scale)
        self._log.info("Generating architecture for: %s", task[:80])
        raw = await self._call_llm(prompt, system=_SYSTEM)
        return self._post_process(raw, task)

    def _build_prompt(
        self, task: str, language: str, framework: str, scale: str
    ) -> str:
        parts = [
            f"Project description: {task}",
            f"Primary language: {language}",
            f"Scale: {scale} (small/medium/large)",
        ]
        if framework:
            parts.append(f"Preferred framework: {framework}")
        parts.append(
            "Generate a complete, production-ready architecture with best practices."
        )
        return "\n".join(parts)

    def _post_process(self, raw: str, task: str) -> str:
        try:
            parsed = json.loads(raw)
            return json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            # Return as-is with a header
            return f"# Architecture for: {task}\n\n{raw}"

    async def generate_scaffold(
        self, structure: dict[str, Any], base_path: str
    ) -> list[str]:
        """Physically create files from a structure dict. Returns created paths."""
        created: list[str] = []
        root = Path(base_path)

        def _create(node: dict[str, Any], current: Path) -> None:
            for name, value in node.items():
                target = current / name
                if isinstance(value, dict):
                    target.mkdir(parents=True, exist_ok=True)
                    _create(value, target)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(f"# {value}\n", encoding="utf-8")
                    created.append(str(target))

        _create(structure, root)
        return created
