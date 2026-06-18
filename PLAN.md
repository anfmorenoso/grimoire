# Plan — feature/duplicate-detection

**Goal:** When adding a new track, if a track with a similar name already exists in the DB (even with a different Spotify link), warn the user and offer to open the existing one instead of creating a duplicate.

---

## Context

The add flow lives in `TrackForm.tsx`. After a Spotify lookup (or manual entry), the form has `name` and `artist`. The existing `GET /tracks?q=...` endpoint does a `LIKE` search on name + artist — we can use it for the similarity check.

The check should trigger in two moments:
1. After a successful Spotify lookup (name + artist are populated automatically)
2. On form submit, as a final guard

---

## Implementation

### 1. Backend — no changes needed

`GET /tracks?q=<name>` already searches `name LIKE %q%`. This is sufficient for fuzzy matching at this scale.

### 2. Frontend — `TrackForm.tsx`

#### A. `checkDuplicates(name, artist)` helper

```ts
async function checkDuplicates(name: string, artist: string): Promise<Track[]> {
  const results = await getTracks({ q: name });
  // filter to same artist (case-insensitive) or close enough
  return results.filter(
    (t) => t.artist.toLowerCase() === artist.toLowerCase()
  );
}
```

#### B. Trigger after Spotify lookup

In the `handleSpotifyLookup` callback (after the form fields are populated), call `checkDuplicates`. If matches found, set a `duplicates` state array.

#### C. Duplicate warning UI

If `duplicates.length > 0`, render a banner above the form:

```
⚠️ A track with this name already exists:
  [Artist — Track name]  →  [Open existing]
```

- "Open existing" calls the `onEdit(track)` callback (switches to edit view for that track)
- User can dismiss the banner to proceed with adding anyway

#### D. Submit guard

On form submit, if `duplicates.length > 0` and the user hasn't dismissed, show a confirmation:
```
"A similar track already exists. Add anyway?"  [Cancel] [Add anyway]
```

### 3. State in `TrackForm.tsx`

```ts
const [duplicates, setDuplicates] = useState<Track[]>([]);
const [duplicatesDismissed, setDuplicatesDismissed] = useState(false);
```

---

## Files to touch

| File | Change |
|------|--------|
| `frontend/src/components/TrackForm.tsx` | Add duplicate check after Spotify lookup + warning UI + submit guard |
| `frontend/src/App.tsx` | Pass `onOpenTrack` callback to `TrackForm` so "Open existing" works |

---

## Edge cases

- Same track on two different labels/pressings → user should be able to add it anyway (dismiss banner)
- Name match but different artist → not a duplicate, don't show warning
- Check fires only in "add" mode, not "edit" mode
