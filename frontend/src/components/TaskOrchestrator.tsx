import React, { useState } from "react";

type AgentType = "coding" | "review" | "debug" | "architect";

interface PipelineStep {
  id: string;
  agentType: AgentType;
  status: "pending" | "running" | "done" | "error";
  result: string;
}

const AVAILABLE_AGENTS: AgentType[] = ["coding", "review", "debug", "architect"];

export default function TaskOrchestrator(): React.ReactElement {
  const [task, setTask] = useState("");
  const [pipeline, setPipeline] = useState<AgentType[]>(["coding", "review"]);
  const [steps, setSteps] = useState<PipelineStep[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [addingAgent, setAddingAgent] = useState<AgentType>("coding");

  const addToPipeline = () => {
    setPipeline((prev) => [...prev, addingAgent]);
  };

  const removeFromPipeline = (idx: number) => {
    setPipeline((prev) => prev.filter((_, i) => i !== idx));
  };

  const runPipeline = async () => {
    if (!task.trim() || pipeline.length === 0 || isRunning) return;

    setIsRunning(true);
    const initialSteps: PipelineStep[] = pipeline.map((a) => ({
      id: crypto.randomUUID(),
      agentType: a,
      status: "pending",
      result: "",
    }));
    setSteps(initialSteps);

    let context: Record<string, string> = {};

    for (let i = 0; i < pipeline.length; i++) {
      const agentType = pipeline[i];
      setSteps((prev) =>
        prev.map((s, idx) => (idx === i ? { ...s, status: "running" } : s))
      );

      try {
        const res = await fetch("/api/v1/agent/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ task, agent_type: agentType, context }),
        });
        const data = (await res.json()) as { message: string };
        context[`${agentType}_result`] = data.message;

        setSteps((prev) =>
          prev.map((s, idx) =>
            idx === i ? { ...s, status: "done", result: data.message } : s
          )
        );
      } catch (err) {
        setSteps((prev) =>
          prev.map((s, idx) =>
            idx === i
              ? { ...s, status: "error", result: String(err) }
              : s
          )
        );
        break;
      }
    }

    setIsRunning(false);
  };

  return (
    <div className="p-4 space-y-4">
      <h2 className="font-semibold text-slate-100">Task Orchestrator</h2>

      <div>
        <label className="text-xs text-slate-400 mb-1 block">Task Description</label>
        <textarea
          value={task}
          onChange={(e) => setTask(e.target.value)}
          className="input-dark resize-none h-20"
          placeholder="Describe the overall task for the pipeline..."
          disabled={isRunning}
        />
      </div>

      <div>
        <label className="text-xs text-slate-400 mb-2 block">
          Pipeline ({pipeline.length} steps)
        </label>
        <div className="space-y-2 mb-3">
          {pipeline.map((agent, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 bg-surface-700 rounded-lg px-3 py-2"
            >
              <span className="text-xs text-brand-400 font-mono w-6">{idx + 1}.</span>
              <span className="text-sm text-slate-200 flex-1 capitalize">
                {agent}Agent
              </span>
              <button
                onClick={() => removeFromPipeline(idx)}
                className="text-slate-500 hover:text-red-400 text-xs"
                disabled={isRunning}
              >
                Remove
              </button>
            </div>
          ))}
        </div>

        <div className="flex gap-2">
          <select
            value={addingAgent}
            onChange={(e) => setAddingAgent(e.target.value as AgentType)}
            className="input-dark flex-1"
            disabled={isRunning}
          >
            {AVAILABLE_AGENTS.map((a) => (
              <option key={a} value={a}>
                {a}Agent
              </option>
            ))}
          </select>
          <button onClick={addToPipeline} className="btn-secondary" disabled={isRunning}>
            Add Step
          </button>
        </div>
      </div>

      <button
        onClick={runPipeline}
        disabled={isRunning || !task.trim() || pipeline.length === 0}
        className="btn-primary w-full"
      >
        {isRunning ? "Running Pipeline..." : "Run Pipeline"}
      </button>

      {steps.length > 0 && (
        <div className="space-y-3 mt-4">
          <h3 className="text-sm font-medium text-slate-300">Pipeline Results</h3>
          {steps.map((step, idx) => (
            <StepResult key={step.id} step={step} index={idx} />
          ))}
        </div>
      )}
    </div>
  );
}

function StepResult({
  step,
  index,
}: {
  step: PipelineStep;
  index: number;
}): React.ReactElement {
  const [expanded, setExpanded] = useState(false);
  const statusColors = {
    pending: "text-slate-500",
    running: "text-brand-400 animate-pulse",
    done: "text-green-400",
    error: "text-red-400",
  };

  return (
    <div className="card">
      <div
        className="flex items-center gap-2 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="text-xs text-slate-400">Step {index + 1}:</span>
        <span className="text-sm text-slate-200 capitalize flex-1">
          {step.agentType}Agent
        </span>
        <span className={`text-xs font-medium ${statusColors[step.status]}`}>
          {step.status.toUpperCase()}
        </span>
        {step.result && (
          <span className="text-xs text-slate-500">{expanded ? "▲" : "▼"}</span>
        )}
      </div>
      {expanded && step.result && (
        <pre className="mt-3 text-xs text-slate-300 whitespace-pre-wrap bg-surface-900 rounded p-3 max-h-48 overflow-y-auto">
          {step.result}
        </pre>
      )}
    </div>
  );
}
