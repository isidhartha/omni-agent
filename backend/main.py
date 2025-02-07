"""OmniAgent — FastAPI application entry point."""

from __future__ import annotations

import asyncio
import json
import sys
import os

# Ensure backend directory is on the path when running with uvicorn
sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.config import get_settings
from shared.logging import setup_logging, get_logger
from shared.models import (
    AgentType,
    DebugRequest,
    DebugResponse,
    PRReviewRequest,
    PRReviewResponse,
    RepoAnalyzeRequest,
    RepoAnalyzeResponse,
    RunAgentRequest,
    RunAgentResponse,
    AgentStatus,
    WebSocketMessage,
)
from agents.orchestrator import Orchestrator
from tools.git_tools import analyze_repo
from tools.diff_analyzer import parse_diff, summarize_diff, detect_issues

setup_logging()
log = get_logger("main")

_orchestrator = Orchestrator()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    log.info("OmniAgent starting up...")
    yield
    log.info("OmniAgent shutting down.")


settings = get_settings()

app = FastAPI(
    title="OmniAgent",
    description="Autonomous Multi-Agent Software Engineer Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "OmniAgent"}


# ---------------------------------------------------------------------------
# Agents list
# ---------------------------------------------------------------------------


@app.get("/api/v1/agents")
async def list_agents() -> list[dict[str, Any]]:
    return Orchestrator.list_agents()


# ---------------------------------------------------------------------------
# Run agent
# ---------------------------------------------------------------------------


@app.post("/api/v1/agent/run", response_model=RunAgentResponse)
async def run_agent(request: RunAgentRequest) -> RunAgentResponse:
    import uuid

    task_id = str(uuid.uuid4())
    context: dict[str, Any] = dict(request.context or {})
    if request.repo_url:
        context["repo_url"] = request.repo_url

    try:
        result = await _orchestrator.run_single(
            task=request.task,
            agent_type=request.agent_type,
            context=context,
        )
        log.info("Agent run complete: %s", task_id)
        return RunAgentResponse(
            task_id=task_id, status=AgentStatus.DONE, message=result
        )
    except Exception as exc:
        log.error("Agent run failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Repo analysis
# ---------------------------------------------------------------------------


@app.post("/api/v1/repo/analyze", response_model=RepoAnalyzeResponse)
async def analyze_repo_endpoint(request: RepoAnalyzeRequest) -> RepoAnalyzeResponse:
    try:
        result = analyze_repo(request.repo_path)
        return RepoAnalyzeResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        log.error("Repo analysis failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# PR review
# ---------------------------------------------------------------------------


@app.post("/api/v1/pr/review", response_model=PRReviewResponse)
async def review_pr(request: PRReviewRequest) -> PRReviewResponse:
    from agents.review_agent import ReviewAgent

    agent = ReviewAgent()
    context = {"diff": request.diff, "context": request.context or ""}
    raw = await agent.run("Review this pull request diff.", context)

    try:
        parsed = json.loads(raw)
        return PRReviewResponse(
            summary=parsed.get("summary", raw[:300]),
            issues=parsed.get("issues", []),
            suggestions=parsed.get("suggestions", []),
            score=parsed.get("score", 70),
        )
    except json.JSONDecodeError:
        files = parse_diff(request.diff)
        issues = detect_issues(files)
        return PRReviewResponse(
            summary=raw[:500],
            issues=issues,
            suggestions=[],
            score=70,
        )


# ---------------------------------------------------------------------------
# Debug
# ---------------------------------------------------------------------------


@app.post("/api/v1/debug", response_model=DebugResponse)
async def debug_code(request: DebugRequest) -> DebugResponse:
    import re as _re

    from agents.debug_agent import DebugAgent

    agent = DebugAgent()
    context = {
        "code": request.code,
        "error": request.error,
        "language": request.language,
    }
    raw = await agent.run(request.error, context)

    def _extract(label: str) -> str:
        m = _re.search(rf"{label}:\s*(.+?)(?=\n[A-Z_]+:|$)", raw, _re.DOTALL)
        return m.group(1).strip() if m else ""

    fixed_code_m = _re.search(r"FIXED_CODE:\s*```(?:\w+)?\n([\s\S]+?)\n```", raw)
    return DebugResponse(
        analysis=_extract("ANALYSIS") or raw[:300],
        root_cause=_extract("ROOT_CAUSE") or "See analysis.",
        fix=_extract("FIX") or "See analysis.",
        fixed_code=fixed_code_m.group(1) if fixed_code_m else None,
    )


# ---------------------------------------------------------------------------
# WebSocket streaming
# ---------------------------------------------------------------------------


@app.websocket("/ws/agent/{task_id}")
async def websocket_agent(websocket: WebSocket, task_id: str) -> None:
    await websocket.accept()
    log.info("WebSocket connected for task %s", task_id)

    try:
        data = await websocket.receive_json()
        task = data.get("task", "")
        agent_type_str = data.get("agent_type", AgentType.CODING.value)
        context = data.get("context", {})

        try:
            agent_type = AgentType(agent_type_str)
        except ValueError:
            await websocket.send_json(
                {"type": "error", "payload": f"Unknown agent type: {agent_type_str}"}
            )
            return

        async for msg in _orchestrator.stream_agent(task, agent_type, context):
            await websocket.send_json(msg.model_dump())
            if msg.type in ("done", "error"):
                break

    except WebSocketDisconnect:
        log.info("WebSocket disconnected for task %s", task_id)
    except Exception as exc:
        log.error("WebSocket error for task %s: %s", task_id, exc)
        try:
            await websocket.send_json({"type": "error", "payload": str(exc)})
        except Exception:
            pass
