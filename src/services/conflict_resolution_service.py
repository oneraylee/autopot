"""ConflictResolutionService – JSON DSL rule engine, five conflict types,
priority ordering, resource budget validation."""
from __future__ import annotations

from typing import Any


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_id(technique: dict) -> str:
    """Return the canonical id of a technique dict.

    Supports both 'technique_id' (conflict DSL usage) and 'skill_code'
    (KnowledgeRepository skill format).
    """
    return technique.get("technique_id") or technique.get("skill_code", "")


# ── Priority order (安全 > KPI > 资源 > 结构 > 版本 > soft) ─────────────────

_PRIORITY_ORDER = [
    "safety",
    "kpi_hard",
    "resource_hard",
    "structural_hard",
    "version",
    "soft_tradeoff",
]


# ── DSL Rule Engine ──────────────────────────────────────────────────────────

class DSLRuleEngine:
    """Evaluates JSON-DSL conflict rules against a set of technique IDs."""

    def __init__(self, *, rules: list[dict]) -> None:
        self.rules: list[dict] = list(rules)

    def evaluate(self, techniques: list[dict]) -> list[dict]:
        """Return list of conflict events for the given technique list.

        Each conflict event:
            {"technique_id": str, "reason_code": str, "reason": str, "severity": str}
        """
        tech_ids = {_get_id(t) for t in techniques}
        events: list[dict] = []

        for rule in self.rules:
            rule_type = rule.get("rule_type", "incompatible_with")
            severity = rule.get("severity", "hard")
            because = rule.get("because", {})
            reason_code = because.get("reason_code", rule_type)
            message = because.get("message", "")

            condition = rule.get("if", {})
            matched_ids = self._eval_condition(condition, tech_ids)
            if matched_ids:
                matched_list = sorted(
                    matched_ids,
                    key=lambda x: list(tech_ids).index(x) if x in tech_ids else 0,
                )
                if rule_type == "objective":
                    # Objective violations: reject ALL matching techniques
                    reject_ids = matched_list
                else:
                    # incompatible_with / structural: keep first, reject rest
                    reject_ids = matched_list[1:]
                for tech_id in reject_ids:
                    events.append({
                        "technique_id": tech_id,
                        "reason_code": reason_code,
                        "reason": message,
                        "severity": severity,
                    })

        return events

    def _eval_condition(self, condition: dict, tech_ids: set[str]) -> set[str]:
        """Evaluate a condition dict against available technique IDs.

        Returns the set of technique IDs involved if condition is satisfied,
        else empty set.
        """
        if "all" in condition:
            involved: set[str] = set()
            for sub in condition["all"]:
                tech = sub.get("technique")
                if tech and tech not in tech_ids:
                    return set()  # not all conditions met
                if tech:
                    involved.add(tech)
            return involved
        if "any" in condition:
            for sub in condition["any"]:
                tech = sub.get("technique")
                if tech and tech in tech_ids:
                    return {tech}
        return set()


# ── ConflictResolutionService ────────────────────────────────────────────────

