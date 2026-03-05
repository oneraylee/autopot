from enum import StrEnum


class JobStatus(StrEnum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    EVALUATING = "evaluating"
    EVAL_SUCCEEDED = "eval_succeeded"
    EVAL_FAILED = "eval_failed"
    EVIDENCE_READY = "evidence_ready"
    LLM_ANALYZING = "llm_analyzing"
    LLM_DONE = "llm_done"
    LLM_FAILED = "llm_failed"


class TaskType(StrEnum):
    TRAINING = "training"
    EVALUATION = "evaluation"
    ANALYSIS = "analysis"
    EXPORT = "export"


class PrecisionMode(StrEnum):
    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"


class ErrorCode(StrEnum):
    TRAIN_OOM = "TRAIN_OOM"
    TRAIN_NAN = "TRAIN_NAN"
    DATA_INVALID = "DATA_INVALID"
    EVAL_FAILED = "EVAL_FAILED"
    LLM_FAILED = "LLM_FAILED"
    EXPORT_FAILED = "EXPORT_FAILED"


__all__ = [
    "JobStatus",
    "TaskType",
    "PrecisionMode",
    "ErrorCode",
]
