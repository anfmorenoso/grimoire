import { useState } from "react";
import type { Wiki } from "../vocabulary";
import type { TrackStats } from "../api";
import type { ActiveFilter } from "../filters";

interface Props {
  wiki: Wiki;
  stats: TrackStats;
  onBack: () => void;
  onFilterApply: (type: keyof ActiveFilter, key: string) => void;
}

const CATEGORY_LABELS: Record<string, string> = {
  grain: "Grain",
  sensations: "Sensations",
  masse_basse: "Masse Basse",
  role_set: "Rôle Set",
};

const ROLE_COLORS: Record<string, string> = {
  amorce: "text-blue-400",
  construction: "text-yellow-400",
  peak_time: "text-red-400",
  planage: "text-purple-400",
};

function entryTitleColor(cat: string, key: string): string {
  if (cat === "role_set") return ROLE_COLORS[key] ?? "text-gray-200";
  if (cat === "sensations") return "text-accent";
  return "text-gray-200";
}

// wiki category key → ActiveFilter key (they match 1:1 here)
const CAT_TO_FILTER: Record<string, keyof ActiveFilter> = {
  grain: "grain",
  sensations: "sensations",
  masse_basse: "masse_basse",
  role_set: "role_set",
};

export default function WikiPage({ wiki, stats, onBack, onFilterApply }: Props) {
  const [long, setLong] = useState(false);

  return (
    <div className="flex flex-col h-screen">
      <header className="flex items-center gap-3 px-4 py-4 border-b border-border sticky top-0 bg-surface z-10">
        <button type="button" onClick={onBack} className="text-muted text-xl">←</button>
        <h1 className="text-base font-semibold flex-1">Wiki</h1>
        <button
          type="button"
          onClick={() => setLong((v) => !v)}
          className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
            long
              ? "bg-accent text-white border-accent"
              : "bg-card text-muted border-border"
          }`}
        >
          {long ? "Long" : "Court"}
        </button>
      </header>

      <main className="flex-1 overflow-y-auto px-4 py-4 space-y-8">
        {(Object.keys(CATEGORY_LABELS) as Array<keyof Wiki>).map((cat) => (
          <section key={cat}>
            <h2 className="text-xs font-semibold uppercase tracking-widest text-muted mb-3">
              {CATEGORY_LABELS[cat]}
            </h2>
            <div className="space-y-3">
              {wiki[cat].map((entry) => {
                const filterType = CAT_TO_FILTER[cat];
                const count = stats[cat as keyof TrackStats]?.[entry.key] ?? 0;
                return (
                  <button
                    key={entry.key}
                    type="button"
                    onClick={() => onFilterApply(filterType, entry.key)}
                    className="w-full text-left bg-card border border-border rounded-xl px-4 py-3 space-y-1 active:bg-border/50 transition-colors"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className={`text-sm font-semibold leading-snug ${entryTitleColor(cat, entry.key)}`}>
                        {long ? `${entry.label.split(" ")[0]} ${entry.notion_value || entry.label}` : entry.label}
                      </p>
                      {count > 0 && (
                        <span className="text-xs text-muted shrink-0">
                          {count} morceau{count !== 1 ? "x" : ""}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 leading-relaxed">
                      {entry.description}
                    </p>
                  </button>
                );
              })}
            </div>
          </section>
        ))}
      </main>
    </div>
  );
}
