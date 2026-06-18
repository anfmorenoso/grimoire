import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv(dotenv_path="../.env")

from database import init_db, get_db, row_to_dict
from models import TrackCreate, TrackUpdate, SpotifyLookupRequest
from notion_sync import sync_from_notion, push_to_notion, update_in_notion, preview_sync
from spotify import lookup_spotify_track
from vocabulary import FULL_WIKI
from llm import suggest_tags


DIST_DIR = Path(__file__).parent / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Auto-sync from Notion on startup so the DB is populated after cold starts
    if os.environ.get("NOTION_TOKEN") and os.environ.get("NOTION_DATABASE_ID"):
        db = await get_db()
        try:
            await sync_from_notion(db)
        except Exception:
            pass  # don't block startup if Notion is unreachable
        finally:
            await db.close()
    yield


app = FastAPI(title="Digg-IT", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Wiki ---

@app.get("/wiki")
async def get_wiki():
    return {
        category: [
            {"key": e.key, "label": e.label, "notion_value": e.notion_value, "description": e.description}
            for e in entries
        ]
        for category, entries in FULL_WIKI.items()
    }


# --- Sync ---

@app.get("/sync/preview")
async def sync_preview():
    db = await get_db()
    try:
        result = await preview_sync(db)
        return result
    finally:
        await db.close()


@app.post("/sync")
async def sync():
    db = await get_db()
    try:
        count = await sync_from_notion(db)
        return {"synced": count}
    finally:
        await db.close()


# --- Labels ---

@app.get("/labels")
async def list_labels():
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT DISTINCT label FROM tracks WHERE label IS NOT NULL AND label != '' ORDER BY label COLLATE NOCASE"
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]
    finally:
        await db.close()


# --- Tracks ---

@app.get("/tracks")
async def list_tracks(
    grain: List[str] = Query(default=[]),
    masse_basse: List[str] = Query(default=[]),
    role_set: List[str] = Query(default=[]),
    sensation: List[str] = Query(default=[]),
    label: List[str] = Query(default=[]),
    q: Optional[str] = None,
    sort: str = "id",
    dir: str = "desc",
):
    db = await get_db()
    try:
        conditions = []
        params: list = []

        if grain:
            conditions.append(f"grain IN ({','.join('?' * len(grain))})")
            params.extend(grain)
        if masse_basse:
            conditions.append(f"masse_basse IN ({','.join('?' * len(masse_basse))})")
            params.extend(masse_basse)
        if role_set:
            conditions.append(f"role_set IN ({','.join('?' * len(role_set))})")
            params.extend(role_set)
        if sensation:
            conditions.append(f"({' OR '.join('sensations LIKE ?' for _ in sensation)})")
            params.extend(f'%"{s}"%' for s in sensation)
        if label:
            conditions.append(f"label IN ({','.join('?' * len(label))})")
            params.extend(label)
        if q:
            conditions.append("(name LIKE ? OR artist LIKE ? OR label LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sort_expr = {"id": "COALESCE(created_at, id)", "name": "name COLLATE NOCASE", "artist": "artist COLLATE NOCASE"}.get(sort, "COALESCE(created_at, id)")
        sort_dir = "ASC" if dir.lower() == "asc" else "DESC"
        cursor = await db.execute(
            f"SELECT * FROM tracks {where} ORDER BY {sort_expr} {sort_dir}", params
        )
        rows = await cursor.fetchall()
        return [row_to_dict(r) for r in rows]
    finally:
        await db.close()


@app.get("/tracks/{track_id}")
async def get_track(track_id: int):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM tracks WHERE id = ?", [track_id])
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Track not found")
        return row_to_dict(row)
    finally:
        await db.close()


@app.post("/tracks", status_code=201)
async def create_track(body: TrackCreate):
    data = body.model_dump()
    notion_id = await push_to_notion(data)

    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO tracks (notion_id, name, artist, album, label, year, bpm, key,
               grain, sensations, masse_basse, role_set, url, downloaded, notes, layering)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                notion_id, data["name"], data["artist"], data["album"],
                data["label"], data.get("year"), data["bpm"], data["key"], data["grain"],
                json.dumps(data["sensations"]), data["masse_basse"],
                data["role_set"], data["url"], int(data["downloaded"]), data["notes"],
                data.get("layering"),
            ),
        )
        await db.commit()
        row_cursor = await db.execute("SELECT * FROM tracks WHERE id = ?", [cursor.lastrowid])
        row = await row_cursor.fetchone()
        return row_to_dict(row)
    finally:
        await db.close()


@app.patch("/tracks/{track_id}")
async def update_track(track_id: int, body: TrackUpdate):
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM tracks WHERE id = ?", [track_id])
        existing = await cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Track not found")

        data = body.model_dump(exclude_none=True)

        set_clauses = []
        params = []
        for field, value in data.items():
            set_clauses.append(f"{field} = ?")
            params.append(json.dumps(value) if field == "sensations" else value)

        if set_clauses:
            params.append(track_id)
            await db.execute(
                f"UPDATE tracks SET {', '.join(set_clauses)} WHERE id = ?", params
            )
            await db.commit()

        notion_id = existing["notion_id"]
        if notion_id and data:
            await update_in_notion(notion_id, data)

        row_cursor = await db.execute("SELECT * FROM tracks WHERE id = ?", [track_id])
        row = await row_cursor.fetchone()
        return row_to_dict(row)
    finally:
        await db.close()


@app.delete("/tracks/{track_id}", status_code=204)
async def delete_track(track_id: int):
    db = await get_db()
    try:
        await db.execute("DELETE FROM tracks WHERE id = ?", [track_id])
        await db.commit()
    finally:
        await db.close()


# --- Spotify lookup ---

@app.post("/spotify/lookup")
async def spotify_lookup(body: SpotifyLookupRequest):
    meta = await lookup_spotify_track(body.url)
    if not meta:
        raise HTTPException(status_code=422, detail="Could not extract track from URL")
    return meta


# --- LLM tag suggestion ---

from pydantic import BaseModel as _BaseModel

class SuggestRequest(_BaseModel):
    name: str
    artist: str
    label: Optional[str] = None
    bpm: Optional[float] = None
    key: Optional[str] = None


@app.post("/suggest")
async def suggest(body: SuggestRequest):
    try:
        result = await suggest_tags(body.name, body.artist, body.label, body.bpm, body.key)
        return result
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")


# --- SPA static file serving (must be last) ---

if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        file = DIST_DIR / full_path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(DIST_DIR / "index.html")
