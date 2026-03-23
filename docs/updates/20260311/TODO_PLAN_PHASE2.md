# 变更修复 Phase 2 开发计划（前端页面接线与主流程闭环）

## 项目概述

本阶段在 Phase 1 契约稳定后，补齐前端主流程页面的真实数据流与动作入口：完成 KPI 编辑、数据集详情与标签编辑、任务创建与启动、任务详情产物展示、Proposal 确认创建、导出状态与基准展示，形成“查 → 提 → 看 → 再创建”的页面闭环。

**架构设计原则**:
- 页面复用优先 - 优先复用已存在的 hooks、form、展示组件，避免重复实现
- 闭环优先 - 先打通真实入口与跳转，再优化视觉与局部体验
- 三态一致 - 所有接线页面必须提供 loading、empty、error 三态和明确反馈

## 架构验收标准

### 页面闭环
- [ ] KPI 页面支持查看与编辑同屏闭环
- [ ] 数据集详情页支持版本、冻结状态、覆盖率与标签编辑
- [ ] 任务列表支持创建任务入口，任务详情支持启动任务与产物查看
- [ ] 候选实验支持打开确认创建弹窗并创建新任务
- [ ] 导出页支持从创建结果进入状态与 benchmark 展示

### 前端契约一致性
- [ ] 所有页面只通过 `frontend/src/lib/api` 与 Query hooks 访问后端
- [ ] 页面展示字段与后端返回结构完全一致，不再手动兜底猜字段
- [ ] `NextExperiments`、`ConfirmCreateDialog`、`ExportStatus` 的输入结构稳定

### 可用性
- [ ] 所有关键页面无白屏、无永久 loading
- [ ] 成功动作具备跳转或刷新反馈
- [ ] 失败动作展示后端 message 与 code

## 阶段输入输出

### 输入
- `docs/changes/20260311/未实现功能清单.md`
- `docs/changes/20260311/TODO_PLAN_PHASE1.md`
- `docs/init/1.产品PRD.md`
- `docs/init/2.系统架构.md`
- `docs/init/3.模块设计文档.md`
- `docs/init/5.附录.md`
- 当前前端页面、hooks、组件、schema、tests

### 输出
- `frontend/src/app/(dashboard)/projects/[id]/kpi-config/page.tsx`
- `frontend/src/app/(dashboard)/datasets/page.tsx`
- `frontend/src/app/(dashboard)/datasets/[id]/page.tsx`
- `frontend/src/app/(dashboard)/jobs/page.tsx`
- `frontend/src/app/(dashboard)/jobs/[id]/page.tsx`
- `frontend/src/app/(dashboard)/proposals/page.tsx`
- `frontend/src/app/(dashboard)/exports/page.tsx`
- `frontend/src/app/(dashboard)/layout.tsx`
- `frontend/src/features/dataset/components/SceneLabelEditor.tsx`
- 必要时更新 `frontend/src/features/**`、`frontend/src/lib/api/**`、`frontend/__tests__/**`

## 依赖关系

- 前置依赖：Phase 1 已提供稳定的列表接口、Proposal 契约、导出接口结构
- 并行关系：局部组件测试可并行编写，但页面联调必须基于 Phase 1 最终响应格式
- 后置依赖：Phase 3 的 E2E、性能与文档验收依赖本阶段页面闭环稳定

## 开发步骤与测试用例

