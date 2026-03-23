"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navItems = [
  { label: "Projects", href: "/projects" },
  { label: "Datasets", href: "/datasets" },
  { label: "Jobs", href: "/jobs" },
  { label: "Proposals", href: "/proposals" },
  { label: "Exports", href: "/exports" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-56 flex-col border-r bg-card px-3 py-4">
      <h2 className="mb-6 px-2 text-lg font-semibold">AI Training</h2>
      <nav className="flex flex-col gap-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            data-testid={`nav-${item.label.toLowerCase()}`}
            className={cn(
              "rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent",
              pathname.startsWith(item.href)
                ? "bg-accent text-accent-foreground"
                : "text-muted-foreground",
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
