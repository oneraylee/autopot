"""RED tests for KnowledgeRetrievalService (Phase 3 Step 2 + Phase 4 Step 2)."""
import pytest
from unittest.mock import MagicMock


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_repo():
    from repositories.knowledge_repository import KnowledgeRepository
    return KnowledgeRepository()


def _make_service(skills=None):
    from services.knowledge_retrieval_service import KnowledgeRetrievalService
    repo = _make_repo()
    # Pre-populate skills if provided
    if skills:
        for sk in skills:
            repo.create_skill(**sk)
    return KnowledgeRetrievalService(knowledge_repo=repo), repo


def _skill_kwargs(skill_code, name, task_type="det", category="augmentation",
                  layer="training", maturity="stable", default_priority=3,
                  internal_prior=0.0):
    return dict(
        skill_code=skill_code,
        name=name,
        category=category,
        layer=layer,
        task_type=task_type,
        maturity=maturity,
        default_priority=default_priority,
        summary=f"Summary for {name}",
    )


def _make_service_with_prior(skills=None, priors=None):
    """Create service; priors is {skill_code: float} for internal_prior."""
    from services.knowledge_retrieval_service import KnowledgeRetrievalService
    repo = _make_repo()
    if skills:
        for sk in skills:
            repo.create_skill(**sk)
    return KnowledgeRetrievalService(knowledge_repo=repo, internal_priors=priors or {}), repo


# ══════════════════════════════════════════════════════════════════════════════
# Step 2 – QuerySignature 构建
# ══════════════════════════════════════════════════════════════════════════════

def test_build_query_signature_from_dataset():
    """从 dataset_report 构建 QuerySignature 字段完整。"""
    from services.knowledge_retrieval_service import KnowledgeRetrievalService
    svc = KnowledgeRetrievalService(knowledge_repo=_make_repo())
    dataset_report = {
        "task_type": "det",
        "stats": {"small_object_ratio": 0.31, "total_images": 10000},
        "scene_gaps": [{"scene": "night", "risk": "high"}],
    }
    sig = svc.build_query_signature_from_dataset(dataset_report)
    assert sig["task_type"] == "det"
    assert sig["small_object_ratio"] == pytest.approx(0.31)
    assert "night" in sig["weak_scenes"]


def test_build_query_signature_from_evidence():
    """从 evidence_pack 构建 QuerySignature 字段完整（含 baseline 信息）。"""
    from services.knowledge_retrieval_service import KnowledgeRetrievalService
    svc = KnowledgeRetrievalService(knowledge_repo=_make_repo())
    evidence_pack = {
        "job_summary": {
            "job_id": "job_015",
            "train_args": {"imgsz": 640, "batch": 16},
        },
        "eval": {
            "business_kpi": 0.73,
            "by_scene": {"night": {"fn": 45}, "rain": {"fn": 30}},
        },
        "dataset_report": {"task_type": "det", "stats": {"small_object_ratio": 0.28}},
    }
    sig = svc.build_query_signature_from_evidence(evidence_pack)
    assert sig["task_type"] == "det"
    assert sig["baseline_job_id"] == "job_015"
    assert "night" in sig["weak_scenes"]


def test_build_query_signature_missing_field_defaults():
    """缺失字段使用合理的默认值。"""
    from services.knowledge_retrieval_service import KnowledgeRetrievalService
    svc = KnowledgeRetrievalService(knowledge_repo=_make_repo())
    sig = svc.build_query_signature_from_dataset({})
    assert sig["task_type"] == "det"  # default
    assert sig["small_object_ratio"] == pytest.approx(0.0)
    assert sig["weak_scenes"] == []


# ══════════════════════════════════════════════════════════════════════════════
# Step 2 – 结构过滤
# ══════════════════════════════════════════════════════════════════════════════

def test_structure_filter_task_type():
    """task_type 过滤：不匹配的技能被排除。"""
    skills_det = [_skill_kwargs("DET-001", "det_skill", task_type="det")]
    skills_cls = [_skill_kwargs("CLS-001", "cls_skill", task_type="cls")]
    svc, _ = _make_service(skills=skills_det + skills_cls)
    result = svc.search({"task_type": "det"})
    ids = [r["skill_code"] for r in result["candidates"]]
    assert "DET-001" in ids
    assert "CLS-001" not in ids


def test_structure_filter_deprecated_excluded():
    """maturity=deprecated 技能被过滤。"""
    skills = [
        _skill_kwargs("STABLE-001", "stable_skill", maturity="stable"),
        _skill_kwargs("DEP-001", "deprecated_skill", maturity="deprecated"),
    ]
    svc, _ = _make_service(skills=skills)
    result = svc.search({"task_type": "det"})
    ids = [r["skill_code"] for r in result["candidates"]]
    assert "STABLE-001" in ids
    assert "DEP-001" not in ids


