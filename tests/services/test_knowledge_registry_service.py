"""RED tests for KnowledgeRegistryService (Phase 2 Step 3)."""
import pytest
from unittest.mock import MagicMock


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_repo():
    from repositories.knowledge_repository import KnowledgeRepository
    return KnowledgeRepository()


def _make_service():
    from services.knowledge_registry_service import KnowledgeRegistryService
    repo = _make_repo()
    return KnowledgeRegistryService(knowledge_repo=repo), repo


# ══════════════════════════════════════════════════════════════════════════════
# Step 3: Skill CRUD
# ══════════════════════════════════════════════════════════════════════════════

def test_create_skill_unique_code():
    svc, _ = _make_service()
    skill = svc.create_skill(
        skill_code="REG-001",
        name="label_smoothing",
        category="regularization",
        layer="training",
        task_type="classification",
        summary="Apply label smoothing to reduce overconfidence.",
        maturity="draft",
    )
    assert skill["skill_id"] is not None
    assert skill["skill_code"] == "REG-001"
    assert skill["name"] == "label_smoothing"


def test_create_skill_duplicate_code_rejected():
    svc, _ = _make_service()
    svc.create_skill(
        skill_code="REG-001",
        name="label_smoothing",
        category="regularization",
        layer="training",
        task_type="classification",
        summary="Apply label smoothing.",
        maturity="draft",
    )
    with pytest.raises(Exception) as exc_info:
        svc.create_skill(
            skill_code="REG-001",
            name="another_skill",
            category="optimizer",
            layer="training",
            task_type="classification",
            summary="Another skill with same code.",
            maturity="draft",
        )
    assert "CONFLICT" in str(exc_info.value) or "already exists" in str(exc_info.value).lower()


def test_update_skill_fields_correct():
    svc, _ = _make_service()
    skill = svc.create_skill(
        skill_code="OPT-001",
        name="adamw",
        category="optimizer",
        layer="training",
        task_type="classification",
        summary="Use AdamW.",
        maturity="draft",
    )
    updated = svc.update_skill(skill["skill_id"], summary="Use AdamW with weight decay.")
    assert updated["summary"] == "Use AdamW with weight decay."
    assert updated["skill_code"] == "OPT-001"


# ══════════════════════════════════════════════════════════════════════════════
# Step 3: 发布状态流转
# ══════════════════════════════════════════════════════════════════════════════

def test_publish_draft_to_reviewed():
    svc, _ = _make_service()
    skill = svc.create_skill(
        skill_code="PUB-001",
        name="dropout",
        category="regularization",
        layer="training",
        task_type="classification",
        summary="Apply dropout.",
        maturity="draft",
    )
    result = svc.publish_skill(skill["skill_id"])
    assert result["publish_status"] == "reviewed"


def test_publish_reviewed_to_verified():
    svc, _ = _make_service()
    skill = svc.create_skill(
        skill_code="PUB-002",
        name="weight_decay",
        category="regularization",
        layer="training",
        task_type="classification",
        summary="Apply weight decay.",
        maturity="draft",
    )
    # draft → reviewed
    svc.publish_skill(skill["skill_id"])
    # reviewed → verified
    result = svc.publish_skill(skill["skill_id"])
    assert result["publish_status"] == "verified"


def test_publish_invalid_transition_rejected():
    """Direct draft → verified transition should be rejected."""
    svc, _ = _make_service()
    skill = svc.create_skill(
        skill_code="PUB-003",
        name="mixup",
        category="data_aug",
        layer="preprocessing",
        task_type="classification",
        summary="Apply mixup augmentation.",
        maturity="draft",
    )
    # Try to move to verified (skip reviewed) - should reject
    with pytest.raises(Exception) as exc_info:
        svc.publish_skill(skill["skill_id"], target_status="verified")
    error_msg = str(exc_info.value).lower()
    assert "invalid" in error_msg or "transition" in error_msg or "forbidden" in error_msg


# ══════════════════════════════════════════════════════════════════════════════
# Step 3: list_skills 多维筛选
# ══════════════════════════════════════════════════════════════════════════════

def _create_test_skills(svc):
    """Create a set of skills with different attributes for filtering tests."""
    svc.create_skill(
        skill_code="REG-010", name="label_smoothing",
        category="regularization", layer="training",
        task_type="classification", summary="LS", maturity="draft",
    )
    svc.create_skill(
        skill_code="OPT-010", name="adamw",
        category="optimizer", layer="training",
        task_type="classification", summary="AdamW", maturity="verified",
    )
    svc.create_skill(
        skill_code="AUG-010", name="mosaic",
        category="data_aug", layer="preprocessing",
        task_type="detection", summary="Mosaic aug", maturity="draft",
    )
    svc.create_skill(
        skill_code="AUG-011", name="mixup",
        category="data_aug", layer="preprocessing",
        task_type="detection", summary="Mixup aug", maturity="reviewed",
    )