| 子任务 | 输入 | 输出 | 依赖 | 测试用例 |
|---|---|---|---|---|
| P2-1 接入 KPI 编辑表单 | 已存在 `KpiConfigForm` + KPI 查询页 | 可查看/可编辑的 KPI 页面 | Phase 1 `kpi-config` 接口稳定 | 默认值正确回填；保存成功后页面展示新值；错误时显示 message/code |
| P2-2 改造数据集列表页为真实列表 | `useDatasetList` + Phase 1 `/datasets` | `/datasets` 页面闭环 | Phase 1 数据集列表接口 | loading/empty/error 三态正确；点击列表项跳转详情 |
| P2-3 补齐数据集详情页 | PRD 数据集详情要求 | `/datasets/[id]` 真实详情页 | P2-2 | 展示版本、冻结状态、覆盖率；无数据时显示空态 |
| P2-4 新增 SceneLabelEditor | 附录场景枚举规则 | `SceneLabelEditor.tsx` | P2-3 | `weather=other` 时额外文本必填；保存成功提示明确；非法枚举显示校验错误 |
| P2-5 接入任务创建入口 | 已存在 `CreateJobForm` | `/jobs` 页面支持创建任务 | Phase 1 `/jobs` 列表接口 | 创建成功跳转详情；失败展示错误码；列表刷新正确 |
| P2-6 接入任务启动入口 | 已存在 `StartJobButton` | `/jobs/[id]` 页面支持启动 | Phase 1 `start_job` 契约 | created/queued 可启动；其他状态按钮禁用；启动成功后状态刷新 |
| P2-7 打通任务产物查询 | `analysis.ts` + 产物组件 | 任务详情页产物 Tab 真实展示 | Phase 1 产物与 Proposal 契约 | eval/evidence/analysis/next-experiments 正常显示；缺产物给出空态 |
| P2-8 接入 Proposal 确认创建弹窗 | `NextExperiments` + `ConfirmCreateDialog` | 候选实验→确认创建→跳转新任务 | P2-7 | 点击候选实验创建按钮弹窗打开；确认后跳转新 job；取消时不发请求 |
| P2-9 补齐导出结果展示链路 | `CreateExportForm` + `ExportStatus` + `DeployBenchmarkView` | `/exports` 页面闭环 | Phase 1 导出接口对齐 | 创建成功后可见 exportId；状态轮询停止条件正确；benchmark 正常展示 |
| P2-10 接入全局状态头部 | `useHealthCheck` | dashboard 顶部状态区 | 后端 `/health` | 后端可用时显示正常；异常时显示离线提示；不影响主内容渲染 |
| P2-11 补齐页面单测 | 现有 Vitest 结构 | 前端页面/组件测试更新 | P2-1~P2-10 | 任务详情产物 Tab 渲染；导出页状态区出现；数据集详情标签编辑可操作 |

## TDD 执行清单

- [ ] Red：先补页面接线失败测试，覆盖真实数据流、空态、错误态、动作反馈
- [ ] Green：接入已有组件和 hooks，形成最小可联调页面闭环
- [ ] Refactor：统一三态展示、表单反馈、详情页布局，减少页面层重复判断

## 交付物

- `frontend/src/app/(dashboard)/projects/[id]/kpi-config/page.tsx`：KPI 查看与编辑闭环
- `frontend/src/app/(dashboard)/datasets/page.tsx`：真实数据集列表页
- `frontend/src/app/(dashboard)/datasets/[id]/page.tsx`：数据集详情页
- `frontend/src/features/dataset/components/SceneLabelEditor.tsx`：标签编辑组件
- `frontend/src/app/(dashboard)/jobs/page.tsx`：任务列表 + 创建入口
- `frontend/src/app/(dashboard)/jobs/[id]/page.tsx`：任务详情 + 启动 + 产物展示
- `frontend/src/app/(dashboard)/exports/page.tsx`：导出创建 + 状态 + benchmark
- `frontend/src/app/(dashboard)/layout.tsx`：全局状态头部
- `frontend/__tests__/**`：页面与组件联调测试补充

## 验收标准

### 功能完整性
- [ ] KPI 配置可更新且立即可见
- [ ] 数据集详情可查看版本、冻结状态、覆盖率并编辑场景标签
- [ ] 任务可创建、可启动、可查看产物
- [ ] 候选实验可确认后创建下一轮任务
- [ ] 导出任务创建后可查看状态与部署基准
- [ ] 顶栏可展示后端健康状态

### 质量标准
- [ ] 页面和组件测试通过
- [ ] `pnpm test`、`pnpm typecheck`、`pnpm build`、`pnpm lint` 持续通过
- [ ] 所有关键页面具备 loading/empty/error 三态

### 与里程碑对齐
- [ ] 满足 M2/M3 的前端闭环：查看训练结果、查看 LLM 建议、确认创建下一轮任务
- [ ] 为 Phase 3 的 E2E 与演示流程提供可操作页面基础