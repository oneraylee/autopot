"""Knowledge Ingestion Service – document import, multi-format parsing, URL fetch, skill extraction, conflict detection."""
from __future__ import annotations

import ast
import hashlib
import html as _html_module
import json
import re
import socket
import urllib.parse
import urllib.request
from html.parser import HTMLParser as _StdHTMLParser
from typing import Any


class IngestionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


# ── HTML tag stripper ────────────────────────────────────────────────────────

class _TagStripper(_StdHTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(p for p in self._parts if p.strip())


def _strip_html(html_text: str) -> str:
    stripper = _TagStripper()
    stripper.feed(html_text)
    return stripper.get_text()


# ── Token count (approximate) ────────────────────────────────────────────────

def _token_count(text: str) -> int:
    """Approximate token count: whitespace-split words."""
    return max(1, len(text.split()))


# ── Parsers ──────────────────────────────────────────────────────────────────

_VALID_DOC_TYPES = {"markdown", "html", "pdf", "notebook", "python"}


def _parse_markdown(content: str) -> list[dict]:
    """Split markdown by headings (# / ## / ###)."""
    if not content.strip():
        return []
    lines = content.splitlines(keepends=True)
    chunks: list[dict] = []
    current_path = ""
    current_lines: list[str] = []

    def _flush(path: str, raw_lines: list[str], idx: int) -> None:
        text = "".join(raw_lines).strip()
        if text:
            chunks.append({
                "section_path": path,
                "chunk_index": idx,
                "raw_text": text,
                "normalized_text": text.lower(),
                "token_count": _token_count(text),
            })

    chunk_idx = 0
    for line in lines:
        heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading_match:
            _flush(current_path, current_lines, chunk_idx)
            if current_lines:
                chunk_idx += 1
            current_lines = []
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            current_path = f"h{level}:{title}"
        else:
            current_lines.append(line)

    _flush(current_path, current_lines, chunk_idx)
    return chunks


def _parse_html(content: str) -> list[dict]:
    """Strip HTML tags and return as a single text chunk (or split by block elements)."""
    if not content.strip():
        return []
    plain = _strip_html(content).strip()
    if not plain:
        return []
    paragraphs = [p.strip() for p in re.split(r"\n{2,}|\s{3,}", plain) if p.strip()]
    if not paragraphs:
        paragraphs = [plain]
    return [
        {
            "section_path": f"para:{i}",
            "chunk_index": i,
            "raw_text": p,
            "normalized_text": p.lower(),
            "token_count": _token_count(p),
        }
        for i, p in enumerate(paragraphs)
    ]


def _parse_pdf(content: str) -> list[dict]:
    """Basic text-based PDF parsing (treats plain text as-is)."""
    if not content.strip():
        return []
    # Split by double newlines as paragraph separator
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", content) if p.strip()]
    if not paragraphs:
        paragraphs = [content.strip()]
    return [
        {
            "section_path": f"page:0/para:{i}",
            "chunk_index": i,
            "raw_text": p,
            "normalized_text": p.lower(),
            "token_count": _token_count(p),
        }
        for i, p in enumerate(paragraphs)
    ]


def _parse_notebook(content: str) -> list[dict]:
    """Parse Jupyter notebook JSON: each cell becomes a chunk."""
    if not content.strip():
        return []
    try:
        nb = json.loads(content)
    except json.JSONDecodeError as exc:
        raise IngestionError("PARSE_ERROR", f"Invalid notebook JSON: {exc}") from exc

    cells = nb.get("cells", [])
    chunks: list[dict] = []
    for i, cell in enumerate(cells):
        cell_type = cell.get("cell_type", "unknown")
        source = cell.get("source", [])
        if isinstance(source, list):
            text = "".join(source).strip()
        else:
            text = str(source).strip()
        if not text:
            continue
        chunks.append({
            "section_path": f"cell:{i}/type:{cell_type}",
            "chunk_index": i,
            "raw_text": text,
            "normalized_text": text.lower(),
            "token_count": _token_count(text),
        })
    return chunks


def _parse_python(content: str) -> list[dict]:
    """Parse Python source: split by top-level function/class definitions."""
    if not content.strip():
        return []
    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        raise IngestionError("PARSE_ERROR", f"Invalid Python syntax: {exc}") from exc

    source_lines = content.splitlines(keepends=True)
    chunks: list[dict] = []
    chunk_idx = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Only top-level nodes (parent is Module)
            if not isinstance(getattr(node, "_parent", None), (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start = node.lineno - 1
                end = node.end_lineno  # type: ignore[attr-defined]
                text = "".join(source_lines[start:end]).strip()
                name = node.name
                kind = "class" if isinstance(node, ast.ClassDef) else "function"
                chunks.append({
                    "section_path": f"{kind}:{name}",
                    "chunk_index": chunk_idx,
                    "raw_text": text,
                    "normalized_text": text.lower(),
                    "token_count": _token_count(text),
                })
                chunk_idx += 1

    # Set parent references so we can check if a node is top-level
    # We need a second pass since _parent isn't set by default
    if not chunks:
        # Fallback: try module-level docstring + whole file
        chunks.append({
            "section_path": "module:main",
            "chunk_index": 0,
            "raw_text": content.strip(),
            "normalized_text": content.strip().lower(),
            "token_count": _token_count(content),
        })
    return chunks


def _parse_python_top_level(content: str) -> list[dict]:
    """Parse Python source: only top-level function/class definitions."""
    if not content.strip():
        return []
    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        raise IngestionError("PARSE_ERROR", f"Invalid Python syntax: {exc}") from exc

    source_lines = content.splitlines(keepends=True)
    chunks: list[dict] = []
    chunk_idx = 0

    for node in tree.body:  # type: ignore[attr-defined]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno - 1
            end = node.end_lineno  # type: ignore[attr-defined]
            text = "".join(source_lines[start:end]).strip()
            name = node.name
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            chunks.append({
                "section_path": f"{kind}:{name}",
                "chunk_index": chunk_idx,
                "raw_text": text,
                "normalized_text": text.lower(),
                "token_count": _token_count(text),
            })
            chunk_idx += 1

    if not chunks:
        chunks.append({
            "section_path": "module:main",
            "chunk_index": 0,
            "raw_text": content.strip(),
            "normalized_text": content.strip().lower(),
            "token_count": _token_count(content),
        })
    return chunks


_PARSERS = {
    "markdown": _parse_markdown,
    "html": _parse_html,
    "pdf": _parse_pdf,
    "notebook": _parse_notebook,
    "python": _parse_python_top_level,
}


# ── SSRF Guard ───────────────────────────────────────────────────────────────

_PRIVATE_IP_RANGES = [
    re.compile(r"^127\."),
    re.compile(r"^10\."),
    re.compile(r"^172\.(1[6-9]|2\d|3[01])\."),
    re.compile(r"^192\.168\."),
    re.compile(r"^::1$"),
    re.compile(r"^localhost$", re.IGNORECASE),
    re.compile(r"^0\.0\.0\.0$"),
]


def _is_private_host(hostname: str) -> bool:
    for pat in _PRIVATE_IP_RANGES:
        if pat.match(hostname):
            return True
    try:
        ip = socket.gethostbyname(hostname)
        for pat in _PRIVATE_IP_RANGES:
            if pat.match(ip):
                return True
    except OSError:
        pass
    return False


# ── Skill name normalizer ────────────────────────────────────────────────────

def _normalize_name(name: str) -> str:
    """Lowercase, replace spaces/hyphens with underscore."""
    return re.sub(r"[\s\-]+", "_", name.strip().lower())


# ══════════════════════════════════════════════════════════════════════════════
# Service
# ══════════════════════════════════════════════════════════════════════════════

class KnowledgeIngestionService:
    """Handles document import, parsing, URL fetching, skill extraction, and conflict detection."""

    def __init__(
        self,
        *,
        knowledge_repo: Any,
        llm_gateway: Any,
        allowed_domains: list[str] | None = None,
        fetch_timeout: float = 10.0,
    ) -> None:
        self._repo = knowledge_repo
        self._llm = llm_gateway
        self._allowed_domains: list[str] = allowed_domains or []
        self._fetch_timeout = fetch_timeout

    # ── Source ───────────────────────────────────────────────────────────────

    def register_source(
        self,
        *,
        source_type: str,
        name: str,
        uri: str,
        author: str,
        license: str,
        trust_level: int,
    ) -> dict:
        return self._repo.register_source(
            source_type=source_type,
            name=name,
            uri=uri,
            author=author,
            license=license,
            trust_level=trust_level,
        )

    # ── Document import ──────────────────────────────────────────────────────

    def import_document(
        self,
        *,
        source_id: str,
        title: str,
        doc_type: str,
        version_label: str,
        content: str,
        language: str,
    ) -> dict:
        if doc_type not in _VALID_DOC_TYPES:
            raise IngestionError(
                "VALIDATION_ERROR",
                f"unsupported doc_type '{doc_type}'; valid: {sorted(_VALID_DOC_TYPES)}",
            )
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        doc = self._repo.import_document(
            source_id=source_id,
            title=title,
            doc_type=doc_type,
            version_label=version_label,
            content_hash=content_hash,
            language=language,
        )
        # Cache raw content in memory (keyed by document_id)
        if not hasattr(self, "_content_cache"):
            self._content_cache: dict[str, str] = {}
        self._content_cache[doc["document_id"]] = content
        return doc

    # ── Parse ────────────────────────────────────────────────────────────────

    def parse_document(self, document_id: str) -> list[dict]:
        doc = self._repo.get_document(document_id)
        doc_type = doc["doc_type"]
        content = getattr(self, "_content_cache", {}).get(document_id, "")

        parser = _PARSERS.get(doc_type)
        if parser is None:
            raise IngestionError("PARSE_ERROR", f"no parser for doc_type '{doc_type}'")

        raw_chunks = parser(content)
        if not raw_chunks:
            return []

        saved = self._repo.save_chunks(document_id=document_id, chunks=raw_chunks)
        return saved

    # ── URL fetch ────────────────────────────────────────────────────────────

    def _http_get(self, url: str, timeout: float) -> str:
        req = urllib.request.Request(url, headers={"User-Agent": "AutoPot-KnowledgeBot/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 – SSRF guarded above
            return resp.read().decode(errors="replace")

    def fetch_web_content(self, url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname or ""

        # Whitelist check
        if self._allowed_domains:
            if not any(hostname == d or hostname.endswith("." + d) for d in self._allowed_domains):
                raise IngestionError(
                    "SSRF_FORBIDDEN",
                    f"domain '{hostname}' not in allowed whitelist",
                )

        # Block private / internal IPs
        if _is_private_host(hostname):
            raise IngestionError("SSRF_FORBIDDEN", f"host '{hostname}' resolves to a private address")

        return self._http_get(url, self._fetch_timeout)

    # ── Skill extraction ─────────────────────────────────────────────────────

    def extract_skills(self, document_id: str) -> list[dict]:
        """Call LLM Gateway to extract candidate skill structs from document chunks."""
        chunks = self._repo.get_chunks_by_document(document_id)
        if not chunks:
            return []

        # Build prompt text from chunks
        chunk_texts = "\n\n---\n\n".join(c["raw_text"] for c in chunks[:10])  # limit context
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a knowledge engineer. Extract training techniques from the given text. "
                    "Return a JSON array where each element has: name, category, layer, condition, action, tradeoff."
                ),
            },
            {"role": "user", "content": chunk_texts},
        ]

        try:
            response = self._llm.chat_completion(
                task_type="skill_extract", messages=messages
            )
            raw_content = response.get("content", "")
            candidates = json.loads(raw_content)
            if not isinstance(candidates, list):
                return []
            # Validate each candidate has required fields
            required = {"name", "category", "layer"}
            valid = [c for c in candidates if required.issubset(c.keys())]
            return valid
        except (json.JSONDecodeError, KeyError, TypeError):
            return []

    # ── Name normalization ───────────────────────────────────────────────────

    def normalize_skill_names(self, skills: list[dict]) -> list[dict]:
        """Normalize skill names: lowercase + underscore."""
        result = []
        for skill in skills:
            normalized = dict(skill)
            normalized["name"] = _normalize_name(skill.get("name", ""))
            result.append(normalized)
        return result

    # ── Duplicate detection ──────────────────────────────────────────────────

    def detect_duplicates(self, skill: dict) -> dict:
        """Check if a skill name already exists in the repository."""
        new_name = _normalize_name(skill.get("name", ""))
        existing = self._repo.list_skills()
        for s in existing:
            if _normalize_name(s.get("name", "")) == new_name:
                return {"is_duplicate": True, "suggestion": "merge", "existing_id": s["skill_id"]}
        return {"is_duplicate": False, "suggestion": None, "existing_id": None}

    # ── Conflict detection ───────────────────────────────────────────────────

    def detect_conflicts_on_import(
        self,
        new_skill: dict,
        *,
        write_relations: bool = False,
    ) -> list[dict]:
        """Detect parameter and structural conflicts with existing skills."""
        conflicts: list[dict] = []

        new_action = new_skill.get("action", {})
        new_target = new_action.get("target_path") if isinstance(new_action, dict) else None
        new_value = new_action.get("value") if isinstance(new_action, dict) else None
        new_layer = new_skill.get("layer")

        existing_skills = self._repo.list_skills()

        for skill in existing_skills:
            skill_id = skill["skill_id"]
            actions = self._repo._actions.get(skill_id, [])

            # Parameter conflict: same target_path, different value
            for act in actions:
                if new_target and act.get("target_path") == new_target:
                    existing_value = act.get("value_json")
                    if existing_value != new_value:
                        conflict = {
                            "conflict_type": "param_conflict",
                            "existing_skill_id": skill_id,
                            "target_path": new_target,
                            "existing_value": existing_value,
                            "new_value": new_value,
                        }
                        conflicts.append(conflict)
                        if write_relations:
                            self._repo.upsert_relation(
                                from_technique_id=skill_id,
                                to_technique_id=skill_id,
                                relation_type="param_conflict",
                                strength="strong",
                                reason_code="PARAM_CONFLICT",
                                description=f"target_path={new_target}",
                            )

        # Structural conflict: same layer, use LLM to assess
        if new_layer and existing_skills:
            same_layer_skills = [s for s in existing_skills if s.get("layer") == new_layer]
            if same_layer_skills:
                try:
                    skill_summaries = [
                        {"id": s["skill_id"], "name": s["name"], "summary": s["summary"]}
                        for s in same_layer_skills[:5]
                    ]
                    messages = [
                        {
                            "role": "system",
                            "content": (
                                "You are a conflict analyzer. Check if a new skill conflicts structurally "
                                "with existing skills in the same layer. "
                                "Return JSON array with elements having conflict_type and reason."
                            ),
                        },
                        {
                            "role": "user",
                            "content": json.dumps({
                                "new_skill": new_skill,
                                "existing_in_same_layer": skill_summaries,
                            }),
                        },
                    ]
                    response = self._llm.chat_completion(
                        task_type="conflict_detect", messages=messages
                    )
                    raw = response.get("content", "[]")
                    llm_conflicts = json.loads(raw)
                    if isinstance(llm_conflicts, list):
                        struct_conflicts = [
                            c for c in llm_conflicts
                            if isinstance(c, dict) and c.get("conflict_type") == "structural_conflict"
                        ]
                        if struct_conflicts:
                            conflicts.extend(struct_conflicts)
                            if write_relations and same_layer_skills:
                                for sc in struct_conflicts:
                                    self._repo.upsert_relation(
                                        from_technique_id=same_layer_skills[0]["skill_id"],
                                        to_technique_id=same_layer_skills[0]["skill_id"],
                                        relation_type="structural_conflict",
                                        strength="moderate",
                                        reason_code="STRUCT_CONFLICT",
                                        description=sc.get("reason", ""),
                                    )
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass

        return conflicts
