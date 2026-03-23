import json
from typing import Any

from common.domain_types import ErrorCode, SkillCategory


_MAX_PAYLOAD_BYTES = 1024 * 1024


def _error(path: str, error_type: str, message: str) -> dict[str, str]:
    return {
        "path": path,
        "error_type": error_type,
        "message": message,
    }


def _ok() -> dict[str, Any]:
    return {"ok": True, "errors": []}


def _fail(*errors: dict[str, str], error_code: ErrorCode = ErrorCode.EVAL_FAILED) -> dict[str, Any]:
    return {
        "ok": False,
        "error_code": error_code.value,
        "errors": list(errors),
    }


def _is_non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def validate_eval_report(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return _fail(_error("$", "type_error", "eval_report must be an object"))

    if "overall" not in data:
        return _fail(_error("overall", "missing_required", "overall is required"))
    if not isinstance(data["overall"], dict):
        return _fail(_error("overall", "type_error", "overall must be object"))

    overall = data["overall"]
    if "business_kpi" not in overall:
        return _fail(_error("overall.business_kpi", "missing_required", "business_kpi is required"))
    if not isinstance(overall["business_kpi"], (int, float)):
        return _fail(_error("overall.business_kpi", "type_error", "business_kpi must be number"))

    if "kpi_components" not in overall:
        return _fail(_error("overall.kpi_components", "missing_required", "kpi_components is required"))
    if not isinstance(overall["kpi_components"], list):
        return _fail(_error("overall.kpi_components", "type_error", "kpi_components must be list"))

    if "by_scene" not in data:
        return _fail(_error("by_scene", "missing_required", "by_scene is required"))
    if not isinstance(data["by_scene"], list):
        return _fail(_error("by_scene", "type_error", "by_scene must be list"))

    if data["by_scene"]:
        first_scene = data["by_scene"][0]
        if not isinstance(first_scene, dict):
            return _fail(_error("by_scene[0]", "type_error", "scene item must be object"))
        if not _is_non_empty_str(first_scene.get("scene")):
            return _fail(_error("by_scene[0].scene", "invalid_enum", "scene must be non-empty string"))

    return _ok()


def validate_evidence_pack(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return _fail(_error("$", "type_error", "evidence_pack must be an object"))

    if "kpi_config" not in data:
        return _fail(_error("kpi_config", "missing_required", "kpi_config is required"))
    if not isinstance(data["kpi_config"], dict):
        return _fail(_error("kpi_config", "type_error", "kpi_config must be object"))

    if "index_paths" not in data:
        return _fail(_error("index_paths", "missing_required", "index_paths is required"))
    if not isinstance(data["index_paths"], dict):
        return _fail(_error("index_paths", "type_error", "index_paths must be object"))

    return _ok()


def validate_next_experiments(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return _fail(_error("$", "type_error", "next_experiments must be an object"))

    experiments = data.get("experiments")
    if not isinstance(experiments, list):
        return _fail(_error("experiments", "type_error", "experiments must be list"))
    if not experiments:
        return _fail(_error("experiments", "missing_required", "experiments cannot be empty"))

    first = experiments[0]
    if not isinstance(first, dict):
        return _fail(_error("experiments[0]", "type_error", "experiment must be object"))

    errors: list[dict[str, str]] = []
    if not _is_non_empty_str(first.get("name")):
        errors.append(_error("experiments[0].name", "missing_required", "name is required"))
    if not isinstance(first.get("changes"), list):
        errors.append(_error("experiments[0].changes", "missing_required", "changes is required"))
    if not _is_non_empty_str(first.get("expected")):
        errors.append(_error("experiments[0].expected", "missing_required", "expected is required"))
    if not isinstance(first.get("evidence_refs"), list):
        errors.append(_error("experiments[0].evidence_refs", "missing_required", "evidence_refs is required"))

    if errors:
        return _fail(*errors)
    return _ok()


def validate_payload(kind: str, data: Any) -> dict[str, Any]:
    payload_size = len(json.dumps(data, ensure_ascii=False)) if data is not None else 0
    if payload_size > _MAX_PAYLOAD_BYTES:
        return _fail(_error("$", "payload_too_large", "payload exceeds max size"))

    if kind == "eval_report":
        return validate_eval_report(data)
    if kind == "evidence_pack":
        return validate_evidence_pack(data)
    if kind == "next_experiments":
        return validate_next_experiments(data)

    return _fail(
        _error("kind", "unsupported_kind", f"unsupported kind: {kind}"),
        error_code=ErrorCode.EVAL_FAILED,
    )


_VALID_CATEGORIES = {e.value for e in SkillCategory}
_VALID_TASK_TYPES = {"det", "seg", "cls", "multi"}


def validate_skill_card(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return _fail(_error("$", "type_error", "skill_card must be an object"))

    errors: list[dict[str, str]] = []
    if not _is_non_empty_str(data.get("skill_code")):
        errors.append(_error("skill_code", "missing_required", "skill_code is required"))
    if not _is_non_empty_str(data.get("name")):
        errors.append(_error("name", "missing_required", "name is required"))

    category = data.get("category")
    if not _is_non_empty_str(category):
        errors.append(_error("category", "missing_required", "category is required"))
    elif category not in _VALID_CATEGORIES:
        errors.append(_error("category", "invalid_enum", f"category must be one of {sorted(_VALID_CATEGORIES)}"))

    if not _is_non_empty_str(data.get("maturity")):
        errors.append(_error("maturity", "missing_required", "maturity is required"))

    if errors:
        return _fail(*errors, error_code=ErrorCode.KNOWLEDGE_IMPORT_FAILED)
    return _ok()


def validate_query_signature(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return _fail(_error("$", "type_error", "query_signature must be an object"))

    errors: list[dict[str, str]] = []
    task_type = data.get("task_type")
    if not _is_non_empty_str(task_type):
        errors.append(_error("task_type", "missing_required", "task_type is required"))
    elif task_type not in _VALID_TASK_TYPES:
        errors.append(_error("task_type", "invalid_enum", f"task_type must be one of {sorted(_VALID_TASK_TYPES)}"))

    if not _is_non_empty_str(data.get("model_family")):
        errors.append(_error("model_family", "missing_required", "model_family is required"))

    if errors:
        return _fail(*errors, error_code=ErrorCode.LLM_GATEWAY_ERROR)
    return _ok()
