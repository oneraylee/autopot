"""KnowledgeRetrievalService – multi-stage hybrid retrieval with QuerySignature,
structure filtering, rule recall, keyword search, simplified scoring, and log."""
from __future__ import annotations

from typing import Any


# ── Scoring formula ──────────────────────────────────────────────────────────

def compute_score(
    *,
    rule_match: float,
    default_priority: float,
    internal_prior: float,
    status_filter: float,
) -> float:
    """Simplified ranking score.

    score = rule_match × (default_priority + internal_prior) × status_filter
    """
    return rule_match * (default_priority + internal_prior) * status_filter


# ── KnowledgeRetrievalService ────────────────────────────────────────────────

class KnowledgeRetrievalService:
    """Multi-stage hybrid retrieval service.

    Pipeline:
        build_query_signature → structure_filter → rule_recall
        → keyword_search → simplified scoring → top_k truncation
        → write retrieval_log
    """

    def __init__(self, *, knowledge_repo: Any, internal_priors: dict[str, float] | None = None, outcome_tracker: Any | None = None) -> None:
        self._repo = knowledge_repo
        self._internal_priors: dict[str, float] = internal_priors or {}
        self._outcome_tracker = outcome_tracker

    # ── QuerySignature builders ──────────────

    def build_query_signature_from_dataset(
        self, dataset_report: dict[str, Any]
    ) -> dict[str, Any]:
        """Build QuerySignature from a dataset_report dict."""
        stats = dataset_report.get("stats", {})
        scene_gaps = dataset_report.get("scene_gaps", [])
        weak_scenes = [sg["scene"] for sg in scene_gaps if "scene" in sg]
        return {
            "task_type": dataset_report.get("task_type", "det"),
            "small_object_ratio": float(stats.get("small_object_ratio", 0.0)),
            "weak_scenes": weak_scenes,
            "total_images": int(stats.get("total_images", 0)),
            "baseline_job_id": "",
        }

    def build_query_signature_from_evidence(
        self, evidence_pack: dict[str, Any]
    ) -> dict[str, Any]:
        """Build QuerySignature from an evidence_pack dict."""
        job_summary = evidence_pack.get("job_summary", {})
        eval_data = evidence_pack.get("eval", {})
        dataset_report = evidence_pack.get("dataset_report", {})

        # Derive weak scenes from eval.by_scene keys
        by_scene = eval_data.get("by_scene", {})
        weak_scenes = list(by_scene.keys())

        stats = dataset_report.get("stats", {})
        return {
            "task_type": dataset_report.get("task_type", "det"),
            "small_object_ratio": float(stats.get("small_object_ratio", 0.0)),
            "weak_scenes": weak_scenes,
            "baseline_job_id": job_summary.get("job_id", ""),
            "business_kpi": float(eval_data.get("business_kpi", 0.0)),
        }

    # ── Main search ──────────────────────────

    def search(
        self,
        query_signature: dict[str, Any],
        *,
        top_k: int = 20,
    ) -> dict[str, Any]:
        """Hybrid retrieval with multi-stage filtering and scoring.

        Returns:
            {"candidates": [...], "total_before_truncation": int}
        """
        task_type = query_signature.get("task_type", "det")
        required_skills: list[str] = query_signature.get("required_skills", [])
        avoid_skills: list[str] = query_signature.get("avoid_skills", [])
        keywords: list[str] = query_signature.get("keywords", [])

        # 1. Retrieve all skills
        all_skills = self._repo.list_skills()

        # 2. Structure filter: task_type match + exclude deprecated
        filtered = [
            s for s in all_skills
            if s.get("task_type") == task_type
            and s.get("maturity") != "deprecated"
        ]

        # 3. Rule recall: exclude avoid_skills
        after_rules = [
            s for s in filtered
            if s.get("name") not in avoid_skills
            and s.get("skill_code") not in avoid_skills
        ]

        # 4. Score each skill
        scored: list[tuple[dict, float]] = []
        for skill in after_rules:
            rule_match = 1.0

            # Boost if in required_skills
            if skill.get("name") in required_skills or skill.get("skill_code") in required_skills:
                rule_match = 2.0

            # Keyword boost: check if any keyword appears in skill name
            skill_name = skill.get("name", "").lower()
            for kw in keywords:
                if kw.lower() in skill_name:
                    rule_match += 1.0

            default_priority = float(skill.get("default_priority", 3))
            skill_code = skill.get("skill_code", "")
            if self._outcome_tracker is not None:
                # Dynamic prior: (win_rate - 0.5) × 2 maps [0,1] → [-1,+1]
                win_rate = self._outcome_tracker.compute_internal_prior(skill_code)
                internal_prior = (win_rate - 0.5) * 2.0
            else:
                internal_prior = self._internal_priors.get(skill_code, 0.0)
            # status_filter: 1.0 for stable, 0.5 for experimental
            maturity = skill.get("maturity", "stable")
            status_filter = 1.0 if maturity == "stable" else 0.5

            score = compute_score(
                rule_match=rule_match,
                default_priority=default_priority,
                internal_prior=internal_prior,
                status_filter=status_filter,
            )
            scored.append((skill, score))

        # 5. Sort descending by score
        scored.sort(key=lambda x: x[1], reverse=True)

        # 6. Build candidate list with scores
        all_candidates = [
            {**s, "retrieval_score": score}
            for s, score in scored
        ]
        total_before = len(all_candidates)

        # 7. top_k truncation
        candidates = all_candidates[:top_k]

        # 8. Write retrieval log
        ranking_scores = [c["retrieval_score"] for c in candidates]
        filtered_out = [
            s.get("skill_code", s.get("technique_id", ""))
            for s in all_skills
            if s not in [c for c in after_rules]
        ]
        self._repo.write_retrieval_log(
            query_type=query_signature.get("query_type", "dataset_plan"),
            query_signature=query_signature,
            candidate_techniques=[c.get("skill_code", "") for c in candidates],
            ranking_scores=ranking_scores,
            filtered_out=filtered_out,
        )

        return {
            "candidates": candidates,
            "total_before_truncation": total_before,
        }
