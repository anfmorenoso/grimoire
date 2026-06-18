# Plan — feature/delete-track

**Goal:** Delete a track from the edit view with a proper inline confirmation modal. Deletion removes from SQLite immediately. The next Notion sync preview will detect it as an orphan and offer to archive it in Notion.

---

## Context

- `DELETE /tracks/{id}` already exists in `backend/main.py`.
- `deleteTrack()` is already imported in `App.tsx`.
- `App.tsx` already has a `handleDelete` but it uses `window.confirm` (ugly on mobile) and a header button (not in TrackForm).
- `preview_sync` currently only returns `{new, updated}` — it doesn't detect local deletions.
- Notion API supports soft-delete via `pages.update(page_id=..., archived=True)`.

---

## Implementation

### 1. Replace `window.confirm` delete with inline modal in TrackForm

Remove the "Supprimer" button from the `App.tsx` header. Add it to the bottom action bar of `TrackForm` (edit mode only):

```
[🗑 Supprimer]              [Annuler] [Sauvegarder]
```

On click, show an inline dark overlay modal:

```
┌─────────────────────────────────────┐
│  Supprimer "Track Name" ?           │
│                                     │
│  Le morceau sera retiré de Grimoire.│
│  Il restera dans Notion jusqu'au    │
│  prochain sync.                     │
│                                     │
│  [Annuler]          [Supprimer] 🔴  │
└─────────────────────────────────────┘
```

Add `onDelete?: () => Promise<void>` prop to TrackForm. `App.tsx` passes it only in edit mode.

### 2. Extend sync preview to detect Notion orphans

In `notion_sync.py → preview_sync()`:

- After iterating Notion pages, query Grimoire for `notion_id`s that exist in Notion but NOT in local SQLite → `to_delete` list.

```python
notion_ids_in_notion = {row["notion_id"] for row in parsed_pages}
c = await db.execute("SELECT notion_id, name, artist FROM tracks WHERE notion_id IS NOT NULL")
local_rows = await c.fetchall()
local_notion_ids = {r[0] for r in local_rows}
orphans = notion_ids_in_notion - local_notion_ids
```

Returns `{new: [...], updated: [...], to_delete: [{name, artist, notion_id}]}`.

### 3. Archive orphans in Notion during sync confirm

Add `archive_in_notion(notion_id: str)` to `notion_sync.py`:

```python
async def archive_in_notion(notion_id: str):
    notion = _get_client()
    try:
        await notion.pages.update(page_id=notion_id, archived=True)
    finally:
        await notion.aclose()
```

In `POST /sync` (`main.py`): after `sync_from_notion`, re-run the orphan detection and archive each one.

### 4. Show to_delete in sync preview modal (frontend)

Update `SyncPreview` interface in `api.ts`:
```ts
to_delete: { name: string; artist: string }[];
```

In `App.tsx` sync preview modal, add a red section "X à supprimer de Notion" below updated.

---

## Files to touch

| File | Change |
|------|--------|
| `backend/notion_sync.py` | `preview_sync` adds `to_delete`; add `archive_in_notion` |
| `backend/main.py` | `POST /sync` archives orphans after pull |
| `frontend/src/api.ts` | `SyncPreview.to_delete` field |
| `frontend/src/App.tsx` | Remove header delete button; pass `onDelete` to TrackForm; show `to_delete` in preview modal |
| `frontend/src/components/TrackForm.tsx` | Delete button + inline confirmation modal + `onDelete` prop |

---

## Important notes

- `window.confirm` is removed entirely — the inline modal replaces it.
- Notion archiving is soft-delete (page is hidden, not destroyed). Reversible from Notion UI.
- Only tracks with a `notion_id` are archived — tracks created locally only are just deleted from SQLite.
- The sync confirm button already exists — no new button needed on frontend for the Notion deletion.
