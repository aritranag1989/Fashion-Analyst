"use client";

import { useState } from "react";
import { compareCompanies } from "@/lib/api-client";
import type { CompanyDetail } from "@/lib/types";

export default function ComparePage() {
  const [idsInput, setIdsInput] = useState("");
  const [companies, setCompanies] = useState<CompanyDetail[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function handleCompare() {
    const ids = idsInput
      .split(",")
      .map((id) => Number(id.trim()))
      .filter((id) => !Number.isNaN(id));
    if (ids.length === 0) return;

    try {
      setCompanies(await compareCompanies(ids));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed");
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Compare companies</h1>
      <div className="flex gap-2">
        <input
          value={idsInput}
          onChange={(e) => setIdsInput(e.target.value)}
          placeholder="Company IDs, comma separated e.g. 1,2,3"
          className="flex-1 rounded-md bg-neutral-900 border border-neutral-700 p-2 text-sm"
        />
        <button onClick={handleCompare} className="rounded-md bg-indigo-600 hover:bg-indigo-500 px-4 py-2 text-sm">
          Compare
        </button>
      </div>
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {companies.length > 0 && (
        <table className="text-sm border-collapse">
          <thead>
            <tr className="text-left text-neutral-500">
              <th className="pr-4 py-1">Name</th>
              <th className="pr-4 py-1">Type</th>
              <th className="pr-4 py-1">Founded</th>
              <th className="pr-4 py-1">Certifications</th>
            </tr>
          </thead>
          <tbody>
            {companies.map((c) => (
              <tr key={c.id} className="border-t border-neutral-800">
                <td className="pr-4 py-1">{c.name}</td>
                <td className="pr-4 py-1">{c.company_type ?? "-"}</td>
                <td className="pr-4 py-1">{c.founded_year ?? "-"}</td>
                <td className="pr-4 py-1">{c.certifications.join(", ") || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
