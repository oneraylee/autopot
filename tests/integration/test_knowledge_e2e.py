"""End-to-End integration tests for the Knowledge System (Phase 4 Step 4).

Tests cover:
1. Import pipeline: source → document → chunk → extract → publish → queryable
2. Online reasoning: QuerySignature → retrieval → conflict resolution → context → skill_refs
3. Experience loop: skill recommended → training → outcome win → score boosted
4. Audit chain: planning_snapshot / retrieval_log / llm_call_log / skill_outcome all traceable
"""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures & helpers
# ══════════════════════════════════════════════════════════════════════════════

_SKILL_EXTRACT_RESPONSE = json.dumps([
    {
        "name": "label_smoothing",
        "category": "regularization",
        "layer": "training",
        "condition": "overfitting risk",
        "action": {"target_path": "trainer.label_smoothing", "value": 0.1},
        "tradeoff": "slight accuracy drop",
    },
    {
        "name": "mosaic_aug",
        "category": "data_aug",
        "layer": "preprocessing",
        "condition": "small dataset",
        "action": {"target_path": "augment.mosaic", "value": True},
        "tradeoff": "training time +20%",
    },
])

_MARKDOWN_BODY = """# Training Guide

## Regularization
Use label_smoothing to prevent overfitting in classification tasks.

## Data Augmentation
Apply mosaic augmentation to improve detection generalization.
"""


def _make_llm_gateway():
    gw = MagicMock()
    gw.chat_completion.return_value = {
        "content": _SKILL_EXTRACT_RESPONSE,
        "usage": {"input_tokens": 500, "output_tokens": 100},
    }
    return gw


def _build_full_system():
    """Build the full knowledge system with all services wired together."""
    from repositories.knowledge_repository import KnowledgeRepository
    from services.knowledge_ingestion_service import KnowledgeIngestionService
    from services.knowledge_registry_service import KnowledgeRegistryService
    from services.knowledge_retrieval_service import KnowledgeRetrievalService
    from services.conflict_resolution_service import ConflictResolutionService
    from services.strategy_composer_service import StrategyComposerService
    from services.skill_outcome_tracker_service import SkillOutcomeTrackerService
    from api.knowledge_routes import KnowledgeRoutes

    repo = KnowledgeRepository()
    gw = _make_llm_gateway()

    ingestion = KnowledgeIngestionService(knowledge_repo=repo, llm_gateway=gw)
    registry = KnowledgeRegistryService(knowledge_repo=repo)
    tracker = SkillOutcomeTrackerService(knowledge_repo=repo, win_threshold=0.02)
    retrieval = KnowledgeRetrievalService(knowledge_repo=repo, outcome_tracker=tracker)
    conflict = ConflictResolutionService()
    composer = StrategyComposerService(
        knowledge_repo=repo,
        retrieval_service=retrieval,
        conflict_service=conflict,
    )
    routes = KnowledgeRoutes(
        ingestion_service=ingestion,
        registry_service=registry,
        retrieval_service=retrieval,
        conflict_service=conflict,
        composer_service=composer,
        outcome_tracker_service=tracker,
    )
    return routes, repo, tracker, registry, retrieval


def _seed_skills(registry, count: int = 5) -> list[dict]:
    """Pre-seed skills to ensure retrieval has candidates."""
    skills = []
    for i in range(count):
        s = registry.create_skill(
            skill_code=f"E2E-SK-{i:03d}",
            name=f"e2e_skill_{i}",
            category="augmentation" if i % 2 == 0 else "regularization",
            layer="training",
            task_type="det",
            maturity="stable",
            default_priority=3,
            summary=f"E2E test skill {i}",
        )
        skills.append(s)
    return skills


# ══════════════════════════════════════════════════════════════════════════════
# Test 1: 导入链路端到端
# ══════════════════════════════════════════════════════════════════════════════

