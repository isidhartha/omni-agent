import React, { useState } from "react";

interface Issue {
  severity?: string;
  type?: string;
  path?: string;
  line?: number;
  detail: string;
}

interface ReviewResult {
  summary: string;
  issues: Issue[];
  suggestions: string[];
  score: number;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "text-red-400 bg-red-900/30 border-red-700",
  major: "text-orange-400 bg-orange-900/30 border-orange-700",
  minor: "text-yellow-400 bg-yellow-900/30 border-yellow-700",
  secret: "text-red-400 bg-red-900/30 border-red-700",
  todo: "text-blue-400 bg-blue-900/30 border-blue-700",
  long_line: "text-slate-400 bg-surface-700 border-surface-600",
};

export default function PRReviewer(): React.ReactElement {
  const [diff, setDiff] = useState("");
  const [context, setContext] = useState("");
  const [result, setResult] = useState<ReviewResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const review = async () => {
    if (!diff.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch("/api/v1/pr/review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ diff, context }),
      });
      if (!res.ok) {
        const err = (await res.json()) as { detail: string };
        throw new Error(err.detail || "Review failed");
      }
      setResult((await res.json()) as ReviewResult);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  const scoreColor =
    result
      ? result.score >= 80
        ? "text-green-400"
        : result.score >= 60
          ? "text-yellow-400"
          : "text-red-400"
      : "";

  return (
    <div className="p-4 space-y-4">
      <h2 className="font-semibold text-slate-100">PR Reviewer</h2>

      <div>
        <label className="text-xs text-slate-400 mb-1 block">PR Context (optional)</label>
        <input
          type="text"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder="What does this PR do?"
          className="input-dark"
        />
      </div>

      <div>
        <label className="text-xs text-slate-400 mb-1 block">Unified Diff</label>
        <textarea
          value={diff}
          onChange={(e) => setDiff(e.target.value)}
          placeholder="Paste your git diff here..."
          className="input-dark font-mono text-xs resize-none h-40"
          disabled={loading}
        />
      </div>

      <button onClick={review} disabled={loading || !diff.trim()} className="btn-primary w-full">
        {loading ? "Reviewing..." : "Review PR"}
      </button>

      {error && (
        <div className="bg-red-900/30 border border-red-700 text-red-300 rounded-lg p-3 text-sm">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="card flex items-start gap-4">
            <div className="text-3xl font-bold ${scoreColor}">
              <span className={scoreColor}>{result.score}</span>
              <span className="text-slate-500 text-lg">/100</span>
            </div>
            <div>
              <h3 className="text-sm font-medium text-slate-300 mb-1">Summary</h3>
              <p className="text-sm text-slate-200">{result.summary}</p>
            </div>
          </div>

          {result.issues.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-medium text-slate-300 mb-2">
                Issues ({result.issues.length})
              </h3>
              <div className="space-y-2">
                {result.issues.map((issue, idx) => {
                  const colorKey = issue.severity || issue.type || "minor";
                  const colors = SEVERITY_COLORS[colorKey] || SEVERITY_COLORS.minor;
                  return (
                    <div
                      key={idx}
                      className={`border rounded-lg px-3 py-2 text-xs ${colors}`}
                    >
                      <div className="font-medium uppercase">
                        {issue.severity || issue.type}
                        {issue.path && (
                          <span className="font-mono ml-2 opacity-70">
                            {issue.path}
                            {issue.line ? `:${issue.line}` : ""}
                          </span>
                        )}
                      </div>
                      <div className="mt-0.5 opacity-90">{issue.detail}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {result.suggestions.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-medium text-slate-300 mb-2">Suggestions</h3>
              <ul className="space-y-1">
                {result.suggestions.map((s, idx) => (
                  <li key={idx} className="text-sm text-slate-300 flex gap-2">
                    <span className="text-brand-400 mt-0.5">•</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
