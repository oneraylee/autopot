# 知识库 Phase 3 开发计划（在线检索 + 冲突消解 + Agent 集成）

## 项目概述

本阶段实现知识增强在线推理能力：ConflictResolutionService 完整版冲突消解、KnowledgeRetrievalService 混合检索、StrategyComposerService 最小知识上下文编排，并将知识上下文注入 AgentService，使 Planning Agent 与 Diagnosis Agent 的输出携带 `skill_refs` 和 `conflict_checked`。同时提供检索/消解/上下文组装 API 和 LLM Gateway 管理 API。

**架构设计原则**:
- 结构化规则优先 - 程序先做筛选和约束，LLM 后做组合和解释
- 最小上下文策略 - 只送 5-12 条技能摘要 + 冲突摘要 + 相似实验结论给 Agent
- 可审计可复现 - 每次规划记录 planning_snapshot，包含已选/已拒技能及 prompt 上下文

## 架构验收标准

### 分层设计
- [x] ConflictResolutionService 仅依赖 KnowledgeRepository + Common 契约
- [x] RetrievalService 依赖 KnowledgeRepository + ConflictResolutionService
- [x] StrategyComposerService 依赖 RetrievalService + ConflictResolutionService
- [x] AgentService 经由 StrategyComposer 获取 SkillContext，经由 LLMGateway 调用 LLM

### 核心组件
- [x] 在线冲突消解覆盖五类冲突（参数/结构/目标/版本/生命周期）
- [x] 检索支持结构过滤 → 规则召回 → 关键词检索 → 内部经验加权（Phase 1 简化公式）
- [x] StrategyComposer 输出 SkillContext 并控制 token 预算
- [x] Agent 输出 next_experiments 含 skill_refs + conflict_checked

### 统一接口
- [x] 检索/消解/上下文组装 API 响应结构与现有 API 一致
- [x] LLM Gateway 管理 API 可查询 Provider / 用量 / 调用日志

## 阶段输入输出

### 输入
- `docs/updates/20260323_知识库/1.知识库架构设计.md`（§ 8 在线检索流程、§ 9 冲突规则设计、§ 10 Agent 输入上下文设计、§ 11.3-11.5 接口定义、§ 12.4-12.5 服务层设计、§ 14 推荐输出格式扩展、§ 15 缓存与低 Token 策略）
- `docs/dev_step/3.业务逻辑层.md`（Step 3.6 AgentService 集成知识系统、Step 3.11、Step 3.12）
- `docs/dev_step/4.接口层.md`（Step 4.5 Proposal 校验增强 skill_refs、Step 4.7 检索/消解/上下文端点、Step 4.8 LLM Gateway 管理 API）
- `docs/init/2.系统架构.md`（§ 5 Agent 交互流程、§ 6.1 知识系统与 Agent 的关系）
- `docs/init/5.附录.md`（§ E NextExperiments 扩展格式 skill_refs / conflict_checked / resource_profile）
- Phase 1 输出（Gateway + 仓储）、Phase 2 输出（已入库技能卡片）

### 输出
- `src/services/conflict_resolution_service.py`（冲突消解服务）
- `src/services/knowledge_retrieval_service.py`（知识检索服务）
- `src/services/strategy_composer_service.py`（策略编排服务）
- `src/services/agent_service.py`（AgentService 增强 — 集成 SkillContext）
- `src/api/knowledge_routes.py`（新增检索/消解/上下文端点）
- `src/api/llm_gateway_routes.py`（Gateway 管理 API）
- `src/api/proposal_routes.py`（增强 skill_refs + 冲突校验）
- 对应测试文件

## 依赖关系

- 前置依赖：Phase 1（Gateway + 仓储）、Phase 2（已入库技能卡片 ≥ 30 条）
- 前置依赖：现有 AgentService（Phase 2 of 业务逻辑层 TODO）已可输出 next_experiments
- 并行关系：可与 Phase 4 的 Outcome Tracker 设计并行讨论
- 后置依赖：Phase 4 内部经验闭环需要本阶段检索排序框架作为基座

## 开发步骤与测试用例

