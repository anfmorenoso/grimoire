import { useEffect, useState } from "react";
import type { Wiki } from "./vocabulary";
import type { Track, DJSet, SyncPreview } from "./api";
import { getWiki, getTracks, getLabels, createTrack, updateTrack, deleteTrack, sync, syncPreview } from "./api";
import type { ActiveFilter, SavedFilter, Sort } from "./filters";
import { EMPTY_FILTER, DEFAULT_SORT, SORT_LABELS, filterCount, toggleTag } from "./filters";
import TrackCard from "./components/TrackCard";
import TrackForm from "./components/TrackForm";
import WikiPage from "./components/WikiPage";
import FilterPanel from "./components/FilterPanel";
import SetContextMenu from "./components/SetContextMenu";
import SetsPage from "./components/SetsPage";
import SetDetailPage from "./components/SetDetailPage";

type View = "list" | "add" | "edit" | "wiki" | "sets" | "set-detail";

const SAVED_FILTERS_KEY = "grimoire_saved_filters";

function loadSavedFilters(): SavedFilter[] {
  try { return JSON.parse(localStorage.getItem(SAVED_FILTERS_KEY) || "[]"); }
  catch { return []; }
}

function persistSavedFilters(filters: SavedFilter[]) {
  localStorage.setItem(SAVED_FILTERS_KEY, JSON.stringify(filters));
}

