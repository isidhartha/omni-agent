import React from "react";
import clsx from "clsx";

type View = "dashboard" | "agent" | "repo" | "pr" | "terminal";

interface NavItem {
  id: View;
  label: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: "dashboard", label: "Dashboard", icon: "⬛" },
  { id: "agent", label: "Agent Chat", icon: "🤖" },
  { id: "repo", label: "Repo Analyzer", icon: "📁" },
  { id: "pr", label: "PR Reviewer", icon: "🔍" },
  { id: "terminal", label: "Terminal", icon: ">" },
];

interface SidebarProps {
  activeView: View;
  onNavigate: (view: View) => void;
}

export default function Sidebar({
  activeView,
  onNavigate,
}: SidebarProps): React.ReactElement {
  return (
    <aside className="w-56 bg-surface-800 border-r border-surface-700 flex flex-col">
      <div className="p-4 border-b border-surface-700">
        <h1 className="text-brand-500 font-bold text-lg tracking-tight">
          OmniAgent
        </h1>
        <p className="text-slate-400 text-xs mt-0.5">AI Engineering Platform</p>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={clsx(
              "w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors duration-150 flex items-center gap-3",
              activeView === item.id
                ? "bg-brand-600 text-white font-medium"
                : "text-slate-300 hover:bg-surface-700 hover:text-white"
            )}
          >
            <span className="text-base">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      <div className="p-3 border-t border-surface-700">
        <div className="text-xs text-slate-500 px-3 py-2">
          v1.0.0 — MIT License
        </div>
      </div>
    </aside>
  );
}
