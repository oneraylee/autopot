# 知识库 Phase 1 开发计划（LLM Gateway + 知识基础设施）

## 项目概述

本阶段搭建知识库系统的底层基础设施：在 Common 层新增知识系统与 Gateway 领域类型和契约对象，在数据层落地知识库表群仓储与 LLM 调用日志仓储，在业务层实现 LLM Gateway 统一网关服务。Gateway 同时接管现有 Agent 调用，实现 Provider 可切换、模型可路由、成本可追踪。

**架构设计原则**:
- 自下而上构建 - Common → 数据层 → 业务层，上层仅依赖下层
- Gateway 统一收口 - 所有 LLM 调用（Agent 推理、技能抽取、冲突分析、Embedding）必须经过 Gateway
- 离线先行 - 先建表和仓储能力，再建在线推理能力

## 架构验收标准

### 分层设计
- [x] Common 层新增枚举/DTO 不依赖业务层或数据层
- [x] 知识库仓储仅依赖 Common 层领域类型，不直连业务逻辑
- [x] LLMGatewayService 仅依赖仓储（LLMCallLogRepository）和 Common 契约

### 核心组件
- [x] 知识系统领域枚举（SkillCategory / SkillLayer / SkillMaturity / LLMCallType / RelationType）完整可用
- [x] 知识系统契约对象（SkillCardSummary / QuerySignature / ConflictReport / SkillContext / LLMCallRecord / SkillRef）完整可用
- [x] 知识库表群仓储（14 张表）CRUD 能力完整
- [x] LLM 调用日志仓储可写入、按多维度查询
- [x] LLMGatewayService 支持 Provider 注册、Model 路由、成本追踪、限流重试

### 统一接口
- [x] LLMProvider / EmbeddingProvider Protocol 可独立 Mock 测试
- [x] 所有仓储返回统一领域模型，错误码与 Common 对齐

## 阶段输入输出

### 输入
- `docs/updates/20260323_知识库/1.知识库架构设计.md`（§ 4 知识对象模型、§ 5 数据库表结构、§ 6 实体关系、§ 12 服务层设计、§ 17 Phase 1）
- `docs/dev_step/1.Common库.md`（Step 1.5、Step 1.6）
- `docs/dev_step/2.数据层.md`（Step 2.6、Step 2.7）
- `docs/dev_step/3.业务逻辑层.md`（Step 3.8）
- `docs/init/2.系统架构.md`（§ 5 LLM Gateway 设计要点）
- `docs/init/3.模块设计文档.md`（§ 9 LLM Gateway）
- `docs/init/5.附录.md`（§ G 错误码、§ I Gateway 配置示例、§ J Skill Card 示例）

### 输出
- `src/common/domain_types.py`（新增知识系统与 Gateway 枚举）
- `src/common/contracts.py`（新增知识系统契约 DTO）
- `src/common/schema_validators.py`（新增 SkillCard / QuerySignature 校验）
- `src/repositories/knowledge_repository.py`（知识库表群仓储）
- `src/repositories/llm_call_log_repository.py`（LLM 调用日志仓储）
- `src/services/llm_gateway_service.py`（LLM Gateway 服务）
- 对应测试文件

## 依赖关系

- 前置依赖：`docs/TODO/1.Common库/1.TODO_PHASE1.md`（基础领域类型与错误码）、`docs/TODO/1.Common库/4.TODO_PHASE4.md`（跨服务 DTO）
- 并行关系：与现有业务层 Phase 1-3 无冲突，可并行开发
- 后置依赖：Phase 2 知识导入与技能管理依赖本阶段仓储与 Gateway 能力

## 开发步骤与测试用例

