# AI Training Platform — 前端

## 环境要求

- Node.js >= 20
- pnpm >= 9

## 快速启动

```bash
# 安装依赖
pnpm install

# 安装 Playwright 浏览器（仅 E2E 测试需要）
pnpm exec playwright install chromium

# 启动开发服务器
pnpm dev
```

打开 http://localhost:3000 访问前端界面。

## 环境配置

在 `frontend/.env.local` 中配置后端地址（默认 `http://localhost:8000`）：

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 联调步骤

1. 启动后端服务：`cd .. && PYTHONPATH=src python -m uvicorn web.app:create_app --factory --port 8000`
2. 启动前端：`pnpm dev`
3. 访问 http://localhost:3000，按演示 SOP 操作

## 质量命令

```bash
# ESLint 检查
pnpm lint

# TypeScript 类型检查
pnpm typecheck

# 单元测试 (Vitest, 141 tests)
pnpm test

# E2E 冒烟测试 (Playwright, 需全栈启动)
pnpm e2e

# Phase 7 单测
pnpm test:phase7:unit

# Phase 7 E2E
pnpm test:phase7:e2e

# Phase 7 E2E（终端输出，不生成 playwright-report 目录）
pnpm test:phase7:e2e:noreport

# Phase 7 全量验证
pnpm verify:phase7

# Phase 7 全量验证（终端输出，不生成 playwright-report 目录）
pnpm verify:phase7:noreport
```

## Phase 7 验证入口

Phase 7 覆盖 Gateway 页面、知识系统 E2E 冒烟、以及 data-testid 集成补全。

```bash
# Gateway Vitest
pnpm test:phase7:unit

# Phase 7 Playwright
pnpm test:phase7:e2e

# 如只需要终端结果且不希望再次生成 playwright-report 目录，使用这个命令
pnpm test:phase7:e2e:noreport

# 一次性跑完 lint / typecheck / unit / e2e
pnpm verify:phase7

# 一次性跑完所有 Phase 7 校验，并避免生成 playwright-report 目录
pnpm verify:phase7:noreport
```

说明：
- `test:phase7:e2e` 使用 Playwright 默认 HTML reporter，适合本地查看详细报告。
- `test:phase7:e2e:noreport` 改为终端 line reporter，避免生成 `playwright-report/` 目录。

## 项目结构

```
src/
  app/(dashboard)/       # 页面路由 (Next.js App Router)
  components/            # 通用组件 (Sidebar, ErrorBoundary, QueryState)
  features/              # 业务模块
    project/             # 项目 KPI 配置
    dataset/             # 数据集导入/冻结
    job/                 # 训练任务管理 + 产物展示
    proposal/            # Proposal 验证与确认
    export/              # 导出与部署基准
  lib/
    api/                 # API Client (request, project, dataset, job, analysis, export, proposal)
    query/               # TanStack Query hooks (useHealthCheck, useMutationWithToast)
  schemas/               # Zod 表单校验 schema
__tests__/               # Vitest 单元测试
tests/e2e/               # Playwright E2E 测试
```

## 演示 SOP

1. 启动后端 + 前端
2. 导航到 **Datasets** → 导入新数据集版本 → 冻结版本
3. 导航到 **Jobs** → 查看任务列表 → 点击任务进入详情
4. 在任务详情页 → 查看日志/指标/产物 Tab
5. 在产物 Tab → 查看评估报告、证据包、分析报告、候选实验
6. 导航到 **Proposals** → 验证候选实验
7. 导航到 **Exports** → 创建导出任务 → 查看导出状态与基准

## 验收清单 (2026-03-11 修复轮次)

本轮修复覆盖接口层契约对齐、前端页面闭环、审计可追溯与性能基线建立。

### 后端验证

```bash
cd .. && PYTHONPATH=src python -m pytest tests/ -v
# 预期: 154 tests passed
```

关键新增覆盖:
- **接口层**: `GET /jobs`, `GET /datasets` 列表接口；Proposal 产物校验；Export `created_at`/`latency_ms` 对齐
- **服务层**: Eval/Agent 审计字段 (`job_id`/`run_id`/`created_at`)
- **仓储层**: 场景覆盖率万级样本性能基线 (单维度 <1ms, 组合 <10ms)

### 前端验证

```bash
# 单元测试
pnpm test
# 预期: 141 tests passed

# E2E 回归 (需先启动后端 + 前端)
pnpm e2e
```

关键新增覆盖:
- **页面闭环**: KPI 预填、场景标签编辑、任务创建/启动/产物查看、Proposal 确认跳转、导出状态轮询
- **全局状态**: HealthBanner 三态一致 (connected/disconnected/loading)
- **E2E 回归**: 主链路冒烟 (`main-flow-regression.spec.ts`) — 数据集→任务→产物→Proposal→导出

## 技术栈

- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript
- **样式**: Tailwind CSS + shadcn/ui
- **数据获取**: TanStack React Query v5
- **表单**: React Hook Form + Zod v3
- **Markdown**: react-markdown + rehype-sanitize (XSS 防护)
- **单元测试**: Vitest + Testing Library
- **E2E 测试**: Playwright

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
