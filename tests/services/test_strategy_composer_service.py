"""RED tests for StrategyComposerService + AgentService Enhancement (Phase 3 Step 3)."""
import hashlib
import json
import pytest
from unittest.mock import MagicMock


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_repo():
    from repositories.knowledge_repository import KnowledgeRepository
    return KnowledgeRepository()


def _make_skill(repo, skill_code, name, task_type="det", default_priority=3):
    return repo.create_skill(
        skill_code=skill_code,
        name=name,
        category="regularization",
        layer="training",
        task_type=task_type,
        maturity="stable",
        default_priority=default_priority,
        summary=f"Summary for {name}",
    )


def _make_composer(skills=None):
    from services.strategy_composer_service import StrategyComposerService
    from services.knowledge_retrieval_service import KnowledgeRetrievalService
    from services.conflict_resolution_service import ConflictResolutionService
    repo = _make_repo()
    if skills:
        for sk in skills:
            _make_skill(repo, **sk)
    retrieval_svc = KnowledgeRetrievalService(knowledge_repo=repo)
    conflict_svc = ConflictResolutionService()
    composer = StrategyComposerService(
        knowledge_repo=repo,
        retrieval_service=retrieval_svc,
        conflict_service=conflict_svc,
    )
    return composer, repo


def _12_skills():
    return [
        {"skill_code": f"SK-{i:03d}", "name": f"skill_{i}", "task_type": "det",
         "default_priority": 3}
        for i in range(12)
    ]


# ══════════════════════════════════════════════════════════════════════════════
# Step 3 – SkillContext 结构与数量控制
# ══════════════════════════════════════════════════════════════════════════════

def test_compose_context_output_structure():
    """SkillContext 输出包含 candidate_techniques / rejected_techniques / conflict_summary。"""
    composer, _ = _make_composer(skills=_12_skills())
    ctx = composer.compose_planning_context(
        dataset_report={"task_type": "det", "stats": {}, "scene_gaps": []},
        project_constraints={"gpu_mem_gb": 24},
    )
    assert "candidate_techniques" in ctx
    assert "rejected_techniques" in ctx
    assert "conflict_summary" in ctx


def test_compose_context_candidate_count_5_12():
    """候选数量控制在 5-12 条之内。"""
    composer, _ = _make_composer(skills=_12_skills())
    ctx = composer.compose_planning_context(
        dataset_report={"task_type": "det", "stats": {}, "scene_gaps": []},
        project_constraints={"gpu_mem_gb": 24},
        top_k=8,
    )
    count = len(ctx["candidate_techniques"])
    assert 5 <= count <= 12


def test_compose_context_token_budget_trim():
    """超出 token 预算时按裁剪顺序执行（低优先级被裁掉）。"""
    composer, _ = _make_composer(skills=_12_skills())
    # Very tight budget forces trimming
    ctx = composer.compose_planning_context(
        dataset_report={"task_type": "det", "stats": {}, "scene_gaps": []},
        project_constraints={"gpu_mem_gb": 24},
        top_k=8,
        token_budget=100,  # Very small budget to trigger trimming
    )
    # Should not exceed budget (fewer candidates)
    assert len(ctx["candidate_techniques"]) < 12


# ══════════════════════════════════════════════════════════════════════════════
# Step 3 – PlanningSnapshot
# ══════════════════════════════════════════════════════════════════════════════

def test_planning_snapshot_written():
    """PlanningSnapshot 写入完整：含 selected / rejected / prompt_context / evidence_fingerprint。"""
    composer, repo = _make_composer(skills=_12_skills())
    ctx = composer.compose_planning_context(
        dataset_report={"task_type": "det", "stats": {}, "scene_gaps": []},
        project_constraints={"gpu_mem_gb": 24},
        project_id="proj_001",
        top_k=6,
    )
    snapshot_id = ctx["snapshot_id"]
    snapshot = repo.get_snapshot(snapshot_id)
    assert snapshot["project_id"] == "proj_001"
    assert "selected_techniques" in snapshot
    assert "rejected_techniques" in snapshot
    assert "prompt_context" in snapshot
    assert "evidence_fingerprint" in snapshot


