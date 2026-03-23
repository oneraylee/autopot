from enum import Enum

import pytest


EXPECTED_JOB_STATUSES = {
    "CREATED",
    "QUEUED",
    "RUNNING",
    "SUCCEEDED",
    "FAILED",
    "CANCELED",
    "EVALUATING",
    "EVAL_SUCCEEDED",
    "EVAL_FAILED",
    "EVIDENCE_READY",
    "LLM_ANALYZING",
    "LLM_DONE",
    "LLM_FAILED",
}

EXPECTED_TASK_TYPES = {
    "TRAINING",
    "EVALUATION",
    "ANALYSIS",
    "EXPORT",
}

EXPECTED_PRECISION_MODES = {
    "fp32",
    "fp16",
    "bf16",
}

EXPECTED_ERROR_CODES = {
    "TRAIN_OOM",
    "TRAIN_NAN",
    "DATA_INVALID",
    "EVAL_FAILED",
    "LLM_FAILED",
    "EXPORT_FAILED",
}


def test_job_status_unique_values():
    from common.domain_types import JobStatus

    assert issubclass(JobStatus, Enum)
    actual_names = {item.name for item in JobStatus}
    assert EXPECTED_JOB_STATUSES.issubset(actual_names)

    values = [item.value for item in JobStatus]
    assert len(values) == len(set(values))


def test_task_type_coverage():
    from common.domain_types import TaskType

    assert issubclass(TaskType, Enum)
    assert {item.name for item in TaskType} == EXPECTED_TASK_TYPES


def test_precision_mode_supported_set():
    from common.domain_types import PrecisionMode

    assert issubclass(PrecisionMode, Enum)
    assert {item.value for item in PrecisionMode} == EXPECTED_PRECISION_MODES


def test_invalid_enum_value_rejected():
    from common.domain_types import JobStatus, PrecisionMode, TaskType

    with pytest.raises(ValueError):
        JobStatus("invalid")
    with pytest.raises(ValueError):
        TaskType("nonsense")
    with pytest.raises(ValueError):
        PrecisionMode("fp8")


def test_error_code_coverage_and_uniqueness():
    from common.domain_types import ErrorCode

    names = {item.name for item in ErrorCode}
    assert EXPECTED_ERROR_CODES.issubset(names)

    values = [item.value for item in ErrorCode]
    assert len(values) == len(set(values))


def test_public_boundary_exports_only_contract_symbols():
    from common import domain_types

    exported = set(domain_types.__all__)
    expected = {
        "JobStatus", "TaskType", "PrecisionMode", "ErrorCode",
        "SkillCategory", "SkillLayer", "SkillMaturity",
        "LLMCallType", "RelationType",
    }
    assert exported == expected