# ══════════════════════════════════════════════════════════════════════════════
# Step 2 – 规则召回
# ══════════════════════════════════════════════════════════════════════════════

def test_rule_recall_required_condition_top():
    """required 条件命中的技能排在前列（score 更高）。"""
    skills = [
        _skill_kwargs("HIGH-001", "required_skill", default_priority=3),
        _skill_kwargs("LOW-001", "low_prio", default_priority=1),
    ]
    svc, _ = _make_service_with_prior(
        skills=skills,
        priors={"HIGH-001": 0.5},
    )
    # Provide a query that has matching rule hint for skill HIGH-001
    result = svc.search({
        "task_type": "det",
        "required_skills": ["required_skill"],
    })
    candidates = result["candidates"]
    assert candidates[0]["skill_code"] == "HIGH-001"


def test_rule_recall_avoid_condition_excluded():
    """avoid 条件命中的技能被剔除。"""
    skills = [
        _skill_kwargs("AVOID-001", "dangerous_skill", default_priority=3),
        _skill_kwargs("OK-001", "safe_skill", default_priority=3),
    ]
    svc, _ = _make_service(skills=skills)
    result = svc.search({
        "task_type": "det",
        "avoid_skills": ["dangerous_skill"],
    })
    ids = [r["skill_code"] for r in result["candidates"]]
    assert "AVOID-001" not in ids
    assert "OK-001" in ids


# ══════════════════════════════════════════════════════════════════════════════
# Step 2 – 关键词检索
# ══════════════════════════════════════════════════════════════════════════════

def test_keyword_search_module_name_boost():
    """关键词命中技能名称的技能获得更高分数，排在前列。"""
    skills = [
        _skill_kwargs("KEYWORD-001", "imgsz_boost_recall", default_priority=2),
        _skill_kwargs("NKWD-001", "generic_technique", default_priority=2),
    ]
    svc, _ = _make_service(skills=skills)
    result = svc.search({
        "task_type": "det",
        "keywords": ["imgsz"],
    })
    candidates = result["candidates"]
    assert len(candidates) >= 1
    assert candidates[0]["skill_code"] == "KEYWORD-001"


# ══════════════════════════════════════════════════════════════════════════════
# Step 2 – 简化排序公式
# ══════════════════════════════════════════════════════════════════════════════

def test_simplified_score_formula_correct():
    """简化排序公式计算正确: score = rule_match × (default_priority + internal_prior)。"""
    from services.knowledge_retrieval_service import compute_score
    score = compute_score(
        rule_match=1.0,
        default_priority=3,
        internal_prior=0.5,
        status_filter=1.0,
    )
    assert score == pytest.approx(3.5)

    # rule_match=0 should zero out the score
    score_no_match = compute_score(
        rule_match=0.0,
        default_priority=3,
        internal_prior=0.5,
        status_filter=1.0,
    )
    assert score_no_match == pytest.approx(0.0)


# ══════════════════════════════════════════════════════════════════════════════
# Step 2 – top_k 截断与日志
# ══════════════════════════════════════════════════════════════════════════════

def test_top_k_truncation():
    """top_k 参数截断候选列表。"""
    skills = [
        _skill_kwargs(f"SK-{i:03d}", f"skill_{i}", default_priority=i % 5)
        for i in range(10)
    ]
    svc, _ = _make_service(skills=skills)
    result = svc.search({"task_type": "det"}, top_k=3)
    assert len(result["candidates"]) <= 3


def test_retrieval_log_written():
    """每次检索自动写入 retrieval_log。"""
    svc, repo = _make_service(skills=[
        _skill_kwargs("SK-001", "skill_one"),
    ])
    svc.search({"task_type": "det"})
    assert len(repo._retrieval_logs) >= 1
    log = repo._retrieval_logs[-1]
    assert "query_signature" in log
    assert "candidate_techniques" in log


# ══════════════════════════════════════════════════════════════════════════════
# Phase 4 Step 2 – 内部经验加权集成
# ══════════════════════════════════════════════════════════════════════════════

def _make_tracker(repo, win_threshold=0.02, default_prior=0.5):
    from services.skill_outcome_tracker_service import SkillOutcomeTrackerService
    return SkillOutcomeTrackerService(
        knowledge_repo=repo,
        win_threshold=win_threshold,
        default_prior=default_prior,
    )


def _make_service_with_tracker(skills=None, tracker=None, repo=None):
    from services.knowledge_retrieval_service import KnowledgeRetrievalService
    if repo is None:
        repo = _make_repo()
    if skills:
        for sk in skills:
            repo.create_skill(**sk)
    svc = KnowledgeRetrievalService(knowledge_repo=repo, outcome_tracker=tracker)
    return svc, repo


