"""RED tests for knowledge system domain enums (Step 1)."""
import pytest


def test_skill_category_covers_four_domains():
    from common.domain_types import SkillCategory

    expected = {"training", "model", "data", "eval_deploy"}
    actual = {e.value for e in SkillCategory}
    assert actual == expected


def test_skill_layer_covers_taxonomy():
    from common.domain_types import SkillLayer

    expected = {
        # Training
        "optimizer", "schedule", "augment", "regularization",
        "precision", "freeze", "hyperparameter", "distributed",
        # Model
        "backbone", "neck", "head", "block",
        "attention", "conv", "loss",
        # Data
        "cleaning", "balancing", "scene_coverage", "split", "preprocessing",
        # Eval & Deploy
        "metric", "calibration", "quantization", "export", "benchmark",
    }
    actual = {e.value for e in SkillLayer}
    assert actual == expected


def test_skill_maturity_lifecycle():
    from common.domain_types import SkillMaturity

    expected = {"draft", "reviewed", "verified", "deprecated"}
    actual = {e.value for e in SkillMaturity}
    assert actual == expected


def test_llm_call_type_variants():
    from common.domain_types import LLMCallType

    expected = {
        "agent_plan", "agent_diagnose", "skill_extract",
        "conflict_analyze", "embedding",
    }
    actual = {e.value for e in LLMCallType}
    assert actual == expected


def test_relation_type_variants():
    from common.domain_types import RelationType

    expected = {
        "incompatible_with", "depends_on", "complements",
        "supersedes", "duplicates",
    }
    actual = {e.value for e in RelationType}
    assert actual == expected


def test_new_error_codes_available():
    from common.domain_types import ErrorCode

    assert ErrorCode.LLM_GATEWAY_ERROR == "LLM_GATEWAY_ERROR"
    assert ErrorCode.KNOWLEDGE_IMPORT_FAILED == "KNOWLEDGE_IMPORT_FAILED"


def test_existing_error_codes_unchanged():
    """Regression: existing ErrorCode values must still work."""
    from common.domain_types import ErrorCode

    assert ErrorCode.TRAIN_OOM == "TRAIN_OOM"
    assert ErrorCode.LLM_FAILED == "LLM_FAILED"
    assert ErrorCode.EXPORT_FAILED == "EXPORT_FAILED"
