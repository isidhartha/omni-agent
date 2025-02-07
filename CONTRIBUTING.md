# Contributing to OmniAgent

Thank you for your interest in contributing. This document outlines the process for contributing to the project.

## Development Setup

1. Fork the repository.
2. Run `bash scripts/setup.sh` to install all dependencies.
3. Copy `.env.example` to `.env` and fill in your API keys.

## Code Standards

### Python (backend)

- All code must pass `ruff check` and `ruff format --check`.
- Functions must have type annotations.
- Functions must stay under 20 lines where possible.
- Tests live in `backend/tests/` and must use `pytest`.
- New agents must extend `BaseAgent` and implement `run()`.

### TypeScript (frontend)

- All components must have explicit prop interfaces.
- No `any` types without a justifying comment.
- Tests use `vitest`.

## Submitting Changes

1. Create a branch: `git checkout -b feat/your-feature`.
2. Make your changes and add tests.
3. Ensure CI passes: `ruff check . && pytest && npm test`.
4. Open a pull request with a clear description.

## Adding a New Agent

1. Create `backend/agents/my_agent.py` extending `BaseAgent`.
2. Set `agent_type`, `name`, `description`, and `capabilities` class attributes.
3. Implement `async def run(self, task, context) -> str`.
4. Register it in `_AGENT_REGISTRY` inside `orchestrator.py`.
5. Add tests in `backend/tests/test_my_agent.py`.

## Reporting Issues

Open a GitHub Issue with:
- A clear title.
- Steps to reproduce.
- Expected vs actual behaviour.
- Python / Node version and OS.
