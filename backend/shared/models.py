"""Shared Pydantic models for OmniAgent API."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class AgentType(str, Enum):
    CODING = "coding"
    REVIEW = "review"
    DEBUG = "debug"
    ARCHITECT = "architect"
    ORCHESTRATOR = "orchestrator"


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class RunAgentRequest(BaseModel):
    task: str = Field(..., min_length=1, description="Task description for the agent")
    agent_type: AgentType = Field(..., description="Type of agent to run")
    repo_url: Optional[str] = Field(None, description="Optional repository URL")
    context: Optional[dict[str, Any]] = Field(default_factory=dict)


class RunAgentResponse(BaseModel):
    task_id: str
    status: AgentStatus
    message: str


class RepoAnalyzeRequest(BaseModel):
    repo_path: str = Field(..., min_length=1, description="Local path to git repository")


class RepoAnalyzeResponse(BaseModel):
    repo_path: str
    structure: dict[str, Any]
    summary: str
    file_count: int
    languages: list[str]


class PRReviewRequest(BaseModel):
    diff: str = Field(..., min_length=1, description="Unified diff string")
    context: Optional[str] = Field(None, description="Additional PR context")


class PRReviewResponse(BaseModel):
    summary: str
    issues: list[dict[str, Any]]
    suggestions: list[str]
    score: int = Field(..., ge=0, le=100)


class DebugRequest(BaseModel):
    code: str = Field(..., min_length=1, description="Code that produced the error")
    error: str = Field(..., min_length=1, description="Error message or traceback")
    language: str = Field(default="python", description="Programming language")


class DebugResponse(BaseModel):
    analysis: str
    root_cause: str
    fix: str
    fixed_code: Optional[str] = None


class AgentInfo(BaseModel):
    agent_type: AgentType
    name: str
    description: str
    capabilities: list[str]


class WebSocketMessage(BaseModel):
    type: str  # "log", "result", "error", "done"
    payload: Any
    task_id: str


class SandboxResult(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    execution_time_ms: float
