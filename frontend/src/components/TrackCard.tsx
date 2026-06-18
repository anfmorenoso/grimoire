import type { Track } from "../api";
import type { Wiki } from "../vocabulary";
import type { ActiveFilter } from "../filters";

interface Props {
  track: Track;
  wiki: Wiki;
  onClick: () => void;
  onTagClick?: (type: keyof ActiveFilter, key: string) => void;
}

const ROLE_COLORS: Record<string, string> = {
  amorce: "text-blue-400",
  construction: "text-yellow-400",
  peak_time: "text-red-400",
  planage: "text-purple-400",
};

function TagChip({
  children, className, type, tagKey, onTagClick,
}: {
  children: string;
  className: string;
  type: keyof ActiveFilter;
  tagKey: string;
  onTagClick?: (type: keyof ActiveFilter, key: string) => void;
}) {
  if (onTagClick) {
    return (
      <button
        type="button"
        onClick={(e) => { e.stopPropagation(); onTagClick(type, tagKey); }}
        className={`${className} hover:opacity-70 transition-opacity`}
      >
        {children}
      </button>
    );
  }
  return <span className={className}>{children}</span>;
}

export default function TrackCard({ track, wiki, onClick, onTagClick }: Props) {
  const roleEntry = wiki.role_set.find((e) => e.key === track.role_set);
  const grainEntry = wiki.grain.find((e) => e.key === track.grain);
  const massEntry = wiki.masse_basse.find((e) => e.key === track.masse_basse);
  const sensationEntries = track.sensations
    .map((s) => wiki.sensations.find((e) => e.key === s))
    .filter(Boolean) as typeof wiki.sensations;

  return (
    <div
      onClick={onClick}
      className="w-full text-left bg-card border border-border rounded-xl p-4 space-y-2 active:scale-[0.98] transition-transform cursor-pointer"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-gray-100 leading-tight truncate">{track.name}</p>
          <p className="text-sm text-muted truncate">{track.artist}</p>
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0 max-w-[110px]">
          {track.label && (
            onTagClick ? (
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); onTagClick("label", track.label!); }}
                className="text-xs text-muted text-right truncate w-full hover:text-accent/80 transition-colors"
              >
                {track.label}
              </button>
            ) : (
              <span className="text-xs text-muted text-right truncate w-full">{track.label}</span>
            )
          )}
          {track.bpm && <span className="text-xs text-muted">{track.bpm} BPM</span>}
          {track.downloaded && (
            <span className="text-xs">{track.hq_download ? "✅✅" : "✅"}</span>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {roleEntry && (
          <TagChip type="role_set" tagKey={track.role_set!} onTagClick={onTagClick}
            className={`text-xs font-medium ${ROLE_COLORS[track.role_set!] ?? "text-gray-400"}`}>
            {roleEntry.label}
          </TagChip>
        )}
        {grainEntry && (
          <TagChip type="grain" tagKey={track.grain!} onTagClick={onTagClick}
            className="text-xs px-2 py-0.5 rounded bg-border text-gray-300">
            {grainEntry.label}
          </TagChip>
        )}
        {massEntry && (
          <TagChip type="masse_basse" tagKey={track.masse_basse!} onTagClick={onTagClick}
            className="text-xs px-2 py-0.5 rounded bg-border text-gray-300">
            {massEntry.label}
          </TagChip>
        )}
        {sensationEntries.map((s) => (
          <TagChip key={s.key} type="sensations" tagKey={s.key} onTagClick={onTagClick}
            className="text-xs px-2 py-0.5 rounded bg-accent/20 text-accent">
            {s.label}
          </TagChip>
        ))}
      </div>
    </div>
  );
}
