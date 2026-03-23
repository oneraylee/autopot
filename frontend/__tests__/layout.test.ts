import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

const root = path.resolve(__dirname, "..");

const NAV_ITEMS = ["projects", "datasets", "jobs", "proposals", "exports"];

describe("Step 2: 全局布局与路由骨架", () => {
  it("test_sidebar_component_exists", () => {
    expect(fs.existsSync(path.join(root, "src/components/Sidebar.tsx"))).toBe(true);
  });

  it("test_layout_file_exists", () => {
    expect(fs.existsSync(path.join(root, "src/app/layout.tsx"))).toBe(true);
  });

  it.each(NAV_ITEMS)("test_route_%s_page_exists", (route) => {
    const pagePath = path.join(root, `src/app/(dashboard)/${route}/page.tsx`);
    expect(fs.existsSync(pagePath)).toBe(true);
  });

  it("test_sidebar_contains_all_nav_items", () => {
    const sidebar = fs.readFileSync(
      path.join(root, "src/components/Sidebar.tsx"),
      "utf-8",
    );
    for (const item of NAV_ITEMS) {
      expect(sidebar.toLowerCase()).toContain(item);
    }
  });

  it("test_dashboard_layout_exists", () => {
    expect(
      fs.existsSync(path.join(root, "src/app/(dashboard)/layout.tsx")),
    ).toBe(true);
  });
});
