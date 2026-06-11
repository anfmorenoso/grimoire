export interface ActiveFilter {
  grain: string[];
  sensations: string[];
  masse_basse: string[];
  role_set: string[];
  label: string[];
}

export interface SavedFilter {
  id: string;
  name: string;
  grain: string[];
  sensations: string[];
  masse_basse: string[];
  role_set: string[];
  label: string[];
}

export type SortField = "id" | "name" | "artist";
export type SortDir = "asc" | "desc";

export interface Sort {
  field: SortField;
  dir: SortDir;
}

export const EMPTY_FILTER: ActiveFilter = { grain: [], sensations: [], masse_basse: [], role_set: [], label: [] };
export const DEFAULT_SORT: Sort = { field: "id", dir: "desc" };

export const SORT_LABELS: Record<SortField, string> = {
  id: "Récent",
  name: "Nom",
  artist: "Artiste",
};

export function filterCount(f: ActiveFilter): number {
  return f.grain.length + f.sensations.length + f.masse_basse.length + f.role_set.length + f.label.length;
}

export function filterIsEmpty(f: ActiveFilter): boolean {
  return filterCount(f) === 0;
}

export function toggleTag(f: ActiveFilter, type: keyof ActiveFilter, key: string): ActiveFilter {
  const current = f[type];
  return {
    ...f,
    [type]: current.includes(key) ? current.filter((k) => k !== key) : [...current, key],
  };
}

export const DEFAULT_PRESETS: SavedFilter[] = [
  {
    id: "preset_peak_time",
    name: "Peak Time",
    grain: [],
    sensations: [],
    masse_basse: ["lourd"],
    role_set: ["peak_time"],
    label: [],
  },
  {
    id: "preset_ouverture",
    name: "Ouverture",
    grain: [],
    sensations: [],
    masse_basse: [],
    role_set: ["amorce", "planage"],
    label: [],
  },
];
