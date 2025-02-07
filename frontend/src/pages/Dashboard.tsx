import React, { useEffect, useState } from "react";
import AgentChat from "../components/AgentChat";
import RepoAnalyzer from "../components/RepoAnalyzer";
import PRReviewer from "../components/PRReviewer";
import Terminal from "../components/Terminal";
import TaskOrchestrator from "../components/TaskOrchestrator";

type ActiveView = "dashboard" | "agent" | "repo" | "pr" | "terminal";

interface DashboardProps {
  activeView: ActiveView;
  onNavigate: (view: ActiveView) => void;
}

interface AgentInfo {
  agent_type: string;
  name: string;
  description: string;
  capabilities: string[];
}

interface HealthStatus {
  status: string;
  service: string;
}

export default function Dashboard({
  activeView,
  onNavigate,
}: DashboardProps): React.ReactElement {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    fetch("/api/v1/agents")
      .then((r) => r.json())
      .then((data) => setAgents(data as AgentInfo[]))
      .catch(() => {});

    fetch("/health")
      .then((r) => r.json())
      .then((data) => setHealth(data as HealthStatus))
      .catch(() => setHealth({ status: "offline", service: "OmniAgent" }));
  }, []);

  if (activeView === "agent") {
    return (
      <div className="h-full">
        <AgentChat />
      </div>
    );
  }
  if (activeView === "repo") {
    return (
      <div className="h-full overflow-y-auto">
        <RepoAnalyzer />
      </div>
    );
  }
  if (activeView === "pr") {
    return (
      <div className="h-full overflow-y-auto">
        <PRReviewer />
      </div>
    );
  }
  if (activeView === "terminal") {
    return (
      <div className="h-full">
        <Terminal />
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">OmniAgent Dashboard</h1>
          <p className="text-slate-400 text-sm mt-1">
            Autonomous Multi-Agent Software Engineer Platform
          </p>
        </div>
        <div
          className={`text-xs font-medium px-3 py-1 rounded-full ${
            health?.status === "ok"
              ? "bg-green-900/40 text-green-400 border border-green-700"
              : "bg-red-900/40 text-red-400 border border-red-700"
          }`}
        >
          {health?.status === "ok" ? "Backend Online" : "Backend Offline"}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { view: "agent" as ActiveView, label: "Agent Chat", desc: "Chat with AI coding agents", color: "brand" },
          { view: "repo" as ActiveView, label: "Repo Analyzer", desc: "Analyse repository structure", color: "purple" },
          { view: "pr" as ActiveView, label: "PR Reviewer", desc: "Review pull request diffs", color: "amber" },
          { view: "terminal" as ActiveView, label: "Terminal", desc: "Execute code in sandbox", color: "emerald" },
        ].map(({ view, label, desc }) => (
          <button
            key={view}
            onClick={() => onNavigate(view)}
            className="card text-left hover:border-brand-500 transition-colors"
          >
            <h3 className="font-medium text-slate-100 text-sm">{label}</h3>
            <p className="text-xs text-slate-400 mt-1">{desc}</p>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <h2 className="font-medium text-slate-100 mb-3 text-sm">Available Agents</h2>
          {agents.length === 0 ? (
            <p className="text-slate-500 text-xs">Loading agents...</p>
          ) : (
            <div className="space-y-3">
              {agents.map((agent) => (
                <div key={agent.agent_type} className="border-l-2 border-brand-600 pl-3">
                  <div className="text-sm font-medium text-slate-200">{agent.name}</div>
                  <div className="text-xs text-slate-400">{agent.description}</div>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {agent.capabilities.slice(0, 3).map((cap) => (
                      <span
                        key={cap}
                        className="text-xs bg-surface-700 text-slate-400 px-2 py-0.5 rounded"
                      >
                        {cap}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="font-medium text-slate-100 mb-3 text-sm">Quick Pipeline</h2>
          <TaskOrchestrator />
        </div>
      </div>
    </div>
  );
}
