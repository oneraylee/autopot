"""RED tests for Knowledge System API (Phase 2 Step 4 + Phase 4 Step 3)."""
import json
import pytest
from unittest.mock import MagicMock


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_repos():
    from repositories.knowledge_repository import KnowledgeRepository
    return KnowledgeRepository()


def _make_ingestion_svc(repo):
    from services.knowledge_ingestion_service import KnowledgeIngestionService
    gw = MagicMock()
    gw.chat_completion.return_value = {
        "content": json.dumps([{
            "name": "label_smoothing",
            "category": "regularization",
            "layer": "training",
            "condition": "overfitting",
            "action": {"target_path": "trainer.label_smoothing", "value": 0.1},
            "tradeoff": "accuracy drop",
        }]),
        "usage": {"input_tokens": 200, "output_tokens": 50},
    }
    return KnowledgeIngestionService(knowledge_repo=repo, llm_gateway=gw)


def _make_registry_svc(repo):
    from services.knowledge_registry_service import KnowledgeRegistryService
    return KnowledgeRegistryService(knowledge_repo=repo)


def _make_routes():
    from api.knowledge_routes import KnowledgeRoutes
    repo = _make_repos()
    ingestion = _make_ingestion_svc(repo)
    registry = _make_registry_svc(repo)
    return KnowledgeRoutes(
        ingestion_service=ingestion,
        registry_service=registry,
    ), repo


_MARKDOWN_BODY = "# Guide\n\nLearn about label smoothing technique in training."


# ══════════════════════════════════════════════════════════════════════════════
# Step 4: POST /knowledge/sources
# ══════════════════════════════════════════════════════════════════════════════

def test_post_sources_register_success():
    routes, _ = _make_routes()
    response = routes.post_sources({
        "source_type": "doc",
        "name": "Ultralytics Docs",
        "uri": "https://docs.ultralytics.com",
        "author": "Ultralytics",
        "license": "MIT",
        "trust_level": 5,
    })
    assert response["ok"] is True
    assert response["data"]["source_id"] is not None
    assert response["data"]["source_type"] == "doc"


def test_post_sources_duplicate_conflict():
    routes, _ = _make_routes()
    payload = {
        "source_type": "doc",
        "name": "Docs",
        "uri": "https://duplicate.example.com",
        "author": "Author",
        "license": "MIT",
        "trust_level": 3,
    }
    routes.post_sources(payload)
    response = routes.post_sources(payload)
    assert response["ok"] is False
    assert response["error"]["code"] == "CONFLICT"


# ══════════════════════════════════════════════════════════════════════════════
# Step 4: POST /knowledge/documents/import
# ══════════════════════════════════════════════════════════════════════════════

def test_post_documents_import_success():
    routes, _ = _make_routes()
    # Register source first
    src_response = routes.post_sources({
        "source_type": "doc",
        "name": "Training Guide",
        "uri": "https://guide.example.com",
        "author": "Team",
        "license": "internal",
        "trust_level": 4,
    })
    source_id = src_response["data"]["source_id"]

    response = routes.post_documents_import({
        "source_id": source_id,
        "title": "Training Guide Doc",
        "doc_type": "markdown",
        "version_label": "v1.0",
        "content": _MARKDOWN_BODY,
        "language": "zh",
    })
    assert response["ok"] is True
    assert response["data"]["document_id"] is not None
    assert response["data"]["parse_status"] == "pending"


# ══════════════════════════════════════════════════════════════════════════════
# Step 4: POST /knowledge/techniques/extract
# ══════════════════════════════════════════════════════════════════════════════

def test_post_techniques_extract_trigger():
    routes, _ = _make_routes()
    src = routes.post_sources({
        "source_type": "doc", "name": "Extract Src",
        "uri": "https://extract-src.example.com",
        "author": "A", "license": "MIT", "trust_level": 3,
    })
    doc = routes.post_documents_import({
        "source_id": src["data"]["source_id"],
        "title": "Extract Guide", "doc_type": "markdown",
        "version_label": "v1", "content": _MARKDOWN_BODY, "language": "zh",
    })

    response = routes.post_techniques_extract({
        "document_id": doc["data"]["document_id"],
    })
    assert response["ok"] is True
    assert "candidates" in response["data"]
    assert isinstance(response["data"]["candidates"], list)


