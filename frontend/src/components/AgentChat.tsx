import React, { useState, useRef, useEffect, useCallback } from "react";

type AgentType = "coding" | "review" | "debug" | "architect";

interface Message {
  id: string;
  role: "user" | "agent" | "system";
  content: string;
  timestamp: Date;
  agentType?: AgentType;
}

const AGENT_LABELS: Record<AgentType, string> = {
  coding: "CodingAgent",
  review: "ReviewAgent",
  debug: "DebugAgent",
  architect: "ArchitectAgent",
};

export default function AgentChat(): React.ReactElement {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "system",
      content: "OmniAgent is ready. Select an agent type and describe your task.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [agentType, setAgentType] = useState<AgentType>("coding");
  const [isRunning, setIsRunning] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addMessage = useCallback((msg: Omit<Message, "id" | "timestamp">) => {
    setMessages((prev) => [
      ...prev,
      { ...msg, id: crypto.randomUUID(), timestamp: new Date() },
    ]);
  }, []);

  const sendMessage = useCallback(async () => {
    if (!input.trim() || isRunning) return;
    const task = input.trim();
    setInput("");
    setIsRunning(true);

    addMessage({ role: "user", content: task });

    const taskId = crypto.randomUUID();
    const wsProto = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${wsProto}://${window.location.host}/ws/agent/${taskId}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(JSON.stringify({ task, agent_type: agentType, context: {} }));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data) as {
          type: string;
          payload: unknown;
        };

        if (data.type === "log") {
          addMessage({
            role: "system",
            content: String(data.payload),
            agentType,
          });
        } else if (data.type === "result") {
          addMessage({
            role: "agent",
            content: String(data.payload),
            agentType,
          });
        } else if (data.type === "error") {
          addMessage({ role: "system", content: `Error: ${data.payload}` });
        } else if (data.type === "done") {
          ws.close();
          setIsRunning(false);
        }
      };

      ws.onerror = () => {
        // Fallback to REST
        fetchRest(task);
      };

      ws.onclose = () => {
        wsRef.current = null;
        setIsRunning(false);
      };
    } catch {
      fetchRest(task);
    }

    async function fetchRest(t: string) {
      try {
        const res = await fetch("/api/v1/agent/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ task: t, agent_type: agentType, context: {} }),
        });
        const data = (await res.json()) as { message: string };
        addMessage({ role: "agent", content: data.message, agentType });
      } catch (err) {
        addMessage({ role: "system", content: `Request failed: ${err}` });
      } finally {
        setIsRunning(false);
      }
    }
  }, [input, isRunning, agentType, addMessage]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 p-4 border-b border-surface-700">
        <h2 className="font-semibold text-slate-100">Agent Chat</h2>
        <select
          value={agentType}
          onChange={(e) => setAgentType(e.target.value as AgentType)}
          className="input-dark w-40"
          disabled={isRunning}
        >
          {(Object.keys(AGENT_LABELS) as AgentType[]).map((t) => (
            <option key={t} value={t}>
              {AGENT_LABELS[t]}
            </option>
          ))}
        </select>
        {isRunning && (
          <span className="text-xs text-brand-500 animate-pulse">Running...</span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={endRef} />
      </div>

      <div className="p-4 border-t border-surface-700">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your task... (Enter to send, Shift+Enter for newline)"
            className="input-dark flex-1 resize-none h-16"
            disabled={isRunning}
          />
          <button
            onClick={sendMessage}
            disabled={isRunning || !input.trim()}
            className="btn-primary self-end"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }): React.ReactElement {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-3xl rounded-xl px-4 py-3 text-sm ${
          isUser
            ? "bg-brand-600 text-white"
            : isSystem
              ? "bg-surface-700 text-slate-400 italic text-xs"
              : "bg-surface-700 text-slate-100"
        }`}
      >
        {!isUser && !isSystem && message.agentType && (
          <div className="text-brand-400 text-xs font-mono mb-1">
            {message.agentType.toUpperCase()} AGENT
          </div>
        )}
        <pre className="whitespace-pre-wrap font-sans">{message.content}</pre>
        <div className="text-xs opacity-40 mt-1">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}
