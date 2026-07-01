"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getCompany } from "@/lib/api-client";
import type { CompanyDetail } from "@/lib/types";

export default function CompanyDetailPage() {
  const params = useParams<{ id: string }>();
  const [company, setCompany] = useState<CompanyDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCompany(Number(params.id))
      .then(setCompany)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load company"));
  }, [params.id]);

  if (error) return <p className="text-red-400 text-sm">{error}</p>;
  if (!company) return <p className="text-sm text-neutral-500">Loading...</p>;

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold">{company.name}</h1>
        {company.name_ja && <p className="text-neutral-400">{company.name_ja}</p>}
      </div>
      {company.description && <p className="text-sm leading-relaxed">{company.description}</p>}

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-xs uppercase text-neutral-500">Type</span>
          <p>{company.company_type ?? "-"}</p>
        </div>
        <div>
          <span className="text-xs uppercase text-neutral-500">Founded</span>
          <p>{company.founded_year ?? "-"}</p>
        </div>
      </div>

      <div>
        <span className="text-xs uppercase text-neutral-500">Products</span>
        <ul className="mt-1 flex flex-wrap gap-2">
          {company.products.map((p) => (
            <li key={p.id} className="text-xs rounded-md bg-neutral-900 border border-neutral-700 px-2 py-1">
              {p.name} {p.fabric_type ? `(${p.fabric_type})` : ""}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <span className="text-xs uppercase text-neutral-500">Contacts</span>
        <ul className="mt-1 text-sm">
          {company.contacts.map((c, i) => (
            <li key={i}>
              {c.type}: {c.value}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <span className="text-xs uppercase text-neutral-500">Addresses</span>
        <ul className="mt-1 text-sm">
          {company.addresses.map((a, i) => (
            <li key={i}>
              {[a.city, a.prefecture, a.country].filter(Boolean).join(", ")}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