# ══════════════════════════════════════════════════════════════════════════════
# Step 4: GET /knowledge/techniques
# ══════════════════════════════════════════════════════════════════════════════

def test_get_techniques_with_filters():
    routes, repo = _make_routes()
    # Pre-create some skills via registry service
    from services.knowledge_registry_service import KnowledgeRegistryService
    registry = KnowledgeRegistryService(knowledge_repo=repo)
    registry.create_skill(
        skill_code="TEST-001", name="label_smoothing",
        category="regularization", layer="training",
        task_type="classification", summary="LS", maturity="draft",
    )
    registry.create_skill(
        skill_code="TEST-002", name="mosaic",
        category="data_aug", layer="preprocessing",
        task_type="detection", summary="Mosaic", maturity="verified",
    )

    response = routes.get_techniques({"category": "regularization"})
    assert response["ok"] is True
    assert len(response["data"]["techniques"]) == 1
    assert response["data"]["techniques"][0]["category"] == "regularization"


def test_get_technique_detail():
    routes, repo = _make_routes()
    from services.knowledge_registry_service import KnowledgeRegistryService
    registry = KnowledgeRegistryService(knowledge_repo=repo)
    skill = registry.create_skill(
        skill_code="DET-001", name="det_skill",
        category="optimizer", layer="training",
        task_type="classification", summary="Detail test skill.", maturity="draft",
    )

    response = routes.get_technique_detail(skill["skill_id"])
    assert response["ok"] is True
    assert response["data"]["skill_id"] == skill["skill_id"]
    assert response["data"]["name"] == "det_skill"
    assert response["data"]["summary"] == "Detail test skill."


# ══════════════════════════════════════════════════════════════════════════════
# Step 4: POST /knowledge/techniques/{id}/publish
# ══════════════════════════════════════════════════════════════════════════════

def test_post_technique_publish_success():
    routes, repo = _make_routes()
    from services.knowledge_registry_service import KnowledgeRegistryService
    registry = KnowledgeRegistryService(knowledge_repo=repo)
    skill = registry.create_skill(
        skill_code="PUB-API-001", name="pub_skill",
        category="regularization", layer="training",
        task_type="classification", summary="Publish test.", maturity="draft",
    )

    response = routes.post_technique_publish(skill["skill_id"])
    assert response["ok"] is True
    assert response["data"]["publish_status"] == "reviewed"


def test_post_technique_publish_invalid_transition():
    routes, repo = _make_routes()
    from services.knowledge_registry_service import KnowledgeRegistryService
    registry = KnowledgeRegistryService(knowledge_repo=repo)
    skill = registry.create_skill(
        skill_code="PUB-API-002", name="pub_invalid_skill",
        category="optimizer", layer="training",
        task_type="classification", summary="Invalid publish test.", maturity="draft",
    )

    # Try to jump to verified directly
    response = routes.post_technique_publish(skill["skill_id"], payload={"target_status": "verified"})
    assert response["ok"] is False
    assert response["error"]["code"] in {"INVALID_TRANSITION", "VALIDATION_ERROR", "FORBIDDEN"}


# ══════════════════════════════════════════════════════════════════════════════
# Step 4: 响应结构一致性
# ══════════════════════════════════════════════════════════════════════════════

def test_response_structure_consistent():
    """All API responses must follow the ok / data / error structure."""
    routes, _ = _make_routes()

    # Success case
    ok_response = routes.post_sources({
        "source_type": "doc",
        "name": "Structure Test",
        "uri": "https://structure.example.com",
        "author": "A", "license": "MIT", "trust_level": 1,
    })
    assert "ok" in ok_response
    assert ok_response["ok"] is True
    assert "data" in ok_response

    # Failure case (duplicate)
    dup_payload = {
        "source_type": "doc",
        "name": "Structure Test 2",
        "uri": "https://structure2.example.com",
        "author": "A", "license": "MIT", "trust_level": 1,
    }
    routes.post_sources(dup_payload)
    error_response = routes.post_sources(dup_payload)
    assert "ok" in error_response
    assert error_response["ok"] is False
    assert "error" in error_response
    assert "code" in error_response["error"]
    assert "message" in error_response["error"]

    # Not found case
    not_found_response = routes.get_technique_detail("nonexistent-id-12345")
    assert "ok" in not_found_response
    assert not_found_response["ok"] is False
    assert "error" in not_found_response


