import SearchExperience from "@/components/search/SearchExperience";

export default function SearchPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Semantic & faceted search</h1>
        <p className="text-sm text-neutral-400 mt-1">
          Same hybrid RAG search as the homepage, with an optional fabric/technique facet filter.
        </p>
      </div>
      <SearchExperience showFacets />
    </div>
  );
}
