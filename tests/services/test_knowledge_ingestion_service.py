"""RED tests for KnowledgeIngestionService (Phase 2 Step 1 & Step 2)."""
import hashlib
import json
import pytest
from unittest.mock import MagicMock


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_repo():
    from repositories.knowledge_repository import KnowledgeRepository
    return KnowledgeRepository()


def _make_gateway(mock_response: dict | None = None):
    """Return a mock LLMGatewayService."""
    gw = MagicMock()
    if mock_response is not None:
        gw.chat_completion.return_value = mock_response
    else:
        gw.chat_completion.return_value = {
            "content": json.dumps([{
                "name": "label_smoothing",
                "category": "regularization",
                "layer": "training",
                "condition": "overfitting detected",
                "action": {"target_path": "trainer.label_smoothing", "value": 0.1},
                "tradeoff": "slight accuracy drop",
            }]),
            "usage": {"input_tokens": 300, "output_tokens": 100},
        }
    return gw


def _make_service(mock_llm_response: dict | None = None):
    from services.knowledge_ingestion_service import KnowledgeIngestionService
    repo = _make_repo()
    gw = _make_gateway(mock_llm_response)
    return KnowledgeIngestionService(knowledge_repo=repo, llm_gateway=gw), repo, gw


# ══════════════════════════════════════════════════════════════════════════════
# Step 1: Source 注册
# ══════════════════════════════════════════════════════════════════════════════

def test_register_source_success():
    svc, repo, _ = _make_service()
    result = svc.register_source(
        source_type="doc",
        name="Ultralytics Docs",
        uri="https://docs.ultralytics.com",
        author="Ultralytics",
        license="MIT",
        trust_level=5,
    )
    assert result["source_id"] is not None
    assert result["source_type"] == "doc"
    assert result["uri"] == "https://docs.ultralytics.com"


def test_register_source_duplicate_rejected():
    svc, _, _ = _make_service()
    svc.register_source(
        source_type="doc",
        name="Ultralytics Docs",
        uri="https://docs.ultralytics.com",
        author="Ultralytics",
        license="MIT",
        trust_level=5,
    )
    with pytest.raises(Exception) as exc_info:
        svc.register_source(
            source_type="doc",
            name="Ultralytics Docs 2",
            uri="https://docs.ultralytics.com",
            author="Ultralytics",
            license="MIT",
            trust_level=5,
        )
    assert "CONFLICT" in str(exc_info.value) or "already exists" in str(exc_info.value).lower()


# ══════════════════════════════════════════════════════════════════════════════
# Step 1: Document 导入
# ══════════════════════════════════════════════════════════════════════════════

def test_import_document_sets_pending_status():
    svc, repo, _ = _make_service()
    src = svc.register_source(
        source_type="doc", name="S", uri="https://example.com",
        author="A", license="MIT", trust_level=3,
    )
    content = "# Hello\n\nSome markdown content."
    result = svc.import_document(
        source_id=src["source_id"],
        title="Test Doc",
        doc_type="markdown",
        version_label="v1",
        content=content,
        language="zh",
    )
    assert result["parse_status"] == "pending"
    assert result["document_id"] is not None


def test_import_document_content_hash_dedup():
    svc, _, _ = _make_service()
    src = svc.register_source(
        source_type="doc", name="S2", uri="https://example2.com",
        author="A", license="MIT", trust_level=3,
    )
    content = "Same content here."
    svc.import_document(
        source_id=src["source_id"],
        title="Doc 1", doc_type="markdown",
        version_label="v1", content=content, language="zh",
    )
    with pytest.raises(Exception) as exc_info:
        svc.import_document(
            source_id=src["source_id"],
            title="Doc 2 (same content)", doc_type="markdown",
            version_label="v1", content=content, language="zh",
        )
    assert "CONFLICT" in str(exc_info.value) or "already exists" in str(exc_info.value).lower()


def test_import_document_invalid_doc_type_error():
    svc, _, _ = _make_service()
    src = svc.register_source(
        source_type="doc", name="S3", uri="https://example3.com",
        author="A", license="MIT", trust_level=3,
    )
    with pytest.raises(Exception) as exc_info:
        svc.import_document(
            source_id=src["source_id"],
            title="Bad doc", doc_type="unknown_type",
            version_label="v1", content="some content", language="zh",
        )
    error_msg = str(exc_info.value).lower()
    assert "doc_type" in error_msg or "invalid" in error_msg or "unsupported" in error_msg


