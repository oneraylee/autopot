import { test, expect } from "@playwright/test";

test.describe("Knowledge Import Workflow", () => {
  test("test_e2e_knowledge_import_workflow", async ({ page }) => {
    const state = {
      sources: [
        {
          source_id: "src-1",
          source_type: "local",
          name: "初始来源",
          uri: "/tmp/init",
          trust_level: 3,
          status: "active",
        },
      ],
      documents: [
        {
          document_id: "doc-1",
          source_id: "src-1",
          title: "Baseline Doc",
          doc_type: "markdown",
          parse_status: "parsed",
        },
      ],
      techniques: [
        {
          technique_id: "tech-1",
          skill_code: "training.optimizer.warmup",
          name: "Warmup",
          category: "training",
          layer: "optimizer",
          task_type: "det",
          maturity: "reviewed",
          status: "active",
        },
      ],
    };

    await page.route("**://localhost:8000/knowledge/sources", async (route, request) => {
      if (request.method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ ok: true, data: { items: state.sources, total: state.sources.length } }),
        });
        return;
      }
      if (request.method() === "POST") {
        const body = request.postDataJSON() as { name: string; uri: string; source_type: string; trust_level: number };
        const created = {
          source_id: "src-new",
          source_type: body.source_type,
          name: body.name,
          uri: body.uri,
          trust_level: body.trust_level,
          status: "active",
        };
        state.sources.unshift(created);
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ ok: true, data: created }),
        });
        return;
      }
      await route.continue();
    });

    await page.route("**://localhost:8000/knowledge/documents/import", async (route, request) => {
      const body = request.postDataJSON() as { source_id: string; title: string; doc_type: string };
      const created = {
        document_id: "doc-new",
        source_id: body.source_id,
        title: body.title,
        doc_type: body.doc_type,
        parse_status: "parsed",
      };
      state.documents = [created];
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ok: true, data: created }),
      });
    });

    await page.route("**://localhost:8000/knowledge/documents/*/chunks", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ok: true, data: { items: [{ chunk_id: "ck-1", text: "chunk", token_count: 12, index: 0 }] } }),
      });
    });

    await page.route("**://localhost:8000/knowledge/documents/*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ok: true, data: state.documents[0] }),
      });
    });

    await page.route("**://localhost:8000/knowledge/techniques**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ok: true, data: { items: state.techniques, total: state.techniques.length } }),
      });
    });

    await page.goto("/knowledge/sources");
    await page.getByTestId("knowledge-source-toggle").click();
    await page.getByLabel("来源名称").fill("测试来源");
    await page.getByLabel("URI / 路径").fill("/tmp/source");
    await page.getByTestId("create-source-btn").click();
    await expect(page.getByTestId("source-list")).toBeVisible();

    await page.goto("/knowledge/documents?source_id=src-new");
    await page.getByTestId("knowledge-doc-toggle-import").click();
    await page.getByLabel("文档标题").fill("导入文档");
    await page.getByTestId("import-document-btn").click();
    await expect(page.getByTestId("document-list")).toBeVisible();
    await expect(page.getByText("已解析")).toBeVisible();

    await page.goto("/knowledge/skills");
    await expect(page.getByTestId("skill-list")).toBeVisible();
    await expect(page.getByTestId("skill-row-tech-1")).toBeVisible();
  });

  test("test_e2e_document_chunk_preview_workflow", async ({ page }) => {
    await page.route("**://localhost:8000/knowledge/documents/*/chunks", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ok: true,
          data: {
            items: [
              {
                chunk_id: "chunk-1",
                document_id: "doc-1",
                section_path: "§ 1.1 数据准备",
                chunk_index: 0,
                token_count: 32,
                keywords: ["warmup", "schedule"],
              },
            ],
          },
        }),
      });
    });

    await page.route("**://localhost:8000/knowledge/documents/*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ok: true,
          data: {
            document_id: "doc-1",
            source_id: "src-chunk",
            title: "Chunk Ready",
            doc_type: "markdown",
            parse_status: "parsed",
          },
        }),
      });
    });

    await page.goto("/knowledge/documents?source_id=src-chunk");
    await expect(page.getByTestId("document-list")).toBeVisible();
    await page.getByTestId("document-row-doc-1").click();
    await expect(page.getByTestId("chunk-viewer")).toBeVisible();
    await expect(page.getByText("§ 1.1 数据准备")).toBeVisible();
    await expect(page.getByText("warmup")).toBeVisible();
  });
});