| 子任务 | 输入 | 输出 | 依赖 | 测试用例 |
|---|---|---|---|---|
| P3-1 实现冲突规则 DSL 引擎 | 知识库设计 § 9.3 | 规则解析与匹配引擎 | Phase 1 仓储 | JSON DSL 规则解析正确；incompatible_with 匹配两个技能时标记 hard 冲突；severity 字段影响判定结果 |
| P3-2 实现在线冲突消解五类判定 | 知识库设计 § 9.1 | `ConflictResolutionService.resolve` | P3-1 | 结构冲突（同一位置不可合并）→ rejected；资源冲突（叠加超预算）→ rejected；目标冲突（KPI 权重判定）→ 按约束决策；版本冲突（framework_version 不满足）→ 直接过滤；生命周期冲突（condition 阶段约束）→ 按条件分流 |
| P3-3 实现冲突优先级排序 | 知识库设计 § 9.2 | 输出 accepted / rejected / warnings | P3-2 | 安全硬约束 > KPI 硬约束 > 资源硬约束 > 结构 hard > 版本 > soft tradeoff 排序正确 |
| P3-4 实现 validate_combination 资源预算校验 | 知识库设计 § 9.1.2 + § 13.4 | `validate_combination` | P3-2 | 多技能叠加后显存超过 gpu_mem_gb → 拒绝；接近边界时输出 warning；满足预算正常通过 |
| P3-5 实现 QuerySignature 生成 | 知识库设计 § 8.2 | `build_query_signature_from_dataset` / `_from_evidence` | Phase 1 契约 | 从 dataset_report 正确提取 task_type / small_object_ratio / weak_scenes 等字段；从 evidence_pack 正确提取 baseline 信息；缺失字段使用默认值 |
| P3-6 实现结构过滤 + 规则召回检索 | 知识库设计 § 8.3 阶段 1-2 | `RetrievalService.search` 基础版 | P3-5 + Phase 2 仓储 | task_type 过滤正确排除不匹配技能；maturity=deprecated 被过滤；required 条件命中的技能排在前列；avoid 条件命中的技能被剔除 |
| P3-7 实现关键词检索与简化排序 | 知识库设计 § 8.3 阶段 3 + § 8.4.1 | 检索结果排序 | P3-6 | 关键词命中模块名/参数名的技能获得更高分数；简化公式 score = rule_match × (default_priority + internal_prior) × status_filter 计算正确；top_k 截断正确 |
| P3-8 实现 StrategyComposer 上下文编排 | 知识库设计 § 10 + § 15.2 | `StrategyComposerService.compose_*_context` | P3-6 / P3-3 | 输出 SkillContext 包含 candidate_techniques / rejected_techniques / conflict_summary；候选数量控制在 5-12 条；token 预算超限时按裁剪顺序执行（长 rationale → 低优先级 → 低可信度） |
| P3-9 实现 PlanningSnapshot 记录 | 知识库设计 § 5.13 | `create_snapshot` | P3-8 | snapshot 写入成功；selected_techniques / rejected_techniques / prompt_context 完整；evidence_fingerprint 可用于复现 |
| P3-10 实现 RetrievalLog 记录 | 知识库设计 § 5.14 | retrieval_log 写入 | P3-7 | 每次检索写入 retrieval_log 成功；candidate_techniques / ranking_scores / filtered_out 完整 |
| P3-11 集成 AgentService + SkillContext | dev_step 3.6 + 知识库设计 § 13.2-13.3 | AgentService.analyze 增强版 | P3-8 + 现有 AgentService | 数据集规划阶段：dataset_evidence + skill_context 送入 Planning Agent → 输出 training_plan_candidates 含 skill_refs；训练后诊断阶段：evidence_pack + skill_context 送入 Diagnosis Agent → 输出 next_experiments 含 skill_refs + conflict_checked；skill_refs 引用可通过 knowledge_repository 验证有效 |
| P3-12 增强 Proposal 校验 | 知识库设计 § 13.4 + dev_step 4.5 | proposal_routes.py 增强 | P3-11 | validate_technique_refs 校验 skill_refs 引用有效；validate_technique_combination 调用 ConflictResolutionService 校验冲突；validate_resource_budget 校验资源预算；validate_version_compatibility 校验版本兼容 |
| P3-13 实现检索/消解/上下文 API | 知识库设计 § 11.3 | knowledge_routes.py 新增端点 | P3-7 / P3-3 / P3-8 | POST /knowledge/retrieval/search 返回候选技能列表；POST /knowledge/retrieval/resolve-conflicts 返回 accepted / rejected；POST /knowledge/retrieval/compose-context 返回 SkillContext + snapshot_id |
| P3-14 实现 LLM Gateway 管理 API | dev_step 4.8 | llm_gateway_routes.py | Phase 1 Gateway | GET /llm-gateway/providers 返回已注册 Provider 列表；GET /llm-gateway/usage 返回按时间范围聚合的用量报表；GET /llm-gateway/call-logs 支持分页 + 时间范围 + call_type 过滤 |

