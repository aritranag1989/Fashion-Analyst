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
