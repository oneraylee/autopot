"""RED tests for KnowledgeRepository (Step 3) – 14-table CRUD."""
import pytest


def _make_repo():
    from repositories.knowledge_repository import KnowledgeRepository
    return KnowledgeRepository()


# ── Source ──────────────────────────────────────

def test_source_crud_and_dedup():
    repo = _make_repo()
    src = repo.register_source(
        source_type="local", name="YOLO docs", uri="/data/yolo.md",
        author="alice", license="MIT", trust_level=4,
    )
    assert src["source_type"] == "local"
    assert src["uri"] == "/data/yolo.md"
    assert src["status"] == "active"

    loaded = repo.get_source(src["source_id"])
    assert loaded["name"] == "YOLO docs"

    sources = repo.list_sources()
    assert len(sources) == 1

    # dedup on (source_type, uri)
    from repositories.errors import RepositoryError
    with pytest.raises(RepositoryError) as exc:
        repo.register_source(
            source_type="local", name="dup", uri="/data/yolo.md",
            author="bob", license="MIT", trust_level=3,
        )
    assert exc.value.code == "CONFLICT"


# ── Document ────────────────────────────────────

def test_document_import_and_hash_dedup():
    repo = _make_repo()
    src = repo.register_source(
        source_type="web", name="Blog", uri="https://example.com/blog",
        author="author", license="CC", trust_level=3,
    )
    doc = repo.import_document(
        source_id=src["source_id"], title="Post 1", doc_type="markdown",
        version_label="v1", content_hash="abc123", language="en",
    )
    assert doc["title"] == "Post 1"
    assert doc["parse_status"] == "pending"

    loaded = repo.get_document(doc["document_id"])
    assert loaded == doc

    docs = repo.list_documents(source_id=src["source_id"])
    assert len(docs) == 1

    # content_hash dedup
    from repositories.errors import RepositoryError
    with pytest.raises(RepositoryError) as exc:
        repo.import_document(
            source_id=src["source_id"], title="Post 1 dup", doc_type="markdown",
            version_label="v1", content_hash="abc123", language="en",
        )
    assert exc.value.code == "CONFLICT"


# ── Chunk ───────────────────────────────────────

def test_chunk_storage_and_query_by_document():
    repo = _make_repo()
    src = repo.register_source(
        source_type="local", name="S1", uri="/s1",
        author="a", license="MIT", trust_level=3,
    )
    doc = repo.import_document(
        source_id=src["source_id"], title="D1", doc_type="markdown",
        version_label="v1", content_hash="hash1", language="zh",
    )
    chunks = [
        {"section_path": "§1", "chunk_index": 0, "raw_text": "hello", "token_count": 5},
        {"section_path": "§2", "chunk_index": 1, "raw_text": "world", "token_count": 5},
    ]
    saved = repo.save_chunks(document_id=doc["document_id"], chunks=chunks)
    assert len(saved) == 2

    loaded = repo.get_chunks_by_document(doc["document_id"])
    assert len(loaded) == 2
    assert loaded[0]["chunk_index"] == 0
    assert loaded[1]["chunk_index"] == 1


# ── Skill ───────────────────────────────────────

def test_skill_crud_and_unique_code():
    repo = _make_repo()
    skill = repo.create_skill(
        skill_code="train.augment.mosaic_scale",
        name="Mosaic增强",
        category="training",
        layer="augment",
        task_type="det",
        summary="小目标增强",
        maturity="draft",
    )
    assert skill["skill_code"] == "train.augment.mosaic_scale"

    updated = repo.update_skill(skill["skill_id"], maturity="verified")
    assert updated["maturity"] == "verified"

    loaded = repo.get_skill(skill["skill_id"])
    assert loaded["maturity"] == "verified"

    skills = repo.list_skills()
    assert len(skills) == 1

    # skill_code unique
    from repositories.errors import RepositoryError
    with pytest.raises(RepositoryError) as exc:
        repo.create_skill(
            skill_code="train.augment.mosaic_scale",
            name="dup", category="training", layer="augment",
            task_type="det", summary="dup", maturity="draft",
        )
    assert exc.value.code == "CONFLICT"


# ── Technique sub-tables ─────────────────────────

def _setup_skill(repo):
    return repo.create_skill(
        skill_code="model.backbone.resnet",
        name="ResNet", category="model", layer="backbone",
        task_type="det", summary="backbone", maturity="draft",
    )