# ══════════════════════════════════════════════════════════════════════════════
# Step 1: Markdown 解析与切分
# ══════════════════════════════════════════════════════════════════════════════

MARKDOWN_CONTENT = """# Chapter 1

Introduction content here. This is a paragraph.

## Section 1.1

Details about section 1.1 with more text here.

## Section 1.2

Details about section 1.2.

# Chapter 2

Second chapter content.
"""


def test_parse_markdown_chapter_split():
    svc, _, _ = _make_service()
    src = svc.register_source(
        source_type="doc", name="MD", uri="https://md.example.com",
        author="A", license="MIT", trust_level=3,
    )
    doc = svc.import_document(
        source_id=src["source_id"], title="MD Doc",
        doc_type="markdown", version_label="v1",
        content=MARKDOWN_CONTENT, language="zh",
    )
    chunks = svc.parse_document(doc["document_id"])
    # Should produce at least 4 chunks (Chapter 1, Section 1.1, Section 1.2, Chapter 2)
    assert len(chunks) >= 4


def test_chunk_fields_complete():
    svc, _, _ = _make_service()
    src = svc.register_source(
        source_type="doc", name="MD2", uri="https://md2.example.com",
        author="A", license="MIT", trust_level=3,
    )
    doc = svc.import_document(
        source_id=src["source_id"], title="MD2 Doc",
        doc_type="markdown", version_label="v1",
        content=MARKDOWN_CONTENT, language="zh",
    )
    chunks = svc.parse_document(doc["document_id"])
    assert len(chunks) > 0
    for chunk in chunks:
        assert "section_path" in chunk
        assert "chunk_index" in chunk
        assert "token_count" in chunk
        assert isinstance(chunk["chunk_index"], int)
        assert isinstance(chunk["token_count"], int)
        assert chunk["token_count"] > 0


def test_parse_empty_document_zero_chunks():
    svc, _, _ = _make_service()
    src = svc.register_source(
        source_type="doc", name="Empty", uri="https://empty.example.com",
        author="A", license="MIT", trust_level=3,
    )
    doc = svc.import_document(
        source_id=src["source_id"], title="Empty Doc",
        doc_type="markdown", version_label="v1",
        content="", language="zh",
    )
    chunks = svc.parse_document(doc["document_id"])
    assert chunks == []


# ══════════════════════════════════════════════════════════════════════════════
# Step 1: HTML 解析
# ══════════════════════════════════════════════════════════════════════════════

HTML_CONTENT = """<html><body>
<h1>Title</h1>
<p>Paragraph with <b>bold</b> and <em>italic</em> text.</p>
<p>Second paragraph.</p>
</body></html>"""


def test_parse_html_strips_tags():
    svc, _, _ = _make_service()
    src = svc.register_source(
        source_type="web", name="HTML", uri="https://html.example.com",
        author="A", license="MIT", trust_level=3,
    )
    doc = svc.import_document(
        source_id=src["source_id"], title="HTML Doc",
        doc_type="html", version_label="v1",
        content=HTML_CONTENT, language="zh",
    )
    chunks = svc.parse_document(doc["document_id"])
    assert len(chunks) > 0
    for chunk in chunks:
        raw = chunk.get("raw_text", "")
        assert "<html>" not in raw
        assert "<body>" not in raw
        assert "<h1>" not in raw
        assert "<b>" not in raw
        assert "Title" in raw or "Paragraph" in raw or "Second" in raw


# ══════════════════════════════════════════════════════════════════════════════
# Step 1: PDF 解析（mock）
# ══════════════════════════════════════════════════════════════════════════════

def test_parse_pdf_basic_text():
    """PDF parsing should extract text. We use mock bytes and a mock extractor."""
    svc, _, _ = _make_service()
    src = svc.register_source(
        source_type="doc", name="PDF", uri="https://pdf.example.com",
        author="A", license="MIT", trust_level=3,
    )
    # Pass raw text content as PDF (service should handle plain text fallback or mock)
    pdf_content = "Introduction to training techniques.\n\nSection: Label Smoothing\nApply label smoothing."
    doc = svc.import_document(
        source_id=src["source_id"], title="PDF Doc",
        doc_type="pdf", version_label="v1",
        content=pdf_content, language="zh",
    )
    chunks = svc.parse_document(doc["document_id"])
    # Should produce at least 1 chunk with text content
    assert len(chunks) >= 1
    all_text = " ".join(c.get("raw_text", "") for c in chunks)
    assert len(all_text.strip()) > 0


