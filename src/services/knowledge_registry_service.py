"""Knowledge Registry Service – Skill CRUD, publish state machine, relation/template management."""
from __future__ import annotations

from typing import Any


class RegistryError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


# Allowed publish status transitions
# {current_status: [allowed_next_statuses]}
_PUBLISH_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["reviewed"],
    "reviewed": ["verified", "draft"],
    "verified": ["deprecated"],
    "deprecated": [],
}

# publish_skill default forward transitions
_FORWARD_TRANSITION: dict[str, str] = {
    "draft": "reviewed",
    "reviewed": "verified",
}


class KnowledgeRegistryService:
    """Manages skill cards: CRUD, publish state machine, relations, and templates."""

    def __init__(self, *, knowledge_repo: Any) -> None:
        self._repo = knowledge_repo
        # Track publish_status separately from repo's 'status' field
        self._publish_status: dict[str, str] = {}

    # ── Skill CRUD ───────────────────────────────────────────────────────────

    def create_skill(
        self,
        *,
        skill_code: str,
        name: str,
        category: str,
        layer: str,
        task_type: str,
        summary: str,
        maturity: str,
        rationale: str = "",
        evidence_level: str = "theory",
        default_priority: int = 5,
    ) -> dict:
        skill = self._repo.create_skill(
            skill_code=skill_code,
            name=name,
            category=category,
            layer=layer,
            task_type=task_type,
            summary=summary,
            maturity=maturity,
            rationale=rationale,
            evidence_level=evidence_level,
            default_priority=default_priority,
        )
        self._publish_status[skill["skill_id"]] = "draft"
        skill["publish_status"] = "draft"
        return skill

    def update_skill(self, skill_id: str, **updates: object) -> dict:
        skill = self._repo.update_skill(skill_id, **updates)
        skill["publish_status"] = self._publish_status.get(skill_id, "draft")
        return skill

    def get_skill(self, skill_id: str) -> dict:
        skill = self._repo.get_skill(skill_id)
        skill["publish_status"] = self._publish_status.get(skill_id, "draft")
        return skill

    # ── Publish state machine ────────────────────────────────────────────────

    def publish_skill(self, skill_id: str, *, target_status: str | None = None) -> dict:
        """
        Advance skill publish status.

        If target_status is None, use the default forward transition.
        If target_status is provided, validate it is an allowed transition from current state.
        """
        skill = self._repo.get_skill(skill_id)
        current = self._publish_status.get(skill_id, "draft")
        allowed = _PUBLISH_TRANSITIONS.get(current, [])

        if target_status is not None:
            if target_status not in allowed:
                raise RegistryError(
                    "INVALID_TRANSITION",
                    f"invalid transition from '{current}' to '{target_status}'; allowed: {allowed}",
                )
            next_status = target_status
        else:
            next_status = _FORWARD_TRANSITION.get(current)
            if next_status is None:
                raise RegistryError(
                    "INVALID_TRANSITION",
                    f"no forward transition available from '{current}'",
                )

        self._publish_status[skill_id] = next_status
        skill["publish_status"] = next_status
        return skill

    # ── List with filtering ──────────────────────────────────────────────────

    def list_skills(
        self,
        *,
        category: str | None = None,
        layer: str | None = None,
        task_type: str | None = None,
        maturity: str | None = None,
    ) -> list[dict]:
        skills = self._repo.list_skills()
        if category is not None:
            skills = [s for s in skills if s.get("category") == category]
        if layer is not None:
            skills = [s for s in skills if s.get("layer") == layer]
        if task_type is not None:
            skills = [s for s in skills if s.get("task_type") == task_type]
        if maturity is not None:
            skills = [s for s in skills if s.get("maturity") == maturity]
        for s in skills:
            s["publish_status"] = self._publish_status.get(s["skill_id"], "draft")
        return skills

    # ── Relations ────────────────────────────────────────────────────────────

    def upsert_relation(
        self,
        *,
        from_technique_id: str,
        to_technique_id: str,
        relation_type: str,
        strength: str,
        reason_code: str = "",
        description: str = "",
    ) -> dict:
        return self._repo.upsert_relation(
            from_technique_id=from_technique_id,
            to_technique_id=to_technique_id,
            relation_type=relation_type,
            strength=strength,
            reason_code=reason_code,
            description=description,
        )

    def get_relations(self, technique_id: str) -> list[dict]:
        """Return all relations where technique_id is from OR to (bidirectional)."""
        return [
            r for r in self._repo._relations
            if r["from_technique_id"] == technique_id or r["to_technique_id"] == technique_id
        ]

    # ── Templates ────────────────────────────────────────────────────────────

    def upsert_template(
        self,
        *,
        technique_id: str,
        template_kind: str,
        payload_json: dict,
        applies_to: dict | None = None,
    ) -> dict:
        return self._repo.upsert_template(
            technique_id=technique_id,
            template_kind=template_kind,
            payload_json=payload_json,
            applies_to=applies_to,
        )

    def get_templates(self, technique_id: str) -> list[dict]:
        return self._repo._templates.get(technique_id, [])
