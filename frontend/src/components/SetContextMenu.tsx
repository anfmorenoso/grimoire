import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { DJSet, Track } from "../api";
import { addTrackToSet, createSet, getSets } from "../api";

interface Props {
  track: Track;
  onClose: () => void;
}

export default function SetContextMenu({ track, onClose }: Props) {
  const [sets, setSets] = useState<DJSet[]>([]);
  const [newName, setNewName] = useState("");
  const [adding, setAdding] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getSets().then(setSets);
  }, []);

  const handleAdd = async (setId: number, force = false) => {
    setAdding(setId);
    try {
      await addTrackToSet(setId, track.id, force);
      onClose();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      if (detail === "already_in_set") {
        if (confirm(`"${track.name}" est déjà dans ce set. Ajouter quand même ?`)) {
          await addTrackToSet(setId, track.id, true);
          onClose();
        }
      }
    } finally {
      setAdding(null);
    }
  };

  const handleCreate = async () => {
    const name = newName.trim();
    if (!name) return;
    setCreating(true);
    try {
      const newSet = await createSet(name);
      await addTrackToSet(newSet.id, track.id);
      onClose();
    } finally {
      setCreating(false);
    }
  };

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-end" onClick={onClose}>
      <div
        className="w-full bg-surface border-t border-border rounded-t-2xl p-4 space-y-3 max-h-[70vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <p className="text-xs text-muted shrink-0">
          Ajouter à un set :{" "}
          <span className="text-white font-medium">{track.name}</span>
        </p>

        <div className="overflow-y-auto flex-1 space-y-2">
          {sets.length === 0 && (
            <p className="text-xs text-muted text-center py-3">Aucun set existant</p>
          )}
          {sets.map((s) => (
            <button
              key={s.id}
              type="button"
              disabled={adding === s.id}
              onClick={() => handleAdd(s.id)}
              className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg bg-card border border-border text-sm text-left disabled:opacity-50"
            >
              <span className="font-medium text-gray-200 truncate">{s.name}</span>
              <span className="text-xs text-muted ml-2 shrink-0">
                {s.track_count} morceau{s.track_count !== 1 ? "x" : ""}
              </span>
            </button>
          ))}
        </div>

        <div className="flex gap-2 shrink-0 pt-1">
          <input
            ref={inputRef}
            className="flex-1 bg-card border border-border rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-muted focus:outline-none focus:border-accent"
            placeholder="Nouveau set..."
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
          />
          <button
            type="button"
            onClick={handleCreate}
            disabled={!newName.trim() || creating}
            className="px-3 py-2 rounded-lg bg-accent text-white text-sm font-medium disabled:opacity-40"
          >
            Créer
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