# ══════════════════════════════════════════════════════════════════════════════
# Step 1: Notebook 解析
# ══════════════════════════════════════════════════════════════════════════════

NOTEBOOK_CONTENT = json.dumps({
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {},
    "cells": [
        {
            "cell_type": "markdown",
            "source": ["# Training Tutorial\n", "This is a guide."],
            "metadata": {},
        },
        {
            "cell_type": "code",
            "source": ["def train():\n", "    pass\n"],
            "metadata": {},
            "outputs": [],
            "execution_count": None,
        },
        {
            "cell_type": "markdown",
            "source": ["## Notes\n", "Remember to set learning rate."],
            "metadata": {},
        },
    ],
})


def test_parse_notebook_cells():
    svc, _, _ = _make_service()
    src = svc.register_source(
        source_type="doc", name="NB", uri="https://nb.example.com",
        author="A", license="MIT", trust_level=3,
    )
    doc = svc.import_document(
        source_id=src["source_id"], title="Notebook",
        doc_type="notebook", version_label="v1",
        content=NOTEBOOK_CONTENT, language="zh",
    )
    chunks = svc.parse_document(doc["document_id"])
    # Should have 3 chunks (2 markdown cells + 1 code cell)
    assert len(chunks) == 3
    cell_types = [c.get("section_path", "") for c in chunks]
    # At least one code chunk and one markdown chunk
    has_code = any("code" in ct.lower() for ct in cell_types)
    has_md = any("markdown" in ct.lower() for ct in cell_types)
    assert has_code
    assert has_md


# ══════════════════════════════════════════════════════════════════════════════
# Step 1: Python 文件解析
# ══════════════════════════════════════════════════════════════════════════════

PYTHON_CONTENT = '''"""Module docstring."""


def compute_loss(predictions, targets):
    """Compute loss."""
    return sum(predictions) - sum(targets)


def preprocess(data):
    """Preprocess data."""
    return [x * 2 for x in data]


class Trainer:
    """Trainer class."""

    def fit(self, model, data):
        """Fit the model."""
        pass

    def evaluate(self, model, data):
        """Evaluate the model."""
        pass
'''


def test_parse_python_by_function_class():
    svc, _, _ = _make_service()
    src = svc.register_source(
        source_type="repo", name="PY", uri="https://py.example.com",
        author="A", license="MIT", trust_level=3,
    )
    doc = svc.import_document(
        source_id=src["source_id"], title="Python File",
        doc_type="python", version_label="v1",
        content=PYTHON_CONTENT, language="zh",
    )
    chunks = svc.parse_document(doc["document_id"])
    # Should produce chunks for: compute_loss, preprocess, Trainer (class)
    assert len(chunks) >= 3
    # Each chunk section_path should identify function or class
    paths = [c.get("section_path", "") for c in chunks]
    all_paths = " ".join(paths)
    assert "compute_loss" in all_paths or "preprocess" in all_paths or "Trainer" in all_paths


# ══════════════════════════════════════════════════════════════════════════════
# Step 1: URL 抓取与 SSRF 防护
# ══════════════════════════════════════════════════════════════════════════════

def test_fetch_url_whitelist_pass(monkeypatch):
    from services.knowledge_ingestion_service import KnowledgeIngestionService
    repo = _make_repo()
    gw = _make_gateway()
    svc = KnowledgeIngestionService(
        knowledge_repo=repo,
        llm_gateway=gw,
        allowed_domains=["docs.ultralytics.com"],
    )

    # Mock the HTTP fetch to return dummy content
    def mock_fetch(url: str, timeout: float) -> str:
        return "<html><body><p>Mocked content from docs.</p></body></html>"

    monkeypatch.setattr(svc, "_http_get", mock_fetch)
    result = svc.fetch_web_content("https://docs.ultralytics.com/guides/tips")
    assert len(result) > 0


def test_fetch_url_non_whitelist_rejected():
    from services.knowledge_ingestion_service import KnowledgeIngestionService
    repo = _make_repo()
    gw = _make_gateway()
    svc = KnowledgeIngestionService(
        knowledge_repo=repo,
        llm_gateway=gw,
        allowed_domains=["docs.ultralytics.com"],
    )
    with pytest.raises(Exception) as exc_info:
        svc.fetch_web_content("https://evil.attacker.com/steal")
    error_msg = str(exc_info.value).lower()
    assert "not allowed" in error_msg or "whitelist" in error_msg or "ssrf" in error_msg or "forbidden" in error_msg


