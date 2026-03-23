"""RED tests for knowledge system contract DTOs (Step 1 + Step 2)."""
import pytest


# ──────────────────────────────────────────────
# Step 1: DTO construction & serialization
# ──────────────────────────────────────────────

def test_skill_card_summary_serialization():
    from common.contracts import SkillCardSummary

    summary = SkillCardSummary(
        skill_code="train.augment.mosaic_scale",
        name="小目标场景启Mosaic+Scale增强",
        category="training",
        layer="augment",
        task_type="det",
        summary="当数据集小目标比例较高时，启用 Mosaic + Scale 增强",
        maturity="verified",
    )
    assert summary.skill_code == "train.augment.mosaic_scale"
    assert summary.category == "training"
    assert summary.maturity == "verified"

    d = summary.to_dict()
    assert d["skill_code"] == "train.augment.mosaic_scale"
    assert d["category"] == "training"

    restored = SkillCardSummary.from_dict(d)
    assert restored == summary


def test_query_signature_construction():
    from common.contracts import QuerySignature

    sig = QuerySignature(
        task_type="det",
        model_family="yolo11",
        small_object_ratio=0.31,
        weak_scenes=["night", "rain"],
        primary_gap="high_fn_night",
    )
    assert sig.task_type == "det"
    assert sig.model_family == "yolo11"
    assert sig.weak_scenes == ["night", "rain"]


def test_conflict_report_construction():
    from common.contracts import ConflictReport

    report = ConflictReport(
        from_skill_code="train.augment.mosaic_scale",
        to_skill_code="train.augment.copypaste",
        relation_type="incompatible_with",
        strength="hard",
        description="两者不能同时启用",
    )
    assert report.from_skill_code == "train.augment.mosaic_scale"
    assert report.relation_type == "incompatible_with"


def test_skill_context_construction():
    from common.contracts import SkillContext

    ctx = SkillContext(
        selected_techniques=["train.augment.mosaic_scale"],
        rejected_techniques=[],
        query_signature={"task_type": "det"},
    )
    assert ctx.selected_techniques == ["train.augment.mosaic_scale"]


def test_llm_call_record_construction():
    from common.contracts import LLMCallRecord

    record = LLMCallRecord(
        call_type="agent_plan",
        provider="openai",
        model="gpt-4o",
        input_tokens=1500,
        output_tokens=500,
        latency_ms=1200,
        cost_estimate=0.032,
        status="success",
    )
    assert record.call_type == "agent_plan"
    assert record.input_tokens == 1500
    assert record.cost_estimate == 0.032


def test_skill_ref_construction():
    from common.contracts import SkillRef

    ref = SkillRef(
        skill_code="train.augment.mosaic_scale",
        name="小目标Mosaic增强",
        category="training",
        layer="augment",
    )
    assert ref.skill_code == "train.augment.mosaic_scale"


def test_contract_missing_required_field_fails():
    from common.contracts import SkillCardSummary

    with pytest.raises((ValueError, TypeError)):
        SkillCardSummary(
            skill_code="",
            name="test",
            category="training",
            layer="augment",
            task_type="det",
            summary="test",
            maturity="draft",
        )


def test_skill_card_summary_missing_name_fails():
    from common.contracts import SkillCardSummary

    with pytest.raises((ValueError, TypeError)):
        SkillCardSummary(
            skill_code="train.augment.x",
            name="",
            category="training",
            layer="augment",
            task_type="det",
            summary="test",
            maturity="draft",
        )


def test_llm_call_record_to_dict():
    from common.contracts import LLMCallRecord

    record = LLMCallRecord(
        call_type="embedding",
        provider="openai",
        model="text-embedding-3-small",
        input_tokens=200,
        output_tokens=0,
        latency_ms=80,
        cost_estimate=0.0001,
        status="success",
    )
    d = record.to_dict()
    assert d["call_type"] == "embedding"
    assert d["provider"] == "openai"
    assert d["input_tokens"] == 200


# ──────────────────────────────────────────────
# Step 2: Schema validation tests
# ──────────────────────────────────────────────


def _valid_skill_card_json():
    return {
        "skill_code": "train.augment.mosaic_scale",
        "name": "小目标Mosaic增强",
        "category": "training",
        "layer": "augment",
        "task_type": "det",
        "summary": "启用 Mosaic + Scale 增强",
        "rationale": "增加小目标样本量",
        "maturity": "verified",
        "evidence_level": "internal_verified",
        "default_priority": 8,
        "status": "active",
    }


def test_valid_skill_card_json_passes():
    from common.schema_validators import validate_skill_card

    result = validate_skill_card(_valid_skill_card_json())
    assert result["ok"] is True


def test_skill_card_missing_skill_code_rejected():
    from common.schema_validators import validate_skill_card

    data = _valid_skill_card_json()
    del data["skill_code"]
    result = validate_skill_card(data)
    assert result["ok"] is False
    assert any("skill_code" in e["path"] for e in result["errors"])


def test_skill_card_invalid_category_rejected():
    from common.schema_validators import validate_skill_card

    data = _valid_skill_card_json()
    data["category"] = "invalid_category"
    result = validate_skill_card(data)
    assert result["ok"] is False
    assert any("category" in e["path"] for e in result["errors"])


def test_query_signature_invalid_task_type_rejected():
    from common.schema_validators import validate_query_signature

    data = {"task_type": "invalid", "model_family": "yolo11"}
    result = validate_query_signature(data)
    assert result["ok"] is False
    assert any("task_type" in e["path"] for e in result["errors"])


def test_query_signature_valid_passes():
    from common.schema_validators import validate_query_signature

    data = {"task_type": "det", "model_family": "yolo11"}
    result = validate_query_signature(data)
    assert result["ok"] is True
