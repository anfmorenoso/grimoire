# Feature: Sets (Playlists)

Create ordered playlists ("sets") from tracks in the grimoire. A DJ set is a curated, ordered list of tracks to play in sequence.

## User Stories

- Long-press a track card → context menu appears → "Ajouter à un set"
  - Shows list of existing sets + "Nouveau set" option
  - If track is already in that set → alert "Déjà dans ce set — ajouter quand même ?"
- New "Sets" button in header (between Wiki and Sync)
- Sets view: list of all sets (name + track count + date)
  - Tap a set → set detail view with ordered tracks
  - Tracks show their position number + full TrackCard
  - Reorder via ↑↓ buttons (mobile-friendly, no drag)
  - Remove individual tracks from set
  - Rename or delete the set

---

## Backend

### New tables — `database.py`

```sql
CREATE TABLE IF NOT EXISTS sets (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL,
    created_at INTEGER DEFAULT (unixepoch())
);

CREATE TABLE IF NOT EXISTS set_tracks (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    set_id   INTEGER NOT NULL REFERENCES sets(id) ON DELETE CASCADE,
    track_id INTEGER REFERENCES tracks(id) ON DELETE SET NULL,  -- NULL = deleted track
    position INTEGER NOT NULL
);
```

`track_id` is nullable with `ON DELETE SET NULL`: when a track is deleted from the grimoire, its slot in the set becomes `NULL` instead of disappearing. The position is preserved so the rest of the set order stays intact.

Add both tables in `init_db()` alongside existing tracks table.

### New routes — `main.py`

| Method | Path | Body | Returns |
|--------|------|------|---------|
| `GET` | `/sets` | — | `[{id, name, created_at, track_count}]` |
| `POST` | `/sets` | `{name}` | `{id, name, created_at}` |
| `PATCH` | `/sets/{id}` | `{name}` | `{id, name, created_at}` |
| `DELETE` | `/sets/{id}` | — | 204 |
| `GET` | `/sets/{id}/tracks` | — | `[{position, ...track fields}]` ordered by position |
| `POST` | `/sets/{id}/tracks` | `{track_id}` | `{id, set_id, track_id, position}` |
| `DELETE` | `/sets/{id}/tracks/{track_id}` | — | 204 (removes entry, re-numbers remaining) |
| `PUT` | `/sets/{id}/tracks/order` | `{track_ids: [1,2,3]}` | 200 (full reorder) |

### New models — `models.py`

```python
class SetCreate(BaseModel):
    name: str

class SetUpdate(BaseModel):
    name: str

class SetTrackAdd(BaseModel):
    track_id: int

class SetTrackOrder(BaseModel):
    track_ids: list[int]
```

---

## Frontend

### New types — `api.ts`

```ts
export interface DJSet {
  id: number;
  name: string;
  created_at: number;
  track_count: number;
}

export interface SetTrack extends Track {
  position: number;
}
```

### New API calls — `api.ts`

```ts
getSets()
createSet(name: string)
renameSet(id: number, name: string)
deleteSet(id: number)
getSetTracks(id: number): SetTrack[]
addTrackToSet(setId: number, trackId: number)
removeTrackFromSet(setId: number, trackId: number)
reorderSetTracks(setId: number, trackIds: number[])
```

### New components

**`TrackCard.tsx`** — add `onLongPress?: () => void` prop
- `onTouchStart` starts a 500ms timer → fires `onLongPress`
- `onTouchEnd` / `onTouchMove` clears timer
- On desktop: right-click or hold mousedown 500ms

**`SetContextMenu.tsx`** — bottom sheet (mobile) shown on long-press
- Lists existing sets with "+" button on each
- "Nouveau set" input at bottom
- Closes on backdrop click

**`SetsPage.tsx`** — top-level sets list view
- Cards: set name, track count, created date
- "Nouveau set" button
- Tap → `SetDetailPage`

**`SetDetailPage.tsx`** — ordered track list for one set
- Back button → SetsPage
- Header actions: "Renommer" and "Supprimer le set"
- Each track row:
  - Position badge (e.g. `#1`)
  - TrackCard (read-only, no tag-click filtering)
  - **↑ button**: move track one position up (disabled on first track)
  - **↓ button**: move track one position down (disabled on last track)
  - **🗑 button**: remove from set (re-numbers remaining positions)
- If `track_id` is `null` (track deleted from grimoire): show a greyed-out "Morceau supprimé" placeholder at that position with:
  - ↑ and ↓ buttons still functional (can reorder the slot)
  - **🗑 button**: remove this deleted-track slot from the set entirely

### State changes — `App.tsx`

- Add `"sets"` and `"set-detail"` to `View` type
- `selectedSet: DJSet | null` state
- "Sets" button in header → `setView("sets")`
- `onLongPress` on each TrackCard in list view → open `SetContextMenu`

---

## Implementation Order

1. `database.py` — add sets + set_tracks tables to `init_db()`
2. `models.py` — add Set* models
3. `main.py` — add all 8 routes
4. `api.ts` — add types + API calls
5. `TrackCard.tsx` — add long-press support
6. `SetContextMenu.tsx` — new component
7. `SetsPage.tsx` — new component
8. `SetDetailPage.tsx` — new component
9. `App.tsx` — wire view routing + long-press handler

---

## Edge Cases

- **Deleted track in set**: `track_id` becomes `NULL` via `ON DELETE SET NULL`. The position slot is kept; `SetDetailPage` renders a greyed "Morceau supprimé" card. User can manually remove the slot with ×.
- **Re-numbering positions**: after any removal (track or slot), query remaining rows ordered by position and reassign 1..N to keep positions contiguous.
- **Empty set**: show "Aucun morceau" placeholder.
- **Set name collision**: allowed — no unique constraint, two sets can share a name.
- **`GET /sets/{id}/tracks` response**: each item includes `position` and either the full track fields or `{position, track_id: null, deleted: true}` for NULL slots.
