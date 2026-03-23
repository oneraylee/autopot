import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AnalysisReport } from "@/features/job/components/AnalysisReport";

describe("AnalysisReport", () => {
  it("test_markdown_renders_headings_and_lists", () => {
    const md = "# Title\n\n- item1\n- item2\n\n## Subtitle\n\nParagraph text.";
    render(<AnalysisReport content={md} />);
    expect(screen.getByText("Title")).toBeInTheDocument();
    expect(screen.getByText("item1")).toBeInTheDocument();
    expect(screen.getByText("Subtitle")).toBeInTheDocument();
  });

  it("test_markdown_sanitizes_xss_scripts", () => {
    const md = 'Hello <script>alert("xss")</script> World';
    const { container } = render(<AnalysisReport content={md} />);
    expect(container.querySelector("script")).toBeNull();
    expect(screen.getByText(/Hello/)).toBeInTheDocument();
    expect(screen.getByText(/World/)).toBeInTheDocument();
  });

  it("test_empty_report_shows_empty_state", () => {
    render(<AnalysisReport content="" />);
    expect(screen.getByText(/暂无分析报告/)).toBeInTheDocument();
  });
});
