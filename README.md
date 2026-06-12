---
title: Grimoire DJ
emoji: 🎛️
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Grimoire DJ

Self-hosted PWA to manage and analyze your DJ music library. Local SQLite cache synced to Notion, with Spotify metadata lookup and AI-powered tag suggestions via Gemini.

## Architecture

### Backend (FastAPI)
- **Database**: aiosqlite (local SQLite, syncs bidirectionally with Notion)
- **External APIs**: 
  - Notion (sync source of truth, stores all metadata)
  - Spotify (track metadata + BPM/key via Audio Features)
  - Gemini 2.5 Flash (LLM for intelligent tag analysis)
- **Key modules**:
  - `database.py` — SQLite schema + row_to_dict serialization
  - `models.py` — Pydantic schemas (Track, TrackCreate, TrackUpdate)
  - `notion_sync.py` — bidirectional sync (Notion ↔ SQLite)
  - `spotify.py` — track lookup + audio features (tempo, key → Camelot)
  - `llm.py` — AI tag suggestions with per-tag reasoning
  - `vocabulary.py` — DJ vocabulary wiki (Grain, Sensations, Masse Basse, Role Set)
  - `main.py` — FastAPI routes

### Frontend (React + Vite + Tailwind)
- **Mobile-first dark theme PWA** (installable on iOS/Android)
- **Components**:
  - `TrackForm.tsx` — create/edit tracks, Spotify lookup, AI analysis UI
  - `TrackCard.tsx` — compact track display with tags
  - `TagGroup.tsx` — multi-select tag interface with AI suggestions
  - `App.tsx` — main layout (list/add/edit views)
- **State**: React hooks + axios
- **API calls**: All to `/api` routes (dynamic baseURL using `window.location.hostname`)

### Vocabulary System
Tags live in code (not Notion) for better LLM reasoning:
- **Grain** (texture): aquatique, poussiéreux, texture, minéral, saturé, épuré
- **Sensations** (vibe): hypnotique, mystérieux, rituel, organique, acide, amorphe, cinématique, nerveux
- **Masse Basse** (kick weight): lourd, squelette, léger
- **Role Set** (set position): amorce, construction, peak_time, planage

Maps: internal short keys ↔ Notion's full select names (e.g., `"aquatique"` ↔ `"Aquatique (Liquide / Profond)"`)

## API Routes

### Metadata
- `GET /wiki` — vocabulary + descriptions (for TagGroup rendering)

### Sync
- `POST /sync` — pull all tracks from Notion → upsert SQLite. Returns `{ synced: N }`

### Tracks
- `GET /tracks` — list all, with optional filters: `?grain=aquatique&role_set=peak_time&q=artist_name`
- `GET /tracks/{id}` — single track
- `POST /tracks` — create new (pushes to Notion, inserts SQLite, returns full Track)
- `PATCH /tracks/{id}` — update tags/notes (updates both SQLite + Notion)
- `DELETE /tracks/{id}` — delete from SQLite only (stays in Notion)

### Spotify
- `POST /spotify/lookup` — extract track from Spotify URL, fetch metadata + BPM + key. Returns `{ name, artist, label?, bpm?, key?, url, image_url? }`

### AI Analysis
- `POST /suggest` — analyze track. Input: `{ name, artist, label?, bpm?, key? }`. Returns `{ grain, grain_reasoning, sensations, sensations_reasoning, ..., bpm_estimate?, label_suggestions?, layering_note, reasoning }`

## Setup

### Backend
```bash
cd grimoire/backend
python3.9 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env
# Fill .env with NOTION_TOKEN, NOTION_DATABASE_ID, SPOTIFY_CLIENT_ID/SECRET, GEMINI_API_KEY
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd grimoire/frontend
npm install
npm run dev -- --host
# Visit http://192.168.x.x:5173 from phone
```

### Notion Setup
1. Create an internal integration at [notion.com/my-integrations](https://www.notion.com/my-integrations)
2. Get the token (starts with `ntn_`)
3. Share your music database with the integration
4. Copy database ID from the URL (`?v=...` is the view ID, the long part before `?` is the database ID)
5. Add a "Layering" rich text property to your Notion database (optional, for local layering notes)

## Data Flow

1. **Notion → SQLite**: `/sync` pulls pages, calls `notion_page_to_dict()`, upserts with `ON CONFLICT`
2. **Local Edits**: `/tracks` PATCH → SQLite + `update_in_notion()` (pushes changes back)
3. **New Tracks**: Form submit → POST `/tracks` → Notion page creation + SQLite insert
4. **Spotify Lookup**: User pastes URL → `lookup_spotify_track()` → extracts metadata + BPM + key
5. **AI Analysis**: User clicks "Analyser" → sends track info + BPM/key to Gemini → returns tags + reasoning
6. **Layering Auto-Fill**: If LLM returns `bpm_estimate` or `label_suggestions`, form fields auto-populate

## LLM Analysis Modes

- **Auto-fill** (empty form): AI tags auto-apply to form
- **Compare** (form has existing tags): AI suggestions appear as badge-marked pills; user can click "Appliquer" to accept

Reasoning shown inline under each tag category for transparency.

## Future: Cloud Migration

See `FUTURE.md` for serverless/container deployment strategy.