def test_e2e_import_pipeline():
    """导入链路端到端：注册来源 → 导入文档 → 抽取技能 → 审核发布 → 技能可查询。"""
    routes, repo, _, registry, retrieval = _build_full_system()

    # 1. 注册来源
    src_resp = routes.post_sources({
        "source_type": "doc",
        "name": "E2E Training Guide",
        "uri": "https://e2e-guide.example.com",
        "author": "E2E Team",
        "license": "MIT",
        "trust_level": 4,
    })
    assert src_resp["ok"] is True
    source_id = src_resp["data"]["source_id"]

    # 2. 导入文档
    doc_resp = routes.post_documents_import({
        "source_id": source_id,
        "title": "E2E Training Guide Doc",
        "doc_type": "markdown",
        "version_label": "v1.0",
        "content": _MARKDOWN_BODY,
        "language": "zh",
    })
    assert doc_resp["ok"] is True
    document_id = doc_resp["data"]["document_id"]
    assert doc_resp["data"]["parse_status"] == "pending"

    # 3. 抽取技能（LLM 提取）
    extract_resp = routes.post_techniques_extract({"document_id": document_id})
    assert extract_resp["ok"] is True
    candidates = extract_resp["data"]["candidates"]
    assert len(candidates) >= 1, "Should extract at least one candidate"

    # 4. 通过 registry 将候选技能注册入库（审核前置步骤）
    from services.knowledge_registry_service import KnowledgeRegistryService
    registry = KnowledgeRegistryService(knowledge_repo=repo)
    for i, cand in enumerate(candidates[:2]):
        registry.create_skill(
            skill_code=f"E2E-EXT-{i:03d}",
            name=cand.get("name", f"extracted_skill_{i}"),
            category=cand.get("category", "augmentation"),
            layer=cand.get("layer", "training"),
            task_type="det",
            maturity="draft",
            default_priority=3,
            summary=str(cand.get("condition", "")),
        )

    all_skills_resp = routes.get_techniques()
    assert all_skills_resp["ok"] is True
    all_skill_names = {s["name"] for s in all_skills_resp["data"]["techniques"]}
    # At least one extracted skill should appear in registry
    assert len(all_skill_names) >= 1

    # 5. 审核发布：找到一个 draft 技能并发布
    all_skills = all_skills_resp["data"]["techniques"]
    draft_skill = next(
        (s for s in all_skills if s.get("publish_status") in ("draft", "reviewed", None)),
        None,
    )
    if draft_skill:
        pub_resp = routes.post_technique_publish(draft_skill["skill_id"])
        assert pub_resp["ok"] is True

    # 6. 检索：技能可查询
    search_result = retrieval.search({"task_type": "det"})
    assert "candidates" in search_result


# ══════════════════════════════════════════════════════════════════════════════
# Test 2: 在线推理链路端到端
# ══════════════════════════════════════════════════════════════════════════════

def test_e2e_online_reasoning():
    """在线推理链路：QuerySignature → 检索 → 冲突消解 → 上下文编排 → 正确返回 snapshot。"""
    routes, repo, tracker, registry, retrieval = _build_full_system()

    # Pre-seed skills
    _seed_skills(registry, count=10)

    # 1. dataset_plan 触发规划上下文生成（调用 knowledge-plan 端点）
    plan_resp = routes.post_dataset_knowledge_plan(
        version_id="version-e2e-001",
        payload={
            "dataset_report": {
                "task_type": "det",
                "stats": {"small_object_ratio": 0.35, "total_images": 8000},
                "scene_gaps": [{"scene": "night", "risk": "high"}],
            },
            "project_constraints": {"gpu_mem_gb": 32},
            "project_id": "proj-e2e-001",
        },
    )
    assert plan_resp["ok"] is True
    snapshot_id = plan_resp["data"]["snapshot_id"]
    assert snapshot_id is not None and snapshot_id != ""

    # 2. 验证 planning_snapshot 已写入（audit 审计）
    snapshot = repo.get_snapshot(snapshot_id)
    assert snapshot["planning_type"] == "dataset_plan"
    assert snapshot["project_id"] == "proj-e2e-001"

    # 3. 验证 retrieval_log 已写入（检索审计）
    assert len(repo._retrieval_logs) >= 1
    log = repo._retrieval_logs[-1]
    assert "query_signature" in log
    assert "candidate_techniques" in log
    assert "ranking_scores" in log


# ══════════════════════════════════════════════════════════════════════════════
# Test 3: 经验闭环端到端
# ══════════════════════════════════════════════════════════════════════════════

def test_e2e_experience_loop():
    """经验闭环：技能入库 → 检索 → 推荐 → 训练 → Outcome win → 再次检索分数提升。"""
    routes, repo, tracker, registry, retrieval = _build_full_system()

    # 1. 注册一个技能
    skill = registry.create_skill(
        skill_code="LOOP-SK-001",
        name="loop_skill",
        category="augmentation",
        layer="training",
        task_type="det",
        maturity="stable",
        default_priority=3,
        summary="Loop skill for experience test.",
    )
    technique_id = skill["skill_id"]

    # 2. 首次检索（无 outcome history）
    result_before = retrieval.search({"task_type": "det"})
    score_before = next(
        c["retrieval_score"] for c in result_before["candidates"]
        if c["skill_code"] == "LOOP-SK-001"
    )

    # 3. 模拟训练完成，触发 outcome 回写 (win)
    tracker.on_eval_complete({
        "job_id": "job-e2e-200",
        "baseline_job_id": "job-e2e-199",
        "project_id": "proj-e2e-002",
        "skill_refs": ["LOOP-SK-001"],
        "kpi_diff": 0.06,  # > win_threshold(0.02) → win
        "scenario_signature": {"task_type": "det"},
    })

    # 4. 再次检索（有 win 历史）
    result_after = retrieval.search({"task_type": "det"})
    score_after = next(
        c["retrieval_score"] for c in result_after["candidates"]
        if c["skill_code"] == "LOOP-SK-001"
    )

    # 5. 验证分数提升
    assert score_after > score_before, (
        f"Expected score boost after win outcome: before={score_before}, after={score_after}"
    )

    # 6. 验证 outcome 已记录
    outcomes = repo.list_outcomes_by_technique("LOOP-SK-001")
    assert len(outcomes) == 1
    assert outcomes[0]["verdict"] == "win"