| 子任务 | 输入 | 输出 | 依赖 | 测试用例 |
|---|---|---|---|---|
| P1-1 新增知识系统领域枚举 | 知识库设计 § 4.3.1 + 附录 § G | `domain_types.py` 新增枚举 | Common Phase 1 | SkillCategory/SkillLayer/SkillMaturity/LLMCallType/RelationType 枚举值完整；新增错误码 LLM_GATEWAY_ERROR / KNOWLEDGE_IMPORT_FAILED 可用 |
| P1-2 新增知识系统契约对象 | 知识库设计 § 4.3.2 / § 8.2 / § 9.4 / § 10 | `contracts.py` 新增 DTO | P1-1 | SkillCardSummary / QuerySignature / ConflictReport / SkillContext / LLMCallRecord / SkillRef 构造与序列化正确；必填字段缺失时校验失败 |
| P1-3 新增 SkillCard / QuerySignature Schema 校验 | 附录 § J + 知识库设计 § 8.2 | `schema_validators.py` 新增校验 | P1-2 | 合法 SkillCard JSON 通过校验；缺失 skill_code / category 被拦截；QuerySignature task_type 非法时拒绝 |
| P1-4 实现知识库表群仓储 | 知识库设计 § 5 全部表结构 | `knowledge_repository.py` | P1-1 | KnowledgeSource CRUD 正确（注册/查询/去重）；KnowledgeDocument 导入与状态查询；KnowledgeChunk 分块存储与按 document 查询；Skill CRUD 与 skill_code 唯一约束；TechniqueVersion / Condition / Action / Tradeoff / Relation / Evidence / Template / Outcome 关联读写；PlanningSnapshot 记录与查询；RetrievalLog 写入 |
| P1-5 实现 LLM 调用日志仓储 | 知识库设计 § 5.15 | `llm_call_log_repository.py` | P1-1 | 写入 LLMCallLog 成功；按 call_type + 时间范围查询正确；按 provider + model 聚合统计正确；batch 查询用于 cost dashboard |
| P1-6 实现 LLMProvider / EmbeddingProvider Protocol | 知识库设计 § 12.1 + 系统架构 § 5.1 | Provider Protocol 定义 | P1-2 | Protocol 可被 Mock 实现；chat / models / embed 接口签名稳定 |
| P1-7 实现 LLMGatewayService 核心 | 知识库设计 § 12.1 + 附录 § I | `llm_gateway_service.py` | P1-5 / P1-6 | chat_completion 经 model_routing 路由到正确 Provider；embed 调用 EmbeddingProvider 正确；调用完成后自动写入 llm_call_log；无效 task_type 返回 LLM_GATEWAY_ERROR |
| P1-8 实现 Provider 注册与限流重试 | 系统架构 § 5.1 | Gateway 注册/限流模块 | P1-7 | list_providers 返回已注册 Provider；RPM 超限时触发限流等待；Provider 暂时不可用时重试后成功；API Key 从环境变量安全读取 |
| P1-9 实现 Cost Tracker 与用量报表 | 知识库设计 § 5.15 | get_usage_report | P1-7 / P1-5 | 按时间范围聚合 token / 成本正确；按 call_type 分组正确；空时间范围返回零值 |

## TDD 执行清单

- [x] Red：在 `tests/common/test_knowledge_domain_types.py`、`tests/common/test_knowledge_contracts.py`、`tests/repositories/test_knowledge_repository.py`、`tests/repositories/test_llm_call_log_repository.py`、`tests/services/test_llm_gateway_service.py` 先写失败用例
- [x] Green：实现最小可通过枚举、DTO、仓储、Gateway 逻辑
- [x] Refactor：确保枚举値与知识库设计文档一致、Provider Protocol 可独立测试、Mock Provider 覆盖全场景

## 交付物

- `src/common/domain_types.py`（新增知识系统枚举 + 错误码）
- `src/common/contracts.py`（新增知识系统契约 DTO）
- `src/common/schema_validators.py`（新增 SkillCard / QuerySignature 校验器）
- `src/repositories/knowledge_repository.py`（知识库 14 张表仓储）
- `src/repositories/llm_call_log_repository.py`（LLM 调用日志仓储）
- `src/services/llm_gateway_service.py`（LLM Gateway 统一网关服务）
- `tests/common/test_knowledge_domain_types.py`
- `tests/common/test_knowledge_contracts.py`
- `tests/repositories/test_knowledge_repository.py`
- `tests/repositories/test_llm_call_log_repository.py`
- `tests/services/test_llm_gateway_service.py`

## 验收标准

### 功能完整性
- [x] 知识系统枚举値覆盖知识库设计 § 4.3.1 分类体系
- [x] 知识库表群仓储支持完整 CRUD（14 张表），`content_hash` 去重与 `skill_code` 唯一约束可生效
- [x] LLMCallLog 可写入并按 call_type / provider / 时间范围多维查询
- [x] LLMGatewayService 可通过 Mock Provider 独立测试：Provider 注册、Model 路由、限流、重试、成本记录全覆盖
- [ ] 现有 AgentService 可迁移至经由 Gateway 调用 LLM（兼容路径）

### 性能指标
- [x] Gateway 单次调用额外开销（路由 + 日志写入）< 10ms
- [x] 知识库仓储基础查询响应 < 50ms

### 质量标准
- [x] Phase 1 对应测试全部通过（共 51 个测试）
- [x] Provider Protocol Mock 覆盖正常返回、异常、超时三类场景
- [x] 知识库仓储的唯一约束与索引与知识库设计 § 5 对齐

### 阶段里程碑
- [x] 达成“LLM Gateway 统一收口 + 知识库基础表与仓储可用”的底层就绪状态
