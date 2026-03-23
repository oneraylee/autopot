"""Knowledge System API Routes – Source / Document / Technique / Retrieval endpoints."""
from __future__ import annotations

from typing import Any

from api._response import error, ok, run_with_error_mapping
from repositories.errors import RepositoryError
from services.knowledge_ingestion_service import IngestionError
from services.knowledge_registry_service import RegistryError


class KnowledgeRoutes:
    """REST API handlers for the knowledge system."""

    def __init__(
        self,
        *,
        ingestion_service: Any,
        registry_service: Any,
        retrieval_service: Any | None = None,
        conflict_service: Any | None = None,
        composer_service: Any | None = None,
        outcome_tracker_service: Any | None = None,
    ) -> None:
        self._ingest = ingestion_service
        self._registry = registry_service
        self._retrieval = retrieval_service
        self._conflict = conflict_service
        self._composer = composer_service
        self._outcome_tracker = outcome_tracker_service

    # ── POST /knowledge/sources ──────────────────────────────────────────────

    def post_sources(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            source = self._ingest.register_source(
                source_type=payload["source_type"],
                name=payload.get("name", ""),
                uri=payload["uri"],
                author=payload.get("author", ""),
                license=payload.get("license", ""),
                trust_level=int(payload.get("trust_level", 3)),
            )
            return source

        try:
            return ok(_run())
        except RepositoryError as exc:
            return error(code=exc.code, message=exc.message)
        except IngestionError as exc:
            return error(code=exc.code, message=exc.message)
        except (KeyError, TypeError, ValueError) as exc:
            return error(code="VALIDATION_ERROR", message=str(exc))

    # ── POST /knowledge/documents/import ────────────────────────────────────

    def post_documents_import(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            doc = self._ingest.import_document(
                source_id=payload["source_id"],
                title=payload.get("title", ""),
                doc_type=payload["doc_type"],
                version_label=payload.get("version_label", ""),
                content=payload.get("content", ""),
                language=payload.get("language", "zh"),
            )
            return doc

        try:
            return ok(_run())
        except RepositoryError as exc:
            return error(code=exc.code, message=exc.message)
        except IngestionError as exc:
            return error(code=exc.code, message=exc.message)
        except (KeyError, TypeError, ValueError) as exc:
            return error(code="VALIDATION_ERROR", message=str(exc))

    # ── POST /knowledge/techniques/extract ──────────────────────────────────

    def post_techniques_extract(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            document_id = payload["document_id"]
            # Parse the document first if not already parsed
            self._ingest.parse_document(document_id)
            candidates = self._ingest.extract_skills(document_id)
            return {"document_id": document_id, "candidates": candidates}

        try:
            return ok(_run())
        except RepositoryError as exc:
            return error(code=exc.code, message=exc.message)
        except IngestionError as exc:
            return error(code=exc.code, message=exc.message)
        except (KeyError, TypeError, ValueError) as exc:
            return error(code="VALIDATION_ERROR", message=str(exc))

    # ── GET /knowledge/techniques ────────────────────────────────────────────

    def get_techniques(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        filters: dict[str, Any] = {}
        if params:
            for key in ("category", "layer", "task_type", "maturity"):
                if key in params:
                    filters[key] = params[key]

        def _run() -> dict[str, Any]:
            techniques = self._registry.list_skills(**filters)
            return {"techniques": techniques, "total": len(techniques)}

        try:
            return ok(_run())
        except RepositoryError as exc:
            return error(code=exc.code, message=exc.message)
        except (TypeError, ValueError) as exc:
            return error(code="VALIDATION_ERROR", message=str(exc))

    # ── GET /knowledge/techniques/{id} ───────────────────────────────────────

    def get_technique_detail(self, technique_id: str) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            return self._registry.get_skill(technique_id)

        try:
            return ok(_run())
        except RepositoryError as exc:
            return error(code=exc.code, message=exc.message)

    # ── POST /knowledge/techniques/{id}/publish ──────────────────────────────

    def post_technique_publish(
        self,
        technique_id: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        target_status: str | None = None
        if payload:
            target_status = payload.get("target_status")

        try:
            result = self._registry.publish_skill(technique_id, target_status=target_status)
            return ok(result)
        except RegistryError as exc:
            code = exc.code if exc.code else "INVALID_TRANSITION"
            return error(code=code, message=exc.message)
        except RepositoryError as exc:
            return error(code=exc.code, message=exc.message)

    # ── POST /knowledge/retrieval/search ─────────────────────────────────────

    def post_retrieval_search(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if self._retrieval is None:
                raise ValueError("retrieval_service not configured")
            query_sig = payload.get("query_signature")
            if not isinstance(query_sig, dict):
                raise ValueError("query_signature is required")
            top_k = int(payload.get("limit", 20))
            result = self._retrieval.search(query_sig, top_k=top_k)
            return {
                "candidates": result["candidates"],
                "total": result.get("total_before_truncation", len(result["candidates"])),
            }

        try:
            return ok(_run())
        except (KeyError, TypeError, ValueError) as exc:
            return error(code="VALIDATION_ERROR", message=str(exc))

    # ── POST /knowledge/retrieval/resolve-conflicts ───────────────────────────

    def post_resolve_conflicts(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if self._conflict is None:
                raise ValueError("conflict_service not configured")
            technique_ids = payload.get("technique_ids", [])
            if not isinstance(technique_ids, list):
                raise ValueError("technique_ids must be a list")
            runtime_constraints = payload.get("runtime_constraints", {})
            # Convert ids to minimal technique dicts for the service
            techniques = [{"technique_id": tid} for tid in technique_ids]
            result = self._conflict.resolve(
                techniques, runtime_constraints=runtime_constraints
            )
            return result

        try:
            return ok(_run())
        except (KeyError, TypeError, ValueError) as exc:
            return error(code="VALIDATION_ERROR", message=str(exc))

    # ── POST /knowledge/retrieval/compose-context ─────────────────────────────

    def post_compose_context(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if self._composer is None:
                raise ValueError("composer_service not configured")
            planning_type = payload.get("planning_type", "dataset_plan")
            project_id = payload.get("project_id", "")
            dataset_report = payload.get("dataset_report", {})
            project_constraints = payload.get("project_constraints", {})
            top_k = int(payload.get("top_k", 8))
            token_budget = payload.get("token_budget")

            if planning_type == "dataset_plan":
                ctx = self._composer.compose_planning_context(
                    dataset_report=dataset_report,
                    project_constraints=project_constraints,
                    project_id=project_id,
                    top_k=top_k,
                    token_budget=token_budget,
                )
            else:
                evidence_pack = payload.get("evidence_pack", {})
                baseline_job_id = payload.get("baseline_job_id", "")
                ctx = self._composer.compose_diagnosis_context(
                    evidence_pack=evidence_pack,
                    project_constraints=project_constraints,
                    project_id=project_id,
                    baseline_job_id=baseline_job_id,
                    top_k=top_k,
                    token_budget=token_budget,
                )

            return {
                "snapshot_id": ctx["snapshot_id"],
                "context": {
                    "candidate_techniques": ctx["candidate_techniques"],
                    "rejected_techniques": ctx["rejected_techniques"],
                    "conflict_summary": ctx["conflict_summary"],
                },
            }

        try:
            return ok(_run())
        except (KeyError, TypeError, ValueError) as exc:
            return error(code="VALIDATION_ERROR", message=str(exc))

    # ── POST /knowledge/outcomes ──────────────────────────────────────────────

    def post_outcomes(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if self._outcome_tracker is None:
                raise ValueError("outcome_tracker_service not configured")
            technique_id = payload.get("technique_id")
            baseline_job_id = payload.get("baseline_job_id")
            candidate_job_id = payload.get("candidate_job_id")
            verdict = payload.get("verdict")
            result_summary = payload.get("result_summary")
            if not all([technique_id, baseline_job_id, candidate_job_id, verdict, result_summary]):
                raise ValueError(
                    "technique_id, baseline_job_id, candidate_job_id, verdict, result_summary are required"
                )
            # Validate technique exists
            self._registry.get_skill(technique_id)
            return self._outcome_tracker.record_outcome(
                technique_id=technique_id,
                project_id=payload.get("project_id", ""),
                baseline_job_id=baseline_job_id,
                candidate_job_id=candidate_job_id,
                result_summary=result_summary,
                verdict=verdict,
                scenario_signature=payload.get("scenario_signature"),
            )

        try:
            return ok(_run())
        except RepositoryError as exc:
            return error(code=exc.code, message=exc.message)
        except (KeyError, TypeError, ValueError) as exc:
            return error(code="VALIDATION_ERROR", message=str(exc))

    # ── POST /datasets/versions/{id}/knowledge-plan ───────────────────────────

    def post_dataset_knowledge_plan(
        self, version_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if self._composer is None:
                raise ValueError("composer_service not configured")
            ctx = self._composer.compose_planning_context(
                dataset_report=payload.get("dataset_report", {}),
                project_constraints=payload.get("project_constraints", {}),
                project_id=payload.get("project_id", ""),
                top_k=int(payload.get("top_k", 8)),
                token_budget=payload.get("token_budget"),
            )
            return {
                "snapshot_id": ctx["snapshot_id"],
                "dataset_version_id": version_id,
                "context": {
                    "candidate_techniques": ctx["candidate_techniques"],
                    "rejected_techniques": ctx["rejected_techniques"],
                },
            }

        try:
            return ok(_run())
        except (KeyError, TypeError, ValueError) as exc:
            return error(code="VALIDATION_ERROR", message=str(exc))

    # ── POST /jobs/{id}/knowledge-diagnosis ───────────────────────────────────

    def post_job_knowledge_diagnosis(
        self, job_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if self._composer is None:
                raise ValueError("composer_service not configured")
            ctx = self._composer.compose_diagnosis_context(
                evidence_pack=payload.get("evidence_pack", {}),
                project_constraints=payload.get("project_constraints", {}),
                project_id=payload.get("project_id", ""),
                baseline_job_id=job_id,
                top_k=int(payload.get("top_k", 8)),
                token_budget=payload.get("token_budget"),
            )
            return {
                "snapshot_id": ctx["snapshot_id"],
                "job_id": job_id,
                "context": {
                    "candidate_techniques": ctx["candidate_techniques"],
                    "rejected_techniques": ctx["rejected_techniques"],
                },
            }

        try:
            return ok(_run())
        except (KeyError, TypeError, ValueError) as exc:
            return error(code="VALIDATION_ERROR", message=str(exc))

    # ── POST /proposals/validate-with-knowledge ───────────────────────────────

    def post_validate_with_knowledge(self, payload: dict[str, Any]) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            if self._conflict is None:
                raise ValueError("conflict_service not configured")
            techniques = payload.get("techniques", [])
            if not techniques:
                technique_ids = payload.get("technique_ids", [])
                techniques = [{"technique_id": tid} for tid in technique_ids]
            runtime_constraints = payload.get("runtime_constraints", {})
            validation = self._conflict.validate_combination(
                techniques=techniques,
                constraints=runtime_constraints,
            )
            return {"validation": validation, "ok": validation["ok"]}

        try:
            result = _run()
            if not result["ok"]:
                return error(
                    code="CONFLICT",
                    message=f"resource budget exceeded: {result['validation'].get('violation')}",
                )
            return ok({"validation": result["validation"]})
        except (KeyError, TypeError, ValueError) as exc:
            return error(code="VALIDATION_ERROR", message=str(exc))

