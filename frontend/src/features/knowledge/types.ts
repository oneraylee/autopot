// Knowledge System TypeScript Types
// Aligned with backend API and database schema

// ──────────────────────────────────────────────────
// Knowledge Source
// ──────────────────────────────────────────────────
export type SourceType = "local" | "web" | "official_doc" | "internal_experiment";
export type SourceStatus = "active" | "deprecated" | "blocked";

export interface KnowledgeSource {
  source_id: string;
  source_type: SourceType;
  name: string;
  uri: string;
  author?: string;
  license?: string;
  trust_level: number;
  status: SourceStatus;
  created_at?: string;
  updated_at?: string;
}

export interface CreateSourcePayload {
  source_type: SourceType;
  name: string;
  uri: string;
  author?: string;
  license?: string;
  trust_level: number;
}

// ──────────────────────────────────────────────────
// Knowledge Document
// ──────────────────────────────────────────────────
export type DocType = "markdown" | "html" | "pdf" | "note";
export type ParseStatus = "pending" | "parsed" | "failed";

export interface KnowledgeDocument {
  document_id: string;
  source_id: string;
  title: string;
  doc_type: DocType;
  version_label?: string;
  content_hash?: string;
  language?: string;
  parse_status: ParseStatus;
  published_at?: string;
  imported_at?: string;
}

export interface ImportDocumentPayload {
  source_id: string;
  title: string;
  doc_type: DocType;
  version_label?: string;
  language?: string;
  content?: string;
  url?: string;
}

// ──────────────────────────────────────────────────
// Knowledge Chunk
// ──────────────────────────────────────────────────
export interface KnowledgeChunk {
  chunk_id: string;
  document_id: string;
  section_path: string;
  chunk_index: number;
  raw_text?: string;
  token_count: number;
  keywords: string[];
  module_tags?: string[];
  task_tags?: string[];
  created_at?: string;
}

// ──────────────────────────────────────────────────
// Technique (Skill Card)
// ──────────────────────────────────────────────────
export type SkillCategory = "training" | "model" | "data" | "eval_deploy";
export type TaskType = "det" | "seg" | "cls" | "multi";
export type MaturityLevel = "draft" | "reviewed" | "verified" | "deprecated";
export type EvidenceLevel = "theory" | "community" | "internal_verified";
export type SkillStatus = "active" | "inactive";

export interface TechniqueCondition {
  condition_id: string;
  technique_id?: string;
  condition_type?: string;
  expr_json?: Record<string, unknown>;
  severity?: string;
  description: string;
}

export interface TechniqueAction {
  action_id: string;
  technique_id?: string;
  action_type?: string;
  target_path?: string;
  value_json?: Record<string, unknown>;
  description: string;
}

export interface TechniqueTradeoff {
  tradeoff_id: string;
  technique_id?: string;
  dimension: string;
  effect_direction: "up" | "down" | "mixed" | "uncertain";
  magnitude?: string;
  condition_text?: string;
  notes?: string;
}

export interface TechniqueEvidence {
  evidence_id: string;
  technique_id?: string;
  evidence_type: string;
  source_ref?: string;
  evidence_path?: string;
  confidence_score?: number;
  notes?: string;
}

export interface TechniqueRelation {
  relation_id: string;
  from_technique_id: string;
  to_technique_id: string;
  relation_type: string;
  strength?: string;
  reason_code?: string;
  description?: string;
}

export interface TechniqueSummary {
  technique_id: string;
  skill_code: string;
  name: string;
  category: SkillCategory;
  layer: string;
  task_type: TaskType;
  maturity: MaturityLevel;
  status: SkillStatus;
  summary?: string;
}

export interface TechniqueDetail extends TechniqueSummary {
  rationale?: string;
  evidence_level?: EvidenceLevel;
  default_priority?: number;
  conditions: TechniqueCondition[];
  actions: TechniqueAction[];
  tradeoffs: TechniqueTradeoff[];
  evidences: TechniqueEvidence[];
  relations?: TechniqueRelation[];
  created_at?: string;
  updated_at?: string;
}

export interface TechniqueListResponse {
  items: TechniqueSummary[];
  total: number;
}

export interface TechniqueFilters {
  category?: SkillCategory;
  layer?: string;
  task_type?: TaskType;
  maturity?: MaturityLevel;
  evidence_level?: EvidenceLevel;
  status?: SkillStatus;
}

export interface CreateTechniquePayload {
  skill_code: string;
  name: string;
  category: SkillCategory;
  layer: string;
  task_type: TaskType;
  summary?: string;
  rationale?: string;
  maturity?: MaturityLevel;
}

// ──────────────────────────────────────────────────
// Skill Extraction Candidate
// ──────────────────────────────────────────────────
export interface SkillCandidate {
  candidate_id: string;
  name: string;
  category: SkillCategory;
  layer: string;
  condition: string;
  action: string;
  tradeoff: string;
}

export interface ExtractTechniquesResponse {
  candidates: SkillCandidate[];
}

// ──────────────────────────────────────────────────
// Conflict
// ──────────────────────────────────────────────────
export interface ConflictPair {
  conflict_id: string;
  technique_a: { technique_id: string; name: string; summary: string };
  technique_b: { technique_id: string; name: string; summary: string };
  conflict_type: string;
  llm_suggestion: string;
}

export type ArbitrationVerdict = "keep_a" | "keep_b" | "split_condition" | "mark_experiment";

export interface ArbitrationPayload {
  conflict_id: string;
  verdict: ArbitrationVerdict;
  technique_ids: string[];
  constraints?: Record<string, unknown>;
}
