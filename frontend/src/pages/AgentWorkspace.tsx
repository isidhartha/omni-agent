import React, { useState } from "react";
import AgentChat from "../components/AgentChat";
import RepoAnalyzer from "../components/RepoAnalyzer";
import Terminal from "../components/Terminal";
import PRReviewer from "../components/PRReviewer";

type Panel = "chat" | "repo" | "terminal" | "pr";

export default function AgentWorkspace(): React.ReactElement {
  const [leftPanel, setLeftPanel] = useState<Panel>("chat");
  const [rightPanel, setRightPanel] = useState<Panel>("terminal");

  const renderPanel = (panel: Panel) => {
    switch (panel) {
      case "chat":
        return <AgentChat />;
      case "repo":
        return <RepoAnalyzer />;
      case "terminal":
        return <Terminal />;
      case "pr":
        return <PRReviewer />;
    }
  };

  const PanelSelector = ({
    value,
    onChange,
  }: {
    value: Panel;
    onChange: (p: Panel) => void;
  }) => (
    <div className="flex gap-1 p-1 bg-surface-900 rounded-lg">
      {(["chat", "repo", "terminal", "pr"] as Panel[]).map((p) => (
        <button
          key={p}
          onClick={() => onChange(p)}
          className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
            value === p
              ? "bg-brand-600 text-white"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          {p.charAt(0).toUpperCase() + p.slice(1)}
        </button>
      ))}
    </div>
  );

  return (
    <div className="h-full flex gap-0">
      <div className="flex-1 flex flex-col border-r border-surface-700">
        <div className="flex items-center gap-2 p-2 border-b border-surface-700 bg-surface-800">
          <PanelSelector value={leftPanel} onChange={setLeftPanel} />
        </div>
        <div className="flex-1 overflow-hidden">{renderPanel(leftPanel)}</div>
      </div>

      <div className="flex-1 flex flex-col">
        <div className="flex items-center gap-2 p-2 border-b border-surface-700 bg-surface-800">
          <PanelSelector value={rightPanel} onChange={setRightPanel} />
        </div>
        <div className="flex-1 overflow-hidden">{renderPanel(rightPanel)}</div>
      </div>
    </div>
  );
}
