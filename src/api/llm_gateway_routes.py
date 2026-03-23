"""LLM Gateway Management API Routes."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from api._response import error, ok


class LLMGatewayRoutes:
    """REST API handlers for LLM Gateway management.

    GET /llm-gateway/providers   – list registered providers
    GET /llm-gateway/usage       – usage report (time range + group-by)
    GET /llm-gateway/call-logs   – call logs with pagination + call_type filter
    """

    def __init__(self, *, gateway_service: Any, call_log_repo: Any) -> None:
        self._gateway = gateway_service
        self._call_log = call_log_repo

    # ── GET /llm-gateway/providers ────────────────────────────────────────────

    def get_providers(self) -> dict[str, Any]:
        def _run() -> dict[str, Any]:
            providers = self._gateway.list_providers()
            return {"providers": providers, "total": len(providers)}

        try:
            return ok(_run())
        except Exception as exc:  # pragma: no cover
            return error(code="SYSTEM_ERROR", message=str(exc))

    # ── GET /llm-gateway/usage ────────────────────────────────────────────────

    def get_usage(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = params or {}

        def _run() -> dict[str, Any]:
            start_time: datetime | None = None
            end_time: datetime | None = None
            if "start_time" in params:
                start_time = datetime.fromisoformat(params["start_time"])
            if "end_time" in params:
                end_time = datetime.fromisoformat(params["end_time"])
            usage = self._gateway.get_usage_report(
                start_time=start_time, end_time=end_time
            )
            return {"usage": usage, "total": len(usage)}

        try:
            return ok(_run())
        except (KeyError, TypeError, ValueError) as exc:
            return error(code="VALIDATION_ERROR", message=str(exc))

    # ── GET /llm-gateway/call-logs ────────────────────────────────────────────

    def get_call_logs(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = params or {}

        def _run() -> dict[str, Any]:
            call_type: str | None = params.get("call_type")
            offset = int(params.get("offset", 0))
            limit = int(params.get("limit", 50))

            if call_type is not None:
                start_time: datetime | None = None
                end_time: datetime | None = None
                if "start_time" in params:
                    start_time = datetime.fromisoformat(params["start_time"])
                if "end_time" in params:
                    end_time = datetime.fromisoformat(params["end_time"])
                logs = self._call_log.query_logs(
                    call_type=call_type,
                    start_time=start_time,
                    end_time=end_time,
                )
                # Apply pagination manually for filtered results
                paginated = logs[offset:offset + limit]
                return {"logs": paginated, "total": len(logs)}
            else:
                paginated = self._call_log.batch_query(offset=offset, limit=limit)
                total = len(self._call_log._logs)
                return {"logs": paginated, "total": total}

        try:
            return ok(_run())
        except (KeyError, TypeError, ValueError) as exc:
            return error(code="VALIDATION_ERROR", message=str(exc))
