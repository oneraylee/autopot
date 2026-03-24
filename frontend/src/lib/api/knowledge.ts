import { request } from "./request";
import type {
  KnowledgeSource,
  CreateSourcePayload,
  KnowledgeDocument,
  ImportDocumentPayload,
  KnowledgeChunk,
  TechniqueSummary,
  TechniqueDetail,
  TechniqueListResponse,
  TechniqueFilters,
  CreateTechniquePayload,
  ExtractTechniquesResponse,
  ArbitrationPayload,
  TechniqueRelation,
} from "@/features/knowledge/types";

export const knowledgeApi = {
  // ──────────────────────────────────────────────────
  // Knowledge Sources
  // ──────────────────────────────────────────────────
  createSource(payload: CreateSourcePayload): Promise<KnowledgeSource> {
    return request<KnowledgeSource>("POST", "/knowledge/sources", {
      body: payload,
    });
  },

  listSources(): Promise<{ items: KnowledgeSource[]; total: number }> {
    return request<{ items: KnowledgeSource[]; total: number }>(
      "GET",
      "/knowledge/sources",
    );
  },

  // ──────────────────────────────────────────────────
  // Knowledge Documents
  // ──────────────────────────────────────────────────
  importDocument(payload: ImportDocumentPayload): Promise<KnowledgeDocument> {
    return request<KnowledgeDocument>("POST", "/knowledge/documents/import", {
      body: payload,
    });
  },

  getDocument(documentId: string): Promise<KnowledgeDocument> {
    return request<KnowledgeDocument>(
      "GET",
      `/knowledge/documents/${encodeURIComponent(documentId)}`,
    );
  },

  getChunks(documentId: string): Promise<{ items: KnowledgeChunk[] }> {
    return request<{ items: KnowledgeChunk[] }>(
      "GET",
      `/knowledge/documents/${encodeURIComponent(documentId)}/chunks`,
    );
  },

  // ──────────────────────────────────────────────────
  // Techniques (Skill Cards)
  // ──────────────────────────────────────────────────
  extractSkills(documentId: string): Promise<ExtractTechniquesResponse> {
    return knowledgeApi.extractTechniques(documentId);
  },

  extractTechniques(documentId: string): Promise<ExtractTechniquesResponse> {
    return request<ExtractTechniquesResponse>(
      "POST",
      "/knowledge/techniques/extract",
      { body: { document_id: documentId } },
    );
  },

  createTechnique(payload: CreateTechniquePayload): Promise<TechniqueSummary> {
    return request<TechniqueSummary>("POST", "/knowledge/techniques", {
      body: payload,
    });
  },

  updateTechnique(
    techniqueId: string,
    payload: Partial<CreateTechniquePayload>,
  ): Promise<TechniqueSummary> {
    return request<TechniqueSummary>(
      "PUT",
      `/knowledge/techniques/${encodeURIComponent(techniqueId)}`,
      { body: payload },
    );
  },

  listTechniques(filters?: TechniqueFilters): Promise<TechniqueListResponse> {
    const params: Record<string, string> = {};
    if (filters) {
      for (const [key, val] of Object.entries(filters)) {
        if (val !== undefined && val !== null) {
          params[key] = String(val);
        }
      }
    }
    return request<
      TechniqueListResponse & { techniques?: TechniqueSummary[] }
    >("GET", "/knowledge/techniques", {
      params,
    }).then((response) => ({
      items: response.items ?? response.techniques ?? [],
      total:
        response.total ??
        response.items?.length ??
        response.techniques?.length ??
        0,
    }));
  },

  getTechnique(techniqueId: string): Promise<TechniqueDetail> {
    return request<TechniqueDetail>(
      "GET",
      `/knowledge/techniques/${encodeURIComponent(techniqueId)}`,
    );
  },

  getTechniqueRelations(techniqueId: string): Promise<{ items: TechniqueRelation[] }> {
    return request<{ items: TechniqueRelation[] }>(
      "GET",
      `/knowledge/techniques/${encodeURIComponent(techniqueId)}/relations`,
    );
  },

  publishTechnique(techniqueId: string): Promise<TechniqueSummary> {
    return request<TechniqueSummary>(
      "POST",
      `/knowledge/techniques/${encodeURIComponent(techniqueId)}/publish`,
    );
  },

  // ──────────────────────────────────────────────────
  // Retrieval / Conflict Resolution
  // ──────────────────────────────────────────────────
  resolveConflicts(payload: ArbitrationPayload): Promise<{ relation_id: string }> {
    return request<{ relation_id: string }>(
      "POST",
      "/knowledge/retrieval/resolve-conflicts",
      { body: payload },
    );
  },
};
