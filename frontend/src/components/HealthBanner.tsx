"use client";

interface HealthBannerProps {
  isConnected: boolean;
  isLoading: boolean;
  error: Error | null;
}

export function HealthBanner({ isConnected, isLoading, error }: HealthBannerProps) {
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 rounded bg-yellow-50 px-3 py-1.5 text-xs text-yellow-800" data-testid="health-banner">
        <span className="h-2 w-2 rounded-full bg-yellow-400" />
        <span>检测中...</span>
      </div>
    );
  }

  if (!isConnected || error) {
    return (
      <div className="flex items-center gap-2 rounded bg-red-50 px-3 py-1.5 text-xs text-red-800" data-testid="health-banner">
        <span className="h-2 w-2 rounded-full bg-red-500" />
        <span>后端异常</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 rounded bg-green-50 px-3 py-1.5 text-xs text-green-800" data-testid="health-banner">
      <span className="h-2 w-2 rounded-full bg-green-500" />
      <span>已连接</span>
    </div>
  );
}
