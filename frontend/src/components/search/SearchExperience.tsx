"use client";

import { useState } from "react";
import { search } from "@/lib/api-client";
import type { SearchResponse } from "@/lib/types";

interface SearchExperienceProps {
  showFacets?: boolean;
}

export default function SearchExperience({ showFacets = false }: SearchExperienceProps) {
  const [query, setQuery] = useState("");
  const [fabricTag, setFabricTag] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<SearchResponse | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const result = await search({
        query,
        fabric_tags: fabricTag.trim() ? [fabricTag.trim()] : [],
      });
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. Which Nishijin weavers work with indigo-dyed silk?"
          rows={3}
          className="w-full rounded-md bg-neutral-900 border border-neutral-700 p-3 text-sm"
        />
        {showFacets && (
          <input
            value={fabricTag}
            onChange={(e) => setFabricTag(e.target.value)}
            placeholder="Filter by fabric/technique tag (optional), e.g. kasuri"
            className="w-full rounded-md bg-neutral-900 border border-neutral-700 p-2 text-sm"
          />
        )}
        <button
          type="submit"
          disabled={loading}
          className="self-start rounded-md bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-4 py-2 text-sm font-medium"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {response && (
        <div className="flex flex-col gap-4 border-t border-neutral-800 pt-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs uppercase tracking-wide text-neutral-500">Answer</span>
              <span className="text-xs rounded-full bg-neutral-800 px-2 py-0.5">
                confidence {response.confidence_overall.toFixed(2)}
              </span>
              {response.insufficient_data && (
                <span className="text-xs rounded-full bg-yellow-900 text-yellow-300 px-2 py-0.5">
                  insufficient verified data
                </span>
              )}
            </div>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{response.answer}</p>
          </div>

          {response.citations.length > 0 && (
            <div>
              <span className="text-xs uppercase tracking-wide text-neutral-500">Citations</span>
              <ul className="mt-2 flex flex-col gap-2">
                {response.citations.map((citation, index) => (
                  <li key={index} className="text-xs text-neutral-400 border-l-2 border-neutral-700 pl-3">
                    <a
                      href={citation.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-indigo-400 hover:underline break-all"
                    >
                      {citation.source_url}
                    </a>
                    <p className="mt-1">{citation.excerpt}</p>
                    <p className="text-neutral-600">confidence {citation.confidence.toFixed(2)}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {response.companies.length > 0 && (
            <div>
              <span className="text-xs uppercase tracking-wide text-neutral-500">Related companies</span>
              <ul className="mt-2 flex flex-wrap gap-2">
                {response.companies.map((company) => (
                  <li key={company.company_id} className="text-xs rounded-md bg-neutral-900 border border-neutral-700 px-2 py-1">
                    {company.name ?? `Company #${company.company_id}`}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
