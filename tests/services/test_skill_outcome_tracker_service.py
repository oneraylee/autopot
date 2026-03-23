"""RED tests for SkillOutcomeTrackerService (Phase 4 Step 1)."""
import pytest
from unittest.mock import MagicMock


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_repo():
    from repositories.knowledge_repository import KnowledgeRepository
    return KnowledgeRepository()


def _make_tracker(repo=None, win_threshold=0.02, default_prior=0.5):
    from services.skill_outcome_tracker_service import SkillOutcomeTrackerService
    if repo is None:
        repo = _make_repo()
    return SkillOutcomeTrackerService(
        knowledge_repo=repo,
        win_threshold=win_threshold,
        default_prior=default_prior,
    )


def _make_repo_with_skill(skill_code="SKILL-001"):
    repo = _make_repo()
    repo.create_skill(
        skill_code=skill_code,
        name=f"skill_{skill_code}",
        category="augmentation",
        layer="training",
        task_type="det",
        maturity="stable",
        default_priority=3,
        summary=f"Summary for {skill_code}",
    )
    return repo


def _record_outcome(tracker, technique_id="SKILL-001", baseline_job_id="job-001",
                    candidate_job_id="job-002", kpi_diff=0.05, verdict=None,
                    scenario_signature=None, project_id="proj-001"):
    if verdict is None:
        verdict = "win" if kpi_diff > 0.02 else ("lose" if kpi_diff < -0.02 else "neutral")
    return tracker.record_outcome(
        technique_id=technique_id,
        project_id=project_id,
        baseline_job_id=baseline_job_id,
        candidate_job_id=candidate_job_id,
        result_summary={"kpi_diff": kpi_diff},
        verdict=verdict,
        scenario_signature=scenario_signature,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Step 1 – Verdict 判定
# ══════════════════════════════════════════════════════════════════════════════

def test_verdict_win_above_threshold():
    """差异超过阈值 → win。"""
    tracker = _make_tracker(win_threshold=0.02)
    verdict = tracker.compute_verdict([0.05])
    assert verdict == "win"


def test_verdict_lose_below_negative_threshold():
    """差异低于负阈值 → lose。"""
    tracker = _make_tracker(win_threshold=0.02)
    verdict = tracker.compute_verdict([-0.05])
    assert verdict == "lose"


def test_verdict_neutral_within_tolerance():
    """差异在容差范围内 → neutral。"""
    tracker = _make_tracker(win_threshold=0.02)
    verdict = tracker.compute_verdict([0.01])
    assert verdict == "neutral"


def test_verdict_unstable_inconsistent():
    """多次实验结果不一致 → unstable（部分 win，部分 lose）。"""
    tracker = _make_tracker(win_threshold=0.02)
    verdict = tracker.compute_verdict([0.05, -0.05])
    assert verdict == "unstable"


def test_verdict_threshold_configurable():
    """阈值可配置：使用大阈值时 0.05 差异应判为 neutral。"""
    tracker = _make_tracker(win_threshold=0.10)
    assert tracker.compute_verdict([0.05]) == "neutral"
    # With small threshold, same diff should be win
    tracker_small = _make_tracker(win_threshold=0.01)
    assert tracker_small.compute_verdict([0.05]) == "win"


# ══════════════════════════════════════════════════════════════════════════════
# Step 1 – Outcome 回写
# ══════════════════════════════════════════════════════════════════════════════

def test_record_outcome_single_success():
    """单条 outcome 写入成功，返回完整记录。"""
    repo = _make_repo_with_skill("SKILL-001")
    tracker = _make_tracker(repo)
    result = _record_outcome(tracker, technique_id="SKILL-001", kpi_diff=0.05, verdict="win")
    assert result["technique_id"] == "SKILL-001"
    assert result["verdict"] == "win"
    assert "outcome_id" in result


def test_record_outcome_batch_correct():
    """多条技能批量回写正确，各技能均有独立记录。"""
    repo = _make_repo()
    for code in ["SK-A", "SK-B", "SK-C"]:
        repo.create_skill(
            skill_code=code, name=code, category="augmentation",
            layer="training", task_type="det", maturity="stable",
            default_priority=3, summary="x",
        )
    tracker = _make_tracker(repo)
    for code in ["SK-A", "SK-B", "SK-C"]:
        _record_outcome(tracker, technique_id=code, baseline_job_id="j-000",
                        candidate_job_id=f"j-{code}", kpi_diff=0.03, verdict="win")

    for code in ["SK-A", "SK-B", "SK-C"]:
        outcomes = repo.list_outcomes_by_technique(code)
        assert len(outcomes) == 1
        assert outcomes[0]["verdict"] == "win"


def test_outcome_fields_complete():
    """写入 outcome 的 scenario_signature / result_summary 字段均完整。"""
    repo = _make_repo_with_skill("SKILL-001")
    tracker = _make_tracker(repo)
    sig = {"task_type": "det", "scene": "night"}
    result = tracker.record_outcome(
        technique_id="SKILL-001",
        project_id="proj-001",
        baseline_job_id="job-001",
        candidate_job_id="job-002",
        result_summary={"kpi_diff": 0.05, "map50": 0.82},
        verdict="win",
        scenario_signature=sig,
    )
    assert result["scenario_signature"] == sig
    assert result["result_summary"]["kpi_diff"] == pytest.approx(0.05)
    assert result["result_summary"]["map50"] == pytest.approx(0.82)


def test_record_outcome_idempotent():
    """相同 baseline + candidate 重复回写，不产生重复记录（幂等）。"""
    repo = _make_repo_with_skill("SKILL-001")
    tracker = _make_tracker(repo)
    # Write twice with same baseline+candidate
    r1 = _record_outcome(tracker, technique_id="SKILL-001",
                         baseline_job_id="job-001", candidate_job_id="job-002",
                         kpi_diff=0.05, verdict="win")
    r2 = _record_outcome(tracker, technique_id="SKILL-001",
                         baseline_job_id="job-001", candidate_job_id="job-002",
                         kpi_diff=0.05, verdict="win")
    outcomes = repo.list_outcomes_by_technique("SKILL-001")
    assert len(outcomes) == 1
    assert r1["outcome_id"] == r2["outcome_id"]


# ══════════════════════════════════════════════════════════════════════════════
# Step 1 – 场景签名查询
# ══════════════════════════════════════════════════════════════════════════════

def test_query_outcomes_by_scenario():
    """按场景签名查询历史 outcome 正确。"""
    repo = _make_repo()
    for code in ["SK-NIGHT", "SK-DAY"]:
        repo.create_skill(
            skill_code=code, name=code, category="augmentation",
            layer="training", task_type="det", maturity="stable",
            default_priority=3, summary="x",
        )
    tracker = _make_tracker(repo)

    night_sig = {"scene": "night"}
    day_sig = {"scene": "day"}

    _record_outcome(tracker, technique_id="SK-NIGHT", baseline_job_id="j-001",
                    candidate_job_id="j-002", kpi_diff=0.05, verdict="win",
                    scenario_signature=night_sig)
    _record_outcome(tracker, technique_id="SK-DAY", baseline_job_id="j-001",
                    candidate_job_id="j-003", kpi_diff=-0.03, verdict="lose",
                    scenario_signature=day_sig)

    night_outcomes = tracker.query_similar_outcomes(night_sig)
    assert len(night_outcomes) == 1
    assert night_outcomes[0]["technique_id"] == "SK-NIGHT"

    day_outcomes = tracker.query_similar_outcomes(day_sig)
    assert len(day_outcomes) == 1
    assert day_outcomes[0]["verdict"] == "lose"


# ══════════════════════════════════════════════════════════════════════════════
# Step 1 – 内部先验计算
# ══════════════════════════════════════════════════════════════════════════════

def test_compute_internal_prior_win_rate():
    """compute_internal_prior 返回正确 win_rate（wins / total non-unstable）。"""
    repo = _make_repo_with_skill("SKILL-001")
    tracker = _make_tracker(repo)
    # 2 win, 1 lose
    _record_outcome(tracker, technique_id="SKILL-001", baseline_job_id="j-001",
                    candidate_job_id="j-002", kpi_diff=0.05, verdict="win")
    _record_outcome(tracker, technique_id="SKILL-001", baseline_job_id="j-001",
                    candidate_job_id="j-003", kpi_diff=0.04, verdict="win")
    _record_outcome(tracker, technique_id="SKILL-001", baseline_job_id="j-002",
                    candidate_job_id="j-004", kpi_diff=-0.03, verdict="lose")

    win_rate = tracker.compute_internal_prior("SKILL-001")
    assert win_rate == pytest.approx(2 / 3)


def test_internal_prior_no_history_default():
    """无历史 outcome 时返回 default_prior（默认 0.5）。"""
    repo = _make_repo_with_skill("SKILL-NEW")
    tracker = _make_tracker(repo, default_prior=0.5)
    win_rate = tracker.compute_internal_prior("SKILL-NEW")
    assert win_rate == pytest.approx(0.5)

    # Custom default prior
    tracker2 = _make_tracker(repo, default_prior=0.3)
    win_rate2 = tracker2.compute_internal_prior("SKILL-NEW")
    assert win_rate2 == pytest.approx(0.3)


# ══════════════════════════════════════════════════════════════════════════════
# Step 1 – 训练后自动回写（Post-eval hook）
# ══════════════════════════════════════════════════════════════════════════════

def test_post_eval_auto_outcome_write():
    """训练完成后调用 on_eval_complete 自动回写 outcome。"""
    repo = _make_repo()
    for code in ["TECH-001", "TECH-002"]:
        repo.create_skill(
            skill_code=code, name=code, category="augmentation",
            layer="training", task_type="det", maturity="stable",
            default_priority=3, summary="x",
        )
    tracker = _make_tracker(repo)
    job_result = {
        "job_id": "job-100",
        "baseline_job_id": "job-099",
        "project_id": "proj-x",
        "skill_refs": ["TECH-001", "TECH-002"],
        "kpi_diff": 0.05,
        "scenario_signature": {"task_type": "det"},
    }
    tracker.on_eval_complete(job_result)

    # Both techniques should have outcomes
    o1 = repo.list_outcomes_by_technique("TECH-001")
    o2 = repo.list_outcomes_by_technique("TECH-002")
    assert len(o1) == 1 and o1[0]["verdict"] == "win"
    assert len(o2) == 1 and o2[0]["verdict"] == "win"


def test_no_skill_refs_skips_outcome():
    """job_result 中无 skill_refs 时跳过回写（不写任何记录）。"""
    repo = _make_repo()
    tracker = _make_tracker(repo)
    job_result = {
        "job_id": "job-200",
        "baseline_job_id": "job-199",
        "project_id": "proj-y",
        "skill_refs": [],  # empty
        "kpi_diff": 0.05,
    }
    tracker.on_eval_complete(job_result)
    # No outcomes written anywhere
    assert all(len(v) == 0 for v in repo._outcomes.values())


def test_outcome_write_failure_not_block():
    """回写失败（repo 抛异常）不影响主流程（不传播异常）。"""
    mock_repo = MagicMock()
    mock_repo.list_outcomes_by_technique.return_value = []
    mock_repo.upsert_outcome.side_effect = RuntimeError("DB error")
    tracker = _make_tracker(mock_repo)
    job_result = {
        "job_id": "job-300",
        "baseline_job_id": "job-299",
        "project_id": "proj-z",
        "skill_refs": ["TECH-FAIL"],
        "kpi_diff": 0.05,
    }
    # Should NOT raise
    tracker.on_eval_complete(job_result)
