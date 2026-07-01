export interface Citation {
  source_url: string;
  source_type: string;
  excerpt: string;
  confidence: number;
  last_verified_at?: string | null;
}

export interface CompanyResult {
  company_id?: number | null;
  name?: string | null;
  address?: string | null;
  country?: string | null;
  website?: string | null;
  contact?: string | null;
  products: string[];
}

export interface SearchResponse {
  answer: string;
  citations: Citation[];
  companies: CompanyResult[];
  confidence_overall: number;
  insufficient_data: boolean;
}

export interface SearchRequest {
  query: string;
  top_k?: number;
  company_id?: number | null;
  fabric_tags?: string[];
}

export interface CompanyDetail {
  id: number;
  name: string;
  name_ja?: string | null;
  company_type?: string | null;
  founded_year?: number | null;
  website_url?: string | null;
  description?: string | null;
  certifications: string[];
  products: { id: number; name: string; fabric_type?: string | null }[];
  contacts: { type: string; value: string }[];
  addresses: { city?: string | null; prefecture?: string | null; country?: string | null }[];
}

export interface Swatch {
  id: number;
  label: string;
  hex_color: string;
  rgb_r: number;
  rgb_g: number;
  rgb_b: number;
  photo_storage_path: string;
  notes?: string | null;
  created_at: string;
}

export interface PatternSwatchRoleInfo {
  swatch_id: number;
  role_index: number;
  hex_color: string;
  label: string;
}

export interface PatternMockup {
  id: number;
  pattern_type: string;
  render_params: Record<string, number>;
  design_source: "manual" | "llm_suggested";
  design_rationale?: string | null;
  batch_id?: string | null;
  swatch_roles: PatternSwatchRoleInfo[];
  created_at: string;
}

export interface ConceptShot {
  id: number;
  mockup_id: number;
  provider_name: string;
  garment_type?: string | null;
  status: "completed" | "failed";
  error_message?: string | null;
  created_at: string;
}

export interface PatternMatrixRequest {
  swatch_ids?: number[] | null;
  pattern_types?: string[] | null;
  num_llm_suggestions?: number;
}

export interface PatternMatrixTriggerResponse {
  task_id: string;
  batch_id: string;
}

export interface PatternGenerationStatus {
  task_id: string;
  status: string;
  result: { batch_id: string; rendered_count: number } | null;
}

export interface ConceptShotRequest {
  garment_type?: string | null;
}

export interface ClearAllPatternDataResult {
  swatches_deleted: number;
  mockups_deleted: number;
  swatch_roles_deleted: number;
  concept_shots_deleted: number;
}