def test_fetch_url_timeout_returns_error(monkeypatch):
    from services.knowledge_ingestion_service import KnowledgeIngestionService
    repo = _make_repo()
    gw = _make_gateway()
    svc = KnowledgeIngestionService(
        knowledge_repo=repo,
        llm_gateway=gw,
        allowed_domains=["docs.ultralytics.com"],
    )

    def mock_fetch_timeout(url: str, timeout: float) -> str:
        raise TimeoutError("Request timed out")

    monkeypatch.setattr(svc, "_http_get", mock_fetch_timeout)
    with pytest.raises(Exception) as exc_info:
        svc.fetch_web_content("https://docs.ultralytics.com/slow-page")
    error_msg = str(exc_info.value).lower()
    assert "timeout" in error_msg or "timed out" in error_msg


# ══════════════════════════════════════════════════════════════════════════════
# Step 2: 技能抽取
# ══════════════════════════════════════════════════════════════════════════════

def test_extract_skills_produces_candidate_structs():
    svc, _, gw = _make_service()
    src = svc.register_source(
        source_type="doc", name="ExtractSrc", uri="https://extract.example.com",
        author="A", license="MIT", trust_level=3,
    )
    doc = svc.import_document(
        source_id=src["source_id"], title="Extract Doc",
        doc_type="markdown", version_label="v1",
        content=MARKDOWN_CONTENT, language="zh",
    )
    svc.parse_document(doc["document_id"])

    candidates = svc.extract_skills(doc["document_id"])
    assert isinstance(candidates, list)
    assert len(candidates) > 0
    for c in candidates:
        assert "name" in c
        assert "category" in c
        assert "layer" in c


def test_extract_skills_noncompliant_llm_marks_failed():
    """When LLM returns non-compliant JSON, result should be marked as failed."""
    bad_response = {"content": "This is not valid JSON skill data", "usage": {}}
    svc, _, gw = _make_service(mock_llm_response=bad_response)
    src = svc.register_source(
        source_type="doc", name="BadSrc", uri="https://bad.example.com",
        author="A", license="MIT", trust_level=3,
    )
    doc = svc.import_document(
        source_id=src["source_id"], title="Bad LLM Doc",
        doc_type="markdown", version_label="v1",
        content=MARKDOWN_CONTENT, language="zh",
    )
    svc.parse_document(doc["document_id"])

    result = svc.extract_skills(doc["document_id"])
    # Should indicate extraction failed or return empty list
    assert result == [] or (len(result) > 0 and all(r.get("status") == "failed" for r in result))


def test_normalize_skill_names_consistent():
    svc, _, _ = _make_service()
    skills = [
        {"name": "Label Smoothing", "category": "reg", "layer": "training"},
        {"name": "label_smoothing", "category": "reg", "layer": "training"},
        {"name": "LABEL SMOOTHING", "category": "reg", "layer": "training"},
    ]
    normalized = svc.normalize_skill_names(skills)
    names = [s["name"] for s in normalized]
    # All should be normalized to the same form
    assert len(set(names)) == 1


def test_dedup_same_name_suggests_merge():
    svc, repo, _ = _make_service()
    # Pre-create an existing skill in the repo
    repo.create_skill(
        skill_code="REG-001",
        name="label_smoothing",
        category="regularization",
        layer="training",
        task_type="classification",
        summary="Apply label smoothing",
        maturity="verified",
    )

    new_skill = {
        "name": "label_smoothing",
        "category": "regularization",
        "layer": "training",
        "condition": "overfitting",
        "action": {},
        "tradeoff": "",
    }
    result = svc.detect_duplicates(new_skill)
    assert result["is_duplicate"] is True
    assert result["suggestion"] == "merge"


