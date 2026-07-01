import type { CompanyDetail, SearchRequest, SearchResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
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
