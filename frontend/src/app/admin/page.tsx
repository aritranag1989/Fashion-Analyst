"use client";

import { useEffect, useState } from "react";
import { getAgentsStatus } from "@/lib/api-client";

interface AgentsStatus {
  agents: string[];
  real_logic: string[];
  stubbed: string[];
  tracked_sources: { id: number; name: string; last_crawled_at: string | null; is_active: boolean }[];
}

export default function AdminPage() {
  const [status, setStatus] = useState<AgentsStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAgentsStatus()
      .then((s) => setStatus(s as AgentsStatus))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load status"));
  }, []);

  if (error) return <p className="text-red-400 text-sm">{error}</p>;
  if (!status) return <p className="text-sm text-neutral-500">Loading...</p>;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Agents & sources admin</h1>

      <div>
        <span className="text-xs uppercase text-neutral-500">Agents with real logic</span>
        <ul className="mt-1 flex flex-wrap gap-2">
          {status.real_logic.map((a) => (
            <li key={a} className="text-xs rounded-md bg-green-950 text-green-300 border border-green-900 px-2 py-1">
              {a}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <span className="text-xs uppercase text-neutral-500">Stubbed agents</span>
        <ul className="mt-1 flex flex-wrap gap-2">
          {status.stubbed.map((a) => (
            <li key={a} className="text-xs rounded-md bg-neutral-800 text-neutral-400 border border-neutral-700 px-2 py-1">
              {a}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <span className="text-xs uppercase text-neutral-500">Tracked sources</span>
        <table className="mt-1 text-sm border-collapse">
          <thead>
            <tr className="text-left text-neutral-500">
              <th className="pr-4 py-1">Name</th>
              <th className="pr-4 py-1">Last crawled</th>
              <th className="pr-4 py-1">Active</th>
            </tr>
          </thead>
          <tbody>
            {status.tracked_sources.map((s) => (
              <tr key={s.id} className="border-t border-neutral-800">
                <td className="pr-4 py-1">{s.name}</td>
                <td className="pr-4 py-1">{s.last_crawled_at ?? "never"}</td>
                <td className="pr-4 py-1">{s.is_active ? "yes" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
