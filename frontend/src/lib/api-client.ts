import type {
  ClearAllPatternDataResult,
  CompanyDetail,
  ConceptShot,
  ConceptShotRequest,
  PatternMatrixRequest,
  PatternMatrixTriggerResponse,
  PatternGenerationStatus,
  PatternMockup,
  SearchRequest,
  SearchResponse,
  Swatch,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  // Don't force Content-Type when the body is FormData (multipart uploads) - fetch sets its own
  // boundary header, and overriding it here would break the upload.
  const headers =
    init?.body instanceof FormData
      ? init?.headers
      : { "Content-Type": "application/json", ...init?.headers };

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    // FastAPI error responses are {"detail": "..."} - surface that specific message (e.g. "Cannot
    // delete 'X': it's used in N existing mockup(s)") instead of a generic status code, since the
    // backend often has something much more useful to say than "409 Conflict".
    const detail = await response
      .json()
      .then((body) => (typeof body?.detail === "string" ? body.detail : null))
      .catch(() => null);
    throw new Error(detail ?? `API request failed: ${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export function search(request: SearchRequest): Promise<SearchResponse> {
  return apiFetch<SearchResponse>("/search", { method: "POST", body: JSON.stringify(request) });
}

export function listCompanies(): Promise<
  { id: number; name: string; company_type?: string | null; website_url?: string | null }[]
> {
  return apiFetch("/companies");
}

export function getCompany(id: number): Promise<CompanyDetail> {
  return apiFetch(`/companies/${id}`);
}

export function compareCompanies(ids: number[]): Promise<CompanyDetail[]> {
  return apiFetch(`/companies/compare?ids=${ids.join(",")}`);
}

export function getCompanyGraph(id: number): Promise<unknown> {
  return apiFetch(`/companies/${id}/graph`);
}

export function getTradeFlows(
  reporterCountry: string,
  partnerCountry: string
): Promise<unknown> {
  return apiFetch(
    `/trade/comtrade?reporter_country=${reporterCountry}&partner_country=${partnerCountry}`
  );
}

export function getAgentsStatus(): Promise<unknown> {
  return apiFetch("/agents/status");
}

export function uploadSwatch(file: File, label: string): Promise<Swatch> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("label", label);
  return apiFetch<Swatch>("/swatches/upload", { method: "POST", body: formData });
}

export function listSwatches(): Promise<Swatch[]> {
  return apiFetch("/swatches");
}

export function updateSwatch(
  id: number,
  updates: { label?: string; notes?: string }
): Promise<Swatch> {
  return apiFetch(`/swatches/${id}`, { method: "PATCH", body: JSON.stringify(updates) });
}

export function deleteSwatch(id: number): Promise<void> {
  return apiFetch(`/swatches/${id}`, { method: "DELETE" });
}

export function generatePatternMatrix(
  request: PatternMatrixRequest
): Promise<PatternMatrixTriggerResponse> {
  return apiFetch("/patterns/generate", { method: "POST", body: JSON.stringify(request) });
}

export function getPatternGenerationStatus(taskId: string): Promise<PatternGenerationStatus> {
  return apiFetch(`/patterns/status/${taskId}`);
}

export function listPatternMockups(batchId?: string): Promise<PatternMockup[]> {
  const qs = batchId ? `?batch_id=${batchId}` : "";
  return apiFetch(`/patterns/mockups${qs}`);
}

export function requestConceptShot(
  mockupId: number,
  request: ConceptShotRequest
): Promise<ConceptShot> {
  return apiFetch(`/patterns/mockups/${mockupId}/concept-shot`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export function listConceptShots(mockupId: number): Promise<ConceptShot[]> {
  return apiFetch(`/patterns/mockups/${mockupId}/concept-shots`);
}

export function tileImageUrl(mockupId: number): string {
  return `${API_BASE_URL}/patterns/mockups/${mockupId}/tile`;
}

export function conceptShotImageUrl(shotId: number): string {
  return `${API_BASE_URL}/patterns/concept-shots/${shotId}/image`;
}

export function clearAllPatternData(confirm: boolean): Promise<ClearAllPatternDataResult> {
  return apiFetch(`/patterns/clear-all?confirm=${confirm}`, { method: "DELETE" });
}
