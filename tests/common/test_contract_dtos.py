import pytest


def test_job_spec_required_fields_and_types():
    from common.contracts import JobSpec

    obj = JobSpec(
        job_id="job_001",
        task_type="TRAINING",
        dataset_uri="s3://bucket/dataset",
        precision_mode="fp16",
    )
    assert obj.job_id == "job_001"


def test_job_spec_missing_required_fields_fail_stably():
    from common.contracts import JobSpec

    with pytest.raises(ValueError):
        JobSpec(job_id="", task_type="TRAINING", dataset_uri="x", precision_mode="fp16")


def test_project_kpi_config_required_fields():
    from common.contracts import ProjectKpiConfig

    cfg = ProjectKpiConfig(primary_kpi="business_kpi", threshold=0.8, scenes=["default"])
    assert cfg.primary_kpi == "business_kpi"


def test_eval_summary_serialization_stable_order_and_names():
    from common.contracts import EvalSummary

    summary = EvalSummary(
        business_kpi=0.91,
        kpi_components=[{"name": "quality", "score": 0.93}],
        by_scene=[{"scene": "default", "business_kpi": 0.9}],
    )
    payload = summary.to_payload()

    assert list(payload.keys()) == ["overall", "by_scene"]
    assert list(payload["overall"].keys()) == ["business_kpi", "kpi_components"]


def test_optional_field_backward_compatible_for_export_spec():
    from common.contracts import ExportSpec

    legacy_data = {"format": "zip", "include": ["weights", "eval"]}
    spec = ExportSpec.from_dict(legacy_data)

    assert spec.destination is None
    assert spec.to_dict()["format"] == "zip"


def test_illegal_values_rejected():
    from common.contracts import ExportSpec

    with pytest.raises(ValueError):
        ExportSpec(format="", include=["weights"])


def test_dto_output_can_be_validated_directly():
    from common.contracts import EvalSummary
    from common.schema_validators import validate_payload

    summary = EvalSummary(
        business_kpi=0.95,
        kpi_components=[{"name": "quality", "score": 0.94}],
        by_scene=[{"scene": "default", "business_kpi": 0.95}],
    )
    result = validate_payload("eval_report", summary.to_payload())
    assert result == {"ok": True, "errors": []}


def test_dto_to_validator_error_path_is_traceable():
    from common.contracts import EvalSummary
    from common.schema_validators import validate_payload

    payload = EvalSummary(
        business_kpi=0.8,
        kpi_components=[{"name": "quality", "score": 0.8}],
        by_scene=[{"scene": "default", "business_kpi": 0.8}],
    ).to_payload()
    del payload["overall"]

    result = validate_payload("eval_report", payload)
    assert result["ok"] is False
    assert result["errors"][0]["path"] == "overall"
