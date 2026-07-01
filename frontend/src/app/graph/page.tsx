"use client";

import { useState } from "react";
import { getCompanyGraph } from "@/lib/api-client";

interface GraphEdge {
  relationship: string;
  neighbor_label: string[];
  neighbor: Record<string, unknown>;
}

export default function GraphPage() {
  const [companyId, setCompanyId] = useState("");
  const [edges, setEdges] = useState<GraphEdge[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleLoad() {
    if (!companyId.trim()) return;
    try {
      const result = (await getCompanyGraph(Number(companyId))) as { edges: GraphEdge[] };
      setEdges(result.edges);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load graph");
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Knowledge graph / supply chain</h1>
      <p className="text-sm text-neutral-400">
        Ego-network view of a company&apos;s relationships (fabrics, products, location, exports).
        Full interactive graph visualization is a later enhancement - this lists the same edges.
      </p>
      <div className="flex gap-2">
        <input
          value={companyId}
          onChange={(e) => setCompanyId(e.target.value)}
          placeholder="Company ID"
          className="flex-1 rounded-md bg-neutral-900 border border-neutral-700 p-2 text-sm"
        />
        <button onClick={handleLoad} className="rounded-md bg-indigo-600 hover:bg-indigo-500 px-4 py-2 text-sm">
          Load
        </button>
      </div>
      {error && <p className="text-red-400 text-sm">{error}</p>}
      {edges && (
        <ul className="flex flex-col gap-2 text-sm">
          {edges.map((edge, i) => (
            <li key={i} className="rounded-md border border-neutral-800 p-2">
              <span className="text-indigo-400">{edge.relationship}</span>{" "}
              <span className="text-neutral-500">({edge.neighbor_label.join(", ")})</span>
              <pre className="text-xs text-neutral-500 mt-1 overflow-x-auto">
                {JSON.stringify(edge.neighbor, null, 2)}
              </pre>
            </li>
          ))}
          {edges.length === 0 && <p className="text-neutral-500">No relationships recorded yet.</p>}
        </ul>
      )}
    </div>
  );
}