def test_technique_version_crud():
    repo = _make_repo()
    skill = _setup_skill(repo)
    v = repo.upsert_version(
        technique_id=skill["skill_id"],
        framework="ultralytics",
        framework_version_range=">=8.2,<8.4",
        model_family="yolo11",
        implementation_mode="config_only",
    )
    assert v["framework"] == "ultralytics"
    assert v["status"] == "active"


def test_technique_condition_crud():
    repo = _make_repo()
    skill = _setup_skill(repo)
    c = repo.upsert_condition(
        technique_id=skill["skill_id"],
        condition_type="dataset",
        expr_json={"field": "dataset.stats.small_object_ratio", "op": ">=", "value": 0.25},
        severity="preferred",
    )
    assert c["condition_type"] == "dataset"
    assert c["severity"] == "preferred"


def test_technique_action_crud():
    repo = _make_repo()
    skill = _setup_skill(repo)
    a = repo.upsert_action(
        technique_id=skill["skill_id"],
        action_type="set_param",
        target_path="train_args.augment.mosaic",
        value_json=1.0,
        merge_mode="replace",
        reversible=True,
    )
    assert a["action_type"] == "set_param"
    assert a["reversible"] is True


def test_technique_tradeoff_crud():
    repo = _make_repo()
    skill = _setup_skill(repo)
    t = repo.upsert_tradeoff(
        technique_id=skill["skill_id"],
        dimension="kpi",
        effect_direction="up",
        magnitude="medium",
    )
    assert t["dimension"] == "kpi"
    assert t["effect_direction"] == "up"


def test_technique_relation_crud():
    repo = _make_repo()
    s1 = repo.create_skill(
        skill_code="a.b.c", name="A", category="training",
        layer="optimizer", task_type="det", summary="s", maturity="draft",
    )
    s2 = repo.create_skill(
        skill_code="a.b.d", name="B", category="training",
        layer="optimizer", task_type="det", summary="s", maturity="draft",
    )
    r = repo.upsert_relation(
        from_technique_id=s1["skill_id"],
        to_technique_id=s2["skill_id"],
        relation_type="incompatible_with",
        strength="hard",
    )
    assert r["relation_type"] == "incompatible_with"
    assert r["strength"] == "hard"


def test_technique_evidence_crud():
    repo = _make_repo()
    skill = _setup_skill(repo)
    e = repo.upsert_evidence(
        technique_id=skill["skill_id"],
        evidence_type="internal_run",
        source_ref="job_001",
        confidence_score=0.95,
    )
    assert e["evidence_type"] == "internal_run"
    assert e["confidence_score"] == 0.95


def test_technique_template_crud():
    repo = _make_repo()
    skill = _setup_skill(repo)
    t = repo.upsert_template(
        technique_id=skill["skill_id"],
        template_kind="train_args",
        payload_json={"lr": 0.01},
    )
    assert t["template_kind"] == "train_args"
    assert t["payload_json"] == {"lr": 0.01}


def test_technique_outcome_crud():
    repo = _make_repo()
    skill = _setup_skill(repo)
    o = repo.upsert_outcome(
        technique_id=skill["skill_id"],
        project_id="proj-1",
        baseline_job_id="job-base",
        candidate_job_id="job-cand",
        result_summary={"kpi_delta": 0.03},
        verdict="win",
    )
    assert o["verdict"] == "win"
    assert o["project_id"] == "proj-1"


# ── Planning & Retrieval ─────────────────────────

def test_planning_snapshot_record():
    repo = _make_repo()
    snap = repo.create_snapshot(
        planning_type="next_experiments",
        project_id="proj-1",
        evidence_fingerprint="fp123",
        selected_techniques=["train.augment.mosaic_scale"],
        rejected_techniques=[],
    )
    assert snap["planning_type"] == "next_experiments"
    assert snap["selected_techniques"] == ["train.augment.mosaic_scale"]

    loaded = repo.get_snapshot(snap["snapshot_id"])
    assert loaded == snap


def test_retrieval_log_write():
    repo = _make_repo()
    log = repo.write_retrieval_log(
        query_type="dataset_plan",
        query_signature={"task_type": "det"},
        candidate_techniques=["train.augment.mosaic_scale"],
        ranking_scores=[{"skill_code": "train.augment.mosaic_scale", "score": 0.9}],
    )
    assert log["query_type"] == "dataset_plan"
    assert log["candidate_techniques"] == ["train.augment.mosaic_scale"]
