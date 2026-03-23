"""SkillOutcomeTrackerService – verdict judgment, outcome write-back,
internal prior calculation, and post-eval hook for experience loop."""
from __future__ import annotations

import logging
from typing import Any

_logger = logging.getLogger(__name__)


class SkillOutcomeTrackerService:
    """Track skill experiment outcomes and provide internal experience priors.

    Responsibilities:
    - compute_verdict: 四种 verdict 判定（win / lose / neutral / unstable）
    - record_outcome: 幂等写入 technique_outcome
    - query_similar_outcomes: 按场景签名查询历史 outcome
    - compute_internal_prior: 计算技能 win_rate（反哺检索排序）
    - on_eval_complete: 训练后自动触发 outcome 回写（non-blocking）
    """

    def __init__(
        self,
        *,
        knowledge_repo: Any,
        win_threshold: float = 0.02,
        default_prior: float = 0.5,
    ) -> None:
        self._repo = knowledge_repo
        self._win_threshold = win_threshold
        self._default_prior = default_prior

    # ── Verdict 判定 ─────────────────────────────────────────────────────────

    def compute_verdict(
        self,
        kpi_diffs: list[float],
        *,
        win_threshold: float | None = None,
    ) -> str:
        """Compute verdict from a list of KPI diffs (candidate minus baseline).

        Rules (evaluated in order):
        1. Multiple diffs with at least one win AND one lose → ``unstable``
        2. Average diff > threshold → ``win``
        3. Average diff < -threshold → ``lose``
        4. Otherwise → ``neutral``
        """
        threshold = win_threshold if win_threshold is not None else self._win_threshold

        if not kpi_diffs:
            return "neutral"

        if len(kpi_diffs) > 1:
            has_win = any(d > threshold for d in kpi_diffs)
            has_lose = any(d < -threshold for d in kpi_diffs)
            if has_win and has_lose:
                return "unstable"

        avg_diff = sum(kpi_diffs) / len(kpi_diffs)
        if avg_diff > threshold:
            return "win"
        if avg_diff < -threshold:
            return "lose"
        return "neutral"

    # ── Outcome 回写 ─────────────────────────────────────────────────────────

    def record_outcome(
        self,
        *,
        technique_id: str,
        project_id: str,
        baseline_job_id: str,
        candidate_job_id: str,
        result_summary: dict,
        verdict: str,
        scenario_signature: dict | None = None,
    ) -> dict:
        """Write a single outcome record – idempotent on (technique_id, baseline, candidate)."""
        existing = self._repo.list_outcomes_by_technique(technique_id)
        for rec in existing:
            if (rec["baseline_job_id"] == baseline_job_id
                    and rec["candidate_job_id"] == candidate_job_id):
                return rec

        return self._repo.upsert_outcome(
            technique_id=technique_id,
            project_id=project_id,
            baseline_job_id=baseline_job_id,
            candidate_job_id=candidate_job_id,
            result_summary=result_summary,
            verdict=verdict,
            scenario_signature=scenario_signature,
        )

    # ── 场景签名查询 ─────────────────────────────────────────────────────────

    def query_similar_outcomes(
        self,
        scenario_signature: dict,
        *,
        technique_id: str | None = None,
    ) -> list[dict]:
        """Return outcomes whose scenario_signature matches the given dict exactly."""
        if technique_id is not None:
            candidates = self._repo.list_outcomes_by_technique(technique_id)
        else:
            candidates = self._repo.list_all_outcomes()

        return [
            o for o in candidates
            if o.get("scenario_signature") == scenario_signature
        ]

    # ── 内部先验计算 ─────────────────────────────────────────────────────────

    def compute_internal_prior(self, technique_id: str) -> float:
        """Return win_rate for a technique based on historical outcomes.

        Only win / lose verdicts count; unstable / neutral outcomes are excluded.
        Returns ``default_prior`` when no qualifying history exists.
        """
        all_outcomes = self._repo.list_outcomes_by_technique(technique_id)
        relevant = [o for o in all_outcomes if o["verdict"] in ("win", "lose")]
        if not relevant:
            return self._default_prior

        wins = sum(1 for o in relevant if o["verdict"] == "win")
        return wins / len(relevant)

    # ── Post-eval Hook ───────────────────────────────────────────────────────

    def on_eval_complete(self, job_result: dict) -> None:
        """Post-eval hook: auto-write outcomes for all skill_refs.

        Designed to be non-blocking — any exception is caught and logged so that
        the training main-flow is never blocked by an outcome write failure.
        """
        try:
            skill_refs: list[str] = job_result.get("skill_refs", [])
            if not skill_refs:
                return

            baseline_job_id: str = job_result.get("baseline_job_id", "")
            candidate_job_id: str = job_result.get("job_id", "")
            project_id: str = job_result.get("project_id", "")
            kpi_diff: float = float(job_result.get("kpi_diff", 0.0))
            scenario_signature: dict | None = job_result.get("scenario_signature")

            verdict = self.compute_verdict([kpi_diff])

            for technique_id in skill_refs:
                self.record_outcome(
                    technique_id=technique_id,
                    project_id=project_id,
                    baseline_job_id=baseline_job_id,
                    candidate_job_id=candidate_job_id,
                    result_summary={"kpi_diff": kpi_diff},
                    verdict=verdict,
                    scenario_signature=scenario_signature,
                )
        except Exception:
            _logger.exception("on_eval_complete: outcome write failed (non-blocking)")
