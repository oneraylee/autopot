"""StrategyComposerService – assembles minimal knowledge context for Agent,
writes PlanningSnapshot, controls token budget, and provides Proposal validators."""
from __future__ import annotations

import hashlib
import json
from typing import Any


# ── Token budget helpers ─────────────────────────────────────────────────────

_TOKEN_PER_TECHNIQUE_EST = 120  # rough estimate: ~120 tokens per technique entry


def _estimate_tokens(candidates: list[dict]) -> int:
    return len(candidates) * _TOKEN_PER_TECHNIQUE_EST


def _trim_to_budget(candidates: list[dict], token_budget: int) -> list[dict]:
    """Trim candidate list to fit within token_budget.

    Trim order: low priority → low score (rationale already brief here)
    """
    # Already sorted by score descending; just truncate from the tail
    max_count = max(1, token_budget // _TOKEN_PER_TECHNIQUE_EST)
    return candidates[:max_count]


# ── Evidence fingerprint ─────────────────────────────────────────────────────

def _make_fingerprint(data: Any) -> str:
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


# ── StrategyComposerService ──────────────────────────────────────────────────

class StrategyComposerService:
    """Assemble Agent knowledge context from retrieval + conflict resolution.

    Responsibilities:
        - compose_planning_context  (dataset planning phase)
        - compose_diagnosis_context (post-training diagnosis phase)
        - create_snapshot           (audit record)
    """

    _MIN_CANDIDATES = 5
    _MAX_CANDIDATES = 12

    def __init__(
        self,
        *,
        knowledge_repo: Any,
        retrieval_service: Any,
        conflict_service: Any,
    ) -> None:
        self._repo = knowledge_repo
        self._retrieval = retrieval_service
        self._conflict = conflict_service

    # ── Public API ──────────────────────────────────────────────────────────

    def compose_planning_context(
        self,
        *,
        dataset_report: dict[str, Any],
        project_constraints: dict[str, Any],
        project_id: str = "",
        dataset_version_id: str = "",
        top_k: int = 12,
        token_budget: int | None = None,
    ) -> dict[str, Any]:
        """Generate SkillContext for the dataset planning phase."""
        # 1. Build query signature
        sig = self._retrieval.build_query_signature_from_dataset(dataset_report)
        sig["query_type"] = "dataset_plan"

        # 2. Hybrid retrieval
        search_result = self._retrieval.search(sig, top_k=top_k)
        candidates = search_result["candidates"]

        # 3. Conflict resolution
        conflict_result = self._conflict.resolve(
            candidates, runtime_constraints=project_constraints
        )
        accepted_ids = set(conflict_result["accepted"])
        accepted = [c for c in candidates if c.get("skill_code") in accepted_ids]
        rejected = [c for c in candidates if c.get("skill_code") not in accepted_ids]

        # 4. Candidate count control
        accepted = accepted[:self._MAX_CANDIDATES]
        if len(accepted) < self._MIN_CANDIDATES:
            # Relax: include top candidates regardless
            accepted = candidates[:self._MIN_CANDIDATES]
            rejected = candidates[self._MIN_CANDIDATES:]

        # 5. Token budget trim
        if token_budget is not None:
            accepted = _trim_to_budget(accepted, token_budget)

        # 6. Build context
        evidence_fingerprint = _make_fingerprint({
            "dataset_report": dataset_report,
            "project_constraints": project_constraints,
        })

        conflict_summary = [
            {"technique_id": r["technique_id"], "reason_code": r["reason_code"]}
            for r in conflict_result["rejected"]
        ]

        prompt_context = {
            "candidate_techniques": accepted,
            "rejected_techniques": rejected,
            "conflict_summary": conflict_summary,
        }

        # 7. Write snapshot
        snapshot = self._repo.create_snapshot(
            planning_type="dataset_plan",
            project_id=project_id,
            dataset_version_id=dataset_version_id,
            evidence_fingerprint=evidence_fingerprint,
            selected_techniques=[c.get("skill_code", "") for c in accepted],
            rejected_techniques=[c.get("skill_code", "") for c in rejected],
            prompt_context=prompt_context,
        )

        return {
            "candidate_techniques": accepted,
            "rejected_techniques": rejected,
            "conflict_summary": conflict_summary,
            "snapshot_id": snapshot["snapshot_id"],
            "evidence_fingerprint": evidence_fingerprint,
        }

    def compose_diagnosis_context(
        self,
        *,
        evidence_pack: dict[str, Any],
        project_constraints: dict[str, Any],
        project_id: str = "",
        baseline_job_id: str = "",
        top_k: int = 12,
        token_budget: int | None = None,
    ) -> dict[str, Any]:
        """Generate SkillContext for the post-training diagnosis phase."""
        sig = self._retrieval.build_query_signature_from_evidence(evidence_pack)
        sig["query_type"] = "next_experiments"

        search_result = self._retrieval.search(sig, top_k=top_k)
        candidates = search_result["candidates"]

        conflict_result = self._conflict.resolve(
            candidates, runtime_constraints=project_constraints
        )
        accepted_ids = set(conflict_result["accepted"])
        accepted = [c for c in candidates if c.get("skill_code") in accepted_ids]
        rejected = [c for c in candidates if c.get("skill_code") not in accepted_ids]

        accepted = accepted[:self._MAX_CANDIDATES]
        if len(accepted) < self._MIN_CANDIDATES:
            accepted = candidates[:self._MIN_CANDIDATES]
            rejected = candidates[self._MIN_CANDIDATES:]

        if token_budget is not None:
            accepted = _trim_to_budget(accepted, token_budget)

        evidence_fingerprint = _make_fingerprint({
            "evidence_pack": evidence_pack,
            "project_constraints": project_constraints,
        })

        conflict_summary = [
            {"technique_id": r["technique_id"], "reason_code": r["reason_code"]}
            for r in conflict_result["rejected"]
        ]

        prompt_context = {
            "candidate_techniques": accepted,
            "rejected_techniques": rejected,
            "conflict_summary": conflict_summary,
        }

        snapshot = self._repo.create_snapshot(
            planning_type="next_experiments",
            project_id=project_id,
            baseline_job_id=baseline_job_id,
            evidence_fingerprint=evidence_fingerprint,
            selected_techniques=[c.get("skill_code", "") for c in accepted],
            rejected_techniques=[c.get("skill_code", "") for c in rejected],
            prompt_context=prompt_context,
        )

        return {
            "candidate_techniques": accepted,
            "rejected_techniques": rejected,
            "conflict_summary": conflict_summary,
            "snapshot_id": snapshot["snapshot_id"],
            "evidence_fingerprint": evidence_fingerprint,
        }


# ── ProposalKnowledgeValidator ───────────────────────────────────────────────

class ProposalKnowledgeValidator:
    """Four enhanced validators for Proposal validation.

    validate_technique_refs      – check skill_refs exist in known catalogue
    validate_technique_combination – check for conflicts
    validate_resource_budget      – check resource budget
    validate_version_compatibility – check version compatibility
    """

    def __init__(self, *, known_skill_codes: list[str]) -> None:
        self._known: set[str] = set(known_skill_codes)

    def validate_technique_refs(
        self, *, experiments: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Check that all technique_refs in experiments are in the known catalogue."""
        unknown: list[str] = []
        for exp in experiments:
            for ref in exp.get("technique_refs", []):
                if ref not in self._known:
                    unknown.append(ref)
        if unknown:
            return {"ok": False, "error": f"unknown technique_refs: {unknown}"}
        return {"ok": True, "error": None}

    def validate_technique_combination(
        self,
        *,
        experiments: list[dict[str, Any]],
        conflict_service: Any,
        technique_lookup: dict[str, Any],
    ) -> dict[str, Any]:
        """Check that combined technique_refs have no hard conflicts."""
        all_refs: list[str] = []
        for exp in experiments:
            all_refs.extend(exp.get("technique_refs", []))
        unique_refs = list(dict.fromkeys(all_refs))  # deduplicate preserving order
        techniques = [
            technique_lookup[ref]
            for ref in unique_refs
            if ref in technique_lookup
        ]
        if not techniques:
            return {"ok": True, "error": None}
        result = conflict_service.resolve(techniques)
        if result["rejected"]:
            return {
                "ok": False,
                "error": f"conflict detected: {[r['technique_id'] for r in result['rejected']]}",
                "conflicts": result["rejected"],
            }
        return {"ok": True, "error": None}

    def validate_resource_budget(
        self,
        *,
        experiments: list[dict[str, Any]],
        constraints: dict[str, Any],
        technique_lookup: dict[str, Any],
        conflict_service: Any,
    ) -> dict[str, Any]:
        """Check that combined resources don't exceed budget."""
        all_refs: list[str] = []
        for exp in experiments:
            all_refs.extend(exp.get("technique_refs", []))
        unique_refs = list(dict.fromkeys(all_refs))
        techniques = [
            technique_lookup[ref]
            for ref in unique_refs
            if ref in technique_lookup
        ]
        result = conflict_service.validate_combination(
            techniques=techniques, constraints=constraints
        )
        if not result["ok"]:
            return {
                "ok": False,
                "error": f"resource budget exceeded: {result['violation']}",
                "total": result["total"],
            }
        return {"ok": True, "error": None, "warnings": result["warnings"]}

    def validate_version_compatibility(
        self,
        *,
        experiments: list[dict[str, Any]],
        constraints: dict[str, Any],
        technique_lookup: dict[str, Any],
        conflict_service: Any,
    ) -> dict[str, Any]:
        """Check version compatibility for all technique_refs."""
        all_refs: list[str] = []
        for exp in experiments:
            all_refs.extend(exp.get("technique_refs", []))
        unique_refs = list(dict.fromkeys(all_refs))
        techniques = [
            technique_lookup[ref]
            for ref in unique_refs
            if ref in technique_lookup
        ]
        result = conflict_service.resolve(
            techniques, runtime_constraints=constraints
        )
        version_rejected = [
            r for r in result["rejected"]
            if r.get("reason_code") == "version_conflict"
        ]
        if version_rejected:
            return {
                "ok": False,
                "error": f"version incompatible: {[r['technique_id'] for r in version_rejected]}",
                "rejected": version_rejected,
            }
        return {"ok": True, "error": None}
