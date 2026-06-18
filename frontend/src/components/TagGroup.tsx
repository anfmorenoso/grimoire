import type { VocabEntry } from "../vocabulary";
import Tooltip from "./Tooltip";

interface Props {
  title: string;
  entries: VocabEntry[];
  selected: string | string[];
  aiSuggested?: string | string[];
  multi?: boolean;
  long?: boolean;
  onChange: (value: string | string[]) => void;
}

export default function TagGroup({ title, entries, selected, aiSuggested, multi, long, onChange }: Props) {
  const isSelected = (key: string) =>
    Array.isArray(selected) ? selected.includes(key) : selected === key;

  const isAiSuggested = (key: string) => {
    if (!aiSuggested) return false;
    return Array.isArray(aiSuggested) ? aiSuggested.includes(key) : aiSuggested === key;
  };

  const toggle = (key: string) => {
    if (multi) {
      const arr = Array.isArray(selected) ? selected : [];
      onChange(arr.includes(key) ? arr.filter((k) => k !== key) : [...arr, key]);
    } else {
      onChange(isSelected(key) ? "" : key);
    }
  };

  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold uppercase tracking-widest text-muted">{title}</h3>
      <div className={`grid gap-2 ${long ? "grid-cols-1" : "grid-cols-2"}`}>
        {entries.map((e) => {
          const sel = isSelected(e.key);
          const ai = isAiSuggested(e.key);
          return (
            <Tooltip key={e.key} content={e.description}>
              <button
                type="button"
                onClick={() => toggle(e.key)}
                className={`
                  px-3 py-2 rounded-lg text-sm font-medium transition-all text-left
                  border leading-tight min-h-[40px] relative w-full
                  ${sel
                    ? "bg-accent text-white border-accent"
                    : ai
                      ? "bg-accent/10 text-accent border-accent/50"
                      : "bg-card text-gray-300 border-border hover:border-accent/50"
                  }
                `}
              >
                {long ? (e.notion_value || e.label) : e.label}
                {ai && !sel && (
                  <span className="absolute top-1 right-1.5 text-[9px] text-accent/70 font-bold">IA</span>
                )}
              </button>
            </Tooltip>
          );
        })}
      </div>
    </div>
  );
}
