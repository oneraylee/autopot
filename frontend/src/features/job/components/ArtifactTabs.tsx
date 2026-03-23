"use client";

import { useState } from "react";
import { EvalReport } from "./EvalReport";
import { EvidencePack } from "./EvidencePack";
import { AnalysisReport } from "./AnalysisReport";
import { NextExperiments } from "./NextExperiments";
import type { EvalReportPayload, NextExperimentsPayload, Candidate } from "@/lib/api/analysis";

type TabKey = "eval" | "evidence" | "analysis" | "experiments";

interface ArtifactData {
  evalReport: EvalReportPayload | null;
  evidencePack: { summary: string; artifact_index: string[]; kpi_config: Record<string, unknown> } | null;
  analysisReport: string | null;
  nextExperiments: NextExperimentsPayload | null;
}

interface ArtifactTabsProps {
  jobId: string;
  artifacts: ArtifactData | null;
  onCreateTask?: (candidate: Candidate) => void;
}

const tabs: { key: TabKey; label: string }[] = [
  { key: "eval", label: "评估报告" },
  { key: "evidence", label: "证据包" },
  { key: "analysis", label: "分析报告" },
  { key: "experiments", label: "候选实验" },
];

export function ArtifactTabs({ artifacts, onCreateTask }: Omit<ArtifactTabsProps, "jobId"> & { jobId?: string }) {
  const [activeTab, setActiveTab] = useState<TabKey>("eval");

  if (!artifacts) {
    return <p className="text-sm text-muted-foreground">暂无产物数据</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2 border-b">
        {tabs.map((t) => (
          <button
            key={t.key}
            data-testid={`artifact-tab-${t.key}`}
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === t.key
                ? "border-b-2 border-primary text-primary"
                : "text-muted-foreground"
            }`}
            onClick={() => setActiveTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div>
        {activeTab === "eval" &&
          (artifacts.evalReport ? (
            <EvalReport data={artifacts.evalReport} />
          ) : (
            <p className="text-sm text-muted-foreground">暂无数据</p>
          ))}

        {activeTab === "evidence" &&
          (artifacts.evidencePack ? (
            <EvidencePack data={artifacts.evidencePack} />
          ) : (
            <p className="text-sm text-muted-foreground">暂无数据</p>
          ))}

        {activeTab === "analysis" &&
          (artifacts.analysisReport ? (
            <AnalysisReport content={artifacts.analysisReport} />
          ) : (
            <p className="text-sm text-muted-foreground">暂无数据</p>
          ))}

        {activeTab === "experiments" &&
          (artifacts.nextExperiments ? (
            <NextExperiments
              baselineJobId={artifacts.nextExperiments.baseline_job_id}
              candidates={artifacts.nextExperiments.candidates}
              onCreateTask={onCreateTask}
            />
          ) : (
            <p className="text-sm text-muted-foreground">暂无数据</p>
          ))}
      </div>
    </div>
  );
}
