# Plan — feature/delete-track

**Goal:** Allow deleting a track from the edit view, with a two-step confirmation to prevent accidents. Deletion removes from SQLite only — the track stays in Notion.

---

## Context

`DELETE /tracks/{id}` already exists in `backend/main.py` and `deleteTrack()` is already imported in `App.tsx`. This is a pure frontend task.

The edit view is rendered by `TrackForm.tsx` when `mode="edit"`. `App.tsx` handles the `onDelete` callback pattern for other actions already.

---

## Implementation

### 1. Add delete button to `TrackForm.tsx`

In the bottom action bar of the edit form, add a delete button (red, left-aligned, away from Save):

```
[🗑 Delete]                    [Cancel] [Save]
```

### 2. Confirmation modal

On click, show an inline confirmation (not `window.confirm` — ugly on mobile):

```
┌─────────────────────────────────┐
│  Delete "Track Name"?           │
│                                 │
│  This removes it from Grimoire  │
│  but keeps it in Notion.        │
│                                 │
│  [Cancel]        [Delete]  🔴   │
└─────────────────────────────────┘
```

- Modal is a dark overlay card, centered on screen
- "Delete" button is red and requires a deliberate tap (not close to Cancel)
- `Escape` key and tap-outside dismiss the modal

### 3. Wire up in `App.tsx`

`TrackForm` already receives `onCancel` and `onSave`. Add `onDelete?: (id: number) => void`.

In `App.tsx`:

```ts
const handleDelete = async (id: number) => {
  await deleteTrack(id);
  setView("list");
  loadTracks();
};
```

Pass `onDelete={handleDelete}` to `<TrackForm>` when `view === "edit"`.

### 4. Loading state

While the DELETE request is in flight, disable both buttons and show a spinner on the Delete button to prevent double-submit.

---

## Files to touch

| File | Change |
|------|--------|
| `frontend/src/components/TrackForm.tsx` | Delete button + confirmation modal + `onDelete` prop |
| `frontend/src/App.tsx` | `handleDelete` handler, pass `onDelete` to TrackForm |

---

## Important notes

- Only show the delete button in `mode="edit"`, never in `mode="add"`
- Clearly state in the confirmation that Notion is NOT affected (user may panic otherwise)
- No undo — deletion is final on the SQLite side
