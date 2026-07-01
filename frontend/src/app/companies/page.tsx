"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listCompanies } from "@/lib/api-client";

interface CompanySummary {
  id: number;
  name: string;
  company_type?: string | null;
  website_url?: string | null;
}

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<CompanySummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCompanies()
      .then(setCompanies)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load companies"));
  }, []);

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Companies</h1>
      {error && <p className="text-red-400 text-sm">{error}</p>}
      <ul className="flex flex-col gap-2">
        {companies.map((company) => (
          <li key={company.id} className="rounded-md border border-neutral-800 p-3 flex justify-between items-center">
            <div>
              <Link href={`/companies/${company.id}`} className="font-medium hover:underline">
                {company.name}
              </Link>
              {company.company_type && (
                <span className="ml-2 text-xs text-neutral-500">{company.company_type}</span>
              )}
            </div>
            {company.website_url && (
              <a href={company.website_url} target="_blank" rel="noreferrer" className="text-xs text-indigo-400">
                website
              </a>
            )}
          </li>
        ))}
      </ul>
      {companies.length === 0 && !error && (
        <p className="text-sm text-neutral-500">
          No companies yet - run scripts/seed_crawl.py to populate the knowledge base.
        </p>
      )}
    </div>
  );
}
