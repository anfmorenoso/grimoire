import axios from "axios";
import type { Wiki } from "./vocabulary";
import type { SortField, SortDir } from "./filters";

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL as string | undefined) ?? "",
  paramsSerializer: (params: Record<string, unknown>) => {
    const parts: string[] = [];
    for (const [key, val] of Object.entries(params)) {
      if (val === undefined || val === null) continue;
      if (Array.isArray(val)) {
        val.forEach((v) => parts.push(`${key}=${encodeURIComponent(String(v))}`));
      } else {
        parts.push(`${key}=${encodeURIComponent(String(val))}`);
      }
    }
    return parts.join("&");
  },
});

export interface Track {
  id: number;
  notion_id?: string;
  name: string;
  artist: string;
  album?: string;
  label?: string;
  year?: number;
  bpm?: number;
  key?: string;
  grain?: string;
  sensations: string[];
  masse_basse?: string;
  role_set?: string;
  url?: string;
  downloaded: boolean;
  notes?: string;
  layering?: string;
}

export interface SpotifyMeta {
  name: string;
  artist: string;
  label?: string;
  year?: number;
  url: string;
  image_url?: string;
  bpm?: number;
  key?: string;
}

export interface SyncPreview {
  new: Array<{ name: string; artist: string }>;
  updated: Array<{ name: string; artist: string }>;
}

export interface TrackFilter {
  q?: string;
  grain?: string[];
  masse_basse?: string[];
  role_set?: string[];
  sensation?: string[];
  label?: string[];
  sort?: SortField;
  dir?: SortDir;
}

export const getWiki = () => api.get<Wiki>("/wiki").then((r) => r.data);
export const getLabels = () => api.get<string[]>("/labels").then((r) => r.data);
export const syncPreview = () => api.get<SyncPreview>("/sync/preview").then((r) => r.data);
export const sync = () => api.post<{ synced: number }>("/sync").then((r) => r.data);
export const getTracks = (params?: TrackFilter) =>
  api.get<Track[]>("/tracks", { params }).then((r) => r.data);
export const createTrack = (data: Partial<Track>) =>
  api.post<Track>("/tracks", data).then((r) => r.data);
export const updateTrack = (id: number, data: Partial<Track>) =>
  api.patch<Track>(`/tracks/${id}`, data).then((r) => r.data);
export const deleteTrack = (id: number) => api.delete(`/tracks/${id}`);
export const lookupSpotify = (url: string) =>
  api.post<SpotifyMeta>("/spotify/lookup", { url }).then((r) => r.data);

export interface AiSuggestion {
  bpm_estimate?: number | null;
  label_suggestions?: string[];
  grain?: string;
  grain_reasoning?: string;
  sensations?: string[];
  sensations_reasoning?: string;
  masse_basse?: string;
  masse_basse_reasoning?: string;
  role_set?: string;
  role_set_reasoning?: string;
  layering_note?: string;
  reasoning?: string;
}

export const suggestTags = (
  name: string,
  artist: string,
  label?: string,
  bpm?: number,
  key?: string,
) => api.post<AiSuggestion>("/suggest", { name, artist, label, bpm, key }).then((r) => r.data);
