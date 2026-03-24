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
  { label: "Knowledge", href: "/knowledge/sources" },
  { label: "Settings", href: "/settings/llm-gateway" },
];

const knowledgeSubItems = [
  { label: "Sources", href: "/knowledge/sources" },
  { label: "Skills", href: "/knowledge/skills" },
  { label: "Review", href: "/knowledge/review" },
];

const settingsSubItems = [{ label: "LLM Gateway", href: "/settings/llm-gateway" }];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-56 flex-col border-r bg-card px-3 py-4">
      <h2 className="mb-6 px-2 text-lg font-semibold">AI Training</h2>
      <nav className="flex flex-col gap-1">
        {navItems.map((item) => {
          const isKnowledge = item.href.startsWith("/knowledge");
          const isKnowledgeActive = pathname?.startsWith("/knowledge") ?? false;
          const isSettings = item.href.startsWith("/settings");
          const isSettingsActive = pathname?.startsWith("/settings") ?? false;

          return (
            <div key={item.href}>
              <Link
                href={item.href}
                data-testid={`nav-${item.label.toLowerCase()}`}
                className={cn(
                  "rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent",
                  (pathname?.startsWith(item.href) ?? false) ||
                    (isKnowledge && isKnowledgeActive) ||
                    (isSettings && isSettingsActive)
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground",
                )}
              >
                {item.label}
              </Link>
              {isKnowledge && isKnowledgeActive && (
                <div className="ml-4 mt-1 flex flex-col gap-0.5">
                  {knowledgeSubItems.map((sub) => (
                    <Link
                      key={sub.href}
                      href={sub.href}
                      className={cn(
                        "rounded-md px-3 py-1 text-xs transition-colors hover:bg-accent",
                        (pathname?.startsWith(sub.href) ?? false)
                          ? "text-accent-foreground"
                          : "text-muted-foreground",
                      )}
                    >
                      {sub.label}
                    </Link>
                  ))}
                </div>
              )}
              {isSettings && isSettingsActive && (
                <div className="ml-4 mt-1 flex flex-col gap-0.5">
                  {settingsSubItems.map((sub) => (
                    <Link
                      key={sub.href}
                      href={sub.href}
                      className={cn(
                        "rounded-md px-3 py-1 text-xs transition-colors hover:bg-accent",
                        (pathname?.startsWith(sub.href) ?? false)
                          ? "text-accent-foreground"
                          : "text-muted-foreground",
                      )}
                    >
                      {sub.label}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </nav>
    </aside>
  );
}

