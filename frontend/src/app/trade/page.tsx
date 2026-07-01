"use client";

import { useState } from "react";
import { getTradeFlows } from "@/lib/api-client";

interface TradeFlowsResponse {
  granularity: string;
  caveat: string;
  flows: {
    reporter_country: string;
    partner_country: string;
    hs_code: string;
    trade_flow: string;
    year: number;
    value_usd: number | null;
    quantity: number | null;
  }[];
}

export default function TradePage() {
  const [reporter, setReporter] = useState("392"); // Japan (UN M49)
  const [partner, setPartner] = useState("356"); // India (UN M49)
  const [data, setData] = useState<TradeFlowsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleLoad() {
    try {
      setData((await getTradeFlows(reporter, partner)) as TradeFlowsResponse);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load trade data");
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Trade route analysis</h1>
      <p className="text-sm rounded-md bg-yellow-950 text-yellow-300 border border-yellow-900 p-3">
        Country-level aggregate flows only (UN Comtrade), by HS code. No company-level shipment
        matching and no city-level (e.g. Kolkata-specific) granularity in Phase 1 - see
        docs/data-sources.md.
      </p>
      <div className="flex gap-2">
        <input
          value={reporter}
          onChange={(e) => setReporter(e.target.value)}
          placeholder="Reporter country (UN M49 code)"
          className="rounded-md bg-neutral-900 border border-neutral-700 p-2 text-sm"
        />
        <input
          value={partner}
          onChange={(e) => setPartner(e.target.value)}
          placeholder="Partner country (UN M49 code)"
          className="rounded-md bg-neutral-900 border border-neutral-700 p-2 text-sm"
        />
        <button onClick={handleLoad} className="rounded-md bg-indigo-600 hover:bg-indigo-500 px-4 py-2 text-sm">
          Load
        </button>
      </div>
      {error && <p className="text-red-400 text-sm">{error}</p>}
      {data && (
        <table className="text-sm border-collapse">
          <thead>
            <tr className="text-left text-neutral-500">
              <th className="pr-4 py-1">Flow</th>
              <th className="pr-4 py-1">HS Code</th>
              <th className="pr-4 py-1">Year</th>
              <th className="pr-4 py-1">Value (USD)</th>
            </tr>
          </thead>
          <tbody>
            {data.flows.map((f, i) => (
              <tr key={i} className="border-t border-neutral-800">
                <td className="pr-4 py-1">{f.trade_flow}</td>
                <td className="pr-4 py-1">{f.hs_code}</td>
                <td className="pr-4 py-1">{f.year}</td>
                <td className="pr-4 py-1">{f.value_usd ?? "-"}</td>
              </tr>
            ))}
            {data.flows.length === 0 && (
              <tr>
                <td colSpan={4} className="text-neutral-500 py-2">
                  No trade flow data cached for this pair yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