def test_multi_evidence_links_single_skill():
    """Multiple chunks from different documents can link to the same skill."""
    svc, repo, _ = _make_service()
    skill = repo.create_skill(
        skill_code="REG-002",
        name="dropout",
        category="regularization",
        layer="training",
        task_type="classification",
        summary="Apply dropout",
        maturity="draft",
    )
    skill_id = skill["skill_id"]

    # Link two evidence items to the same skill
    ev1 = repo.upsert_evidence(
        technique_id=skill_id,
        evidence_type="document_chunk",
        source_ref="doc-1/chunk-0",
        confidence_score=0.9,
    )
    ev2 = repo.upsert_evidence(
        technique_id=skill_id,
        evidence_type="document_chunk",
        source_ref="doc-2/chunk-1",
        confidence_score=0.85,
    )

    evidences = repo._evidences.get(skill_id, [])
    assert len(evidences) == 2
    assert ev1["technique_id"] == skill_id
    assert ev2["technique_id"] == skill_id


# ══════════════════════════════════════════════════════════════════════════════
# Step 2: 冲突检测
# ══════════════════════════════════════════════════════════════════════════════

def test_conflict_detect_param_conflict():
    """Same target_path with different values → parameter conflict."""
    svc, repo, _ = _make_service()
    # Existing skill has target_path trainer.label_smoothing = 0.1
    skill_a = repo.create_skill(
        skill_code="LS-001",
        name="label_smoothing_low",
        category="regularization",
        layer="training",
        task_type="classification",
        summary="Low label smoothing",
        maturity="draft",
    )
    repo.upsert_action(
        technique_id=skill_a["skill_id"],
        action_type="set_param",
        target_path="trainer.label_smoothing",
        value_json=0.1,
    )

    # New skill has same target_path but value 0.3
    new_skill = {
        "name": "label_smoothing_high",
        "category": "regularization",
        "layer": "training",
        "action": {"target_path": "trainer.label_smoothing", "value": 0.3},
    }
    conflicts = svc.detect_conflicts_on_import(new_skill)
    param_conflicts = [c for c in conflicts if c["conflict_type"] == "param_conflict"]
    assert len(param_conflicts) > 0


def test_conflict_detect_structural_conflict():
    """Same layer with substantially different structures → structural conflict."""
    svc, repo, gw = _make_service()
    # Existing skill in training layer
    skill_b = repo.create_skill(
        skill_code="STRUCT-001",
        name="adamw_optimizer",
        category="optimizer",
        layer="training",
        task_type="classification",
        summary="Use AdamW optimizer",
        maturity="draft",
    )

    conflict_response = {"content": json.dumps([{
        "conflict_type": "structural_conflict",
        "reason": "Different optimizer strategies in same layer",
    }]), "usage": {}}
    gw.chat_completion.return_value = conflict_response

    new_skill = {
        "name": "sgd_optimizer",
        "category": "optimizer",
        "layer": "training",  # same layer
        "action": {"target_path": "trainer.optimizer", "value": "SGD"},
    }
    conflicts = svc.detect_conflicts_on_import(new_skill)
    struct_conflicts = [c for c in conflicts if c["conflict_type"] == "structural_conflict"]
    assert len(struct_conflicts) > 0


def test_conflict_detect_writes_relation():
    """Detected conflict should be written to technique_relation."""
    svc, repo, gw = _make_service()
    skill_c = repo.create_skill(
        skill_code="REL-001",
        name="cosine_lr",
        category="scheduler",
        layer="training",
        task_type="classification",
        summary="Cosine LR schedule",
        maturity="draft",
    )
    repo.upsert_action(
        technique_id=skill_c["skill_id"],
        action_type="set_param",
        target_path="trainer.scheduler",
        value_json="cosine",
    )

    conflict_response = {"content": json.dumps([{
        "conflict_type": "param_conflict",
        "reason": "Same scheduler parameter, different strategies",
    }]), "usage": {}}
    gw.chat_completion.return_value = conflict_response

    new_skill = {
        "name": "step_lr",
        "category": "scheduler",
        "layer": "training",
        "action": {"target_path": "trainer.scheduler", "value": "step"},
    }

    initial_relation_count = len(repo._relations)
    svc.detect_conflicts_on_import(new_skill, write_relations=True)
    assert len(repo._relations) > initial_relation_count


def test_no_conflict_normal_import():
    """When no conflicts found, no relation written, returns empty conflict list."""
    svc, repo, _ = _make_service()
    new_skill = {
        "name": "unique_technique_xyz",
        "category": "data_aug",
        "layer": "preprocessing",
        "action": {"target_path": "augment.mosaic_prob", "value": 0.5},
    }
    initial_relation_count = len(repo._relations)
    conflicts = svc.detect_conflicts_on_import(new_skill)
    assert conflicts == []
    assert len(repo._relations) == initial_relation_count
