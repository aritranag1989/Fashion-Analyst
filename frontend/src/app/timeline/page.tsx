export default function TimelinePage() {
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Timeline</h1>
      <p className="text-sm text-neutral-400">
        Trade fair / exhibition / founding-date timeline view. The `events` table and
        Company-Event knowledge graph edges exist in the schema, but the ingestion agents don&apos;t
        populate event data yet in Phase 1 (no trade-fair-specific crawling implemented) - this
        page will start rendering real timelines once that source is added.
      </p>
    </div>
  );
}