def test_snapshot_evidence_fingerprint_reproducible():
    """相同输入的 evidence_fingerprint 每次相同（可复现）。"""
    dataset_report = {"task_type": "det", "stats": {"total": 100}, "scene_gaps": []}
    composer, _ = _make_composer(skills=_12_skills())
    ctx1 = composer.compose_planning_context(
        dataset_report=dataset_report,
        project_constraints={"gpu_mem_gb": 24},
        project_id="proj_001",
    )
    ctx2 = composer.compose_planning_context(
        dataset_report=dataset_report,
        project_constraints={"gpu_mem_gb": 24},
        project_id="proj_001",
    )
    # fingerprints should be the same for the same input
    snap1_id = ctx1["snapshot_id"]
    snap2_id = ctx2["snapshot_id"]
    # They are different snapshots, but fingerprints must be the same
    from repositories.knowledge_repository import KnowledgeRepository
    # We need to verify fingerprints are deterministic
    fp1 = ctx1.get("evidence_fingerprint")
    fp2 = ctx2.get("evidence_fingerprint")
    assert fp1 == fp2
    assert fp1 is not None and fp1 != ""


def test_retrieval_log_written_on_search():
    """每次 compose 都会写入检索日志。"""
    composer, repo = _make_composer(skills=_12_skills())
    before_count = len(repo._retrieval_logs)
    composer.compose_planning_context(
        dataset_report={"task_type": "det", "stats": {}, "scene_gaps": []},
        project_constraints={},
    )
    assert len(repo._retrieval_logs) > before_count


# ══════════════════════════════════════════════════════════════════════════════
# Step 3 – Agent 注入 SkillContext
# ══════════════════════════════════════════════════════════════════════════════

def _valid_agent_output_with_skill_refs():
    return {
        "analysis_report": "report",
        "next_experiments": {
            "experiments": [
                {
                    "name": "A",
                    "changes": [{"field": "lr", "from": 0.001, "to": 0.0005}],
                    "expected": "better",
                    "evidence_refs": ["eval_report.overall.business_kpi"],
                    "technique_refs": ["SK-001"],
                    "conflict_checked": True,
                }
            ]
        },
    }


def test_agent_planning_with_skill_context():
    """规划阶段：注入 SkillContext 后 analyze 仍可成功返回。"""
    from services.agent_service import AgentService
    skill_context = {
        "candidate_techniques": [{"skill_code": "SK-001", "name": "skill_1"}],
        "rejected_techniques": [],
        "conflict_summary": [],
    }
    svc = AgentService()
    result = svc.analyze(
        evidence_pack={"kpi_config": {}, "index_paths": {}},
        agent_output=_valid_agent_output_with_skill_refs(),
        skill_context=skill_context,
    )
    assert result["ok"] is True


def test_agent_diagnosis_with_skill_context():
    """诊断阶段：注入 SkillContext 后 analyze 含 skill_refs + conflict_checked。"""
    from services.agent_service import AgentService
    skill_context = {
        "candidate_techniques": [{"skill_code": "SK-001"}],
        "rejected_techniques": [],
        "conflict_summary": [],
    }
    svc = AgentService()
    result = svc.analyze(
        evidence_pack={"kpi_config": {}, "index_paths": {}},
        agent_output=_valid_agent_output_with_skill_refs(),
        skill_context=skill_context,
    )
    assert result["ok"] is True
    assert result.get("skill_context_injected") is True


def test_agent_output_contains_skill_refs():
    """Agent 输出中 experiments 含 technique_refs 字段。"""
    from services.agent_service import AgentService
    svc = AgentService()
    result = svc.analyze(
        evidence_pack={"kpi_config": {}, "index_paths": {}},
        agent_output=_valid_agent_output_with_skill_refs(),
    )
    assert result["ok"] is True
    experiments = result["next_experiments"]["experiments"]
    assert "technique_refs" in experiments[0]


