import SearchExperience from "@/components/search/SearchExperience";

export default function HomePage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Ask about Japanese handloom & textile companies</h1>
        <p className="text-sm text-neutral-400 mt-1">
          Natural-language search over verified, cited data - every answer traces back to a source
          and a confidence score.
        </p>
      </div>
      <SearchExperience />
    </div>
  );
}
