"""Knowledge System API Routes – Source / Document / Technique endpoints."""
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
    ) -> None:
        self._ingest = ingestion_service
        self._registry = registry_service

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
