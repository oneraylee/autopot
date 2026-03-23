# 知识库 Phase 4 开发计划（内部经验闭环 + Proposal 增强 + 端到端验收）

## 项目概述

本阶段完成知识系统最后一环：SkillOutcomeTrackerService 实现内部经验闭环（训练完成后自动回写技能效果，反哺检索排序），完善 Proposal 校验流程，补齐 Outcome 回写 API 和知识系统相关的训练流程耦合接口，通过端到端集成测试验证"知识导入 → 检索 → Agent 增强 → 实验 → Outcome 回写 → 再次检索排序提升"的完整闭环。

**架构设计原则**:
- 经验闭环 - 内部实验结果作为高优先级证据，反哺后续检索排序
- 审计完整 - planning_snapshot + retrieval_log + skill_outcome 三表联合支撑完整审计链
- 渐进增强 - Phase 4 完成后即可投入生产使用，Phase 5+ 向量检索/自动化作为增量优化

## 架构验收标准

### 分层设计
- [ ] SkillOutcomeTrackerService 依赖 KnowledgeRepository + JobRepository + EvalService 输出
- [ ] Outcome 回写不影响主训练流程（异步或后置执行）

### 核心组件
- [ ] SkillOutcomeTrackerService 支持 win/lose/neutral/unstable 四种 verdict 判定
- [ ] 内部经验加权可被 RetrievalService 在检索排序中使用
- [ ] Proposal 校验四项增强（skill_refs / 冲突 / 资源 / 版本）全部落地
- [ ] 知识系统端到端集成测试覆盖完整闭环

### 统一接口
- [ ] Outcome 回写 API 与现有 API 响应结构一致
- [ ] 训练流程耦合接口（knowledge-plan / knowledge-diagnosis）可由现有路由调用

## 阶段输入输出

### 输入
- `docs/updates/20260323_知识库/1.知识库架构设计.md`（§ 5.12 technique_outcome、§ 11.5 Outcome 回写接口、§ 11.4 训练流程耦合接口、§ 12.6 SkillOutcomeService、§ 13 与现有平台集成点、§ 16 审计与治理）
- `docs/dev_step/3.业务逻辑层.md`（Step 3.13 SkillOutcomeTrackerService）
- `docs/dev_step/4.接口层.md`（Step 4.5 Proposal 增强、Step 4.7 Outcome 回写端点）
- Phase 1-3 输出（Gateway + 仓储 + 导入 + 检索 + 冲突消解 + Agent 集成）

### 输出
- `src/services/skill_outcome_tracker_service.py`（技能效果追踪服务）
- `src/api/knowledge_routes.py`（新增 Outcome 回写 + 训练流程耦合端点）
- 知识系统端到端集成测试
- 对应测试文件

## 依赖关系

- 前置依赖：Phase 1-3（Gateway + 仓储 + 导入 + 检索 + Agent 集成全部就绪）
- 前置依赖：现有业务层已可输出训练评估结果（EvalReport + EvidencePack）
- 结束条件：通过端到端集成测试与审计链验证后，知识系统可投入生产使用

## 开发步骤与测试用例

| 子任务 | 输入 | 输出 | 依赖 | 测试用例 |
|---|---|---|---|---|
| P4-1 实现 verdict 判定逻辑 | 知识库设计 § 5.12 + dev_step 3.13 | verdict 计算器 | Phase 1 仓储 | baseline 与 candidate 的 business_kpi 差异 > 阈值 → win；差异 < 负阈值 → lose；差异在容差范围 → neutral；多次实验结果不一致 → unstable；阈值可配置 |
| P4-2 实现 Outcome 回写 | 知识库设计 § 12.6 | `SkillOutcomeTrackerService.record_outcome` | P4-1 | 单条技能 outcome 写入 technique_outcome 成功；多条技能批量回写正确；scenario_signature / result_summary 字段完整；重复回写（同 baseline + candidate）幂等处理 |
| P4-3 实现 Outcome 查询与内部先验计算 | 知识库设计 § 12.6 | `query_similar_outcomes` / `compute_internal_prior` | P4-2 | 按场景签名查询历史 outcome 正确（task_type + dominant_scenes 匹配）；compute_internal_prior 返回 win_rate 正确；无历史 outcome 时返回默认先验 |
| P4-4 集成内部经验加权到检索排序 | 知识库设计 § 8.3 阶段 5 + § 8.4.1 | RetrievalService 排序增强 | P4-3 + Phase 3 检索 | 有 win 记录的技能排序分数提升；有 lose 记录的技能排序分数降低；unstable 技能不调整分数；简化公式中 S_internal 项正确生效 |
| P4-5 实现训练完成后自动 Outcome 回写 | dev_step 3.13 | 训练后钩子（post-eval hook） | P4-2 + 现有 EvalService | 训练完成 → 评估完成后，自动提取 baseline_job_id + candidate_job_id + skill_refs → 计算 verdict → 回写 outcome；无 skill_refs 的任务跳过；回写失败不影响主流程 |
| P4-6 实现 Outcome 回写 API | 知识库设计 § 11.5 | POST /knowledge/outcomes | P4-2 | 请求包含 technique_ids / baseline_job_id / candidate_job_id / result_summary / verdict → 回写成功；缺必填字段拒绝；technique_id 不存在返回错误 |
| P4-7 实现训练流程耦合接口 | 知识库设计 § 11.4 | knowledge-plan / knowledge-diagnosis 端点 | Phase 3 StrategyComposer | POST /datasets/versions/{id}/knowledge-plan 触发数据集规划阶段知识上下文生成；POST /jobs/{id}/knowledge-diagnosis 触发训练后诊断阶段知识上下文生成；POST /proposals/validate-with-knowledge 增强校验通过 |
| P4-8 端到端集成测试：知识导入链路 | Phase 2 输出 | 导入链路集成用例 | Phase 1-2 | 注册来源 → 导入文档 → chunk 切分 → 技能抽取 → 冲突检测 → 审核发布 → 技能可查询 |
| P4-9 端到端集成测试：在线推理链路 | Phase 3 输出 | 在线推理集成用例 | Phase 1-3 | 构建 query_signature → 检索候选 → 冲突消解 → 上下文编排 → Agent 输出含 skill_refs → Proposal 校验通过 |
| P4-10 端到端集成测试：经验闭环 | Phase 4 输出 | 经验闭环集成用例 | Phase 1-4 | 技能入库 → 检索排序 → Agent 推荐含该技能 → 训练完成 → Outcome 回写 win → 再次检索排序时该技能分数提升 |
| P4-11 审计链验证 | 知识库设计 § 16 | 审计完整性测试 | Phase 1-4 | planning_snapshot 可回溯到具体规划上下文；retrieval_log 可回溯检索过程；llm_call_log 可追踪所有 LLM 调用成本；skill_outcome 可追溯技能在实验中的表现 |

