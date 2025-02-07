# OmniAgent API Reference

Base URL: `http://localhost:8000`

All request and response bodies are JSON. All timestamps are ISO 8601.

---

## Health

### GET /health

Returns service health status.

**Response 200**
```json
{"status": "ok", "service": "OmniAgent"}
```

---

## Agents

### GET /api/v1/agents

Lists all available agent types and their capabilities.

**Response 200**
```json
[
  {
    "agent_type": "coding",
    "name": "CodingAgent",
    "description": "Writes, refactors, and tests code across multiple languages.",
    "capabilities": ["code_generation", "refactoring", "test_generation", "code_review", "documentation"]
  }
]
```

---

### POST /api/v1/agent/run

Runs a single agent synchronously.

**Request**
```json
{
  "task": "Write a Python function that computes the Fibonacci sequence",
  "agent_type": "coding",
  "repo_url": "https://github.com/user/repo",
  "context": {"language": "python"}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| task | string | Yes | Task description |
| agent_type | enum | Yes | `coding`, `review`, `debug`, `architect` |
| repo_url | string | No | Optional repository URL for context |
| context | object | No | Additional key-value context |

**Response 200**
```json
{
  "task_id": "uuid",
  "status": "done",
  "message": "...<agent output>..."
}
```

---

## Repository Analysis

### POST /api/v1/repo/analyze

Analyses a local repository's structure and language breakdown.

**Request**
```json
{"repo_path": "/path/to/local/repo"}
```

**Response 200**
```json
{
  "repo_path": "/path/to/local/repo",
  "structure": {"src": {"main.py": "Python", "utils.py": "Python"}},
  "summary": "Repository 'repo' contains 12 files. Primary languages: Python (8), YAML (2).",
  "file_count": 12,
  "languages": ["Python", "YAML"]
}
```

---

## PR Review

### POST /api/v1/pr/review

Reviews a unified diff and returns structured feedback.

**Request**
```json
{
  "diff": "diff --git a/main.py b/main.py\n...",
  "context": "Adds authentication middleware"
}
```

**Response 200**
```json
{
  "summary": "The PR adds authentication middleware with a potential SQL injection issue.",
  "issues": [
    {"severity": "critical", "path": "main.py", "detail": "Possible SQL injection on line 42"}
  ],
  "suggestions": ["Use parameterised queries", "Add rate limiting"],
  "score": 62
}
```

---

## Debugging

### POST /api/v1/debug

Analyses a code error and returns a fix.

**Request**
```json
{
  "code": "def add(a, b):\n    return a + b\n\nadd(1, '2')",
  "error": "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
  "language": "python"
}
```

**Response 200**
```json
{
  "analysis": "The function receives mixed types...",
  "root_cause": "String passed where integer expected on line 4.",
  "fix": "Convert the second argument to int before addition.",
  "fixed_code": "def add(a, b):\n    return a + int(b)\n"
}
```

---

## WebSocket Streaming

### WS /ws/agent/{task_id}

Stream agent execution in real time.

**Connection:** `ws://localhost:8000/ws/agent/<uuid>`

**Send after connect:**
```json
{
  "task": "Refactor this function for readability",
  "agent_type": "coding",
  "context": {"code": "def f(x):\n  return x*x"}
}
```

**Receive message types:**

| Type | Payload | Description |
|------|---------|-------------|
| `log` | string | Intermediate log line |
| `result` | string | Final agent result |
| `error` | string | Error message |
| `done` | `{task_id, status}` | Task complete |
