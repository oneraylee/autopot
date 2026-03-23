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
    LLM_GATEWAY_ERROR = "LLM_GATEWAY_ERROR"
    KNOWLEDGE_IMPORT_FAILED = "KNOWLEDGE_IMPORT_FAILED"


class SkillCategory(StrEnum):
    TRAINING = "training"
    MODEL = "model"
    DATA = "data"
    EVAL_DEPLOY = "eval_deploy"


class SkillLayer(StrEnum):
    # Training
    OPTIMIZER = "optimizer"
    SCHEDULE = "schedule"
    AUGMENT = "augment"
    REGULARIZATION = "regularization"
    PRECISION = "precision"
    FREEZE = "freeze"
    HYPERPARAMETER = "hyperparameter"
    DISTRIBUTED = "distributed"
    # Model
    BACKBONE = "backbone"
    NECK = "neck"
    HEAD = "head"
    BLOCK = "block"
    ATTENTION = "attention"
    CONV = "conv"
    LOSS = "loss"
    # Data
    CLEANING = "cleaning"
    BALANCING = "balancing"
    SCENE_COVERAGE = "scene_coverage"
    SPLIT = "split"
    PREPROCESSING = "preprocessing"
    # Eval & Deploy
    METRIC = "metric"
    CALIBRATION = "calibration"
    QUANTIZATION = "quantization"
    EXPORT = "export"
    BENCHMARK = "benchmark"


class SkillMaturity(StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    VERIFIED = "verified"
    DEPRECATED = "deprecated"


class LLMCallType(StrEnum):
    AGENT_PLAN = "agent_plan"
    AGENT_DIAGNOSE = "agent_diagnose"
    SKILL_EXTRACT = "skill_extract"
    CONFLICT_ANALYZE = "conflict_analyze"
    EMBEDDING = "embedding"


class RelationType(StrEnum):
    INCOMPATIBLE_WITH = "incompatible_with"
    DEPENDS_ON = "depends_on"
    COMPLEMENTS = "complements"
    SUPERSEDES = "supersedes"
    DUPLICATES = "duplicates"


__all__ = [
    "JobStatus",
    "TaskType",
    "PrecisionMode",
    "ErrorCode",
    "SkillCategory",
    "SkillLayer",
    "SkillMaturity",
    "LLMCallType",
    "RelationType",
]
