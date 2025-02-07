# OmniAgent — Architecture

## Overview

OmniAgent is a multi-agent software engineering platform built around a FastAPI backend and a React frontend. Agents communicate through the Orchestrator, which coordinates task pipelines.

## Component Diagram

```mermaid
C4Component
    title OmniAgent System Components

    Container(frontend, "Frontend", "React + Vite", "SPA dashboard for interacting with agents")
    Container(backend, "Backend", "FastAPI + Python", "REST + WebSocket API")
    Container(redis, "Redis", "Redis 7", "Task queue and pub/sub")
    Container(postgres, "PostgreSQL", "Postgres 16", "Task history and audit log")

    Component(orchestrator, "Orchestrator", "Python", "Coordinates multi-agent pipelines")
    Component(coding, "CodingAgent", "Python", "Writes, refactors, and tests code")
    Component(review, "ReviewAgent", "Python", "Reviews PRs and diffs")
    Component(debug, "DebugAgent", "Python", "Analyses errors and produces fixes")
    Component(architect, "ArchitectAgent", "Python", "Generates scaffolds and architecture docs")
    Component(sandbox, "Sandbox", "Python", "Isolated subprocess execution")
    Component(gittools, "GitTools", "Python", "Repo analysis and diff parsing")

    Rel(frontend, backend, "REST / WebSocket", "HTTP/WS")
    Rel(backend, orchestrator, "delegates tasks")
    Rel(orchestrator, coding, "runs")
    Rel(orchestrator, review, "runs")
    Rel(orchestrator, debug, "runs")
    Rel(orchestrator, architect, "runs")
    Rel(coding, sandbox, "executes code")
    Rel(debug, sandbox, "verifies fixes")
    Rel(review, gittools, "parses diffs")
    Rel(backend, redis, "queues tasks")
    Rel(backend, postgres, "stores history")
```

## Data Flow

1. User submits a task via the dashboard.
2. Frontend sends a REST POST or opens a WebSocket to `/ws/agent/{task_id}`.
3. `main.py` validates the request with Pydantic models.
4. `Orchestrator.run_single()` or `stream_agent()` is called.
5. The appropriate agent calls the configured LLM provider (OpenAI / Anthropic).
6. For code/debug tasks, the Sandbox validates output by running it.
7. Results are streamed back via WebSocket or returned as JSON.

## Agent Design

All agents extend `BaseAgent` which provides:
- `_call_llm()` — provider-agnostic LLM call with graceful fallback
- `run()` — abstract method each agent must implement
- `stream()` — default streaming that wraps `run()`
- `to_info_dict()` — serialisation for the `/api/v1/agents` endpoint

## Security Model

- Sandbox uses `asyncio.create_subprocess_exec` (not shell=True).
- Subprocess timeout enforced via `asyncio.wait_for`.
- Dangerous environment variables (`LD_PRELOAD`, `PYTHONPATH`) stripped.
- Non-root user in Docker container.
- CORS restricted to known frontend origins.
