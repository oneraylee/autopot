"use client";

import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex min-h-[200px] items-center justify-center p-6">
          <div className="text-center space-y-2">
            <h2 className="text-lg font-semibold text-destructive">页面发生错误</h2>
            <p className="text-sm text-muted-foreground">
              {this.state.error?.message ?? "未知错误"}
            </p>
            <button
              className="mt-2 rounded bg-primary px-4 py-2 text-sm text-primary-foreground"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              重试
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
