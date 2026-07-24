"""LLM service — delegates to shared/llm_router for full multi-provider support."""
from __future__ import annotations

from shared.llm_router import _PROVIDER as LLM_PROVIDER, chat, complete

__all__ = ["LLM_PROVIDER", "chat", "complete"]
