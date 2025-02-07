import React, { useState } from "react";

interface RepoStructure {
  [key: string]: RepoStructure | string;
}

interface AnalysisResult {
  repo_path: string;
  structure: RepoStructure;
  summary: string;
  file_count: number;
  languages: string[];
}

export default function RepoAnalyzer(): React.ReactElement {
  const [repoPath, setRepoPath] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const analyze = async () => {
    if (!repoPath.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch("/api/v1/repo/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_path: repoPath }),
      });

      if (!res.ok) {
        const err = (await res.json()) as { detail: string };
        throw new Error(err.detail || "Analysis failed");
      }

      const data = (await res.json()) as AnalysisResult;
      setResult(data);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 space-y-4">
      <h2 className="font-semibold text-slate-100">Repository Analyzer</h2>

      <div className="flex gap-2">
        <input
          type="text"
          value={repoPath}
          onChange={(e) => setRepoPath(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && analyze()}
          placeholder="/path/to/local/repo"
          className="input-dark flex-1"
          disabled={loading}
        />
        <button onClick={analyze} disabled={loading || !repoPath.trim()} className="btn-primary">
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 text-red-300 rounded-lg p-3 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="card">
            <h3 className="text-sm font-medium text-slate-300 mb-2">Summary</h3>
            <p className="text-sm text-slate-200">{result.summary}</p>
            <div className="mt-3 flex gap-4 text-xs text-slate-400">
              <span>{result.file_count} files</span>
              <span>{result.languages.slice(0, 5).join(", ")}</span>
            </div>
          </div>

          <div className="card">
            <h3 className="text-sm font-medium text-slate-300 mb-2">Structure</h3>
            <div className="overflow-y-auto max-h-64">
              <TreeView node={result.structure} indent={0} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function TreeView({
  node,
  indent,
}: {
  node: RepoStructure;
  indent: number;
}): React.ReactElement {
  return (
    <div style={{ paddingLeft: `${indent * 16}px` }}>
      {Object.entries(node).map(([key, value]) => (
        <div key={key}>
          <div className="text-xs py-0.5 flex items-center gap-1">
            {typeof value === "object" ? (
              <>
                <span className="text-brand-400">📁</span>
                <span className="text-slate-300 font-medium">{key}/</span>
              </>
            ) : (
              <>
                <span className="text-slate-600">📄</span>
                <span className="text-slate-400">{key}</span>
                <span className="text-slate-600 ml-1">({value})</span>
              </>
            )}
          </div>
          {typeof value === "object" && (
            <TreeView node={value as RepoStructure} indent={indent + 1} />
          )}
        </div>
      ))}
    </div>
  );
}