# ══════════════════════════════════════════════════════════════════════════════
# Phase 4 Step 3 – Outcome 回写 API
# ══════════════════════════════════════════════════════════════════════════════

def _make_routes_with_outcome_tracker():
    """Build KnowledgeRoutes with an outcome_tracker_service attached."""
    from api.knowledge_routes import KnowledgeRoutes
    from repositories.knowledge_repository import KnowledgeRepository
    from services.knowledge_ingestion_service import KnowledgeIngestionService
    from services.knowledge_registry_service import KnowledgeRegistryService
    from services.skill_outcome_tracker_service import SkillOutcomeTrackerService

    repo = KnowledgeRepository()
    gw = MagicMock()
    gw.chat_completion.return_value = {
        "content": json.dumps([{
            "name": "label_smoothing",
            "category": "regularization", "layer": "training",
            "condition": "overfitting",
            "action": {"target_path": "trainer.label_smoothing", "value": 0.1},
            "tradeoff": "accuracy drop",
        }]),
        "usage": {"input_tokens": 100, "output_tokens": 30},
    }
    ingestion = KnowledgeIngestionService(knowledge_repo=repo, llm_gateway=gw)
    registry = KnowledgeRegistryService(knowledge_repo=repo)
    tracker = SkillOutcomeTrackerService(knowledge_repo=repo)
    return KnowledgeRoutes(
        ingestion_service=ingestion,
        registry_service=registry,
        outcome_tracker_service=tracker,
    ), repo, tracker


def _make_routes_with_composer_and_tracker():
    """Build KnowledgeRoutes with composer + tracker."""
    from api.knowledge_routes import KnowledgeRoutes
    from repositories.knowledge_repository import KnowledgeRepository
    from services.knowledge_ingestion_service import KnowledgeIngestionService
    from services.knowledge_registry_service import KnowledgeRegistryService
    from services.knowledge_retrieval_service import KnowledgeRetrievalService
    from services.conflict_resolution_service import ConflictResolutionService
    from services.strategy_composer_service import StrategyComposerService
    from services.skill_outcome_tracker_service import SkillOutcomeTrackerService

    repo = KnowledgeRepository()
    gw = MagicMock()
    gw.chat_completion.return_value = {
        "content": json.dumps([]), "usage": {"input_tokens": 50, "output_tokens": 10},
    }
    ingestion = KnowledgeIngestionService(knowledge_repo=repo, llm_gateway=gw)
    registry = KnowledgeRegistryService(knowledge_repo=repo)
    retrieval = KnowledgeRetrievalService(knowledge_repo=repo)
    conflict = ConflictResolutionService()
    composer = StrategyComposerService(
        retrieval_service=retrieval,
        conflict_service=conflict,
        knowledge_repo=repo,
    )
    tracker = SkillOutcomeTrackerService(knowledge_repo=repo)
    return KnowledgeRoutes(
        ingestion_service=ingestion,
        registry_service=registry,
        retrieval_service=retrieval,
        conflict_service=conflict,
        composer_service=composer,
        outcome_tracker_service=tracker,
    ), repo


def test_post_outcomes_success():
    """POST /knowledge/outcomes 回写成功，返回 outcome 记录。"""
    routes, repo, tracker = _make_routes_with_outcome_tracker()
    # Create a skill first
    from services.knowledge_registry_service import KnowledgeRegistryService
    registry = KnowledgeRegistryService(knowledge_repo=repo)
    skill = registry.create_skill(
        skill_code="TECH-OUT-001", name="outcome_skill",
        category="augmentation", layer="training",
        task_type="det", maturity="stable",
        default_priority=3, summary="Outcome test skill.",
    )

    response = routes.post_outcomes({
        "technique_id": skill["skill_id"],
        "project_id": "proj-001",
        "baseline_job_id": "job-001",
        "candidate_job_id": "job-002",
        "result_summary": {"kpi_diff": 0.05, "map50": 0.82},
        "verdict": "win",
        "scenario_signature": {"task_type": "det", "scene": "night"},
    })
    assert response["ok"] is True
    assert response["data"]["verdict"] == "win"
    assert "outcome_id" in response["data"]


