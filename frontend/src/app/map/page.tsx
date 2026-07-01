"use client";

import { useEffect, useState } from "react";
import { listCompanies } from "@/lib/api-client";

export default function MapPage() {
  const [companies, setCompanies] = useState<{ id: number; name: string }[]>([]);

  useEffect(() => {
    listCompanies().then(setCompanies).catch(() => setCompanies([]));
  }, []);

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Map search</h1>
      <p className="text-sm text-neutral-400">
        An interactive map (lat/lng plotting) is a later enhancement once address geocoding is
        wired into the ingestion pipeline. For now, this lists companies with known addresses.
      </p>
      <ul className="flex flex-col gap-1 text-sm">
        {companies.map((c) => (
          <li key={c.id}>{c.name}</li>
        ))}
        {companies.length === 0 && <p className="text-neutral-500">No companies ingested yet.</p>}
      </ul>
    </div>
  );
}
