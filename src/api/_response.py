from collections.abc import Callable
from typing import Any

from repositories.errors import RepositoryError


def ok(data: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "data": data}


def error(*, code: str, message: str, details: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    error_type = "business_error"
    if code == "VALIDATION_ERROR":
        error_type = "parameter_error"
    elif code in {"SYSTEM_ERROR"}:
        error_type = "system_error"

    return {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "type": error_type,
        },
    }


def run_with_error_mapping(fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return ok(fn())
    except RepositoryError as exc:
        return error(code=exc.code, message=exc.message)
    except ValueError as exc:
        return error(code="VALIDATION_ERROR", message=str(exc))
    except Exception as exc:  # pragma: no cover - defensive path
        return error(code="SYSTEM_ERROR", message=str(exc))
