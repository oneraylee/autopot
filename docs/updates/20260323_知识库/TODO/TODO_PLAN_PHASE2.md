# 知识库 Phase 2 开发计划（知识导入 + 技能卡片管理）

## 项目概述

本阶段实现知识沉淀能力：文档解析 Pipeline（Markdown / HTML / PDF / Notebook / Python 代码 → chunk）、经 LLM Gateway 半自动技能抽取、导入时冲突检测、技能卡片（Skill Card）CRUD 与发布管理。同时提供知识系统基础 API（Source / Document / Technique CRUD），实现首批高价值技能入库。

**架构设计原则**:
- 离线重加工 - 原始文档一次解析、一次 LLM 处理，后续在线查询不消费原始文档 token
- 半自动 + 人工审核 - LLM 生成候选技能，人工确认 / 修改 / 拒绝后方可发布
- 入库前冲突检测 - 新技能导入时必须完成冲突检测，不等到在线阶段

## 架构验收标准

### 分层设计
- [x] KnowledgeIngestionService 仅依赖 KnowledgeRepository + LLMGatewayService，不直连接口层
- [x] KnowledgeRegistryService 仅依赖 KnowledgeRepository + Common 契约

### 核心组件
- [x] 文档解析器支持 Markdown / HTML / PDF / Notebook / Python 代码五种格式
- [x] chunk 切分策略按章节/段落切分，token 数可控
- [x] 半自动技能抽取经 LLM Gateway 调用 LLM，输出候选 Skill 结构体
- [x] 导入时冲突检测识别参数冲突 / 结构冲突 / 目标冲突三类候选
- [x] 技能卡片 CRUD 与发布状态流转（draft → reviewed → verified）完整可用

### 统一接口
- [x] 知识系统 API（Source / Document / Technique）响应结构与现有 API 一致（ok / data / error）
- [x] URL 来源仅允许白名单域名（防 SSRF）

## 阶段输入输出

### 输入
- `docs/updates/20260323_知识库/1.知识库架构设计.md`（§ 7 知识导入流程、§ 7.4 导入时冲突检测、§ 7.5 互联网资料接入、§ 11.1-11.2 接口定义、§ 12.2-12.3 服务层设计）
- `docs/dev_step/3.业务逻辑层.md`（Step 3.9、Step 3.10）
- `docs/dev_step/4.接口层.md`（Step 4.7 知识系统 API 部分：Source / Document / Technique CRUD）
- `docs/init/5.附录.md`（§ J Skill Card 示例）
- Phase 1 输出（知识库仓储 + LLM Gateway + 领域类型）

### 输出
- `src/services/knowledge_ingestion_service.py`（知识导入服务）
- `src/services/knowledge_registry_service.py`（技能卡片管理服务）
- `src/api/knowledge_routes.py`（知识系统 API — Source / Document / Technique 部分）
- 对应测试文件

## 依赖关系

- 前置依赖：Phase 1（知识库仓储可 CRUD、LLMGateway 可调用 chat_completion）
- 并行关系：可与 Phase 3 的冲突消解规则设计并行讨论，但入库冲突检测需在本阶段实现
- 后置依赖：Phase 3 在线检索需要已入库的技能卡片作为检索目标

## 开发步骤与测试用例

