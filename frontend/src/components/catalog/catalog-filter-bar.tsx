"use client";

/** Search-by-name filter for a catalog category list. */
export function CatalogFilterBar({
  search,
  onSearchChange,
}: {
  search: string;
  onSearchChange: (value: string) => void;
}) {
  return (
    <div className="mb-4">
      <label htmlFor="catalog-search" className="sr-only">
        Buscar no catálogo
      </label>
      <input
        id="catalog-search"
        type="search"
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        placeholder="Buscar por nome…"
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm sm:max-w-sm"
      />
    </div>
  );
}
