# Grimoire DJ — Status & Next Steps

## Project Overview

**Grimoire DJ** is a mobile-first DJ track management app.  
Stack: FastAPI + aiosqlite + Gemini 2.5 Flash + Notion + Spotify / React + TypeScript + Vite + Tailwind.

---

## Current State

### Backend (complete)
- Track CRUD — SQLite via aiosqlite
- Notion sync — bidirectional pull/push/update
- Spotify lookup — URL parsing, BPM, key (Camelot), label extraction
- Gemini LLM tag suggestion — grain, sensations, masse_basse, role_set, layering_note
- Unit tests — 185+ cases across spotify, llm, notion_sync, database, models

### Frontend (complete)
- Track list with live search (title, artist, label)
- Add / Edit / Delete track flow
- Sync button (Notion pull)
- TrackCard, TrackForm, TagPill, TagGroup components
- Mobile-first dark UI

---

## Dev Environment — Current State

WSL (Ubuntu) setup **complete**.

| Task | Status |
|------|--------|
| uv installed in WSL (`~/.local/bin`) | done |
| uv on PATH (`.zshrc`) | done |
| Python 3.12 via uv | done (3.12.13) |
| venv created at `backend/.venv` | done |
| dependencies installed | done |
| zsh + oh-my-zsh | done |
| `.zshrc` aliases | done (fixed paths) |
| `code .` from WSL | done — Remote-WSL connected |
| Port proxy Windows → WSL | done (8000 + 5173 → 172.27.32.208) |
| Tests passing | **64/64 ✓** |

---

## Immediate Next Steps

### Run the app

```bash
grimoire-back    # FastAPI on :8000
grimoire-front   # Vite on :5173
grimoire-test    # pytest (64 tests)
```

---

## Port Proxy Reference

The WSL IP changes on restart. Re-run from PowerShell (admin) when needed:

```powershell
$wslIp = wsl hostname -I | ForEach-Object { $_.Trim().Split(" ")[0] }
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0
netsh interface portproxy delete v4tov4 listenport=5173 listenaddress=0.0.0.0
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIp
netsh interface portproxy add v4tov4 listenport=5173 listenaddress=0.0.0.0 connectport=5173 connectaddress=$wslIp
```

Phone access: `http://192.168.1.110:5173`

---

## Feature Backlog

- **Filter bar** — filter tracks by grain, masse_basse, role_set, sensation from the list view
- **Layering view** — display layering_note prominently on track detail
- **Offline mode** — queue writes and replay when API is back
- **Integration tests** — test FastAPI routes end-to-end (currently only unit tests)
