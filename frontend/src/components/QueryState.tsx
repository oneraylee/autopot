import type { ReactNode } from "react";

interface QueryStateProps {
  isLoading: boolean;
  error: Error | null;
  isEmpty?: boolean;
  emptyMessage?: string;
  onRetry?: () => void;
  children: ReactNode;
}

export function QueryState({
  isLoading,
  error,
  isEmpty,
  emptyMessage = "暂无数据",
  onRetry,
  children,
}: QueryStateProps) {
  if (isLoading) {
    return <div className="p-6 text-muted-foreground">加载中...</div>;
  }

  if (error) {
    return (
      <div className="p-6">
        <p className="text-destructive">{error.message}</p>
        {onRetry && (
          <button
            className="mt-2 rounded border px-3 py-1 text-sm"
            onClick={onRetry}
          >
            重试
          </button>
        )}
      </div>
    );
  }

  if (isEmpty) {
    return <div className="p-6 text-muted-foreground">{emptyMessage}</div>;
  }

  return <>{children}</>;
}
