import React, { useState, useRef, useEffect } from "react";

interface TerminalLine {
  id: string;
  type: "input" | "stdout" | "stderr" | "system";
  content: string;
}

export default function Terminal(): React.ReactElement {
  const [lines, setLines] = useState<TerminalLine[]>([
    { id: "0", type: "system", content: "OmniAgent Terminal — run code snippets safely" },
  ]);
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("python");
  const [running, setRunning] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  const addLine = (type: TerminalLine["type"], content: string) => {
    setLines((prev) => [...prev, { id: crypto.randomUUID(), type, content }]);
  };

  const runCode = async () => {
    if (!code.trim() || running) return;
    setRunning(true);
    addLine("input", `$ [${language}] running...`);

    // Use the debug endpoint as a proxy to sandbox execution
    try {
      const res = await fetch("/api/v1/debug", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, error: "", language }),
      });

      if (!res.ok) {
        addLine("stderr", `HTTP ${res.status}: ${res.statusText}`);
      } else {
        const data = (await res.json()) as {
          analysis: string;
          fix: string;
          fixed_code?: string;
        };
        addLine("stdout", data.analysis || "Done.");
        if (data.fix && data.fix !== "See analysis.") {
          addLine("system", `Suggestion: ${data.fix}`);
        }
      }
    } catch (err) {
      addLine("stderr", String(err));
    } finally {
      setRunning(false);
    }
  };

  const clearTerminal = () => {
    setLines([{ id: "0", type: "system", content: "Terminal cleared." }]);
  };

  const lineColors: Record<TerminalLine["type"], string> = {
    input: "text-brand-400",
    stdout: "text-slate-200",
    stderr: "text-red-400",
    system: "text-slate-500 italic",
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 p-4 border-b border-surface-700">
        <h2 className="font-semibold text-slate-100">Terminal</h2>
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="input-dark w-32"
          disabled={running}
        >
          <option value="python">Python</option>
          <option value="javascript">JavaScript</option>
          <option value="bash">Bash</option>
        </select>
        <button onClick={clearTerminal} className="btn-secondary ml-auto text-xs">
          Clear
        </button>
      </div>

      <div className="flex-1 overflow-y-auto bg-black/30 p-4 font-mono text-xs">
        {lines.map((line) => (
          <div key={line.id} className={`${lineColors[line.type]} leading-5`}>
            {line.content}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <div className="p-4 border-t border-surface-700 space-y-2">
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder={`Enter ${language} code to execute...`}
          className="input-dark font-mono text-xs resize-none h-28"
          disabled={running}
        />
        <button
          onClick={runCode}
          disabled={running || !code.trim()}
          className="btn-primary w-full"
        >
          {running ? "Running..." : "Execute"}
        </button>
      </div>
    </div>
  );
}
