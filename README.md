# OmniAgent

I built OmniAgent because I kept running into the same wall: AI coding assistants are great at answering questions, but they can't actually *do* anything. They suggest. You implement. OmniAgent flips that. It's a platform where multiple specialized AI agents work together — one writes code, one reviews it, one debugs it, one thinks about the architecture — and they hand work off to each other in a real pipeline.

The idea is that you describe a task, and the agents figure out how to tackle it from every angle without you babysitting the process.

---

## What it does

**Coding agent** — Takes a description of what you need and writes working code. It's not autocomplete. You give it a problem statement, it produces files.

**Review agent** — Analyzes code diffs and pull requests. Grades issues by severity, explains what's wrong, and gives you actionable suggestions rather than vague warnings.

**Debug agent** — You paste in code and an error, it traces the failure, identifies the root cause, and produces a fix. It can also execute code in a sandboxed subprocess and work from actual runtime output.

**Architect agent** — Generates project scaffolds, writes architecture decision records, and produces Mermaid diagrams. Useful when you're starting something new and want structure before you start typing.

**Multi-agent pipelines** — This is where it gets interesting. You can chain agents together: architect designs the approach, coder implements it, reviewer checks it, debugger fixes what breaks. Each agent sees what the previous one produced.

**Real-time streaming** — Everything streams over WebSocket. You watch the agent think and write in real time on the dashboard, rather than waiting for a response to pop up.

**Repo analysis** — Point it at a local git repository and it'll parse the structure, understand the language breakdown, read key files, and answer questions about the codebase.

---

## Tech stack

Backend is Python with FastAPI streaming WebSocket responses. AI providers are OpenAI (gpt-4o-mini) and Anthropic (claude-sonnet-4-6) — you can switch between them with a config flag. The code sandbox runs in a restricted subprocess with timeout and resource limits so it can't do anything destructive. Frontend is React 18 with TypeScript and Tailwind CSS, built on Vite. PostgreSQL stores task history and agent results. Redis handles caching and session state.

---

## How to run it

**Prerequisites**: Docker and Docker Compose. One of `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`.

**1. Clone the repo**

```bash
git clone https://github.com/isidhartha/omni-agent.git
cd omni-agent
```

**2. Set up your config**

```bash
cp .env.example .env
```

Open `.env` and paste in your API key:

```
OPENAI_API_KEY=sk-your-key-here
# or
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**3. Start everything**

```bash
docker-compose up --build
```

First build takes a few minutes while it installs dependencies. After that it comes up in seconds.

**4. Open the dashboard**

Go to `http://localhost:3000`. Pick an agent from the sidebar and describe your task in the input box.

---

## Free local LLM option (no API key needed)

If you don't have OpenAI API credits, you can run OmniAgent entirely for free using [Ollama](https://ollama.com) — a local LLM runner that works on Mac, Linux, and Windows.

**1. Install Ollama**

Download and install from https://ollama.com. It takes about 2 minutes.

**2. Pull the model**

```bash
ollama pull llama3.2
```

This downloads a ~2GB model to your machine. You only do this once.

**3. Set the provider in your `.env`**

```
LLM_PROVIDER=ollama
```

Leave `OPENAI_API_KEY` blank — it won't be used.

**4. Start OmniAgent as normal**

```bash
docker-compose up --build
```

Ollama needs to be running on your host machine (not inside Docker). If you want to run it inside Docker too, uncomment the `ollama` service in `docker-compose.yml`.

> **Switching back to OpenAI**: set `LLM_PROVIDER=openai` and add your `OPENAI_API_KEY`.

---

## Without Docker

If you want to run it locally without containers:

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Backend runs on port 8000, frontend on 5173.

---

## API

Swagger UI is at `http://localhost:8000/docs` when the backend is running.

Key endpoints:

```
POST /api/v1/agent/run         — Run a single agent on a task
POST /api/v1/repo/analyze      — Analyze a local repository
POST /api/v1/pr/review         — Review a PR diff
POST /api/v1/debug             — Debug code + error trace
WS   /ws/agent/{task_id}       — Stream agent output in real time
```

Full reference is in [docs/API.md](docs/API.md).

---

## Configuration

| Variable | What it does | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API access | — |
| `ANTHROPIC_API_KEY` | Anthropic API access | — |
| `DATABASE_URL` | PostgreSQL connection | see `.env.example` |
| `REDIS_URL` | Redis connection | `redis://redis:6379` |
| `MAX_AGENT_ITERATIONS` | How many LLM loops per task before stopping | `10` |
| `SANDBOX_TIMEOUT` | Code execution timeout in seconds | `30` |

Without a real API key the platform runs in stub mode — useful for exploring the UI but agents won't produce real output.

---

## Project layout

```
omni-agent/
├── backend/
│   ├── main.py          # FastAPI entry point
│   ├── agents/          # CodingAgent, ReviewAgent, DebugAgent, ArchitectAgent
│   ├── tools/           # Git, sandbox, diff, code analysis utilities
│   └── shared/          # Config, logging, Pydantic models
├── frontend/
│   └── src/
│       ├── components/  # AgentChat, PRReviewer, Terminal, StreamOutput
│       └── pages/       # Dashboard, AgentWorkspace
├── docs/
├── scripts/
├── Dockerfile
└── docker-compose.yml
```

---

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before sending a PR. The agent system is modular — adding a new agent type is straightforward if you follow the existing pattern.

---

## License

MIT. Do whatever you want with it.