## TDD 执行清单

- [x] Red：在 `tests/services/test_conflict_resolution_service.py`、`tests/services/test_knowledge_retrieval_service.py`、`tests/services/test_strategy_composer_service.py`、`tests/api/test_retrieval_api.py` 先写失败用例
- [x] Green：实现最小可通过冲突消解、检索排序、上下文编排、Agent 集成逻辑
- [x] Refactor：冲突规则用 JSON DSL 描述避免硬编码、Phase 1 简化排序公式可配置、向量检索为可选插件（内部先验预留接口）

## 交付物

- `src/services/conflict_resolution_service.py`：冲突消解服务（五类冲突 + DSL 引擎）
- `src/services/knowledge_retrieval_service.py`：混合检索服务（结构过滤 + 规则召回 + 关键词 + 简化排序）
- `src/services/strategy_composer_service.py`：策略编排服务（最小上下文 + token 预算 + snapshot）
- `src/services/agent_service.py`：AgentService 增强（集成 SkillContext 注入）
- `src/api/knowledge_routes.py`：新增检索/消解/上下文组装端点
- `src/api/llm_gateway_routes.py`：Gateway 管理 API
- `src/api/proposal_routes.py`：增强 skill_refs / 冲突 / 资源 / 版本校验
- `tests/services/test_conflict_resolution_service.py`：冲突判定五大类 + DSL 引擎测试
- `tests/services/test_knowledge_retrieval_service.py`：检索过滤、排序、日志测试
- `tests/services/test_agent_service.py`：Agent + SkillContext 集成测试
- `tests/api/test_knowledge_api.py`：检索/消解/上下文端点测试
- `tests/api/test_llm_gateway_api.py`：Gateway 管理 API 测试

## 验收标准

### 功能完整性
- [x] 在线冲突消解覆盖参数/结构/目标/版本/生命周期五类冲突，输出 accepted / rejected / warnings
- [x] 混合检索支持结构过滤 → 规则召回 → 关键词检索 → 简化排序，输出候选技能排序列表
- [x] StrategyComposer 输出 SkillContext 控制在 5-12 条候选，token 预算超限时按裁剪顺序执行
- [x] AgentService 在数据集规划和训练后诊断两个阶段均可注入 SkillContext
- [x] Agent 输出 next_experiments 含 skill_refs + conflict_checked，引用可校验有效
- [x] Proposal 校验增加 skill_refs 有效性 + 技能组合冲突 + 资源预算 + 版本兼容四项检查
- [x] 每次规划记录 planning_snapshot，包含 evidence_fingerprint / selected / rejected / prompt_context

### 性能指标
- [x] 冲突 DSL 规则引擎单次评估过测，全链路读内存计算无外部依赖
- [x] Phase 3 测试全部通过，全链路读内存计算无外部依赖

### 质量标准
- [x] Phase 3 对应测试全部通过（298 passed，零回归）
- [x] 冲突规则 DSL 可在不修改代码的情况下扩展新规则
- [x] 检索排序公式参数可配置，为 Phase 4 引入向量检索预留接口

### 阶段里程碑
- [x] 达成"知识检索 + 冲突消解 + Agent 知识增强推理"的在线闭环
- [x] 数据集规划与训练后诊断两个阶段均可享受知识增强

### 前端配套
- 本阶段检索/消解 API 和 LLM Gateway 管理 API 就绪后，前端 Phase 7（`docs/TODO/5.前端层/7.TODO_PHASE7.md`）可启动 Gateway 设置页面开发