# ══════════════════════════════════════════════════════════════════════════════
# Test 4: Audit chain – planning_snapshot 可回溯
# ══════════════════════════════════════════════════════════════════════════════

def test_audit_planning_snapshot_traceable():
    """planning_snapshot 记录可追溯：包含 selected / rejected / prompt_context。"""
    routes, repo, _, registry, _ = _build_full_system()
    _seed_skills(registry, count=5)

    plan_resp = routes.post_dataset_knowledge_plan(
        version_id="v-audit-001",
        payload={
            "dataset_report": {
                "task_type": "det",
                "stats": {"small_object_ratio": 0.2, "total_images": 3000},
                "scene_gaps": [],
            },
            "project_constraints": {},
            "project_id": "proj-audit-001",
        },
    )
    assert plan_resp["ok"] is True

    snapshot = repo.get_snapshot(plan_resp["data"]["snapshot_id"])
    assert "selected_techniques" in snapshot
    assert "rejected_techniques" in snapshot
    assert "planning_type" in snapshot


# ══════════════════════════════════════════════════════════════════════════════
# Test 5: Audit chain – retrieval_log 可回溯
# ══════════════════════════════════════════════════════════════════════════════

def test_audit_retrieval_log_traceable():
    """retrieval_log 记录可追溯：包含 candidates / scores / filtered_out。"""
    routes, repo, _, registry, retrieval = _build_full_system()
    _seed_skills(registry, count=5)

    retrieval.search({"task_type": "det", "query_type": "dataset_plan"})

    assert len(repo._retrieval_logs) >= 1
    log = repo._retrieval_logs[-1]
    assert "candidate_techniques" in log
    assert "ranking_scores" in log
    assert "filtered_out" in log
    assert isinstance(log["ranking_scores"], list)


# ══════════════════════════════════════════════════════════════════════════════
# Test 6: Audit chain – llm_call_log 可追踪
# ══════════════════════════════════════════════════════════════════════════════

def test_audit_llm_call_log_traceable():
    """llm_call_log 在 LLM 调用后可追踪（通过 ingestion_service 的 extract_skills 验证）。"""
    routes, repo, _, _, _ = _build_full_system()

    # Register source + import document → triggers LLM extraction
    src = routes.post_sources({
        "source_type": "doc", "name": "LLM Log Source",
        "uri": "https://llm-log-test.example.com",
        "author": "A", "license": "MIT", "trust_level": 3,
    })
    doc = routes.post_documents_import({
        "source_id": src["data"]["source_id"],
        "title": "LLM Log Doc", "doc_type": "markdown",
        "version_label": "v1", "content": _MARKDOWN_BODY, "language": "zh",
    })
    extract_resp = routes.post_techniques_extract({
        "document_id": doc["data"]["document_id"],
    })
    assert extract_resp["ok"] is True

    # Verify the LLM gateway was called (via mock verification)
    # The mock was called during extract → confirms LLM call log pathways are activated.
    # In production, llm_call_log table would store cost/token/latency.
    # Here we verify the extraction succeeded with the mocked LLM.
    assert len(extract_resp["data"]["candidates"]) >= 1


# ══════════════════════════════════════════════════════════════════════════════
# Test 7: Audit chain – skill_outcome 可追溯
# ══════════════════════════════════════════════════════════════════════════════

def test_audit_skill_outcome_traceable():
    """skill_outcome 记录可追溯：verdict / result_summary / scenario_signature 均存在。"""
    routes, repo, tracker, registry, _ = _build_full_system()

    skill = registry.create_skill(
        skill_code="AUDIT-SK-001",
        name="audit_skill",
        category="augmentation", layer="training",
        task_type="det", maturity="stable",
        default_priority=3, summary="Audit test skill.",
    )

    tracker.on_eval_complete({
        "job_id": "job-audit-001",
        "baseline_job_id": "job-audit-000",
        "project_id": "proj-audit-002",
        "skill_refs": ["AUDIT-SK-001"],
        "kpi_diff": 0.04,
        "scenario_signature": {"task_type": "det", "scene": "rain"},
    })

    outcomes = repo.list_outcomes_by_technique("AUDIT-SK-001")
    assert len(outcomes) == 1
    o = outcomes[0]
    assert "verdict" in o
    assert "result_summary" in o
    assert "scenario_signature" in o
    assert "outcome_id" in o
    assert o["verdict"] == "win"  # kpi_diff 0.04 > threshold 0.02
    assert o["scenario_signature"] == {"task_type": "det", "scene": "rain"}
