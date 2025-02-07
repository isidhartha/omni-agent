"""Review agent — analyses PRs and diffs and returns structured feedback."""

from __future__ import annotations

import json
from typing import Any

from shared.models import AgentType
from tools.diff_analyzer import detect_issues, parse_diff, summarize_diff
from .base_agent import BaseAgent

_SYSTEM = """You are a senior software engineer conducting a thorough code review.
Analyse the provided diff carefully. Identify:
1. Bugs or logical errors
2. Security vulnerabilities
3. Performance issues
4. Code style / maintainability problems
5. Missing tests or documentation

Return structured feedback as JSON with keys:
- summary: str  (2-3 sentence overview)
- issues: list of {severity: "critical"|"major"|"minor", path: str, detail: str}
- suggestions: list of str (actionable improvements)
- score: int 0-100 (overall quality)"""


class ReviewAgent(BaseAgent):
    agent_type = AgentType.REVIEW
    name = "ReviewAgent"
    description = "Reviews pull request diffs and provides structured feedback."
    capabilities = [
        "diff_analysis",
        "security_scan",
        "code_quality",
        "pr_summary",
        "suggestion_generation",
    ]

    async def run(self, task: str, context: dict[str, Any]) -> str:
        diff_text = context.get("diff", task)
        pr_context = context.get("context", "")

        # Static analysis first
        files = parse_diff(diff_text)
        static_issues = detect_issues(files)
        summary_stats = summarize_diff(files)

        prompt = self._build_prompt(diff_text, pr_context, static_issues, summary_stats)
        self._log.info(
            "Reviewing diff: %d files changed", summary_stats["files_changed"]
        )
        raw = await self._call_llm(prompt, system=_SYSTEM)
        return self._format_result(raw, static_issues, summary_stats)

    def _build_prompt(
        self,
        diff: str,
        ctx: str,
        static_issues: list[dict[str, Any]],
        stats: dict[str, Any],
    ) -> str:
        parts = [
            f"Diff stats: {stats['files_changed']} files, "
            f"+{stats['total_additions']} -{stats['total_deletions']} lines.",
        ]
        if ctx:
            parts.append(f"PR context: {ctx}")
        if static_issues:
            parts.append(
                f"Static analysis found {len(static_issues)} issue(s): "
                + "; ".join(i["type"] for i in static_issues[:5])  # type: ignore[arg-type]
            )
        # Limit diff length to avoid token overflow
        diff_preview = diff[:6000] + ("... [truncated]" if len(diff) > 6000 else "")
        parts.append(f"Diff:\n{diff_preview}")
        return "\n\n".join(parts)

    def _format_result(
        self,
        raw: str,
        static_issues: list[dict[str, Any]],
        stats: dict[str, Any],
    ) -> str:
        # Try to parse JSON from LLM; if it fails, wrap in a basic structure
        try:
            parsed = json.loads(raw)
            return json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            result = {
                "summary": raw[:500],
                "issues": static_issues[:10],
                "suggestions": [],
                "score": 70,
                "stats": stats,
            }
            return json.dumps(result, indent=2)
