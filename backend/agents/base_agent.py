"""Abstract base agent with LLM provider abstraction."""

from __future__ import annotations

import abc
import asyncio
import json
from typing import Any, AsyncIterator, Optional

from shared.config import get_settings
from shared.logging import AgentLogger
from shared.models import AgentType
import llm_service


class BaseAgent(abc.ABC):
    """All specialized agents inherit from this class."""

    agent_type: AgentType
    name: str
    description: str
    capabilities: list[str]

    def __init__(self) -> None:
        self._log = AgentLogger(self.name)
        self._settings = get_settings()

    @abc.abstractmethod
    async def run(self, task: str, context: dict[str, Any]) -> str:
        """Execute the agent task and return a result string."""

    async def stream(
        self, task: str, context: dict[str, Any]
    ) -> AsyncIterator[str]:
        """Yield incremental result chunks. Default: run then yield once."""
        result = await self.run(task, context)
        yield result

    async def _call_llm(self, prompt: str, system: str = "") -> str:
        """Call the configured LLM provider. Supports Ollama, OpenAI, and Anthropic."""
        if llm_service.LLM_PROVIDER == "ollama":
            return await asyncio.get_event_loop().run_in_executor(
                None, lambda: llm_service.complete(prompt, system=system or None)
            )
        if self._settings.has_openai:
            return await self._call_openai(prompt, system)
        if self._settings.has_anthropic:
            return await self._call_anthropic(prompt, system)
        return self._stub_response(prompt)

    async def _call_openai(self, prompt: str, system: str) -> str:
        try:
            from openai import AsyncOpenAI  # type: ignore[import]

            client = AsyncOpenAI(api_key=self._settings.openai_api_key)
            messages: list[dict[str, str]] = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,  # type: ignore[arg-type]
                max_tokens=2048,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            self._log.error("OpenAI call failed: %s", exc)
            return self._stub_response(prompt)

    async def _call_anthropic(self, prompt: str, system: str) -> str:
        try:
            import anthropic  # type: ignore[import]

            client = anthropic.AsyncAnthropic(api_key=self._settings.anthropic_api_key)
            kwargs: dict[str, Any] = {
                "model": "claude-sonnet-4-6",
                "max_tokens": 2048,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system

            message = await client.messages.create(**kwargs)
            block = message.content[0]
            return block.text if hasattr(block, "text") else str(block)
        except Exception as exc:
            self._log.error("Anthropic call failed: %s", exc)
            return self._stub_response(prompt)

    def _stub_response(self, prompt: str) -> str:
        """Return a descriptive stub when no LLM key is configured."""
        return (
            f"[STUB] {self.name} received task. "
            "Configure OPENAI_API_KEY or ANTHROPIC_API_KEY to get real responses. "
            f"Task preview: {prompt[:120]}..."
        )

    def to_info_dict(self) -> dict[str, Any]:
        return {
            "agent_type": self.agent_type.value,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
        }
