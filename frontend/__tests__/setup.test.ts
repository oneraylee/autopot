import { describe, it, expect } from "vitest";
import fs from "fs";
import path from "path";

describe("Step 1: 工程初始化与开发工具链", () => {
  const root = path.resolve(__dirname, "..");

  it("test_typescript_strict_mode_enabled", () => {
    const tsconfig = JSON.parse(
      fs.readFileSync(path.join(root, "tsconfig.json"), "utf-8"),
    );
    expect(tsconfig.compilerOptions.strict).toBe(true);
  });

  it("test_env_example_contains_api_base_url", () => {
    const envExample = fs.readFileSync(path.join(root, ".env.example"), "utf-8");
    expect(envExample).toContain("NEXT_PUBLIC_API_BASE_URL");
  });

  it("test_vitest_config_exists", () => {
    expect(fs.existsSync(path.join(root, "vitest.config.ts"))).toBe(true);
  });

  it("test_prettier_config_exists", () => {
    expect(fs.existsSync(path.join(root, ".prettierrc"))).toBe(true);
  });

  it("test_shadcn_button_component_exists", () => {
    expect(fs.existsSync(path.join(root, "src/components/ui/button.tsx"))).toBe(true);
  });

  it("test_path_alias_configured", () => {
    const tsconfig = JSON.parse(
      fs.readFileSync(path.join(root, "tsconfig.json"), "utf-8"),
    );
    expect(tsconfig.compilerOptions.paths).toHaveProperty("@/*");
  });
});
