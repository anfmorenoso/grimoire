import { useState } from "react";
import type { Wiki } from "../vocabulary";
import type { Collection } from "../api";
import type { ActiveFilter, SavedFilter, Sort, SortField } from "../filters";
import { DEFAULT_PRESETS, EMPTY_FILTER, SORT_LABELS, filterIsEmpty, toggleTag } from "../filters";

interface Props {
  wiki: Wiki;
  filter: ActiveFilter;
  sort: Sort;
  savedFilters: SavedFilter[];
  availableLabels: string[];
  collections: Collection[];
  onFilterChange: (f: ActiveFilter) => void;
  onSortChange: (s: Sort) => void;
  onSaveFilter: (name: string) => void;
  onDeleteSaved: (id: string) => void;
  onClose: () => void;
}

const ROLE_INACTIVE: Record<string, string> = {
  amorce: "text-blue-400 border-blue-400/30",
  construction: "text-yellow-400 border-yellow-400/30",
  peak_time: "text-red-400 border-red-400/30",
  planage: "text-purple-400 border-purple-400/30",
};

const SECTIONS: Array<{ key: keyof ActiveFilter; wikiKey: keyof Wiki; label: string }> = [
  { key: "role_set",    wikiKey: "role_set",    label: "Rôle Set"    },
  { key: "grain",       wikiKey: "grain",       label: "Grain"       },
  { key: "masse_basse", wikiKey: "masse_basse", label: "Masse Basse" },
  { key: "sensations",  wikiKey: "sensations",  label: "Sensations"  },
];

