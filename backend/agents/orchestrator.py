"""Multi-agent orchestrator — coordinates specialized agents into pipelines."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, AsyncIterator, Callable, Optional

from shared.logging import get_logger
from shared.models import AgentStatus, AgentType, WebSocketMessage
from .base_agent import BaseAgent
from .coding_agent import CodingAgent
from .debug_agent import DebugAgent
from .review_agent import ReviewAgent
from .architect_agent import ArchitectAgent

log = get_logger("orchestrator")

# Registry of available agent types
_AGENT_REGISTRY: dict[AgentType, type[BaseAgent]] = {
    AgentType.CODING: CodingAgent,
    AgentType.REVIEW: ReviewAgent,
    AgentType.DEBUG: DebugAgent,
    AgentType.ARCHITECT: ArchitectAgent,
}


class TaskContext:
    """Shared mutable context passed between agents in a pipeline."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        self.data: dict[str, Any] = {}
        self.messages: list[WebSocketMessage] = []

    def emit(self, msg_type: str, payload: Any) -> WebSocketMessage:
        msg = WebSocketMessage(type=msg_type, payload=payload, task_id=self.task_id)
        self.messages.append(msg)
        return msg


class Orchestrator:
    """Coordinates multiple agents and streams their output."""

    def __init__(self) -> None:
        self._agents: dict[AgentType, BaseAgent] = {}
        self._active_tasks: dict[str, asyncio.Task[Any]] = {}

    def _get_agent(self, agent_type: AgentType) -> BaseAgent:
        if agent_type not in self._agents:
            cls = _AGENT_REGISTRY.get(agent_type)
            if cls is None:
                raise ValueError(f"Unknown agent type: {agent_type}")
            self._agents[agent_type] = cls()
        return self._agents[agent_type]

    async def run_single(
        self,
        task: str,
        agent_type: AgentType,
        context: dict[str, Any],
        on_message: Optional[Callable[[WebSocketMessage], Any]] = None,
    ) -> str:
        task_id = str(uuid.uuid4())
        ctx = TaskContext(task_id)

        agent = self._get_agent(agent_type)
        log.info("[%s] Starting %s on: %s", task_id, agent.name, task[:80])

        msg = ctx.emit("log", f"Agent {agent.name} starting...")
        if on_message:
            await _maybe_await(on_message(msg))

        try:
            result = await agent.run(task, context)
            msg = ctx.emit("result", result)
            if on_message:
                await _maybe_await(on_message(msg))
            done_msg = ctx.emit("done", {"task_id": task_id, "status": AgentStatus.DONE})
            if on_message:
                await _maybe_await(on_message(done_msg))
            return result
        except Exception as exc:
            log.error("[%s] Agent error: %s", task_id, exc)
            err_msg = ctx.emit("error", str(exc))
            if on_message:
                await _maybe_await(on_message(err_msg))
            raise

    async def run_pipeline(
        self,
        task: str,
        agent_types: list[AgentType],
        initial_context: dict[str, Any],
        on_message: Optional[Callable[[WebSocketMessage], Any]] = None,
    ) -> dict[str, str]:
        """Run agents sequentially, passing results as context to the next."""
        context = dict(initial_context)
        results: dict[str, str] = {}

        for agent_type in agent_types:
            result = await self.run_single(task, agent_type, context, on_message)
            results[agent_type.value] = result
            # Feed result into next agent's context
            context[f"{agent_type.value}_result"] = result

        return results

    async def stream_agent(
        self, task: str, agent_type: AgentType, context: dict[str, Any]
    ) -> AsyncIterator[WebSocketMessage]:
        task_id = str(uuid.uuid4())
        ctx = TaskContext(task_id)
        agent = self._get_agent(agent_type)

        yield ctx.emit("log", f"Agent {agent.name} starting...")

        try:
            async for chunk in agent.stream(task, context):
                yield ctx.emit("log", chunk)
            yield ctx.emit("done", {"task_id": task_id, "status": AgentStatus.DONE})
        except Exception as exc:
            yield ctx.emit("error", str(exc))

    @staticmethod
    def list_agents() -> list[dict[str, Any]]:
        return [cls().to_info_dict() for cls in _AGENT_REGISTRY.values()]


async def _maybe_await(value: Any) -> None:
    if asyncio.iscoroutine(value):
        await value