export default function App() {
  const [wiki, setWiki] = useState<Wiki | null>(null);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [availableLabels, setAvailableLabels] = useState<string[]>([]);
  const [view, setView] = useState<View>("list");
  const [selected, setSelected] = useState<Track | null>(null);
  const [search, setSearch] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [preview, setPreview] = useState<SyncPreview | null>(null);
  const [filter, setFilter] = useState<ActiveFilter>(EMPTY_FILTER);
  const [selectedSet, setSelectedSet] = useState<DJSet | null>(null);
  const [contextTrack, setContextTrack] = useState<Track | null>(null);
  const [sort, setSort] = useState<Sort>(DEFAULT_SORT);
  const [filterOpen, setFilterOpen] = useState(false);
  const [savedFilters, setSavedFilters] = useState<SavedFilter[]>(loadSavedFilters);

  useEffect(() => {
    getWiki().then(setWiki);
    getLabels().then(setAvailableLabels);
    loadTracks();
  }, []);

  // Reload when filter or sort changes
  useEffect(() => {
    loadTracks();
  }, [filter, sort]);

  const buildQuery = (overrideQ?: string, overrideF?: ActiveFilter, overrideS?: Sort) => {
    const q = overrideQ !== undefined ? overrideQ : search;
    const f = overrideF ?? filter;
    const s = overrideS ?? sort;
    return {
      sort: s.field, dir: s.dir,
      ...(q ? { q } : {}),
      ...(f.grain.length ? { grain: f.grain } : {}),
      ...(f.masse_basse.length ? { masse_basse: f.masse_basse } : {}),
      ...(f.role_set.length ? { role_set: f.role_set } : {}),
      ...(f.sensations.length ? { sensation: f.sensations } : {}),
      ...(f.label.length ? { label: f.label } : {}),
    };
  };

  const loadTracks = (overrideQ?: string, overrideF?: ActiveFilter, overrideS?: Sort) =>
    getTracks(buildQuery(overrideQ, overrideF, overrideS)).then(setTracks);

  const handleFilterChange = (newFilter: ActiveFilter) => {
    setFilter(newFilter);
    loadTracks(undefined, newFilter);
  };

  const handleSortChange = (newSort: Sort) => {
    setSort(newSort);
    loadTracks(undefined, undefined, newSort);
  };

  const handleTagClick = (type: keyof ActiveFilter, key: string) => {
    const newFilter = toggleTag(filter, type, key);
    handleFilterChange(newFilter);
  };

  const handleSaveFilter = (name: string) => {
    const newSaved: SavedFilter = { id: `user_${Date.now()}`, name, ...filter };
    const updated = [...savedFilters, newSaved];
    setSavedFilters(updated);
    persistSavedFilters(updated);
  };

  const handleDeleteSaved = (id: string) => {
    const updated = savedFilters.filter((f) => f.id !== id);
    setSavedFilters(updated);
    persistSavedFilters(updated);
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const data = await syncPreview();
      setSyncing(false);
      setPreview(data);
    } catch {
      setSyncing(false);
      alert("Erreur lors du chargement de l'aperçu Notion");
    }
  };

  const handleConfirmSync = async () => {
    setPreview(null);
    setSyncing(true);
    try {
      const { synced } = await sync();
      await Promise.all([loadTracks(), getLabels().then(setAvailableLabels)]);
      alert(`Sync OK — ${synced} morceaux`);
    } finally {
      setSyncing(false);
    }
  };

  const handleSave = async (data: Partial<Track>) => {
    if (selected) {
      await updateTrack(selected.id, data);
    } else {
      await createTrack(data);
    }
    await loadTracks();
    setView("list");
    setSelected(null);
  };

  const handleEdit = (track: Track) => {
    setSelected(track);
    setView("edit");
  };

  const handleDelete = async () => {
    if (!selected) return;
    await deleteTrack(selected.id);
    await loadTracks();
    setView("list");
    setSelected(null);
  };

  const handleSearch = (q: string) => {
    setSearch(q);
    loadTracks(q);
  };

  const getTagLabel = (type: keyof ActiveFilter, key: string): string => {
    if (type === "label") return key;
    const map: Record<Exclude<keyof ActiveFilter, "label">, keyof Wiki> = {
      grain: "grain", sensations: "sensations", masse_basse: "masse_basse", role_set: "role_set",
    };
    return wiki![map[type]].find((e) => e.key === key)?.label ?? key;
  };

  if (!wiki) {
    return (
      <div className="flex items-center justify-center h-screen text-muted text-sm">
        Chargement...
      </div>
    );
  }

  if (view === "wiki") {
    return <WikiPage wiki={wiki} onBack={() => setView("list")} />;
  }

  if (view === "sets") {
    return (
      <SetsPage
        onBack={() => setView("list")}
        onOpenSet={(s) => { setSelectedSet(s); setView("set-detail"); }}
      />
    );
  }

  if (view === "set-detail" && selectedSet) {
    return (
      <SetDetailPage
        set={selectedSet}
        wiki={wiki}
        onBack={() => setView("sets")}
        onSetUpdated={(s) => setSelectedSet(s)}
      />
    );
  }

  if (view === "add" || view === "edit") {
    return (
      <div className="flex flex-col h-screen">
        <header className="flex items-center gap-3 px-4 py-4 border-b border-border sticky top-0 bg-surface z-10">
          <button
            type="button"
            onClick={() => { setView("list"); setSelected(null); }}
            className="text-muted text-xl"
          >
            ←
          </button>
          <h1 className="text-base font-semibold flex-1">
            {view === "edit" ? "Modifier" : "Nouveau morceau"}
          </h1>
        </header>
        <div className="flex-1 overflow-y-auto px-4 pt-4">
          <TrackForm
            key={selected?.id ?? "new"}
            wiki={wiki}
            initial={selected || {}}
            mode={view === "edit" ? "edit" : "add"}
            onSave={handleSave}
            onCancel={() => { setView("list"); setSelected(null); }}
            onDelete={view === "edit" ? handleDelete : undefined}
            onOpenTrack={view === "add" ? handleEdit : undefined}
          />
        </div>
      </div>
    );
  }

  const activeCount = filterCount(filter);

  return (
    <div className="flex flex-col h-screen">
      {/* Sync preview modal */}
      {preview && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 px-4 pb-6">
          <div className="w-full max-w-md bg-surface border border-border rounded-xl p-5 space-y-4">
            <h2 className="text-sm font-semibold text-white">Sync Notion — aperçu</h2>
            {preview.new.length === 0 && preview.updated.length === 0 ? (
              <p className="text-sm text-muted">Aucun changement détecté.</p>
            ) : (
              <>
                {preview.new.length > 0 && (
                  <div>
                    <p className="text-xs text-accent font-medium mb-1">
                      {preview.new.length} nouveau{preview.new.length > 1 ? "x" : ""}
                    </p>
                    <ul className="space-y-0.5 max-h-32 overflow-y-auto">
                      {preview.new.map((t, i) => (
                        <li key={i} className="text-xs text-gray-300 truncate">
                          {t.name} <span className="text-muted">— {t.artist}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {preview.updated.length > 0 && (
                  <div>
                    <p className="text-xs text-muted font-medium mb-1">{preview.updated.length} mis à jour</p>
                    <ul className="space-y-0.5 max-h-24 overflow-y-auto">
                      {preview.updated.map((t, i) => (
                        <li key={i} className="text-xs text-gray-500 truncate">
                          {t.name} <span className="text-muted">— {t.artist}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
            <div className="flex gap-2 pt-1">
              <button type="button" onClick={handleConfirmSync}
                className="flex-1 text-xs py-2 rounded-lg bg-accent text-white font-medium">
                Confirmer
              </button>
              <button type="button" onClick={() => setPreview(null)}
                className="flex-1 text-xs py-2 rounded-lg border border-border text-muted">
                Annuler
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Filter panel */}
      {filterOpen && (
        <FilterPanel
          wiki={wiki}
          filter={filter}
          sort={sort}
          savedFilters={savedFilters}
          availableLabels={availableLabels}
          onFilterChange={handleFilterChange}
          onSortChange={handleSortChange}
          onSaveFilter={handleSaveFilter}
          onDeleteSaved={handleDeleteSaved}
          onClose={() => setFilterOpen(false)}
        />
      )}

      <header className="sticky top-0 bg-surface z-10 border-b border-border">
        {/* Top row */}
        <div className="flex items-center justify-between px-4 py-3">
          <h1 className="text-base font-semibold text-accent">Digg IT 🪏</h1>
          <div className="flex gap-2">
            <button type="button" onClick={() => setView("wiki")}
              className="text-xs px-3 py-1.5 rounded-lg border border-border text-muted">
              Wiki
            </button>
            <button type="button" onClick={() => setView("sets")}
              className="text-xs px-3 py-1.5 rounded-lg border border-border text-muted">
              Sets
            </button>
            <button type="button" onClick={handleSync} disabled={syncing}
              className="text-xs px-3 py-1.5 rounded-lg border border-border text-muted disabled:opacity-40">
              {syncing ? "Sync..." : "⟳ Sync"}
            </button>
            <button type="button" onClick={() => setView("add")}
              className="text-xs px-3 py-1.5 rounded-lg bg-accent text-white font-medium">
              + Ajouter
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="px-4 pb-2">
          <input
            className="w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-muted focus:outline-none focus:border-accent"
            placeholder="Rechercher artiste, titre, label..."
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
          />
        </div>

        {/* Filter row */}
        <div className="flex items-center gap-2 px-4 pb-3">
          <button
            type="button"
            onClick={() => setFilterOpen(true)}
            className={`flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg border shrink-0 transition-colors ${
              activeCount > 0
                ? "border-accent text-accent bg-accent/10"
                : "border-border text-muted"
            }`}
          >
            ⊞{activeCount > 0 ? ` ${activeCount}` : " Filtres"}
          </button>

          {/* Active filter pills */}
          {activeCount > 0 && (
            <div className="flex gap-1.5 overflow-x-auto flex-1 scrollbar-hide">
              {(Object.keys(filter) as Array<keyof ActiveFilter>).flatMap((type) =>
                filter[type].map((key) => (
                  <button
                    key={`${type}-${key}`}
                    type="button"
                    onClick={() => handleFilterChange(toggleTag(filter, type, key))}
                    className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-accent/15 text-accent border border-accent/30 whitespace-nowrap shrink-0"
                  >
                    {getTagLabel(type, key)} <span className="text-accent/50">×</span>
                  </button>
                ))
              )}
            </div>
          )}

          {/* Results count — shown when filtering or searching */}
          {(activeCount > 0 || search) && (
            <span className="text-xs text-muted shrink-0 ml-auto">
              {tracks.length} résultat{tracks.length !== 1 ? "s" : ""}
            </span>
          )}

          {/* Sort toggle */}
          <div className={`flex items-center gap-0.5 shrink-0 ${activeCount > 0 || search ? "" : "ml-auto"}`}>
            <button
              type="button"
              onClick={() => {
                const fields = ["id", "name", "artist"] as const;
                const next = fields[(fields.indexOf(sort.field) + 1) % fields.length];
                handleSortChange({ field: next, dir: next === "id" ? "desc" : "asc" });
              }}
              className="text-xs text-muted px-1"
            >
              {SORT_LABELS[sort.field]}
            </button>
            <button
              type="button"
              onClick={() => handleSortChange({ ...sort, dir: sort.dir === "asc" ? "desc" : "asc" })}
              className="text-xs text-muted w-4 text-center"
            >
              {sort.dir === "desc" ? "↓" : "↑"}
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {tracks.length === 0 ? (
          <p className="text-center text-muted text-sm pt-12">
            {search || activeCount > 0 ? "Aucun résultat" : "Lance un Sync pour charger tes morceaux"}
          </p>
        ) : (
          tracks.map((t) => (
            <TrackCard
              key={t.id}
              track={t}
              wiki={wiki}
              onClick={() => handleEdit(t)}
              onTagClick={handleTagClick}
              onLongPress={() => setContextTrack(t)}
            />
          ))
        )}
      </main>

      <div className="px-4 py-2 border-t border-border text-xs text-muted text-center">
        {tracks.length} morceaux{activeCount > 0 ? " (filtrés)" : ""}
      </div>

      {contextTrack && (
        <SetContextMenu
          track={contextTrack}
          onClose={() => setContextTrack(null)}
        />
      )}
    </div>
  );
}
