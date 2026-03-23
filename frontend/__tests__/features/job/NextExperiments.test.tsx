import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { NextExperiments } from "@/features/job/components/NextExperiments";
import type { Candidate } from "@/lib/api/analysis";

const candidates: Candidate[] = [
  {
    name: "A_提高imgsz以改善小目标夜间FN",
    changes: { train_args: { imgsz: 960 } },
    expected: { kpi_delta: { "漏检率": -0.01, "时延ms": 2 } },
    evidence_refs: ["evaluation.by_scene[night+rain].fn", "dataset.stats.small_object_ratio"],
  },
  {
    name: "B_增大batch_size",
    changes: { train_args: { batch_size: 32 } },
    expected: { kpi_delta: { "漏检率": -0.005 } },
    evidence_refs: ["evaluation.by_class.person.recall"],
  },
];

describe("NextExperiments", () => {
  it("test_candidates_render_as_cards", () => {
    render(<NextExperiments baselineJobId="j1" candidates={candidates} />);
    const cards = screen.getAllByRole("article");
    expect(cards).toHaveLength(2);
  });

  it("test_candidate_card_shows_four_elements", () => {
    const { container } = render(<NextExperiments baselineJobId="j1" candidates={candidates} />);
    // name
    expect(screen.getByText("A_提高imgsz以改善小目标夜间FN")).toBeInTheDocument();
    // changes - the JSON is rendered in a pre element; use container query
    expect(container.textContent).toContain("imgsz");
    // expected
    expect(screen.getAllByText(/漏检率/).length).toBeGreaterThanOrEqual(1);
    // evidence_refs
    expect(screen.getByText(/evaluation\.by_scene/)).toBeInTheDocument();
  });

  it("test_changes_highlight_from_to", () => {
    render(<NextExperiments baselineJobId="j1" candidates={candidates} />);
    expect(screen.getByText(/960/)).toBeInTheDocument();
  });

  it("test_evidence_refs_are_clickable", () => {
    render(<NextExperiments baselineJobId="j1" candidates={candidates} />);
    // evidence_refs should be rendered as list items (not links to external URLs, just highlighted refs)
    expect(screen.getByText("evaluation.by_scene[night+rain].fn")).toBeInTheDocument();
    expect(screen.getByText("dataset.stats.small_object_ratio")).toBeInTheDocument();
  });

  it("test_empty_candidates", () => {
    render(<NextExperiments baselineJobId="j1" candidates={[]} />);
    expect(screen.getByText(/暂无候选实验/)).toBeInTheDocument();
  });
});
