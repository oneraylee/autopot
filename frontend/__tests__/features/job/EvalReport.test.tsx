import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { EvalReport } from "@/features/job/components/EvalReport";

describe("EvalReport", () => {
  const evalData = {
    overall: {
      business_kpi: 0.92,
      kpi_components: { "漏检率": 0.031, "误检率": 0.052, "时延ms": 18.4 },
    },
    by_class: [
      { class_name: "car", precision: 0.95, recall: 0.9 },
      { class_name: "person", precision: 0.88, recall: 0.85 },
    ],
    by_scene: [
      { scene: { time_of_day: "night", weather: "rain" }, kpi: 0.85, fn: 3, fp: 1 },
      { scene: { time_of_day: "day", weather: "clear" }, kpi: 0.95, fn: 0, fp: 2 },
    ],
  };

  it("test_eval_report_renders_overall_kpi", () => {
    render(<EvalReport data={evalData} />);
    expect(screen.getByText("0.92")).toBeInTheDocument();
    expect(screen.getByText(/business_kpi/i)).toBeInTheDocument();
  });

  it("test_eval_report_renders_by_class_table", () => {
    render(<EvalReport data={evalData} />);
    expect(screen.getByText("car")).toBeInTheDocument();
    expect(screen.getByText("person")).toBeInTheDocument();
  });

  it("test_eval_report_renders_by_scene_table", () => {
    render(<EvalReport data={evalData} />);
    expect(screen.getByText("night")).toBeInTheDocument();
    expect(screen.getByText("rain")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument(); // fn
  });

  it("test_eval_report_renders_kpi_components", () => {
    render(<EvalReport data={evalData} />);
    expect(screen.getByText("漏检率")).toBeInTheDocument();
    expect(screen.getByText("0.031")).toBeInTheDocument();
  });

  it("test_eval_report_empty_data", () => {
    const empty = { overall: { business_kpi: 0, kpi_components: {} }, by_class: [], by_scene: [] };
    render(<EvalReport data={empty} />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });
});