def test_list_skills_filter_by_category():
    svc, _ = _make_service()
    _create_test_skills(svc)
    results = svc.list_skills(category="data_aug")
    assert len(results) == 2
    assert all(s["category"] == "data_aug" for s in results)


def test_list_skills_filter_by_layer():
    svc, _ = _make_service()
    _create_test_skills(svc)
    results = svc.list_skills(layer="preprocessing")
    assert len(results) == 2
    assert all(s["layer"] == "preprocessing" for s in results)


def test_list_skills_filter_by_task_type():
    svc, _ = _make_service()
    _create_test_skills(svc)
    results = svc.list_skills(task_type="detection")
    assert len(results) == 2
    assert all(s["task_type"] == "detection" for s in results)


def test_list_skills_filter_by_maturity():
    svc, _ = _make_service()
    _create_test_skills(svc)
    results = svc.list_skills(maturity="draft")
    assert len(results) == 2
    assert all(s["maturity"] == "draft" for s in results)


# ══════════════════════════════════════════════════════════════════════════════
# Step 3: 关系管理
# ══════════════════════════════════════════════════════════════════════════════

def test_upsert_relation_correct():
    svc, _ = _make_service()
    skill_a = svc.create_skill(
        skill_code="REL-A", name="skill_a",
        category="optimizer", layer="training",
        task_type="classification", summary="A", maturity="draft",
    )
    skill_b = svc.create_skill(
        skill_code="REL-B", name="skill_b",
        category="regularization", layer="training",
        task_type="classification", summary="B", maturity="draft",
    )
    relation = svc.upsert_relation(
        from_technique_id=skill_a["skill_id"],
        to_technique_id=skill_b["skill_id"],
        relation_type="conflicts_with",
        strength="strong",
        description="These two compete.",
    )
    assert relation["from_technique_id"] == skill_a["skill_id"]
    assert relation["to_technique_id"] == skill_b["skill_id"]
    assert relation["relation_type"] == "conflicts_with"


def test_relation_graph_bidirectional():
    """get_relations should return both A→B and B→A relations."""
    svc, _ = _make_service()
    skill_a = svc.create_skill(
        skill_code="BID-A", name="bid_skill_a",
        category="optimizer", layer="training",
        task_type="classification", summary="A", maturity="draft",
    )
    skill_b = svc.create_skill(
        skill_code="BID-B", name="bid_skill_b",
        category="regularization", layer="training",
        task_type="classification", summary="B", maturity="draft",
    )
    svc.upsert_relation(
        from_technique_id=skill_a["skill_id"],
        to_technique_id=skill_b["skill_id"],
        relation_type="conflicts_with",
        strength="moderate",
    )

    # Query from A's perspective
    relations_from_a = svc.get_relations(skill_a["skill_id"])
    assert len(relations_from_a) >= 1
    assert any(r["to_technique_id"] == skill_b["skill_id"] for r in relations_from_a)

    # Query from B's perspective (bidirectional)
    relations_from_b = svc.get_relations(skill_b["skill_id"])
    assert len(relations_from_b) >= 1
    assert any(r["from_technique_id"] == skill_a["skill_id"] for r in relations_from_b)


# ══════════════════════════════════════════════════════════════════════════════
# Step 3: 模板管理
# ══════════════════════════════════════════════════════════════════════════════

def test_template_payload_roundtrip():
    svc, _ = _make_service()
    skill = svc.create_skill(
        skill_code="TMPL-001", name="cosine_lr",
        category="scheduler", layer="training",
        task_type="classification", summary="Cosine LR.", maturity="draft",
    )
    payload = {
        "scheduler_type": "cosine",
        "warmup_epochs": 3,
        "min_lr": 1e-6,
        "params": {"eta_min": 0.0},
    }
    svc.upsert_template(
        technique_id=skill["skill_id"],
        template_kind="training_config",
        payload_json=payload,
    )
    templates = svc.get_templates(skill["skill_id"])
    assert len(templates) == 1
    stored = templates[0]["payload_json"]
    assert stored["scheduler_type"] == "cosine"
    assert stored["warmup_epochs"] == 3
    assert stored["params"]["eta_min"] == 0.0