class ConflictResolutionService:
    """Five-type conflict resolution with DSL rule engine and resource budget
    validation."""

    def __init__(self, *, rules: list[dict] | None = None) -> None:
        self._dsl_engine = DSLRuleEngine(rules=rules or [])

    # ── Public API ──────────────────────

    def resolve(
        self,
        techniques: list[dict],
        *,
        runtime_constraints: dict[str, Any] | None = None,
    ) -> dict:
        """Evaluate all conflict types and return accepted/rejected/warnings.

        Args:
            techniques: list of technique dicts (must have 'technique_id').
            runtime_constraints: e.g. {"gpu_mem_gb": 24, "framework_version": "8.0",
                "training_stage": "initial", "latency_ms_max": 25}.

        Returns:
            {"accepted": [...], "rejected": [...], "warnings": [...]}
        """
        constraints = runtime_constraints or {}
        rejected_map: dict[str, dict] = {}  # technique_id -> rejection info
        warnings: list[dict] = []

        # 1. DSL rule evaluation (structural / objective / incompatible_with)
        dsl_events = self._dsl_engine.evaluate(techniques)
        for event in dsl_events:
            tid = event["technique_id"]
            if event["severity"] == "soft":
                warnings.append(event)
            else:
                if tid not in rejected_map:
                    rejected_map[tid] = {
                        "technique_id": tid,
                        "reason_code": event["reason_code"],
                        "reason": event["reason"],
                    }

        # 2. Remaining conflicts checked per-technique
        for tech in techniques:
            tid = _get_id(tech)
            if tid in rejected_map:
                continue  # already rejected

            # 2a. Version conflict
            if "framework_version" in constraints:
                req_min = tech.get("framework_version_min")
                if req_min and self._version_lt(constraints["framework_version"], req_min):
                    rejected_map[tid] = {
                        "technique_id": tid,
                        "reason_code": "version_conflict",
                        "reason": (
                            f"requires framework >= {req_min}, "
                            f"current is {constraints['framework_version']}"
                        ),
                    }
                    continue

            # 2b. Lifecycle / stage conflict
            applicable_stage = tech.get("applicable_stage")
            if applicable_stage and "training_stage" in constraints:
                if applicable_stage != constraints["training_stage"]:
                    rejected_map[tid] = {
                        "technique_id": tid,
                        "reason_code": "lifecycle_conflict",
                        "reason": (
                            f"only applicable to stage '{applicable_stage}', "
                            f"current stage is '{constraints['training_stage']}'"
                        ),
                    }
                    continue

        # 3. Resource conflict (cumulative; reject the last one that pushes over)
        gpu_budget = constraints.get("gpu_mem_gb")
        if gpu_budget is not None:
            active_techniques = [
                t for t in techniques if _get_id(t) not in rejected_map
            ]
            cumulative_gpu = 0.0
            for tech in active_techniques:
                resources = tech.get("resources", {})
                gpu_req = float(resources.get("gpu_mem_gb", 0.0))
                cumulative_gpu += gpu_req
                if cumulative_gpu > float(gpu_budget):
                    tid = _get_id(tech)
                    rejected_map[tid] = {
                        "technique_id": tid,
                        "reason_code": "resource_conflict",
                        "reason": (
                            f"cumulative gpu_mem_gb {cumulative_gpu:.1f} "
                            f"exceeds budget {gpu_budget}"
                        ),
                    }

        accepted = [
            _get_id(t)
            for t in techniques
            if _get_id(t) not in rejected_map
        ]
        return {
            "accepted": accepted,
            "rejected": list(rejected_map.values()),
            "warnings": warnings,
        }

    def validate_combination(
        self,
        *,
        techniques: list[dict],
        constraints: dict[str, Any],
    ) -> dict:
        """Validate resource budget for a set of techniques.

        Returns:
            {"ok": bool, "warnings": list, "violation": str | None,
             "total": dict}
        """
        gpu_budget = float(constraints.get("gpu_mem_gb", 0.0))
        total_gpu = sum(
            float(t.get("resources", {}).get("gpu_mem_gb", 0.0))
            for t in techniques
        )

        violation: str | None = None
        warnings: list[str] = []

        if gpu_budget > 0:
            ratio = total_gpu / gpu_budget
            if ratio > 1.0:
                violation = "gpu_mem_gb"
            elif ratio > 0.8:
                warnings.append(
                    f"gpu usage {total_gpu:.1f}/{gpu_budget:.1f} GB "
                    f"({ratio * 100:.0f}%) is near budget limit"
                )

        return {
            "ok": violation is None,
            "warnings": warnings,
            "violation": violation,
            "total": {"gpu_mem_gb": total_gpu},
        }

    @staticmethod
    def conflict_priority_order() -> list[str]:
        """Return the canonical conflict priority ordering."""
        return list(_PRIORITY_ORDER)

    # ── Helpers ────────────────────────

    @staticmethod
    def _version_lt(current: str, required: str) -> bool:
        """Return True if current version < required version."""
        def _parse(v: str) -> tuple[int, ...]:
            try:
                return tuple(int(x) for x in v.split("."))
            except ValueError:
                return (0,)

        return _parse(current) < _parse(required)
