import React, { useState } from "react";
import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import AgentWorkspace from "./pages/AgentWorkspace";

type ActiveView = "dashboard" | "agent" | "repo" | "pr" | "terminal";

export default function App(): React.ReactElement {
  const [activeView, setActiveView] = useState<ActiveView>("dashboard");

  return (
    <div className="flex h-screen overflow-hidden bg-surface-900">
      <Sidebar activeView={activeView} onNavigate={setActiveView} />
      <main className="flex-1 overflow-hidden">
        <Routes>
          <Route
            path="/"
            element={
              <Dashboard activeView={activeView} onNavigate={setActiveView} />
            }
          />
          <Route path="/workspace" element={<AgentWorkspace />} />
        </Routes>
      </main>
    </div>
  );
}