export default function FilterPanel({
  wiki, filter, sort, savedFilters, availableLabels, collections,
  onFilterChange, onSortChange, onSaveFilter, onDeleteSaved, onClose,
}: Props) {
  const [saveName, setSaveName] = useState("");

  const handleSave = () => {
    if (!saveName.trim()) return;
    onSaveFilter(saveName.trim());
    setSaveName("");
  };

  const loadPreset = (sf: SavedFilter) =>
    onFilterChange({ grain: sf.grain, sensations: sf.sensations, masse_basse: sf.masse_basse, role_set: sf.role_set, label: sf.label ?? [], collection: sf.collection ?? [] });

  return (
    <div className="fixed inset-0 z-50 flex items-end bg-black/60" onClick={onClose}>
      <div
        className="w-full bg-surface border-t border-border rounded-t-2xl max-h-[82vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
          <h2 className="text-sm font-semibold text-white">Filtres & Tri</h2>
          <div className="flex items-center gap-4">
            {!filterIsEmpty(filter) && (
              <button type="button" onClick={() => onFilterChange(EMPTY_FILTER)}
                className="text-xs text-muted underline underline-offset-2">
                Tout effacer
              </button>
            )}
            <button type="button" onClick={onClose} className="text-muted text-lg leading-none">✕</button>
          </div>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 px-4 py-4 space-y-5">

          {/* Sort */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-widest text-muted">Tri</h3>
            <div className="flex gap-2 items-center">
              {(["id", "name", "artist"] as SortField[]).map((field) => (
                <button
                  key={field}
                  type="button"
                  onClick={() => onSortChange({ field, dir: sort.field === field ? (sort.dir === "asc" ? "desc" : "asc") : (field === "id" ? "desc" : "asc") })}
                  className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-colors ${
                    sort.field === field
                      ? "bg-accent text-white border-accent"
                      : "bg-card text-gray-300 border-border"
                  }`}
                >
                  {SORT_LABELS[field]} {sort.field === field ? (sort.dir === "asc" ? "↑" : "↓") : ""}
                </button>
              ))}
            </div>
          </div>

          {/* Presets */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-widest text-muted">Présets</h3>
            <div className="flex flex-wrap gap-2">
              {DEFAULT_PRESETS.map((p) => (
                <button key={p.id} type="button" onClick={() => loadPreset(p)}
                  className="text-xs px-3 py-1.5 rounded-full border border-border bg-card text-gray-300 hover:border-accent/50 transition-colors">
                  {p.name}
                </button>
              ))}
              {savedFilters.map((sf) => (
                <div key={sf.id} className="flex">
                  <button type="button" onClick={() => loadPreset(sf)}
                    className="text-xs px-3 py-1.5 rounded-l-full border border-r-0 border-accent/40 bg-accent/10 text-accent">
                    {sf.name}
                  </button>
                  <button type="button" onClick={() => onDeleteSaved(sf.id)}
                    className="text-xs px-2 py-1.5 rounded-r-full border border-accent/40 bg-accent/10 text-muted hover:text-red-400 transition-colors">
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Tag sections */}
          {SECTIONS.map(({ key, wikiKey, label }) => (
            <div key={key} className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-widest text-muted">{label}</h3>
              <div className="flex flex-wrap gap-2">
                {wiki[wikiKey].map((entry) => {
                  const active = filter[key].includes(entry.key);
                  const inactiveColor =
                    key === "role_set" ? (ROLE_INACTIVE[entry.key] ?? "text-gray-300 border-border") :
                    key === "sensations" ? "text-accent/80 border-accent/30" :
                    "text-gray-300 border-border";
                  return (
                    <button
                      key={entry.key}
                      type="button"
                      onClick={() => onFilterChange(toggleTag(filter, key, entry.key))}
                      className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-colors ${
                        active ? "bg-accent text-white border-accent" : `bg-card ${inactiveColor}`
                      }`}
                    >
                      {entry.label}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Collections */}
          {collections.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-widest text-muted">Collection</h3>
              <div className="flex flex-wrap gap-2">
                <button type="button"
                  onClick={() => onFilterChange(toggleTag(filter, "collection", "__none__"))}
                  className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-colors ${
                    filter.collection.includes("__none__") ? "bg-accent text-white border-accent" : "bg-card text-gray-300 border-border"
                  }`}
                >
                  Sans collection
                </button>
                {collections.filter(c => !c.hidden).map(({ collection, count }) => {
                  const label = collection.includes(" > ") ? collection.split(" > ").pop()! : collection;
                  const active = filter.collection.includes(collection);
                  return (
                    <button key={collection} type="button"
                      onClick={() => onFilterChange(toggleTag(filter, "collection", collection))}
                      className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-colors ${
                        active ? "bg-accent text-white border-accent" : "bg-card text-gray-300 border-border"
                      }`}
                    >
                      {label} <span className="opacity-50">{count}</span>
                    </button>
                  );
                })}
              </div>
              {collections.some(c => c.hidden) && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {collections.filter(c => c.hidden).map(({ collection, count }) => {
                    const active = filter.collection.includes(collection);
                    return (
                      <button key={collection} type="button"
                        onClick={() => onFilterChange(toggleTag(filter, "collection", collection))}
                        className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                          active ? "bg-accent/20 text-accent border-accent/40" : "bg-card text-muted border-border/50 opacity-50"
                        }`}
                      >
                        {collection} <span className="opacity-50">{count}</span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Labels */}
          {availableLabels.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-widest text-muted">Label</h3>
              <div className="flex flex-wrap gap-2">
                {availableLabels.map((lbl) => {
                  const active = filter.label.includes(lbl);
                  return (
                    <button
                      key={lbl}
                      type="button"
                      onClick={() => onFilterChange(toggleTag(filter, "label", lbl))}
                      className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-colors ${
                        active ? "bg-accent text-white border-accent" : "bg-card text-gray-300 border-border"
                      }`}
                    >
                      {lbl}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Save */}
          {!filterIsEmpty(filter) && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-widest text-muted">Sauvegarder</h3>
              <div className="flex gap-2">
                <input
                  className="flex-1 bg-card border border-border rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-muted focus:outline-none focus:border-accent"
                  placeholder="Nom du filtre..."
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSave()}
                />
                <button type="button" onClick={handleSave} disabled={!saveName.trim()}
                  className="text-xs px-3 py-2 rounded-lg bg-accent text-white disabled:opacity-40">
                  + Sauver
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
