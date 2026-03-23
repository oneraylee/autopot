"use client";

import type { Candidate } from "@/lib/api/analysis";

interface NextExperimentsProps {
  baselineJobId: string;
  candidates: Candidate[];
  onCreateTask?: (candidate: Candidate) => void;
}

export function NextExperiments({ baselineJobId, candidates, onCreateTask }: NextExperimentsProps) {
  if (candidates.length === 0) {
    return <p className="text-sm text-muted-foreground">暂无候选实验</p>;
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        基准任务: <span className="font-mono">{baselineJobId}</span>
      </p>
      {candidates.map((c) => (
        <article key={c.name} className="border rounded-lg p-4 space-y-3">
          {/* Name */}
          <h4 className="font-semibold text-base">{c.name}</h4>

          {/* Changes */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">变更参数</p>
            <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
              {JSON.stringify(c.changes, null, 2)}
            </pre>
          </div>

          {/* Expected KPI Delta */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">预期影响</p>
            <div className="flex gap-3 flex-wrap">
              {Object.entries(c.expected.kpi_delta).map(([metric, delta]) => (
                <span
                  key={metric}
                  className={`text-xs px-2 py-1 rounded ${delta < 0 ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"}`}
                >
                  {metric}: {delta > 0 ? "+" : ""}{delta}
                </span>
              ))}
            </div>
          </div>

          {/* Evidence Refs */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">证据引用</p>
            <ul className="space-y-0.5">
              {c.evidence_refs.map((ref) => (
                <li key={ref} className="text-xs font-mono text-blue-600">{ref}</li>
              ))}
            </ul>
          </div>

          {/* Create Task Button */}
          {onCreateTask && (
            <button
              type="button"
              className="text-sm px-3 py-1 bg-primary text-primary-foreground rounded hover:opacity-90"
              data-testid="candidate-create-task-btn"
              onClick={() => onCreateTask(c)}
            >
              创建任务
            </button>
          )}
        </article>
      ))}
    </div>
  );
}
