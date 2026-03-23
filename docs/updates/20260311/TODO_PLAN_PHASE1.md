# 变更修复 Phase 1 开发计划（后端接口补齐与契约统一）

## 项目概述

本阶段优先修复当前主流程最核心的后端缺口：补齐前端依赖的列表查询接口，统一 Proposal 校验契约，并对齐导出与产物查询响应结构，使前后端能在同一协议下完成联调。

**架构设计原则**:
- 契约先行 - 先统一请求/响应结构，再补页面接线，避免前端继续围绕错误协议开发
- 最小破坏 - 复用现有 repository/service 能力，在接口层补齐缺口，不重写已通过测试的核心逻辑
- 可联调验收 - 每个接口修复都必须能被 FastAPI HTTP 测试和前端 API client 同时消费

## 架构验收标准

### 接口完备性
- [ ] 提供前端读页面所需的 `GET /jobs` 与 `GET /datasets` 接口
- [ ] Proposal 校验接口的输入语义与前端页面、系统架构文档保持一致
- [ ] 导出状态与部署基准接口返回结构与前端 API client 类型一致

### 契约一致性
- [ ] `next_experiments` 结构统一为附录定义的 `baseline_job_id + candidates`
- [ ] 产物查询接口、Proposal 校验接口、导出接口均遵循统一 `{ok, data/error}` 响应格式
- [ ] 参数错误、资源错误、缺失资源错误映射到稳定错误码

### 可测性
- [ ] API 单元测试覆盖新增列表接口与契约修复路径
- [ ] Web 层 HTTP 测试覆盖真实请求/响应流
- [ ] 前端 API client 现有测试无需绕过或特判错误结构

## 阶段输入输出

### 输入
- `docs/changes/20260311/未实现功能清单.md`
- `docs/init/1.产品PRD.md`
- `docs/init/2.系统架构.md`
- `docs/init/3.模块设计文档.md`
- `docs/init/5.附录.md`
- 当前接口实现：`src/web/routes.py`、`src/api/*.py`
- 当前前端 API client：`frontend/src/lib/api/*.ts`

### 输出
- `src/web/routes.py`
- `src/api/job_routes.py`
- `src/api/dataset_routes.py`
- `src/api/proposal_routes.py`
- `src/api/export_routes.py`
- 必要时补充 `src/api/analysis_routes.py`
- `tests/api/test_job_api.py`
- `tests/api/test_dataset_api.py`
- `tests/api/test_proposal_workflow_api.py`
- `tests/api/test_export_api.py`
- `tests/web/test_fastapi_app.py`

## 依赖关系

- 前置依赖：现有 repository/service 已能提供任务、数据集、导出、Agent 基础能力
- 并行关系：Phase 2 可先准备前端接线代码，但必须等待本阶段接口契约稳定后再联调
- 后置依赖：Phase 2 的前端页面闭环、Phase 3 的 E2E 回归都依赖本阶段接口口径固定

## 开发步骤与测试用例

| 子任务 | 输入 | 输出 | 依赖 | 测试用例 |
|---|---|---|---|---|
| P1-1 梳理列表页接口契约 | 未实现清单 + 前端 hooks | `/jobs`、`/datasets` 响应字段清单 | 前端 `useJobList`、`useDatasetList` | 列表为空时返回空数组；字段满足前端表格展示；不存在额外包裹层 |
| P1-2 实现任务列表接口 | JobRepository 当前模型 | `GET /jobs` 路由与 job_routes 列表能力 | P1-1 | 返回 `job_id/task_type/status/created_at/updated_at`；多任务排序稳定；无任务时返回空集合 |
| P1-3 实现数据集列表接口 | DatasetRepository 当前模型 | `GET /datasets` 路由与 dataset_routes 列表能力 | P1-1 | 返回 `dataset_id/name/latest_version/created_at`；无数据时返回空集合 |
| P1-4 统一 Proposal 校验输入契约 | PRD + 系统架构 + 附录 E | `validate_proposals` 请求体规范 | 当前 ProposalRoutes/AgentService | 以 `job_id/run_id` 查询产物并校验；缺 run_id 拒绝；缺 next_experiments 产物返回 NOT_FOUND 或 DATA_INVALID |
| P1-5 对齐 `next_experiments` 数据结构 | 附录 E `baseline_job_id + candidates` | Proposal/Analysis 统一 payload 结构 | P1-4 | 旧结构 `experiments` 不再泄漏到 HTTP 层；候选实验包含 `name/changes/expected/evidence_refs` |
| P1-6 修正导出状态与 benchmark 返回结构 | 前端 `export.ts` 类型 | `GET /exports/{id}` 与 `GET /exports/{id}/deploy-benchmark` 返回契约 | ExportRoutes | 状态接口返回 `export_id/job_id/run_id/backend/status/created_at`；benchmark 返回前端期望字段；错误路径仍走统一 error |
| P1-7 补齐 HTTP 回归测试 | FastAPI app 与 API route 测试 | 扩展测试套件 | P1-2~P1-6 | 浏览器联调路径可请求 Jobs/Datasets；Proposal validate 使用真实 job_id/run_id 通过；导出 benchmark 字段对齐前端类型 |

## TDD 执行清单

- [ ] Red：先补失败测试，覆盖列表接口缺失、Proposal 契约错位、导出返回结构错位
- [ ] Green：以最小改动补齐 route 层和 adapter 层能力
- [ ] Refactor：抽取统一列表序列化与 Proposal/Export 响应格式化逻辑，避免后续 Phase 2 再做兼容代码

## 交付物

- `src/web/routes.py`：新增并对齐 HTTP 路由
- `src/api/job_routes.py`：任务列表查询能力
- `src/api/dataset_routes.py`：数据集列表查询能力
- `src/api/proposal_routes.py`：Proposal 校验契约统一
- `src/api/export_routes.py`：导出状态与 benchmark 契约对齐
- `tests/api/*.py`：新增失败/成功路径测试
- `tests/web/test_fastapi_app.py`：补齐 HTTP 联调回归

## 验收标准

### 功能完整性
- [ ] 前端 Jobs/Datasets 页面依赖的列表接口全部可用
- [ ] Proposal 校验接口可以基于 `job_id + run_id` 工作
- [ ] `next_experiments` 输出结构与附录 E 保持一致
- [ ] 导出状态与部署基准接口可被前端直接消费，无额外兼容层

### 质量标准
- [ ] API 单元测试全部通过
- [ ] FastAPI HTTP 测试覆盖新增读接口与修复后的写接口
- [ ] 错误码语义清晰：`NOT_FOUND`、`VALIDATION_ERROR`、`DATA_INVALID`、`EXPORT_FAILED`

### 与里程碑对齐
- [ ] 满足 M1/M2 的接口前置条件：前端可查看、可校验、可查询导出结果
- [ ] 为 Phase 2 页面接线提供稳定 API 基线