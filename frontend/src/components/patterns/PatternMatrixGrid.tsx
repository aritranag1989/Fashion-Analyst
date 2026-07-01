"use client";

import { useState } from "react";
import {
  generatePatternMatrix,
  getPatternGenerationStatus,
  listPatternMockups,
  tileImageUrl,
} from "@/lib/api-client";
import type { PatternMockup } from "@/lib/types";
import ConceptShotPanel from "./ConceptShotPanel";

const POLL_INTERVAL_MS = 1500;

export default function PatternMatrixGrid() {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mockups, setMockups] = useState<PatternMockup[]>([]);
  const [activeMockupId, setActiveMockupId] = useState<number | null>(null);

  function pollUntilDone(taskId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const interval = setInterval(async () => {
        try {
          const status = await getPatternGenerationStatus(taskId);
          if (status.status === "SUCCESS") {
            clearInterval(interval);
            resolve();
          } else if (status.status === "FAILURE") {
            clearInterval(interval);
            reject(new Error("Pattern generation task failed"));
          }
        } catch (err) {
          clearInterval(interval);
          reject(err);
        }
      }, POLL_INTERVAL_MS);
    });
  }

  async function handleGenerate() {
    setGenerating(true);
    setError(null);
    try {
      const { task_id, batch_id } = await generatePatternMatrix({});
      await pollUntilDone(task_id);
      const result = await listPatternMockups(batch_id);
      setMockups(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Matrix generation failed");
    } finally {
      setGenerating(false);
    }
  }

  const activeMockup = mockups.find((m) => m.id === activeMockupId) ?? null;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <h2 className="text-lg font-medium">Pattern matrix</h2>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="rounded-md bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-4 py-2 text-sm font-medium"
          suppressHydrationWarning
        >
          {generating ? "Generating..." : "Generate matrix"}
        </button>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      {mockups.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {mockups.map((mockup) => (
            <div
              key={mockup.id}
              className="flex flex-col gap-2 rounded-md border border-neutral-700 p-2"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={tileImageUrl(mockup.id)}
                alt={`${mockup.pattern_type} mockup`}
                className="w-full aspect-square object-cover rounded-md bg-neutral-900"
              />
              <span className="text-xs uppercase text-neutral-500">{mockup.pattern_type}</span>
              {mockup.design_rationale && (
                <p className="text-xs text-neutral-400">{mockup.design_rationale}</p>
              )}
              <button
                onClick={() => setActiveMockupId(mockup.id)}
                className="text-xs rounded-md border border-neutral-700 hover:border-indigo-500 px-2 py-1"
                suppressHydrationWarning
              >
                Generate concept shot
              </button>
            </div>
          ))}
        </div>
      )}

      {activeMockup && (
        <ConceptShotPanel mockup={activeMockup} onClose={() => setActiveMockupId(null)} />
      )}
    </div>
  );
}
