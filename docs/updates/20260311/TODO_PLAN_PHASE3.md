# 变更修复 Phase 3 开发计划（审计补强、性能验证与回归验收）

## 项目概述

本阶段处理当前剩余的非功能和交付收尾问题：补齐 LLM/评估审计记录、验证场景覆盖率性能基线、补充 docstring 与回归测试，并同步更新前端/变更文档，确保本轮修复不是“能跑一次”，而是可回归、可审计、可交付。

**架构设计原则**:
- 审计优先 - 建议生成、失败日志、关键动作都必须可按 `job_id/run_id/timestamp` 追溯
- 证据化验收 - 性能与质量标准必须有基准测试、E2E 或文档记录支撑
- 文档跟代码同步 - 修复完成后同步清理已过期的 TODO 状态，避免再次出现文档失真

## 架构验收标准

### 审计与追溯
- [ ] Eval 失败日志与 Agent 建议生成记录可定位到 `job_id`、`run_id`、时间戳
- [ ] Proposal 创建链路与 LLM 建议产出链路具备统一审计字段
- [ ] 审计信息可被 API、服务测试或文档清楚验证

### 性能与稳定性
- [ ] 场景覆盖率查询具备明确性能基线与基准测试结果
- [ ] 导出状态轮询、产物查询、Proposal 创建等关键路径具备回归测试
- [ ] E2E 冒烟流程可覆盖主链路修复点

### 可维护性
- [ ] repository/service public 方法补齐必要 docstring
- [ ] 变更文档与实际实现状态同步
- [ ] README 或变更说明可指导验证本轮修复效果

## 阶段输入输出

### 输入
- `docs/changes/20260311/未实现功能清单.md`
- `docs/changes/20260311/TODO_PLAN_PHASE1.md`
- `docs/changes/20260311/TODO_PLAN_PHASE2.md`
- `docs/init/1.产品PRD.md`
- `docs/init/2.系统架构.md`
- `docs/init/3.模块设计文档.md`
- `docs/init/5.附录.md`
- 当前测试与 README 文档

### 输出
- `src/services/eval_service.py`
- `src/services/agent_service.py`
- 必要时 `src/repositories/job_repository.py` 或新增审计存储模块
- `src/repositories/scene_label_repository.py`
- `tests/services/test_eval_service.py`
- `tests/services/test_agent_service.py`
- `tests/repositories/test_scene_label_repository.py`
- `frontend/tests/e2e/*.spec.ts`
- `frontend/README.md`
- 必要时同步更新 `docs/changes/20260311/未实现功能清单.md`

## 依赖关系

- 前置依赖：Phase 1 接口稳定、Phase 2 页面接线完成
- 并行关系：docstring 与 README 可并行处理，但审计字段和性能基线应在 E2E 回归前完成
- 结束条件：本阶段完成后，本轮缺口可从“部分实现”转为“已实现/已验证”

## 开发步骤与测试用例

| 子任务 | 输入 | 输出 | 依赖 | 测试用例 |
|---|---|---|---|---|
| P3-1 设计评估与建议审计记录结构 | PRD 审计要求 + 系统架构 | 审计字段清单与存储位置 | JobRepository / EvalService / AgentService | 每次 eval 失败可追溯 stdout/stderr 路径与时间；每次 Agent 生成可追溯 job_id/run_id/created_at |
| P3-2 实现 Eval 失败日志追溯增强 | 现有日志落盘逻辑 | 可检索的 eval 审计记录 | P3-1 | job_id、run_id、stdout_path、stderr_path、created_at 完整存在 |
| P3-3 实现 Agent 建议生成审计记录 | 现有 AgentService | LLM 生成记录持久化/可查询结构 | P3-1 | 成功生成与失败生成都记录；可关联 baseline_job_id 和产物路径 |
| P3-4 补充 Proposal/LLM 审计测试 | API 与 service 现有测试 | 扩展服务测试 | P3-2, P3-3 | 审计字段完整；失败原因稳定；时间戳存在 |
| P3-5 建立场景覆盖率性能基线 | TODO 未实现清单 + 数据层实现 | 基准测试与目标数据规模说明 | SceneLabelRepository | 在目标规模数据下执行时间有记录；回归不明显退化 |
| P3-6 优化场景覆盖率实现（如需要） | P3-5 基准结果 | 更稳定的聚合实现或性能说明 | P3-5 | 单维度与组合维度结果不变；基准达到目标 |
| P3-7 补齐 public 方法 docstring | repository/service 模块 | 更清晰的接口说明 | 现有源码 | 关键 public 方法说明输入、返回、异常语义 |
| P3-8 更新 E2E 冒烟覆盖 | Phase 2 页面闭环 | Playwright 回归用例 | 前端页面与后端 API 均稳定 | 数据集查看 → 任务创建/启动 → 产物查看 → Proposal 创建 → 导出查看 主链路通过 |
| P3-9 同步 README 与变更文档 | 本轮实现结果 | 更新验证说明 | P3-1~P3-8 | 非开发者可按文档完成验证；未实现项文档状态收敛 |

## TDD 执行清单

- [ ] Red：补充审计、性能和 E2E 失败场景测试
- [ ] Green：以最小设计增加审计记录与基准能力
- [ ] Refactor：整理日志/审计结构命名，统一文档和测试夹具，减少二次维护成本

## 交付物

- `src/services/eval_service.py`：增强 eval 审计与失败日志索引
- `src/services/agent_service.py`：增强建议生成审计记录
- `src/repositories/scene_label_repository.py`：性能基线下的稳定实现或基准说明
- `tests/services/test_eval_service.py`：审计记录测试
- `tests/services/test_agent_service.py`：建议生成审计测试
- `tests/repositories/test_scene_label_repository.py`：性能与结果一致性测试
- `frontend/tests/e2e/*.spec.ts`：主链路回归
- `frontend/README.md`：联调与验证步骤更新
- `docs/changes/20260311/未实现功能清单.md`：状态同步（如有必要）

## 验收标准

### 功能完整性
- [ ] Eval 失败与 LLM 建议生成具备可检索审计记录
- [ ] 场景覆盖率查询具备明确性能基线
- [ ] 主链路 E2E 冒烟覆盖本轮修复点

### 质量标准
- [ ] 服务测试、仓储测试、前端 E2E 测试全部通过
- [ ] 关键 public 方法补齐 docstring
- [ ] README 与变更文档反映真实状态，无明显过期信息

### 与里程碑对齐
- [ ] 满足“可回归、可审计、可交付”的本轮修复完成标准
- [ ] 为后续继续开发提供稳定基线，而不是临时兼容实现