import { useState } from "react";
import type { Wiki } from "../vocabulary";
import type { Track, SpotifyMeta, AiSuggestion } from "../api";
import { lookupSpotify, suggestTags } from "../api";
import TagGroup from "./TagGroup";

interface Props {
  wiki: Wiki;
  initial?: Partial<Track>;
  onSave: (data: Partial<Track>) => Promise<void>;
  onCancel: () => void;
}

type AiState = "idle" | "loading" | "done";

function AiNote({ children }: { children: string }) {
  return (
    <p className="text-xs text-gray-500 leading-relaxed bg-accent/5 border border-accent/15 rounded-lg px-3 py-2">
      {children}
    </p>
  );
}

function hasUserTags(form: Partial<Track>): boolean {
  return !!(form.grain || (form.sensations?.length ?? 0) > 0 || form.masse_basse || form.role_set);
}

export default function TrackForm({ wiki, initial = {}, onSave, onCancel }: Props) {
  const [form, setForm] = useState<Partial<Track>>({
    name: "", artist: "", album: "", label: "", year: undefined, bpm: undefined,
    key: "", grain: "", sensations: [], masse_basse: "", role_set: "",
    url: "", downloaded: false, hq_download: false, notes: "", layering: "",
    ...initial,
  });

  const [spotifyUrl, setSpotifyUrl] = useState("");
  const [lookingUp, setLookingUp] = useState(false);
  const [saving, setSaving] = useState(false);
  const [aiState, setAiState] = useState<AiState>("idle");
  const [aiSuggestion, setAiSuggestion] = useState<AiSuggestion | null>(null);
  const [compareMode, setCompareMode] = useState(false);
  const [longNames, setLongNames] = useState(false);

  const set = (field: keyof Track, value: unknown) =>
    setForm((f) => ({ ...f, [field]: value }));

  const handleSpotifyLookup = async () => {
    if (!spotifyUrl) return;
    setLookingUp(true);
    try {
      const meta: SpotifyMeta = await lookupSpotify(spotifyUrl);
      setForm((f) => ({
        ...f,
        name: meta.name,
        artist: meta.artist,
        label: meta.label || f.label,
        year: meta.year ?? f.year,
        url: meta.url,
        bpm: meta.bpm ?? f.bpm,
        key: meta.key ?? f.key,
      }));
      setSpotifyUrl("");
      setAiSuggestion(null);
      setCompareMode(false);
    } catch {
      alert("Impossible de récupérer les métadonnées Spotify.");
    } finally {
      setLookingUp(false);
    }
  };

  const handleAiSuggest = async () => {
    if (!form.name || !form.artist) {
      alert("Remplis au minimum le titre et l'artiste avant d'analyser.");
      return;
    }
    const isCompare = hasUserTags(form);
    setAiState("loading");
    setCompareMode(isCompare);
    try {
      const suggestion = await suggestTags(
        form.name, form.artist, form.label ?? undefined,
        form.bpm ?? undefined, form.key ?? undefined,
      );
      setAiSuggestion(suggestion);
      if (!isCompare) {
        setForm((f) => ({
          ...f,
          grain: suggestion.grain || f.grain,
          sensations: suggestion.sensations || f.sensations,
          masse_basse: suggestion.masse_basse || f.masse_basse,
          role_set: suggestion.role_set || f.role_set,
          layering: suggestion.layering_note || f.layering,
          bpm: f.bpm ?? (suggestion.bpm_estimate ?? undefined),
        }));
      } else {
        setForm((f) => ({
          ...f,
          layering: suggestion.layering_note || f.layering,
          bpm: f.bpm ?? (suggestion.bpm_estimate ?? undefined),
        }));
      }
      setAiState("done");
    } catch {
      alert("Erreur lors de l'analyse IA.");
      setAiState("idle");
    }
  };

  const applyAiSuggestion = () => {
    if (!aiSuggestion) return;
    setForm((f) => ({
      ...f,
      grain: aiSuggestion.grain || f.grain,
      sensations: aiSuggestion.sensations || f.sensations,
      masse_basse: aiSuggestion.masse_basse || f.masse_basse,
      role_set: aiSuggestion.role_set || f.role_set,
    }));
    setCompareMode(false);
  };


  const handleSave = async () => {
    if (!form.name || !form.artist) { alert("Titre et artiste obligatoires."); return; }
    setSaving(true);
    try { await onSave(form); } finally { setSaving(false); }
  };

  const input = "w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-muted focus:outline-none focus:border-accent";

  const aiButtonLabel = () => {
    if (aiState === "loading") return "Analyse...";
    if (compareMode && aiState === "done") return "✨ Ré-analyser";
    if (hasUserTags(form)) return "✨ Comparer avec IA";
    return "✨ Analyser avec IA";
  };

  return (
    <div className="flex flex-col gap-5 pb-8">

      {/* Spotify */}
      <div className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted">Import Spotify</h3>
        <div className="flex gap-2">
          <input
            className={`${input} flex-1`}
            placeholder="Colle un lien Spotify..."
            value={spotifyUrl}
            onChange={(e) => setSpotifyUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSpotifyLookup()}
          />
          <button type="button" onClick={handleSpotifyLookup} disabled={lookingUp || !spotifyUrl}
            className="px-4 py-2 rounded-lg bg-accent text-white text-sm font-medium disabled:opacity-40">
            {lookingUp ? "..." : "→"}
          </button>
        </div>
      </div>

      {/* Basic info */}
      <div className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted">Infos</h3>
        <input className={input} placeholder="Titre *" value={form.name || ""} onChange={(e) => set("name", e.target.value)} />
        <input className={input} placeholder="Artiste *" value={form.artist || ""} onChange={(e) => set("artist", e.target.value)} />
        <input className={input} placeholder="Label" value={form.label || ""} onChange={(e) => set("label", e.target.value)} />
        {aiSuggestion?.label_suggestions && aiSuggestion.label_suggestions.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {aiSuggestion.label_suggestions.map((l) => (
              <button
                key={l}
                type="button"
                onClick={() => set("label", l)}
                className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                  form.label === l
                    ? "bg-accent text-white border-accent"
                    : "bg-accent/10 text-accent border-accent/40 hover:bg-accent/20"
                }`}
              >
                {l}
              </button>
            ))}
          </div>
        )}
        <div className="flex gap-2">
          <input className={`${input} w-24`} placeholder="BPM" type="number" value={form.bpm || ""} onChange={(e) => set("bpm", e.target.value ? Number(e.target.value) : undefined)} />
          <input className={`${input} flex-1`} placeholder="Clé (ex: 4A)" value={form.key || ""} onChange={(e) => set("key", e.target.value)} />
        </div>
        <input className={`${input} w-28`} placeholder="Année" type="number" min="1950" max="2099" value={form.year || ""} onChange={(e) => set("year", e.target.value ? Number(e.target.value) : undefined)} />
        {aiState === "done" && aiSuggestion?.bpm_estimate && (
          <div className="flex items-center gap-2 text-xs text-accent/70">
            <span>BPM estimé par IA : {aiSuggestion.bpm_estimate}</span>
            {form.bpm !== aiSuggestion.bpm_estimate && (
              <button type="button" onClick={() => set("bpm", aiSuggestion.bpm_estimate!)}
                className="underline underline-offset-2 hover:text-accent">
                Appliquer
              </button>
            )}
          </div>
        )}
        <input className={input} placeholder="URL" value={form.url || ""} onChange={(e) => set("url", e.target.value)} />
        <div className="flex gap-4">
          <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
            <input type="checkbox" checked={form.downloaded || false} onChange={(e) => set("downloaded", e.target.checked)} className="accent-accent" />
            Téléchargé
          </label>
          <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
            <input type="checkbox" checked={form.hq_download || false} onChange={(e) => set("hq_download", e.target.checked)} className="accent-accent" />
            ✅✅ HQ
          </label>
        </div>
      </div>

      {/* AI button */}
      <button
        type="button"
        onClick={handleAiSuggest}
        disabled={aiState === "loading"}
        className="w-full py-2.5 rounded-lg border border-accent/40 text-accent text-sm font-medium disabled:opacity-40 hover:bg-accent/10 transition-colors"
      >
        {aiButtonLabel()}
      </button>

      {/* AI overall summary */}
      {aiState === "done" && aiSuggestion?.reasoning && (
        <p className="text-xs text-accent/70 italic leading-relaxed px-1">{aiSuggestion.reasoning}</p>
      )}

      {/* Tags — each followed by its AI reasoning */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-widest text-muted">Étiquettes</span>
        <button
          type="button"
          onClick={() => setLongNames((v) => !v)}
          className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
            longNames
              ? "bg-accent text-white border-accent"
              : "bg-card text-muted border-border"
          }`}
        >
          {longNames ? "Long" : "Court"}
        </button>
      </div>

      <TagGroup
        title="Grain"
        entries={wiki.grain}
        selected={form.grain || ""}
        aiSuggested={compareMode ? aiSuggestion?.grain : undefined}
        long={longNames}
        onChange={(v) => set("grain", v)}
      />
      {aiState === "done" && aiSuggestion?.grain_reasoning && (
        <AiNote>{aiSuggestion.grain_reasoning}</AiNote>
      )}

      <TagGroup
        title="Sensations"
        entries={wiki.sensations}
        selected={form.sensations || []}
        aiSuggested={compareMode ? aiSuggestion?.sensations : undefined}
        multi
        long={longNames}
        onChange={(v) => set("sensations", v)}
      />
      {aiState === "done" && aiSuggestion?.sensations_reasoning && (
        <AiNote>{aiSuggestion.sensations_reasoning}</AiNote>
      )}

      <TagGroup
        title="Masse Basse"
        entries={wiki.masse_basse}
        selected={form.masse_basse || ""}
        aiSuggested={compareMode ? aiSuggestion?.masse_basse : undefined}
        long={longNames}
        onChange={(v) => set("masse_basse", v)}
      />
      {aiState === "done" && aiSuggestion?.masse_basse_reasoning && (
        <AiNote>{aiSuggestion.masse_basse_reasoning}</AiNote>
      )}

      <TagGroup
        title="Role Set"
        entries={wiki.role_set}
        selected={form.role_set || ""}
        aiSuggested={compareMode ? aiSuggestion?.role_set : undefined}
        long={longNames}
        onChange={(v) => set("role_set", v)}
      />
      {aiState === "done" && aiSuggestion?.role_set_reasoning && (
        <AiNote>{aiSuggestion.role_set_reasoning}</AiNote>
      )}

      {/* Layering — editable, auto-filled by AI */}
      <div className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted">
          Layering
          {aiState === "done" && aiSuggestion?.layering_note && (
            <span className="ml-2 text-[9px] text-accent/60 normal-case font-normal tracking-normal">généré par IA — éditable</span>
          )}
        </h3>
        <textarea
          className={`${input} resize-none h-32`}
          placeholder="Histoire du morceau et conseils de layering..."
          value={form.layering || ""}
          onChange={(e) => set("layering", e.target.value)}
        />
      </div>

      {/* Apply button (compare mode) */}
      {compareMode && aiState === "done" && (
        <button type="button" onClick={applyAiSuggestion}
          className="text-xs text-accent underline underline-offset-2">
          Appliquer les suggestions IA
        </button>
      )}

      {/* Notes */}
      <div className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted">Notes</h3>
        <textarea className={`${input} resize-none h-20`} placeholder="Notes libres..."
          value={form.notes || ""} onChange={(e) => set("notes", e.target.value)} />
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button type="button" onClick={onCancel}
          className="flex-1 py-3 rounded-lg border border-border text-gray-400 text-sm font-medium">
          Annuler
        </button>
        <button type="button" onClick={handleSave} disabled={saving}
          className="flex-1 py-3 rounded-lg bg-accent text-white text-sm font-semibold disabled:opacity-40">
          {saving ? "Envoi..." : "Sauvegarder"}
        </button>
      </div>
    </div>
  );
}
