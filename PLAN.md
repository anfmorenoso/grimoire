# Plan — feature/hq-download

**Goal:** Add a "high quality download" boolean field to each track, displayed as a checkbox with a double-check emoji (✅ or ✔️✔️). Indicates the track has been obtained in lossless/high-bitrate format.

---

## Context

The existing `downloaded` boolean already tracks whether a track is in the library at all. `hq_download` is a separate concern — the track is downloaded AND in a high quality format (FLAC, WAV, 320kbps+).

This field is local-only (SQLite). It does not need to sync to Notion (Notion doesn't have this field, and it's a technical/workflow detail, not a musical attribute).

---

## Implementation

### 1. Backend — `database.py`

Add `hq_download INTEGER DEFAULT 0` to the `CREATE TABLE` statement and to the `init_db()` migration block:

```python
"ALTER TABLE tracks ADD COLUMN hq_download INTEGER DEFAULT 0",
```

### 2. Backend — `models.py`

Add to `TrackCreate`, `TrackUpdate`, and the base `Track` model:

```python
hq_download: bool = False
```

### 3. Backend — `main.py`

In `create_track` and the INSERT query, add `hq_download` to the column list and values.
In `row_to_dict` (or `database.py`), cast it to `bool` like `downloaded`.

> `update_track` already handles arbitrary fields via `body.model_dump(exclude_none=True)` — no change needed there as long as it's in the model.

### 4. Frontend — `api.ts`

Add `hq_download: boolean` to the `Track` interface.

### 5. Frontend — `TrackForm.tsx`

Next to the existing "Downloaded" checkbox, add:

```
☑ Downloaded    ✅ HQ Download
```

Both checkboxes on the same row. Label: `✅ HQ` (keep it short).

### 6. Frontend — `TrackCard.tsx`

In the track card footer where `downloaded` is shown, add the HQ indicator:

- If `downloaded && hq_download`: show `✅✅` or `✅ HQ`
- If `downloaded && !hq_download`: show `✅`
- If `!downloaded`: show nothing (or `—`)

---

## Files to touch

| File | Change |
|------|--------|
| `backend/database.py` | Add column to schema + migration |
| `backend/models.py` | Add `hq_download: bool` to all models |
| `backend/main.py` | Include in INSERT + `row_to_dict` bool cast |
| `frontend/src/api.ts` | Add to `Track` interface |
| `frontend/src/components/TrackForm.tsx` | Add HQ checkbox next to Downloaded |
| `frontend/src/components/TrackCard.tsx` | Show HQ indicator in card |

---

## Notes

- `hq_download` is intentionally not pushed to Notion — keep `update_in_notion()` and `push_to_notion()` unchanged
- Default is `false` — existing tracks are unaffected
- The migration in `init_db()` is safe to run on an existing DB (wrapped in try/except already)