def test_win_record_boosts_score():
    """win 记录（win_rate = 1.0）使技能排序分数高于无历史的同等技能。"""
    repo = _make_repo()
    for code in ["WIN-001", "BASE-001"]:
        repo.create_skill(**_skill_kwargs(code, f"skill_{code}", default_priority=3))

    tracker = _make_tracker(repo)
    # Record a win for WIN-001 skill
    tracker.record_outcome(
        technique_id="WIN-001",
        project_id="proj",
        baseline_job_id="j-001",
        candidate_job_id="j-002",
        result_summary={"kpi_diff": 0.05},
        verdict="win",
    )

    svc, _ = _make_service_with_tracker(tracker=tracker, repo=repo)
    result = svc.search({"task_type": "det"})
    candidates = {c["skill_code"]: c["retrieval_score"] for c in result["candidates"]}
    assert candidates["WIN-001"] > candidates["BASE-001"]


def test_lose_record_lowers_score():
    """lose 记录（win_rate = 0.0）使技能排序分数低于无历史的同等技能。"""
    repo = _make_repo()
    for code in ["LOSE-001", "BASE-001"]:
        repo.create_skill(**_skill_kwargs(code, f"skill_{code}", default_priority=3))

    tracker = _make_tracker(repo)
    tracker.record_outcome(
        technique_id="LOSE-001",
        project_id="proj",
        baseline_job_id="j-001",
        candidate_job_id="j-002",
        result_summary={"kpi_diff": -0.05},
        verdict="lose",
    )

    svc, _ = _make_service_with_tracker(tracker=tracker, repo=repo)
    result = svc.search({"task_type": "det"})
    candidates = {c["skill_code"]: c["retrieval_score"] for c in result["candidates"]}
    assert candidates["LOSE-001"] < candidates["BASE-001"]


def test_unstable_record_no_change():
    """unstable 记录不调整分数：与无历史技能分数相同。"""
    repo = _make_repo()
    for code in ["UNSTABLE-001", "BASE-001"]:
        repo.create_skill(**_skill_kwargs(code, f"skill_{code}", default_priority=3))

    tracker = _make_tracker(repo)
    # Unstable: one win, one lose
    tracker.record_outcome(
        technique_id="UNSTABLE-001",
        project_id="proj",
        baseline_job_id="j-001",
        candidate_job_id="j-002",
        result_summary={"kpi_diff": 0.05},
        verdict="unstable",
    )

    svc, _ = _make_service_with_tracker(tracker=tracker, repo=repo)
    result = svc.search({"task_type": "det"})
    candidates = {c["skill_code"]: c["retrieval_score"] for c in result["candidates"]}
    # unstable outcome excluded from win_rate → same default prior → same score
    assert candidates["UNSTABLE-001"] == pytest.approx(candidates["BASE-001"])


def test_internal_prior_in_simplified_formula():
    """S_internal 在简化公式中正确生效：
    score = rule_match × (default_priority + S_internal) × status_filter
    S_internal = (win_rate - 0.5) × 2
    """
    from services.knowledge_retrieval_service import compute_score
    # win_rate = 1.0 → S_internal = 1.0
    s_internal_win = (1.0 - 0.5) * 2
    score_win = compute_score(
        rule_match=1.0,
        default_priority=3,
        internal_prior=s_internal_win,
        status_filter=1.0,
    )
    assert score_win == pytest.approx(4.0)

    # win_rate = 0.0 → S_internal = -1.0
    s_internal_lose = (0.0 - 0.5) * 2
    score_lose = compute_score(
        rule_match=1.0,
        default_priority=3,
        internal_prior=s_internal_lose,
        status_filter=1.0,
    )
    assert score_lose == pytest.approx(2.0)

    # win_rate = 0.5 (default) → S_internal = 0.0
    s_internal_default = (0.5 - 0.5) * 2
    score_default = compute_score(
        rule_match=1.0,
        default_priority=3,
        internal_prior=s_internal_default,
        status_filter=1.0,
    )
    assert score_default == pytest.approx(3.0)


def test_no_outcome_uses_default_prior():
    """无 outcome 时使用默认先验：S_internal = (0.5 - 0.5) × 2 = 0.0，分数不变。"""
    repo = _make_repo()
    repo.create_skill(**_skill_kwargs("SK-NEW", "new_skill", default_priority=3))

    tracker = _make_tracker(repo, default_prior=0.5)
    # No outcomes recorded for SK-NEW
    svc, _ = _make_service_with_tracker(tracker=tracker, repo=repo)
    result = svc.search({"task_type": "det"})
    candidates = {c["skill_code"]: c["retrieval_score"] for c in result["candidates"]}

    # Score should equal rule_match(1.0) × (default_priority(3) + S_internal(0.0)) × status(1.0) = 3.0
    assert candidates["SK-NEW"] == pytest.approx(3.0)
