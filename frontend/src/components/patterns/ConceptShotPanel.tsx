"use client";

import { useState } from "react";
import { conceptShotImageUrl, requestConceptShot } from "@/lib/api-client";
import type { ConceptShot, PatternMockup } from "@/lib/types";

interface ConceptShotPanelProps {
  mockup: PatternMockup;
  onClose: () => void;
}

export default function ConceptShotPanel({ mockup, onClose }: ConceptShotPanelProps) {
  const [garmentType, setGarmentType] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shot, setShot] = useState<ConceptShot | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    setShot(null);
    try {
      const result = await requestConceptShot(mockup.id, {
        garment_type: garmentType.trim() || null,
      });
      if (result.status === "failed") {
        setError(result.error_message ?? "Concept shot generation failed");
      } else {
        setShot(result);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Concept shot generation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-6 z-50">
      <div className="bg-neutral-900 border border-neutral-700 rounded-md p-6 max-w-md w-full flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium">Concept shot — {mockup.pattern_type}</h3>
          <button
            onClick={onClose}
            className="text-neutral-500 hover:text-neutral-200"
            suppressHydrationWarning
          >
            ×
          </button>
        </div>

        <p className="text-xs text-neutral-500">
          This calls a paid AI image model one image at a time — not automatic like the free tile
          matrix.
        </p>

        <input
          value={garmentType}
          onChange={(e) => setGarmentType(e.target.value)}
          placeholder="Garment type (optional), e.g. kimono, jacket"
          className="rounded-md bg-neutral-950 border border-neutral-700 px-3 py-2 text-sm"
          suppressHydrationWarning
        />

        <button
          onClick={handleGenerate}
          disabled={loading}
          className="rounded-md bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-4 py-2 text-sm font-medium"
          suppressHydrationWarning
        >
          {loading ? "Generating (~20s)..." : "Generate concept shot"}
        </button>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        {shot && shot.status === "completed" && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={conceptShotImageUrl(shot.id)}
            alt="AI concept shot"
            className="w-full rounded-md"
          />
        )}
      </div>
    </div>
  );
}
