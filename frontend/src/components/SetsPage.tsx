import { useEffect, useState } from "react";
import type { DJSet } from "../api";
import { createSet, deleteSet, getSets } from "../api";

interface Props {
  onBack: () => void;
  onOpenSet: (set: DJSet) => void;
}

export default function SetsPage({ onBack, onOpenSet }: Props) {
  const [sets, setSets] = useState<DJSet[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);

  const load = () => getSets().then(setSets);
  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    const name = newName.trim();
    if (!name) return;
    setCreating(true);
    try {
      await createSet(name);
      setNewName("");
      setShowCreate(false);
      await load();
    } finally {
      setCreating(false);
    }
  };

  const openCreate = () => { setNewName(""); setShowCreate(true); };

  const handleDelete = async (set: DJSet, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Supprimer le set "${set.name}" ?`)) return;
    await deleteSet(set.id);
    await load();
  };

  return (
    <div className="flex flex-col h-screen">
      <header className="flex items-center gap-3 px-4 py-4 border-b border-border sticky top-0 bg-surface z-10">
        <button type="button" onClick={onBack} className="text-muted text-xl">
          ←
        </button>
        <h1 className="text-base font-semibold flex-1">Sets</h1>
        <button
          type="button"
          onClick={openCreate}
          className="text-xs px-3 py-1.5 rounded-lg bg-accent text-white font-medium"
        >
          + Nouveau
        </button>
      </header>

      {showCreate && (
        <div className="px-4 py-3 border-b border-border flex gap-2 bg-surface">
          <input
            autoFocus
            className="flex-1 bg-card border border-border rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-muted focus:outline-none focus:border-accent"
            placeholder="Nom du set..."
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleCreate();
              if (e.key === "Escape") setShowCreate(false);
            }}
          />
          <button
            type="button"
            onClick={handleCreate}
            disabled={!newName.trim() || creating}
            className="px-3 py-2 rounded-lg bg-accent text-white text-sm font-medium disabled:opacity-40"
          >
            Créer
          </button>
          <button
            type="button"
            onClick={() => setShowCreate(false)}
            className="px-3 py-2 rounded-lg border border-border text-muted text-sm"
          >
            ✕
          </button>
        </div>
      )}

      <main className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {sets.length === 0 && !showCreate && (
          <p className="text-center text-muted text-sm pt-12">
            Aucun set — appuie sur + Nouveau pour commencer
          </p>
        )}
        {sets.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => onOpenSet(s)}
            className="w-full text-left bg-card border border-border rounded-xl px-4 py-3 flex items-center gap-3"
          >
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-gray-100 truncate">{s.name}</p>
              <p className="text-xs text-muted mt-0.5">
                {s.track_count} morceau{s.track_count !== 1 ? "x" : ""}
              </p>
            </div>
            <button
              type="button"
              onClick={(e) => handleDelete(s, e)}
              className="text-muted hover:text-red-400 transition-colors text-base px-1 shrink-0"
            >
              🗑
            </button>
          </button>
        ))}
      </main>

    </div>
  );
}
