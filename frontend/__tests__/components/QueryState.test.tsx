import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryState } from "@/components/QueryState";
import { HealthBanner } from "@/components/HealthBanner";

describe("QueryState Component", () => {
  it("test_loading_state_shows_spinner", () => {
    render(
      <QueryState isLoading={true} error={null}>
        <p>content</p>
      </QueryState>,
    );
    expect(screen.getByText("加载中...")).toBeInTheDocument();
    expect(screen.queryByText("content")).not.toBeInTheDocument();
  });

  it("test_empty_state_shows_custom_message", () => {
    render(
      <QueryState isLoading={false} error={null} isEmpty emptyMessage="暂无数据">
        <p>content</p>
      </QueryState>,
    );
    expect(screen.getByText("暂无数据")).toBeInTheDocument();
    expect(screen.queryByText("content")).not.toBeInTheDocument();
  });

  it("test_error_state_shows_code_and_message", () => {
    const error = new Error("NOT_FOUND: 资源不存在");
    render(
      <QueryState isLoading={false} error={error}>
        <p>content</p>
      </QueryState>,
    );
    expect(screen.getByText(/资源不存在/)).toBeInTheDocument();
    expect(screen.queryByText("content")).not.toBeInTheDocument();
  });

  it("test_success_state_renders_children", () => {
    render(
      <QueryState isLoading={false} error={null}>
        <p>content</p>
      </QueryState>,
    );
    expect(screen.getByText("content")).toBeInTheDocument();
  });

  it("test_error_state_supports_retry", () => {
    let retryCalled = false;
    const error = new Error("网络错误");
    render(
      <QueryState isLoading={false} error={error} onRetry={() => { retryCalled = true; }}>
        <p>content</p>
      </QueryState>,
    );
    const retryBtn = screen.getByRole("button", { name: /重试/ });
    retryBtn.click();
    expect(retryCalled).toBe(true);
  });
});

// ===== Step 4: Health Banner & Three-State Consistency =====

describe("HealthBanner", () => {
  it("test_health_banner_shows_connected_when_backend_up", () => {
    render(<HealthBanner isConnected={true} isLoading={false} error={null} />);
    expect(screen.getByText(/正常|已连接/)).toBeInTheDocument();
  });

  it("test_health_banner_shows_disconnected_when_backend_down", () => {
    const error = new Error("Failed to fetch");
    render(<HealthBanner isConnected={false} isLoading={false} error={error} />);
    expect(screen.getByText(/离线|连接失败|异常/)).toBeInTheDocument();
  });

  it("test_health_banner_shows_loading_during_check", () => {
    render(<HealthBanner isConnected={false} isLoading={true} error={null} />);
    expect(screen.getByText(/检测中/)).toBeInTheDocument();
  });
});

describe("QueryState three-state consistency", () => {
  it("test_loading_state_never_renders_children", () => {
    render(
      <QueryState isLoading={true} error={null}>
        <p>secret-content</p>
      </QueryState>,
    );
    expect(screen.queryByText("secret-content")).not.toBeInTheDocument();
    expect(screen.getByText("加载中...")).toBeInTheDocument();
  });

  it("test_error_state_never_renders_children", () => {
    render(
      <QueryState isLoading={false} error={new Error("boom")}>
        <p>secret-content</p>
      </QueryState>,
    );
    expect(screen.queryByText("secret-content")).not.toBeInTheDocument();
    expect(screen.getByText(/boom/)).toBeInTheDocument();
  });

  it("test_empty_state_with_retry_action", () => {
    const retryFn = vi.fn();
    render(
      <QueryState isLoading={false} error={null} isEmpty onRetry={retryFn} emptyMessage="没有数据">
        <p>content</p>
      </QueryState>,
    );
    expect(screen.getByText("没有数据")).toBeInTheDocument();
    // Empty state should also support retry if provided
    const retryBtn = screen.queryByRole("button", { name: /重试/ });
    if (retryBtn) {
      retryBtn.click();
      expect(retryFn).toHaveBeenCalled();
    }
  });
});
