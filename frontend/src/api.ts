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
  hq_download: boolean;
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

export interface Collection {
  collection: string;
  count: number;
  hidden: boolean;
}

export interface TrackFilter {
  q?: string;
  grain?: string[];
  masse_basse?: string[];
  role_set?: string[];
  sensation?: string[];
  label?: string[];
  collection?: string[];
  sort?: SortField;
  dir?: SortDir;
}

export interface TrackStats {
  grain: Record<string, number>;
  sensations: Record<string, number>;
  masse_basse: Record<string, number>;
  role_set: Record<string, number>;
}

export const getWiki = () => api.get<Wiki>("/wiki").then((r) => r.data);
export const getTrackStats = () => api.get<TrackStats>("/tracks/stats").then((r) => r.data);
export const getLabels = () => api.get<string[]>("/labels").then((r) => r.data);
export const getCollections = () => api.get<Collection[]>("/collections").then((r) => r.data);
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

export interface DJSet {
  id: number;
  name: string;
  created_at: number;
  track_count: number;
}

export type SetTrackEntry =
  | { set_track_id: number; position: number; deleted: true }
  | ({ set_track_id: number; position: number; deleted?: false } & Track);

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

export const getSets = () => api.get<DJSet[]>("/sets").then((r) => r.data);
export const createSet = (name: string) => api.post<DJSet>("/sets", { name }).then((r) => r.data);
export const renameSet = (id: number, name: string) =>
  api.patch<DJSet>(`/sets/${id}`, { name }).then((r) => r.data);
export const deleteSet = (id: number) => api.delete(`/sets/${id}`);
export const getSetTracks = (id: number) =>
  api.get<SetTrackEntry[]>(`/sets/${id}/tracks`).then((r) => r.data);
export const addTrackToSet = (setId: number, trackId: number, force = false) =>
  api.post(`/sets/${setId}/tracks`, { track_id: trackId, force }).then((r) => r.data);
export const removeFromSet = (setId: number, setTrackId: number) =>
  api.delete(`/sets/${setId}/tracks/${setTrackId}`);
export const reorderSet = (setId: number, orderedIds: number[]) =>
  api.put(`/sets/${setId}/tracks/order`, { ordered_ids: orderedIds }).then((r) => r.data);

export const suggestTags = (
  name: string,
  artist: string,
  label?: string,
  bpm?: number,
  key?: string,
) => api.post<AiSuggestion>("/suggest", { name, artist, label, bpm, key }).then((r) => r.data);
