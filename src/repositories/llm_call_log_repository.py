"""LLM call log repository – in-memory write & multi-dimensional query."""
from copy import deepcopy
from datetime import UTC, datetime
from uuid import uuid4


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _uid() -> str:
    return str(uuid4())


class LLMCallLogRepository:
    def __init__(self) -> None:
        self._logs: list[dict] = []

    def write_log(
        self, *, call_type: str, provider: str, model: str,
        input_tokens: int, output_tokens: int, latency_ms: int,
        cost_estimate: float, status: str, context_ref: str = "",
    ) -> dict:
        record = {
            "call_id": _uid(),
            "call_type": call_type,
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
            "cost_estimate": cost_estimate,
            "status": status,
            "context_ref": context_ref,
            "created_at": _now(),
        }
        self._logs.append(record)
        return deepcopy(record)

    def query_logs(
        self, *, call_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        provider: str | None = None,
    ) -> list[dict]:
        results = self._logs
        if call_type is not None:
            results = [r for r in results if r["call_type"] == call_type]
        if provider is not None:
            results = [r for r in results if r["provider"] == provider]
        if start_time is not None or end_time is not None:
            results = [r for r in results if self._in_range(r["created_at"], start_time, end_time)]
        return [deepcopy(r) for r in results]

    def aggregate_usage(
        self, *, start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[dict]:
        filtered = self._logs
        if start_time is not None or end_time is not None:
            filtered = [r for r in filtered if self._in_range(r["created_at"], start_time, end_time)]
        groups: dict[tuple[str, str], dict] = {}
        for r in filtered:
            key = (r["provider"], r["model"])
            if key not in groups:
                groups[key] = {
                    "provider": r["provider"],
                    "model": r["model"],
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_cost": 0.0,
                    "count": 0,
                }
            g = groups[key]
            g["total_input_tokens"] += r["input_tokens"]
            g["total_output_tokens"] += r["output_tokens"]
            g["total_cost"] += r["cost_estimate"]
            g["count"] += 1
        return list(groups.values())

    def batch_query(self, *, offset: int = 0, limit: int = 50) -> list[dict]:
        return [deepcopy(r) for r in self._logs[offset:offset + limit]]

    @staticmethod
    def _in_range(created_at_str: str, start: datetime | None, end: datetime | None) -> bool:
        ts = datetime.fromisoformat(created_at_str)
        if start is not None and ts < start:
            return False
        if end is not None and ts > end:
            return False
        return True
