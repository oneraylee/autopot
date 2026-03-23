"use client";

import { useQueries } from "@tanstack/react-query";
import { getEvalReport, getEvidencePack, getAnalysisReport, getNextExperiments } from "@/lib/api/analysis";
import type { EvalReportPayload, NextExperimentsPayload } from "@/lib/api/analysis";

interface ArtifactData {
  evalReport: EvalReportPayload | null;
  evidencePack: { summary: string; artifact_index: string[]; kpi_config: Record<string, unknown> } | null;
  analysisReport: string | null;
  nextExperiments: NextExperimentsPayload | null;
}

export function useJobArtifacts(jobId: string) {
  const runId = jobId; // default run_id = job_id

  const results = useQueries({
    queries: [
      {
        queryKey: ["artifact", "eval-report", jobId],
        queryFn: () => getEvalReport(jobId, runId),
        retry: false,
      },
      {
        queryKey: ["artifact", "evidence-pack", jobId],
        queryFn: () => getEvidencePack(jobId, runId),
        retry: false,
      },
      {
        queryKey: ["artifact", "analysis-report", jobId],
        queryFn: () => getAnalysisReport(jobId, runId),
        retry: false,
      },
      {
        queryKey: ["artifact", "next-experiments", jobId],
        queryFn: () => getNextExperiments(jobId, runId),
        retry: false,
      },
    ],
  });

  const [evalQ, evidenceQ, analysisQ, experimentsQ] = results;
  const isLoading = results.some((q) => q.isLoading);
  const allSettled = results.every((q) => !q.isLoading);

  const data: ArtifactData | null = allSettled
    ? {
        evalReport: evalQ.data?.payload ?? null,
        evidencePack: evidenceQ.data?.payload ?? null,
        analysisReport: analysisQ.data?.payload?.analysis_report ?? null,
        nextExperiments: experimentsQ.data?.payload ?? null,
      }
    : null;

  return { data, isLoading };
}
