import { useEffect, useState } from "react";
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
  const [tracks, setTracks] = useState<SetTrackEntry[]>([]);
  const [renaming, setRenaming] = useState(false);
  const [newName, setNewName] = useState(set.name);

  const load = () => getSetTracks(set.id).then(setTracks);
  useEffect(() => { load(); }, [set.id]);

  const handleRemove = async (setTrackId: number) => {
    await removeFromSet(set.id, setTrackId);
    await load();
  };

  const handleMove = async (index: number, dir: -1 | 1) => {
    const next = index + dir;
    if (next < 0 || next >= tracks.length) return;
    const reordered = [...tracks];
    [reordered[index], reordered[next]] = [reordered[next], reordered[index]];
    setTracks(reordered);
    await reorderSet(set.id, reordered.map((t) => t.set_track_id));
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

      <main className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {tracks.length === 0 && (
          <p className="text-center text-muted text-sm pt-12">Aucun morceau dans ce set</p>
        )}
        {tracks.map((entry, i) => (
          <div key={entry.set_track_id} className="flex items-start gap-2">
            <span className="text-xs text-muted font-mono mt-[18px] w-5 shrink-0 text-right">
              {entry.position}
            </span>

            <div className="flex-1 min-w-0">
              {entry.deleted ? (
                <div className="bg-card border border-border rounded-xl px-4 py-3 opacity-40">
                  <p className="text-sm text-muted italic">Morceau supprimé</p>
                </div>
              ) : (
                <TrackCard
                  track={entry}
                  wiki={wiki}
                  onClick={() => {}}
                />
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
                disabled={i === tracks.length - 1}
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
        {tracks.length} morceau{tracks.length !== 1 ? "x" : ""}
      </div>
    </div>
  );
}