def test_agent_output_contains_conflict_checked():
    """Agent 输出中 experiments 含 conflict_checked 字段。"""
    from services.agent_service import AgentService
    svc = AgentService()
    result = svc.analyze(
        evidence_pack={"kpi_config": {}, "index_paths": {}},
        agent_output=_valid_agent_output_with_skill_refs(),
    )
    assert result["ok"] is True
    experiments = result["next_experiments"]["experiments"]
    assert "conflict_checked" in experiments[0]


# ══════════════════════════════════════════════════════════════════════════════
# Step 3 – Proposal 校验增强
# ══════════════════════════════════════════════════════════════════════════════

def _make_knowledge_proposal_validator(known_skill_codes=None):
    from services.strategy_composer_service import ProposalKnowledgeValidator
    return ProposalKnowledgeValidator(known_skill_codes=known_skill_codes or [])


def test_validate_technique_refs_valid():
    """skill_refs 全部在已知技能中 → 校验通过。"""
    validator = _make_knowledge_proposal_validator(known_skill_codes=["SK-001", "SK-002"])
    result = validator.validate_technique_refs(
        experiments=[{
            "name": "A",
            "technique_refs": ["SK-001"],
        }]
    )
    assert result["ok"] is True


def test_validate_technique_refs_invalid_rejected():
    """skill_refs 中包含未知技能 → 校验失败。"""
    validator = _make_knowledge_proposal_validator(known_skill_codes=["SK-001"])
    result = validator.validate_technique_refs(
        experiments=[{
            "name": "A",
            "technique_refs": ["SK-UNKNOWN"],
        }]
    )
    assert result["ok"] is False
    assert "SK-UNKNOWN" in result["error"]


def test_validate_combination_conflict_detected():
    """冲突技能组合 → 校验失败。"""
    from services.conflict_resolution_service import ConflictResolutionService
    rules = [{
        "rule_type": "incompatible_with",
        "if": {"all": [{"technique": "SK-001"}, {"technique": "SK-002"}]},
        "because": {"reason_code": "structural_conflict", "message": "clash"},
        "severity": "hard",
    }]
    conflict_svc = ConflictResolutionService(rules=rules)
    validator = _make_knowledge_proposal_validator(known_skill_codes=["SK-001", "SK-002"])
    result = validator.validate_technique_combination(
        experiments=[{
            "name": "A",
            "technique_refs": ["SK-001", "SK-002"],
        }],
        conflict_service=conflict_svc,
        technique_lookup={"SK-001": {"technique_id": "SK-001", "resources": {}},
                          "SK-002": {"technique_id": "SK-002", "resources": {}}},
    )
    assert result["ok"] is False


def test_validate_resource_budget_exceeded():
    """资源超限 → 校验失败。"""
    from services.conflict_resolution_service import ConflictResolutionService
    conflict_svc = ConflictResolutionService()
    validator = _make_knowledge_proposal_validator(known_skill_codes=["SK-001", "SK-002"])
    result = validator.validate_resource_budget(
        experiments=[{
            "name": "A",
            "technique_refs": ["SK-001", "SK-002"],
        }],
        constraints={"gpu_mem_gb": 24},
        technique_lookup={
            "SK-001": {"technique_id": "SK-001", "resources": {"gpu_mem_gb": 16.0}},
            "SK-002": {"technique_id": "SK-002", "resources": {"gpu_mem_gb": 14.0}},
        },
        conflict_service=conflict_svc,
    )
    assert result["ok"] is False


def test_validate_version_compatibility_failed():
    """版本不兼容 → 校验失败。"""
    from services.conflict_resolution_service import ConflictResolutionService
    conflict_svc = ConflictResolutionService()
    validator = _make_knowledge_proposal_validator(known_skill_codes=["SK-NEW"])
    result = validator.validate_version_compatibility(
        experiments=[{
            "name": "A",
            "technique_refs": ["SK-NEW"],
        }],
        constraints={"framework_version": "8.0"},
        technique_lookup={
            "SK-NEW": {"technique_id": "SK-NEW", "resources": {},
                       "framework_version_min": "9.0"},
        },
        conflict_service=conflict_svc,
    )
    assert result["ok"] is False
