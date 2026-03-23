import Link from "next/link";

export default function ProjectsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Projects</h1>
      <p className="text-muted-foreground">选择一个项目查看 KPI 配置。</p>
      <div className="rounded-lg border p-4">
        <Link
          href="/projects/default/kpi-config"
          className="text-primary underline hover:opacity-80"
        >
          默认项目 → KPI 配置
        </Link>
      </div>
    </div>
  );
}
