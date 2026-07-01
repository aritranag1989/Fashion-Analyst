"use client";

import { useState } from "react";
import { clearAllPatternData } from "@/lib/api-client";

interface ClearAllButtonProps {
  onCleared: () => void;
}

export default function ClearAllButton({ onCleared }: ClearAllButtonProps) {
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setError(null);
    setClearing(true);
    try {
      await clearAllPatternData(false);
      onCleared();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Clear failed";
      // A 409 here means concept shots exist and cost real money to regenerate - surface that
      // specific warning (with exact counts, from the backend's detail message) via a native
      // confirm rather than failing silently.
      if (window.confirm(`${message}\n\nProceed anyway?`)) {
        try {
          await clearAllPatternData(true);
          onCleared();
        } catch (retryErr) {
          setError(retryErr instanceof Error ? retryErr.message : "Clear failed");
        }
      }
    } finally {
      setClearing(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        onClick={handleClick}
        disabled={clearing}
        className="rounded-md border border-red-800 text-red-400 hover:bg-red-950 disabled:opacity-50 px-4 py-2 text-sm font-medium shrink-0"
        suppressHydrationWarning
      >
        {clearing ? "Clearing..." : "Clear all"}
      </button>
      {error && <p className="text-red-400 text-xs">{error}</p>}
    </div>
  );
}
