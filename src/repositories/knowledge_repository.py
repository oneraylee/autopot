"""Knowledge repository – in-memory CRUD for 14 knowledge tables."""
from copy import deepcopy
from datetime import UTC, datetime
from uuid import uuid4

from .errors import RepositoryError, require_non_empty


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _uid() -> str:
    return str(uuid4())


class KnowledgeRepository:
    def __init__(self) -> None:
        self._sources: dict[str, dict] = {}
        self._source_dedup: set[tuple[str, str]] = set()
        self._documents: dict[str, dict] = {}
        self._doc_hashes: set[str] = set()
        self._chunks: dict[str, list[dict]] = {}  # document_id -> chunks
        self._skills: dict[str, dict] = {}
        self._skill_codes: set[str] = set()
        self._versions: dict[str, list[dict]] = {}
        self._conditions: dict[str, list[dict]] = {}
        self._actions: dict[str, list[dict]] = {}
        self._tradeoffs: dict[str, list[dict]] = {}
        self._relations: list[dict] = []
        self._evidences: dict[str, list[dict]] = {}
        self._templates: dict[str, list[dict]] = {}
        self._outcomes: dict[str, list[dict]] = {}
        self._snapshots: dict[str, dict] = {}
        self._retrieval_logs: list[dict] = []

    # ── Source ──────────────────────────────────

    def register_source(
        self, *, source_type: str, name: str, uri: str,
        author: str, license: str, trust_level: int,
    ) -> dict:
        require_non_empty(source_type, field_name="source_type")
        require_non_empty(uri, field_name="uri")
        key = (source_type, uri)
        if key in self._source_dedup:
            raise RepositoryError("CONFLICT", "source (source_type, uri) already exists")
        source_id = _uid()
        ts = _now()
        record = {
            "source_id": source_id,
            "source_type": source_type,
            "name": name,
            "uri": uri,
            "author": author,
            "license": license,
            "trust_level": trust_level,
            "status": "active",
            "created_at": ts,
            "updated_at": ts,
        }
        self._sources[source_id] = record
        self._source_dedup.add(key)
        return deepcopy(record)

    def get_source(self, source_id: str) -> dict:
        rec = self._sources.get(source_id)
        if rec is None:
            raise RepositoryError("NOT_FOUND", "source not found")
        return deepcopy(rec)

    def list_sources(self) -> list[dict]:
        return [deepcopy(s) for s in self._sources.values()]

    # ── Document ────────────────────────────────

    def import_document(
        self, *, source_id: str, title: str, doc_type: str,
        version_label: str, content_hash: str, language: str,
    ) -> dict:
        require_non_empty(content_hash, field_name="content_hash")
        if content_hash in self._doc_hashes:
            raise RepositoryError("CONFLICT", "document content_hash already exists")
        document_id = _uid()
        ts = _now()
        record = {
            "document_id": document_id,
            "source_id": source_id,
            "title": title,
            "doc_type": doc_type,
            "version_label": version_label,
            "content_hash": content_hash,
            "language": language,
            "parse_status": "pending",
            "imported_at": ts,
        }
        self._documents[document_id] = record
        self._doc_hashes.add(content_hash)
        return deepcopy(record)

    def get_document(self, document_id: str) -> dict:
        rec = self._documents.get(document_id)
        if rec is None:
            raise RepositoryError("NOT_FOUND", "document not found")
        return deepcopy(rec)

    def list_documents(self, source_id: str | None = None) -> list[dict]:
        docs = self._documents.values()
        if source_id is not None:
            docs = [d for d in docs if d["source_id"] == source_id]
        return [deepcopy(d) for d in docs]

    # ── Chunk ──────────────────────────────────

    def save_chunks(self, *, document_id: str, chunks: list[dict]) -> list[dict]:
        saved: list[dict] = []
        for c in chunks:
            chunk_id = _uid()
            record = {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "section_path": c.get("section_path", ""),
                "chunk_index": c.get("chunk_index", 0),
                "raw_text": c.get("raw_text", ""),
                "normalized_text": c.get("normalized_text", ""),
                "token_count": c.get("token_count", 0),
                "created_at": _now(),
            }
            saved.append(record)
        self._chunks.setdefault(document_id, []).extend(saved)
        return [deepcopy(r) for r in saved]

    def get_chunks_by_document(self, document_id: str) -> list[dict]:
        chunks = self._chunks.get(document_id, [])
        return [deepcopy(c) for c in sorted(chunks, key=lambda x: x["chunk_index"])]

    # ── Skill ──────────────────────────────────

    def create_skill(
        self, *, skill_code: str, name: str, category: str,
        layer: str, task_type: str, summary: str, maturity: str,
        rationale: str = "", evidence_level: str = "theory",
        default_priority: int = 5, status: str = "active",
    ) -> dict:
        require_non_empty(skill_code, field_name="skill_code")
        if skill_code in self._skill_codes:
            raise RepositoryError("CONFLICT", "skill_code already exists")
        skill_id = _uid()
        ts = _now()
        record = {
            "skill_id": skill_id,
            "skill_code": skill_code,
            "name": name,
            "category": category,
            "layer": layer,
            "task_type": task_type,
            "summary": summary,
            "rationale": rationale,
            "maturity": maturity,
            "evidence_level": evidence_level,
            "default_priority": default_priority,
            "status": status,
            "created_at": ts,
            "updated_at": ts,
        }
        self._skills[skill_id] = record
        self._skill_codes.add(skill_code)
        return deepcopy(record)

    def update_skill(self, skill_id: str, **updates: object) -> dict:
        rec = self._skills.get(skill_id)
        if rec is None:
            raise RepositoryError("NOT_FOUND", "skill not found")
        for k, v in updates.items():
            if k in rec and k not in ("skill_id", "skill_code", "created_at"):
                rec[k] = v
        rec["updated_at"] = _now()
        return deepcopy(rec)

    def get_skill(self, skill_id: str) -> dict:
        rec = self._skills.get(skill_id)
        if rec is None:
            raise RepositoryError("NOT_FOUND", "skill not found")
        return deepcopy(rec)

    def list_skills(self) -> list[dict]:
        return [deepcopy(s) for s in self._skills.values()]

    # ── Technique sub-tables ────────────────────

    def upsert_version(self, *, technique_id: str, framework: str,
                       framework_version_range: str = "", model_family: str = "",
                       implementation_mode: str = "config_only",
                       status: str = "active", compatibility_notes: str = "") -> dict:
        record = {
            "technique_version_id": _uid(),
            "technique_id": technique_id,
            "framework": framework,
            "framework_version_range": framework_version_range,
            "model_family": model_family,
            "implementation_mode": implementation_mode,
            "status": status,
            "compatibility_notes": compatibility_notes,
            "created_at": _now(),
        }
        self._versions.setdefault(technique_id, []).append(record)
        return deepcopy(record)

    def upsert_condition(self, *, technique_id: str, condition_type: str,
                         expr_json: dict, severity: str,
                         description: str = "") -> dict:
        record = {
            "condition_id": _uid(),
            "technique_id": technique_id,
            "condition_type": condition_type,
            "expr_json": expr_json,
            "severity": severity,
            "description": description,
        }
        self._conditions.setdefault(technique_id, []).append(record)
        return deepcopy(record)

    def upsert_action(self, *, technique_id: str, action_type: str,
                      target_path: str, value_json: object,
                      merge_mode: str = "replace", reversible: bool = True,
                      description: str = "") -> dict:
        record = {
            "action_id": _uid(),
            "technique_id": technique_id,
            "action_type": action_type,
            "target_path": target_path,
            "value_json": value_json,
            "merge_mode": merge_mode,
            "reversible": reversible,
            "description": description,
        }
        self._actions.setdefault(technique_id, []).append(record)
        return deepcopy(record)

    def upsert_tradeoff(self, *, technique_id: str, dimension: str,
                        effect_direction: str, magnitude: str,
                        condition_text: str = "", notes: str = "") -> dict:
        record = {
            "tradeoff_id": _uid(),
            "technique_id": technique_id,
            "dimension": dimension,
            "effect_direction": effect_direction,
            "magnitude": magnitude,
            "condition_text": condition_text,
            "notes": notes,
        }
        self._tradeoffs.setdefault(technique_id, []).append(record)
        return deepcopy(record)

    def upsert_relation(self, *, from_technique_id: str, to_technique_id: str,
                        relation_type: str, strength: str,
                        reason_code: str = "", description: str = "") -> dict:
        record = {
            "relation_id": _uid(),
            "from_technique_id": from_technique_id,
            "to_technique_id": to_technique_id,
            "relation_type": relation_type,
            "strength": strength,
            "reason_code": reason_code,
            "description": description,
            "created_at": _now(),
        }
        self._relations.append(record)
        return deepcopy(record)

    def upsert_evidence(self, *, technique_id: str, evidence_type: str,
                        source_ref: str, confidence_score: float,
                        evidence_path: str = "", notes: str = "") -> dict:
        record = {
            "evidence_id": _uid(),
            "technique_id": technique_id,
            "evidence_type": evidence_type,
            "source_ref": source_ref,
            "evidence_path": evidence_path,
            "confidence_score": confidence_score,
            "notes": notes,
            "created_at": _now(),
        }
        self._evidences.setdefault(technique_id, []).append(record)
        return deepcopy(record)

    def upsert_template(self, *, technique_id: str, template_kind: str,
                        payload_json: dict, applies_to: dict | None = None) -> dict:
        record = {
            "template_id": _uid(),
            "technique_id": technique_id,
            "template_kind": template_kind,
            "payload_json": payload_json,
            "applies_to": applies_to,
            "created_at": _now(),
        }
        self._templates.setdefault(technique_id, []).append(record)
        return deepcopy(record)

    def upsert_outcome(self, *, technique_id: str, project_id: str,
                       baseline_job_id: str, candidate_job_id: str,
                       result_summary: dict, verdict: str,
                       scenario_signature: dict | None = None) -> dict:
        record = {
            "outcome_id": _uid(),
            "technique_id": technique_id,
            "project_id": project_id,
            "baseline_job_id": baseline_job_id,
            "candidate_job_id": candidate_job_id,
            "scenario_signature": scenario_signature,
            "result_summary": result_summary,
            "verdict": verdict,
            "created_at": _now(),
        }
        self._outcomes.setdefault(technique_id, []).append(record)
        return deepcopy(record)

    def list_outcomes_by_technique(self, technique_id: str) -> list[dict]:
        return [deepcopy(o) for o in self._outcomes.get(technique_id, [])]

    def list_all_outcomes(self) -> list[dict]:
        result = []
        for outcomes in self._outcomes.values():
            result.extend(deepcopy(o) for o in outcomes)
        return result

    # ── Planning & Retrieval ────────────────────

    def create_snapshot(self, *, planning_type: str, project_id: str,
                        evidence_fingerprint: str = "",
                        selected_techniques: list | None = None,
                        rejected_techniques: list | None = None,
                        prompt_context: dict | None = None,
                        dataset_version_id: str = "",
                        baseline_job_id: str = "",
                        agent_output_ref: str = "") -> dict:
        snapshot_id = _uid()
        record = {
            "snapshot_id": snapshot_id,
            "planning_type": planning_type,
            "project_id": project_id,
            "dataset_version_id": dataset_version_id,
            "baseline_job_id": baseline_job_id,
            "evidence_fingerprint": evidence_fingerprint,
            "selected_techniques": selected_techniques or [],
            "rejected_techniques": rejected_techniques or [],
            "prompt_context": prompt_context,
            "agent_output_ref": agent_output_ref,
            "created_at": _now(),
        }
        self._snapshots[snapshot_id] = record
        return deepcopy(record)

    def get_snapshot(self, snapshot_id: str) -> dict:
        rec = self._snapshots.get(snapshot_id)
        if rec is None:
            raise RepositoryError("NOT_FOUND", "snapshot not found")
        return deepcopy(rec)

    def write_retrieval_log(self, *, query_type: str, query_signature: dict,
                            candidate_techniques: list,
                            ranking_scores: list,
                            filtered_out: list | None = None) -> dict:
        record = {
            "retrieval_id": _uid(),
            "query_type": query_type,
            "query_signature": query_signature,
            "candidate_techniques": candidate_techniques,
            "ranking_scores": ranking_scores,
            "filtered_out": filtered_out or [],
            "created_at": _now(),
        }
        self._retrieval_logs.append(record)
        return deepcopy(record)