## TDD 执行清单

- [ ] Red：在 `tests/services/test_skill_outcome_tracker_service.py`、`tests/api/test_knowledge_api.py`（Outcome 端点）、`tests/integration/test_knowledge_e2e.py` 先写失败用例
- [ ] Green：实现最小可通过 Outcome 计算、回写、内部经验加权、训练流程耦合逻辑
- [ ] Refactor：verdict 判定逻辑可配置阈值、Outcome 回写异步化、审计字段一致性

## 交付物

- `src/services/skill_outcome_tracker_service.py`：技能效果追踪服务（verdict 判定 + Outcome 回写 + 内部先验计算）
- `src/api/knowledge_routes.py`：新增 Outcome 回写 + 训练流程耦合端点
- `tests/services/test_skill_outcome_tracker_service.py`：verdict 判定、Outcome 回写、内部先验测试
- `tests/integration/test_knowledge_e2e.py`：知识系统端到端集成测试（导入链路 + 在线推理 + 经验闭环 + 审计链）
- 审计与治理验证报告

## 验收标准

### 功能完整性
- [ ] SkillOutcomeTrackerService 支持 win/lose/neutral/unstable 四种 verdict，阈值可配置
- [ ] 内部经验加权可在检索排序中生效（win 提升分数、lose 降低分数）
- [ ] 训练完成→评估完成后自动 Outcome 回写，不影响主训练流程
- [ ] Outcome 回写 API 与训练流程耦合接口可供前端或脚本调用
- [ ] Proposal 校验增强四项（skill_refs / 冲突 / 资源 / 版本）已落地并可验证

### 审计完整性
- [ ] planning_snapshot 记录每次规划的 selected / rejected / prompt_context
- [ ] retrieval_log 记录每次检索的 candidates / scores / filtered_out
- [ ] llm_call_log 记录所有 LLM 调用的 provider / model / tokens / cost / latency
- [ ] skill_outcome 记录每次实验中技能的 verdict / result_summary / scenario_signature

### 质量标准
- [ ] Phase 4 对应测试全部通过
- [ ] 端到端集成测试覆盖三条关键链路（导入 / 在线推理 / 经验闭环）
- [ ] 知识系统与现有训练流程集成无回归

### 阶段里程碑
- [ ] 达成"知识导入 → 在线检索 → Agent 增强 → 训练 → Outcome 回写 → 检索优化"的完整闭环
- [ ] 知识系统可投入生产使用，后续 Phase 5+（向量检索 / 自动化 / 持续学习）作为增量优化

### 前端配套
- 前端 Phase 6（`docs/TODO/5.前端层/6.TODO_PHASE6.md`）：知识系统管理页面（知识源注册/文档导入/技能卡片/审核仲裁）
- 前端 Phase 7（`docs/TODO/5.前端层/7.TODO_PHASE7.md`）：LLM Gateway 设置页面 + 知识系统 E2E 测试

---

## 后续展望（Phase 5+，不在本阶段交付范围）

以下能力作为增量优化，在 Phase 4 完成后按需启动：

### Phase 5：向量检索与自动化
- 引入 Embedding Provider（可通过 LLM Gateway 配置云端或本地模型）
- pgvector 向量索引 + 混合检索完整排序公式 $score = \alpha S_{structure} + \beta S_{rule} + \gamma S_{bm25} + \delta S_{vector} + \epsilon S_{internal} - \lambda P_{risk}$
- 半自动从实验结果中发现新技能候选
- URL 定期同步（官方文档更新检测）

### Phase 6：持续学习
- 自动发现技能重复和关系变化
- 基于 outcome 统计自动调整 default_priority
- 知识库健康度报告
- 知识库维护仪表盘
