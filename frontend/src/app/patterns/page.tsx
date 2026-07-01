"use client";

import { useState } from "react";
import ClearAllButton from "@/components/patterns/ClearAllButton";
import PatternMatrixGrid from "@/components/patterns/PatternMatrixGrid";
import SwatchUploader from "@/components/patterns/SwatchUploader";

export default function PatternsPage() {
  const [resetKey, setResetKey] = useState(0);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Fabric pattern mockups</h1>
          <p className="text-sm text-neutral-400 mt-1">
            Upload swatch photos, generate a matrix of pattern mockups, and request an AI concept
            shot for any favorite.
          </p>
        </div>
        <ClearAllButton onCleared={() => setResetKey((k) => k + 1)} />
      </div>
      <SwatchUploader key={`swatches-${resetKey}`} />
      <PatternMatrixGrid key={`mockups-${resetKey}`} />
    </div>
  );
}
