import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { EvidencePack } from "@/features/job/components/EvidencePack";

describe("EvidencePack", () => {
  const packData = {
    summary: "训练完成，KPI 达标",
    artifact_index: ["/data/sample_visuals", "/data/curves/loss.json", "/data/confusion_matrix.png"],
    kpi_config: {
      weights: { "漏检率": 0.5, "误检率": 0.3, "时延ms": 0.2 },
      thresholds: { "漏检率": 0.05, "误检率": 0.1 },
    },
  };

  it("test_evidence_pack_renders_summary", () => {
    render(<EvidencePack data={packData} />);
    expect(screen.getByText(/训练完成/)).toBeInTheDocument();
  });

  it("test_evidence_pack_renders_artifact_index", () => {
    render(<EvidencePack data={packData} />);
    expect(screen.getByText("/data/sample_visuals")).toBeInTheDocument();
    expect(screen.getByText("/data/curves/loss.json")).toBeInTheDocument();
    expect(screen.getByText("/data/confusion_matrix.png")).toBeInTheDocument();
  });

  it("test_evidence_pack_renders_kpi_config", () => {
    render(<EvidencePack data={packData} />);
    expect(screen.getAllByText("漏检率").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("0.5")).toBeInTheDocument(); // weight
  });

  it("test_evidence_pack_empty_index", () => {
    const empty = { summary: "空", artifact_index: [], kpi_config: {} };
    render(<EvidencePack data={empty} />);
    expect(screen.getByText(/暂无产物/)).toBeInTheDocument();
  });
});