| 子任务 | 输入 | 输出 | 依赖 | 测试用例 |
|---|---|---|---|---|
| P2-1 实现 Source 注册管理 | 知识库设计 § 5.1 + § 11.1 | `KnowledgeIngestionService.register_source` | Phase 1 仓储 | source 创建成功；重复 (source_type, uri) 拒绝；状态查询正确 |
| P2-2 实现文档导入与解析分发 | 知识库设计 § 7.2 | `import_document` + 解析器分发 | P2-1 | Markdown 文档导入并设置 parse_status=pending；content_hash 去重（重复文档拒绝）；非法 doc_type 返回错误 |
| P2-3 实现 chunk 切分引擎 | 知识库设计 § 4.2 + § 5.3 | `parse_document` → chunk 列表 | P2-2 | Markdown 按章节切分 chunk 数量正确；每个 chunk 的 section_path / chunk_index / token_count 字段完整；空文档产出零 chunk |
| P2-4 实现多格式解析器扩展 | 知识库设计 § 7.2 | HTML / PDF / Notebook / Python 解析器 | P2-3 | HTML 去标签后纯文本正确；PDF 基本文本提取可用；Notebook code+markdown cell 分别处理；Python 按函数/类切分 |
| P2-5 实现 URL 来源内容抓取 | 知识库设计 § 7.5 | `fetch_web_content(url)` | P2-2 | 白名单域名抓取成功；非白名单域名拒绝（防 SSRF）；抓取超时返回错误；HTML 内容正确转为 Markdown/纯文本 |
| P2-6 实现半自动技能抽取 | 知识库设计 § 7.2 步骤 4 | `extract_skills(document_id)` | P2-3 + Phase 1 Gateway | 调用 LLM Gateway 生成候选 Skill 结构体；输出包含 name / category / layer / condition / action / tradeoff；LLM 返回不合规时标记为抽取失败 |
| P2-7 实现归一化与去重合并 | 知识库设计 § 7.3 | 技能名称归一化 + 去重策略 | P2-6 | 同名技能检测到重复并建议合并；模块名/ 参数名归一化后一致；多条 evidence 可关联到同一 skill |
| P2-8 实现导入时冲突检测 | 知识库设计 § 7.4 | `detect_conflicts_on_import` | P2-6 + Phase 1 Gateway | 同一 action.target_path + 不同 value_json → 标记为参数冲突候选；同一 layer + 不同结构 → 标记为结构冲突候选；LLM 分析输出冲突类型判定写入 technique_relation；无冲突时正常入库 |
| P2-9 实现 KnowledgeRegistryService | 知识库设计 § 12.2 + dev_step 3.10 | 技能卡片 CRUD + 发布管理 | Phase 1 仓储 | create_skill 成功且 skill_code 唯一；update_skill 更新字段正确；publish_skill 状态从 draft→reviewed→verified 流转正确；非法流转被拒；list_skills 按 category / layer / task_type / maturity 筛选正确 |
| P2-10 实现 Skill 关系与模板管理 | 知识库设计 § 5.9 / § 5.11 | upsert_relation / CRUD template | P2-9 | 关系写入 technique_relation 正确；关系图查询可返回双向关系；template payload_json 存取完整 |
| P2-11 实现知识系统基础 API | 知识库设计 § 11.1-11.2 | `knowledge_routes.py` (Source/Document/Technique) | P2-1~P2-10 | POST /knowledge/sources 注册成功；POST /knowledge/documents/import 触发导入；POST /knowledge/techniques/extract 触发抽取；GET /knowledge/techniques 支持筛选参数；POST /knowledge/techniques/{id}/publish 发布成功；响应结构与现有 API 一致 |

## TDD 执行清单

- [x] Red：在 `tests/services/test_knowledge_ingestion_service.py`、`tests/services/test_knowledge_registry_service.py`、`tests/api/test_knowledge_api.py` 先写失败用例
- [x] Green：实现最小可通过导入、解析、抽取、注册、发布逻辑
- [x] Refactor：chunk 切分策略可配置、解析器可扩展、Taxonomy 枚举与知识库设计 § 4.3.1 保持一致

## 交付物

- `src/services/knowledge_ingestion_service.py`：知识导入全流程服务  
- `src/services/knowledge_registry_service.py`：技能卡片管理服务
- `src/api/knowledge_routes.py`：知识系统 API（Source / Document / Technique 部分）
- `tests/services/test_knowledge_ingestion_service.py`：导入、解析、抽取、冲突检测测试
- `tests/services/test_knowledge_registry_service.py`：技能 CRUD、发布、关系管理测试
- `tests/api/test_knowledge_api.py`：知识系统 API 测试（Source / Document / Technique 端点）

## 验收标准

### 功能完整性
- [x] 知识来源注册与文档导入全流程可执行（本地文件 + URL 白名单抓取）
- [x] 文档解析 → chunk 切分 → LLM 半自动抽取 → 候选技能产出链路打通
- [x] 导入时冲突检测可识别参数/结构/目标三类冲突候选并写入 technique_relation
- [x] 技能卡片 CRUD 完整，发布状态流转（draft → reviewed → verified）严格受控
- [x] 知识系统基础 API 可供前端或脚本调用

### 性能指标
- [ ] 单篇 Markdown 文档（< 50KB）解析 + 切分 < 2s
- [ ] 半自动技能抽取主要受 LLM 响应时间约束，平台侧额外开销 < 100ms

### 质量标准
- [ ] Phase 2 对应测试全部通过
- [x] URL 来源安全校验覆盖 SSRF 防护场景
- [x] contenthash 去重与 skill_code 唯一约束可稳定生效
- [x] chunk 切分策略可配置（按章节 / 按段落 / 按 token 数上限）

### 阶段里程碑
- [x] 达成"文档可导入 → 技能可抽取 → 技能卡片可管理"的知识沉淀闭环
- [ ] 首批 30-80 条高价值技能卡片可入库（从本地 YOLO 资料 + Ultralytics 官方文档抽取）

### 前端配套
- 本阶段后端 API 就绪后，前端 Phase 6（`docs/TODO/5.前端层/6.TODO_PHASE6.md`）可启动知识系统管理页面开发
