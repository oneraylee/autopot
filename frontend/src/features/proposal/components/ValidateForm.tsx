"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { validateProposals } from "@/lib/api/proposal";
import type { ValidateResult } from "@/lib/api/proposal";

export function ValidateForm() {
  const [jobId, setJobId] = useState("");
  const [runId, setRunId] = useState("");
  const [result, setResult] = useState<ValidateResult | null>(null);

  const mutation = useMutation({
    mutationFn: () => validateProposals(jobId, runId),
    onSuccess: (data) => setResult(data),
  });

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="validate-job-id" className="block text-sm font-medium">
          Job ID
        </label>
        <input
          id="validate-job-id"
          value={jobId}
          onChange={(e) => setJobId(e.target.value)}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
      </div>
      <div>
        <label htmlFor="validate-run-id" className="block text-sm font-medium">
          Run ID
        </label>
        <input
          id="validate-run-id"
          value={runId}
          onChange={(e) => setRunId(e.target.value)}
          className="mt-1 block w-full rounded border px-3 py-2 text-sm"
        />
      </div>
      <button
        onClick={() => mutation.mutate()}
        disabled={!jobId || !runId || mutation.isPending}
        className="rounded bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
      >
        {mutation.isPending ? "校验中..." : "校验"}
      </button>

      {mutation.error && (
        <p className="text-sm text-destructive">{mutation.error.message}</p>
      )}

      {result && (
        <div className="rounded-lg border p-4">
          <p className="font-medium">
            通过: {result.accepted} / 拒绝: {result.rejected}
          </p>
          {result.details.length > 0 && (
            <ul className="mt-2 space-y-1 text-sm">
              {result.details.map((d, i) => (
                <li key={i}>
                  {d.name}: {d.status}
                  {d.reason && <span className="text-muted-foreground"> - {d.reason}</span>}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
