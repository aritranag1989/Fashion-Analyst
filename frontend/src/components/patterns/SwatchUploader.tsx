"use client";

import { useEffect, useState } from "react";
import { deleteSwatch, listSwatches, uploadSwatch } from "@/lib/api-client";
import type { Swatch } from "@/lib/types";

interface SwatchUploaderProps {
  onSwatchesChange?: (swatches: Swatch[]) => void;
}

export default function SwatchUploader({ onSwatchesChange }: SwatchUploaderProps) {
  const [swatches, setSwatches] = useState<Swatch[]>([]);
  const [label, setLabel] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const result = await listSwatches();
    setSwatches(result);
    onSwatchesChange?.(result);
  }

  useEffect(() => {
    refresh().catch((err) =>
      setError(err instanceof Error ? err.message : "Failed to load swatches")
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleUpload(event: React.FormEvent) {
    event.preventDefault();
    if (!file || !label.trim()) return;

    setUploading(true);
    setError(null);
    try {
      await uploadSwatch(file, label.trim());
      setLabel("");
      setFile(null);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id: number) {
    setError(null);
    try {
      await deleteSwatch(id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-medium">Swatch library</h2>

      <form onSubmit={handleUpload} className="flex flex-wrap items-center gap-3">
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="text-sm"
          suppressHydrationWarning
        />
        <input
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="Swatch label, e.g. Indigo hemp"
          className="rounded-md bg-neutral-900 border border-neutral-700 px-3 py-2 text-sm"
          suppressHydrationWarning
        />
        <button
          type="submit"
          disabled={uploading || !file || !label.trim()}
          className="rounded-md bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-4 py-2 text-sm font-medium"
          suppressHydrationWarning
        >
          {uploading ? "Uploading..." : "Upload swatch"}
        </button>
      </form>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <ul className="flex flex-wrap gap-3">
        {swatches.map((swatch) => (
          <li
            key={swatch.id}
            className="flex items-center gap-2 rounded-md bg-neutral-900 border border-neutral-700 px-2 py-1 text-xs"
          >
            <span
              className="w-4 h-4 rounded-full border border-neutral-600 shrink-0"
              style={{ backgroundColor: swatch.hex_color }}
            />
            <span>{swatch.label}</span>
            <span className="text-neutral-500">{swatch.hex_color}</span>
            <button
              onClick={() => handleDelete(swatch.id)}
              className="text-neutral-500 hover:text-red-400"
              aria-label={`Delete ${swatch.label}`}
              suppressHydrationWarning
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
