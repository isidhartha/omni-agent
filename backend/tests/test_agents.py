"""Unit tests for individual agents."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from agents.coding_agent import CodingAgent
from agents.debug_agent import DebugAgent
from agents.review_agent import ReviewAgent
from agents.architect_agent import ArchitectAgent
from agents.orchestrator import Orchestrator
from shared.models import AgentType


@pytest.fixture
def coding_agent():
    return CodingAgent()


@pytest.fixture
def debug_agent():
    return DebugAgent()


@pytest.fixture
def review_agent():
    return ReviewAgent()


@pytest.fixture
def orchestrator():
    return Orchestrator()


def test_coding_agent_info(coding_agent):
    info = coding_agent.to_info_dict()
    assert info["agent_type"] == "coding"
    assert "code_generation" in info["capabilities"]


def test_debug_agent_info(debug_agent):
    info = debug_agent.to_info_dict()
    assert info["agent_type"] == "debug"
    assert "error_analysis" in info["capabilities"]


def test_review_agent_info(review_agent):
    info = review_agent.to_info_dict()
    assert info["agent_type"] == "review"
    assert "diff_analysis" in info["capabilities"]


@pytest.mark.asyncio
async def test_coding_agent_stub_run(coding_agent):
    """Without API keys, agent should return a stub response."""
    result = await coding_agent.run("write a hello world function", {})
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_debug_agent_stub_run(debug_agent):
    context = {"code": "x = 1/0", "error": "ZeroDivisionError", "language": "python"}
    result = await debug_agent.run("ZeroDivisionError", context)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_review_agent_stub_run(review_agent):
    diff = "diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-old\n+new"
    context = {"diff": diff}
    result = await review_agent.run("Review this", context)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_orchestrator_list_agents():
    agents = Orchestrator.list_agents()
    assert len(agents) >= 4
    agent_types = [a["agent_type"] for a in agents]
    assert "coding" in agent_types
    assert "debug" in agent_types


@pytest.mark.asyncio
async def test_orchestrator_run_single(orchestrator):
    messages = []

    async def collect(msg):
        messages.append(msg)

    result = await orchestrator.run_single(
        task="write a greeting function",
        agent_type=AgentType.CODING,
        context={},
        on_message=collect,
    )
    assert isinstance(result, str)
    # Should have received at least log + result + done messages
    assert len(messages) >= 3
    msg_types = [m.type for m in messages]
    assert "done" in msg_types
