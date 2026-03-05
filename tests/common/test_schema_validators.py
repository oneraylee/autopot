from copy import deepcopy

import pytest


VALID_EVAL_REPORT = {
    "overall": {
        "business_kpi": 0.91,
        "kpi_components": [{"name": "quality", "score": 0.93}],
    },
    "by_scene": [{"scene": "default", "business_kpi": 0.9}],
}

VALID_EVIDENCE_PACK = {
    "kpi_config": {
        "target": "business_kpi",
        "threshold": 0.85,
    },
    "index_paths": {
        "run_dir": "/tmp/run_001",
        "eval_report": "/tmp/run_001/eval/eval_report.json",
    },
}

VALID_NEXT_EXPERIMENTS = {
    "experiments": [
        {
            "name": "exp_a",
            "changes": ["learning_rate=1e-4"],
            "expected": "kpi提升",
            "evidence_refs": ["ev://run_001/1"],
        }
    ]
}


def assert_has_error_shape(result):
    assert result["ok"] is False
    assert "errors" in result
    assert isinstance(result["errors"], list)
    assert result["errors"]
    first = result["errors"][0]
    assert set(first.keys()) >= {"path", "error_type", "message"}


def test_missing_required_field_returns_structured_error():
    from common.schema_validators import validate_eval_report

    payload = deepcopy(VALID_EVAL_REPORT)
    del payload["overall"]

    result = validate_eval_report(payload)
    assert_has_error_shape(result)
    assert result["errors"][0]["path"] == "overall"


def test_type_error_returns_structured_error():
    from common.schema_validators import validate_evidence_pack

    payload = deepcopy(VALID_EVIDENCE_PACK)
    payload["kpi_config"] = "bad-type"

    result = validate_evidence_pack(payload)
    assert_has_error_shape(result)
    assert result["errors"][0]["path"] == "kpi_config"


def test_enum_like_value_error_returns_structured_error():
    from common.schema_validators import validate_eval_report

    payload = deepcopy(VALID_EVAL_REPORT)
    payload["by_scene"][0]["scene"] = ""

    result = validate_eval_report(payload)
    assert_has_error_shape(result)


def test_validate_eval_report_success():
    from common.schema_validators import validate_eval_report

    result = validate_eval_report(VALID_EVAL_REPORT)
    assert result == {"ok": True, "errors": []}


def test_validate_evidence_pack_success():
    from common.schema_validators import validate_evidence_pack

    result = validate_evidence_pack(VALID_EVIDENCE_PACK)
    assert result == {"ok": True, "errors": []}


def test_validate_next_experiments_success():
    from common.schema_validators import validate_next_experiments

    result = validate_next_experiments(VALID_NEXT_EXPERIMENTS)
    assert result == {"ok": True, "errors": []}


def test_validate_next_experiments_missing_minimum_fields():
    from common.schema_validators import validate_next_experiments

    payload = {"experiments": [{"name": "x"}]}
    result = validate_next_experiments(payload)

    assert_has_error_shape(result)
    paths = {item["path"] for item in result["errors"]}
    assert "experiments[0].changes" in paths
    assert "experiments[0].expected" in paths
    assert "experiments[0].evidence_refs" in paths


def test_dispatch_validate_payload_success():
    from common.schema_validators import validate_payload

    result = validate_payload("eval_report", VALID_EVAL_REPORT)
    assert result == {"ok": True, "errors": []}


def test_dispatch_unknown_kind_rejected_with_stable_error_code():
    from common.domain_types import ErrorCode
    from common.schema_validators import validate_payload

    result = validate_payload("unsupported_kind", {})
    assert_has_error_shape(result)
    assert result["error_code"] == ErrorCode.EVAL_FAILED.value


def test_large_payload_has_explicit_failure_strategy():
    from common.schema_validators import validate_payload

    huge_payload = {"blob": "x" * (2 * 1024 * 1024)}
    result = validate_payload("eval_report", huge_payload)

    assert_has_error_shape(result)
    assert result["errors"][0]["error_type"] == "payload_too_large"
