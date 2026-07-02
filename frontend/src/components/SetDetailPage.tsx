import { useEffect, useRef, useState } from "react";
import type { DJSet, SetTrackEntry } from "../api";
import { getSetTracks, removeFromSet, renameSet, reorderSet } from "../api";
import type { Wiki } from "../vocabulary";
import TrackCard from "./TrackCard";

interface Props {
  set: DJSet;
  wiki: Wiki;
  onBack: () => void;
  onSetUpdated: (set: DJSet) => void;
}

export default function SetDetailPage({ set, wiki, onBack, onSetUpdated }: Props) {
  const [saved, setSaved] = useState<SetTrackEntry[]>([]);   // last committed state
  const [pending, setPending] = useState<SetTrackEntry[]>([]); // working copy
  const [removed, setRemoved] = useState<Set<number>>(new Set());
  const [saving, setSaving] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [newName, setNewName] = useState(set.name);
  const loadedRef = useRef(false);

  const isDirty = removed.size > 0 ||
    pending.some((t, i) => t.set_track_id !== saved[i]?.set_track_id);

  const load = async () => {
    const data = await getSetTracks(set.id);
    setSaved(data);
    setPending(data);
    setRemoved(new Set());
  };

  useEffect(() => {
    if (!loadedRef.current) { loadedRef.current = true; load(); }
  }, [set.id]);

  const handleMove = (index: number, dir: -1 | 1) => {
    const next = index + dir;
    if (next < 0 || next >= pending.length) return;
    const reordered = [...pending];
    [reordered[index], reordered[next]] = [reordered[next], reordered[index]];
    setPending(reordered);
  };

  const handleRemove = (setTrackId: number) => {
    setPending((p) => p.filter((t) => t.set_track_id !== setTrackId));
    setRemoved((r) => new Set([...r, setTrackId]));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Delete removed entries
      for (const id of removed) {
        await removeFromSet(set.id, id);
      }
      // Reorder remaining (backend re-numbers positions 1..N)
      if (pending.length > 0) {
        await reorderSet(set.id, pending.map((t) => t.set_track_id));
      }
      await load();
    } finally {
      setSaving(false);
    }
  };

  const handleDiscard = () => {
    setPending([...saved]);
    setRemoved(new Set());
  };

  const handleRename = async () => {
    const name = newName.trim();
    setRenaming(false);
    if (!name || name === set.name) return;
    const updated = await renameSet(set.id, name);
    onSetUpdated({ ...set, ...updated });
  };

  return (
    <div className="flex flex-col h-screen">
      <header className="flex items-center gap-3 px-4 py-4 border-b border-border sticky top-0 bg-surface z-10">
        <button type="button" onClick={onBack} className="text-muted text-xl">
          ←
        </button>
        {renaming ? (
          <input
            autoFocus
            className="flex-1 bg-card border border-accent rounded-lg px-2 py-1 text-sm text-gray-200 focus:outline-none"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onBlur={handleRename}
            onKeyDown={(e) => e.key === "Enter" && handleRename()}
          />
        ) : (
          <h1 className="text-base font-semibold flex-1 truncate">{set.name}</h1>
        )}
        <button
          type="button"
          onClick={() => { setNewName(set.name); setRenaming((r) => !r); }}
          className="text-xs text-muted px-2 py-1 border border-border rounded-lg shrink-0"
        >
          ✏️
        </button>
      </header>

      {isDirty && (
        <div className="flex gap-2 px-4 py-2 border-b border-border bg-surface shrink-0">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="flex-1 text-xs py-2 rounded-lg bg-accent text-white font-medium disabled:opacity-50"
          >
            {saving ? "Sauvegarde…" : "Sauvegarder"}
          </button>
          <button
            type="button"
            onClick={handleDiscard}
            disabled={saving}
            className="flex-1 text-xs py-2 rounded-lg border border-border text-muted"
          >
            Annuler
          </button>
        </div>
      )}

      <main className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {pending.length === 0 && (
          <p className="text-center text-muted text-sm pt-12">Aucun morceau dans ce set</p>
        )}
        {pending.map((entry, i) => (
          <div key={entry.set_track_id} className="flex items-start gap-2">
            <span className="text-xs text-muted font-mono mt-[18px] w-5 shrink-0 text-right">
              {i + 1}
            </span>

            <div className="flex-1 min-w-0 space-y-1">
              {entry.deleted ? (
                <div className="bg-card border border-border rounded-xl px-4 py-3 opacity-40">
                  <p className="text-sm text-muted italic">Morceau supprimé</p>
                </div>
              ) : (
                <>
                  <TrackCard track={entry} wiki={wiki} onClick={() => {}} />
                  {(entry.layering || entry.notes) && (
                    <div className="px-3 py-2 rounded-lg bg-card/50 border border-border/50">
                      {entry.layering && (
                        <p className="text-xs text-muted leading-relaxed">{entry.layering}</p>
                      )}
                      {entry.notes && (
                        <p className="text-xs text-gray-500 leading-relaxed mt-0.5">{entry.notes}</p>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="flex flex-col gap-1 mt-2 shrink-0">
              <button
                type="button"
                onClick={() => handleMove(i, -1)}
                disabled={i === 0}
                className="text-xs text-muted w-7 h-7 flex items-center justify-center rounded border border-border disabled:opacity-20 active:bg-border"
              >
                ↑
              </button>
              <button
                type="button"
                onClick={() => handleMove(i, 1)}
                disabled={i === pending.length - 1}
                className="text-xs text-muted w-7 h-7 flex items-center justify-center rounded border border-border disabled:opacity-20 active:bg-border"
              >
                ↓
              </button>
              <button
                type="button"
                onClick={() => handleRemove(entry.set_track_id)}
                className="text-xs w-7 h-7 flex items-center justify-center rounded border border-red-400/30 text-red-400 active:bg-red-400/10"
              >
                🗑
              </button>
            </div>
          </div>
        ))}
      </main>

      <div className="px-4 py-2 border-t border-border text-xs text-muted text-center">
        {pending.length} morceau{pending.length !== 1 ? "x" : ""}
        {isDirty && <span className="text-accent ml-1">· modifié</span>}
      </div>
    </div>
  );
}
