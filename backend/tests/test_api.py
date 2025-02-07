"""Integration tests for the FastAPI application."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "OmniAgent"


def test_list_agents():
    res = client.get("/api/v1/agents")
    assert res.status_code == 200
    agents = res.json()
    assert isinstance(agents, list)
    assert len(agents) >= 4
    types = [a["agent_type"] for a in agents]
    for expected in ("coding", "review", "debug", "architect"):
        assert expected in types


def test_repo_analyze_invalid_path():
    res = client.post(
        "/api/v1/repo/analyze",
        json={"repo_path": "/nonexistent/path/12345"},
    )
    assert res.status_code == 400


def test_pr_review_empty_diff():
    res = client.post(
        "/api/v1/pr/review",
        json={"diff": "diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-old\n+new"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "issues" in data
    assert "score" in data


def test_debug_endpoint():
    res = client.post(
        "/api/v1/debug",
        json={
            "code": "x = 1 / 0",
            "error": "ZeroDivisionError: division by zero",
            "language": "python",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "analysis" in data
    assert "root_cause" in data
    assert "fix" in data


def test_run_agent_coding():
    res = client.post(
        "/api/v1/agent/run",
        json={
            "task": "Write a hello world function",
            "agent_type": "coding",
            "context": {"language": "python"},
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "done"
    assert "task_id" in data
    assert len(data["message"]) > 0


def test_run_agent_unknown_type():
    res = client.post(
        "/api/v1/agent/run",
        json={"task": "test", "agent_type": "unknown_agent"},
    )
    assert res.status_code == 422  # Pydantic validation error
