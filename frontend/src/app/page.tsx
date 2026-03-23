import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="mb-4 text-3xl font-bold">AI Training Platform</h1>
      <p className="mb-8 text-muted-foreground">管理控制台</p>
      <Button asChild>
        <Link href="/projects">开始使用</Link>
      </Button>
    </main>
  );
}