def test_post_outcomes_missing_field_rejected():
    """POST /knowledge/outcomes 缺必填字段被拒（VALIDATION_ERROR）。"""
    routes, _, _ = _make_routes_with_outcome_tracker()
    response = routes.post_outcomes({
        # missing technique_id, baseline_job_id, etc.
        "project_id": "proj-001",
    })
    assert response["ok"] is False
    assert response["error"]["code"] == "VALIDATION_ERROR"


def test_post_outcomes_invalid_technique_error():
    """POST /knowledge/outcomes technique_id 不存在时返回错误。"""
    routes, _, _ = _make_routes_with_outcome_tracker()
    response = routes.post_outcomes({
        "technique_id": "nonexistent-skill-id",
        "project_id": "proj-001",
        "baseline_job_id": "job-001",
        "candidate_job_id": "job-002",
        "result_summary": {"kpi_diff": 0.03},
        "verdict": "win",
    })
    assert response["ok"] is False
    assert response["error"]["code"] in {"NOT_FOUND", "VALIDATION_ERROR"}


def test_post_knowledge_plan_trigger():
    """POST /datasets/versions/{id}/knowledge-plan 触发规划上下文生成，返回 snapshot_id。"""
    routes, _ = _make_routes_with_composer_and_tracker()
    response = routes.post_dataset_knowledge_plan(
        version_id="version-001",
        payload={
            "dataset_report": {
                "task_type": "det",
                "stats": {"small_object_ratio": 0.3, "total_images": 5000},
                "scene_gaps": [{"scene": "night", "risk": "high"}],
            },
            "project_constraints": {"gpu_mem_gb": 16},
            "project_id": "proj-001",
        },
    )
    assert response["ok"] is True
    assert "snapshot_id" in response["data"]


def test_post_knowledge_diagnosis_trigger():
    """POST /jobs/{id}/knowledge-diagnosis 触发诊断上下文生成，返回 snapshot_id。"""
    routes, _ = _make_routes_with_composer_and_tracker()
    response = routes.post_job_knowledge_diagnosis(
        job_id="job-001",
        payload={
            "evidence_pack": {
                "job_summary": {"job_id": "job-001", "train_args": {}},
                "eval": {"business_kpi": 0.72, "by_scene": {"night": {"fn": 45}}},
                "dataset_report": {
                    "task_type": "det",
                    "stats": {"small_object_ratio": 0.25},
                },
            },
            "project_constraints": {},
            "project_id": "proj-001",
        },
    )
    assert response["ok"] is True
    assert "snapshot_id" in response["data"]


def test_post_validate_with_knowledge_pass():
    """POST /proposals/validate-with-knowledge 无冲突技能组合校验通过。"""
    routes, _ = _make_routes_with_composer_and_tracker()
    response = routes.post_validate_with_knowledge({
        "technique_ids": [],
        "runtime_constraints": {"gpu_mem_gb": 32},
    })
    assert response["ok"] is True


def test_post_validate_with_knowledge_conflict_fail():
    """POST /proposals/validate-with-knowledge GPU 超限时校验失败。"""
    routes, repo = _make_routes_with_composer_and_tracker()
    # Place a skill with high GPU requirement
    from services.knowledge_registry_service import KnowledgeRegistryService
    registry = KnowledgeRegistryService(knowledge_repo=repo)
    registry.create_skill(
        skill_code="GPU-HEAVY-001", name="heavy_skill",
        category="augmentation", layer="training",
        task_type="det", maturity="stable", default_priority=3,
        summary="GPU heavy.",
    )

    response = routes.post_validate_with_knowledge({
        "technique_ids": [],
        "runtime_constraints": {"gpu_mem_gb": 0.1},  # effectively zero budget
        "techniques": [
            {"technique_id": "GPU-HEAVY-001", "resources": {"gpu_mem_gb": 10.0}},
        ],
    })
    # Conflict: GPU exceeds budget → validation fails
    assert response["ok"] is False or (
        response["ok"] is True and response["data"].get("validation", {}).get("ok") is False
    )
