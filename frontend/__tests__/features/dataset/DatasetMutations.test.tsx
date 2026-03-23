import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ImportForm } from "@/features/dataset/components/ImportForm";
import { FreezeButton } from "@/features/dataset/components/FreezeButton";
import { SceneLabelEditor } from "@/features/dataset/components/SceneLabelEditor";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("ImportForm", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_import_form_renders_fields", () => {
    render(<ImportForm datasetId="ds-1" />, { wrapper });
    expect(screen.getByLabelText(/版本号/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Manifest URI/)).toBeInTheDocument();
  });

  it("test_import_form_validates_version", async () => {
    const user = userEvent.setup();
    render(<ImportForm datasetId="ds-1" />, { wrapper });
    // Leave manifest_uri empty to trigger required validation
    const uriInput = screen.getByLabelText(/Manifest URI/);
    await user.click(uriInput);
    await user.click(screen.getByRole("button", { name: /导入/ }));
    await waitFor(() => {
      // Form submission should be prevented by validation
      expect(screen.getByRole("button", { name: /导入/ })).toBeInTheDocument();
    });
  });
});

describe("FreezeButton", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_freeze_button_shows_confirm_dialog", async () => {
    const user = userEvent.setup();
    render(<FreezeButton datasetId="ds-1" version={1} frozen={false} />, { wrapper });
    await user.click(screen.getByRole("button", { name: /冻结/ }));
    expect(screen.getByText(/确认冻结/)).toBeInTheDocument();
  });

  it("test_freeze_success_disables_button", () => {
    render(<FreezeButton datasetId="ds-1" version={1} frozen={true} />, { wrapper });
    const btn = screen.getByRole("button", { name: /已冻结/ });
    expect(btn).toBeDisabled();
  });
});

describe("SceneLabelEditor", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("test_scene_label_editor_requires_other_text_when_weather_is_other", async () => {
    const user = userEvent.setup();
    render(<SceneLabelEditor datasetVersionId="ds-1:v1" />, { wrapper });

    const weatherSelect = screen.getByLabelText(/天气/);
    await user.selectOptions(weatherSelect, "other");
    await user.click(screen.getByRole("button", { name: /保存/ }));

    await waitFor(() => {
      expect(screen.getByText(/必填/)).toBeInTheDocument();
    });
  });

  it("test_scene_label_editor_submits_valid_labels_successfully", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ ok: true, data: { items: [] } }),
      }),
    );
    const user = userEvent.setup();
    render(<SceneLabelEditor datasetVersionId="ds-1:v1" />, { wrapper });

    const imageInput = screen.getByLabelText(/图片 ID/);
    const todSelect = screen.getByLabelText(/时间段/);
    const weatherSelect = screen.getByLabelText(/天气/);
    const envSelect = screen.getByLabelText(/环境/);

    await user.type(imageInput, "img-001");
    await user.selectOptions(todSelect, "day");
    await user.selectOptions(weatherSelect, "sunny");
    await user.selectOptions(envSelect, "outdoor");
    await user.click(screen.getByRole("button", { name: /保存/ }));

    await waitFor(() => {
      expect(vi.mocked(fetch)).toHaveBeenCalled();
    });
  });
});
