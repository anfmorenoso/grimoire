import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv(dotenv_path="../.env")

from database import init_db, get_db, row_to_dict
from models import TrackCreate, TrackUpdate, SpotifyLookupRequest, SetCreate, SetUpdate, SetTrackAdd, SetTrackOrder
from notion_sync import (
    sync_from_notion, push_to_notion, update_in_notion, preview_sync, archive_in_notion,
    push_set_to_notion, update_set_in_notion, archive_set_in_notion,
    push_set_track_to_notion, update_set_track_position_in_notion, archive_set_track_in_notion,
    sync_sets_from_notion,
)
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
            await sync_sets_from_notion(db)
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


HIDDEN_COLLECTIONS: frozenset[str] = frozenset({
    "All",
    "Penichemise en lin",
    "Set 2",
    "Test 1",
    "Something else",
    "VERY ACID",
    "Kinda Playful",
})


# --- Collections ---

@app.get("/collections")
async def list_collections():
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT collection, COUNT(*) count FROM tracks WHERE collection IS NOT NULL GROUP BY collection ORDER BY count DESC"
        )
        rows = await cursor.fetchall()
        return [
            {"collection": row[0], "count": row[1], "hidden": row[0] in HIDDEN_COLLECTIONS}
            for row in rows
        ]
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
    collection: List[str] = Query(default=[]),
    q: Optional[str] = None,
    sort: str = "id",
    dir: str = "desc",
):
    db = await get_db()
    try:
        conditions = []
        params: list = []

        if collection:
            conditions.append(f"collection IN ({','.join('?' * len(collection))})")
            params.extend(collection)
        else:
            placeholders = ",".join("?" * len(HIDDEN_COLLECTIONS))
            conditions.append(f"(collection IS NULL OR collection NOT IN ({placeholders}))")
            params.extend(HIDDEN_COLLECTIONS)
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
        sort_expr = {"id": "notion_updated_at", "name": "name COLLATE NOCASE", "artist": "artist COLLATE NOCASE"}.get(sort, "notion_updated_at")
        sort_dir = "ASC" if dir.lower() == "asc" else "DESC"
        cursor = await db.execute(
            f"SELECT * FROM tracks {where} ORDER BY {sort_expr} {sort_dir}", params
        )
        rows = await cursor.fetchall()
        return [row_to_dict(r) for r in rows]
    finally:
        await db.close()


@app.get("/tracks/stats")
async def track_stats():
    db = await get_db()
    try:
        stats: dict = {}
        for col in ("grain", "masse_basse", "role_set"):
            c = await db.execute(
                f"SELECT {col}, COUNT(*) FROM tracks WHERE {col} IS NOT NULL GROUP BY {col}"
            )
            stats[col] = {row[0]: row[1] for row in await c.fetchall()}
        c = await db.execute(
            "SELECT sensations FROM tracks WHERE sensations IS NOT NULL AND sensations != '[]'"
        )
        counts: dict = {}
        for row in await c.fetchall():
            try:
                for s in json.loads(row[0]):
                    counts[s] = counts.get(s, 0) + 1
            except Exception:
                pass
        stats["sensations"] = counts
        return stats
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
               grain, sensations, masse_basse, role_set, url, downloaded, hq_download, notes, layering,
               notion_updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                notion_id, data["name"], data["artist"], data["album"],
                data["label"], data.get("year"), data["bpm"], data["key"], data["grain"],
                json.dumps(data["sensations"], ensure_ascii=False), data["masse_basse"],
                data["role_set"], data["url"], int(data["downloaded"]),
                int(data.get("hq_download", False)), data["notes"], data.get("layering"),
                datetime.now(timezone.utc).isoformat(),
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
            params.append(json.dumps(value, ensure_ascii=False) if field == "sensations" else value)

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
        c = await db.execute("SELECT notion_id FROM tracks WHERE id = ?", [track_id])
        row = await c.fetchone()
        notion_id = row["notion_id"] if row else None

        await db.execute("DELETE FROM tracks WHERE id = ?", [track_id])
        await db.commit()

        if notion_id:
            try:
                await archive_in_notion(notion_id)
            except Exception:
                pass
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


# --- Sets ---

@app.get("/sets")
async def list_sets():
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT s.id, s.name, s.created_at, COUNT(st.id) as track_count
               FROM sets s LEFT JOIN set_tracks st ON s.id = st.set_id
               GROUP BY s.id ORDER BY s.created_at DESC"""
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


@app.post("/sets", status_code=201)
async def create_set(body: SetCreate):
    notion_id = await push_set_to_notion(body.name)
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO sets (notion_id, name) VALUES (?, ?)", [notion_id, body.name]
        )
        await db.commit()
        c = await db.execute("SELECT * FROM sets WHERE id = ?", [cursor.lastrowid])
        return dict(await c.fetchone())
    finally:
        await db.close()


@app.patch("/sets/{set_id}")
async def rename_set(set_id: int, body: SetUpdate):
    db = await get_db()
    try:
        c = await db.execute("SELECT notion_id FROM sets WHERE id = ?", [set_id])
        row = await c.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Set not found")
        await db.execute("UPDATE sets SET name = ? WHERE id = ?", [body.name, set_id])
        await db.commit()
        if row["notion_id"]:
            await update_set_in_notion(row["notion_id"], body.name)
        c = await db.execute("SELECT * FROM sets WHERE id = ?", [set_id])
        return dict(await c.fetchone())
    finally:
        await db.close()


@app.delete("/sets/{set_id}", status_code=204)
async def delete_set(set_id: int):
    db = await get_db()
    try:
        c = await db.execute("SELECT notion_id FROM sets WHERE id = ?", [set_id])
        set_row = await c.fetchone()
        # Archive all set_track pages in Notion before deleting
        c = await db.execute(
            "SELECT notion_id FROM set_tracks WHERE set_id = ? AND notion_id IS NOT NULL", [set_id]
        )
        for row in await c.fetchall():
            await archive_set_track_in_notion(row["notion_id"])
        await db.execute("DELETE FROM sets WHERE id = ?", [set_id])
        await db.commit()
        if set_row and set_row["notion_id"]:
            await archive_set_in_notion(set_row["notion_id"])
    finally:
        await db.close()


@app.get("/sets/{set_id}/tracks")
async def get_set_tracks(set_id: int):
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT st.id as set_track_id, st.position, st.track_id,
                      t.id, t.notion_id, t.name, t.artist, t.album, t.label, t.year,
                      t.bpm, t.key, t.grain, t.sensations, t.masse_basse, t.role_set,
                      t.url, t.downloaded, t.hq_download, t.notes, t.layering
               FROM set_tracks st
               LEFT JOIN tracks t ON st.track_id = t.id
               WHERE st.set_id = ?
               ORDER BY st.position""",
            [set_id],
        )
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            if d["track_id"] is None:
                result.append({"set_track_id": d["set_track_id"], "position": d["position"], "deleted": True})
            else:
                d["sensations"] = json.loads(d["sensations"]) if d.get("sensations") else []
                d["downloaded"] = bool(d.get("downloaded", 0))
                d["hq_download"] = bool(d.get("hq_download", 0))
                result.append(d)
        return result
    finally:
        await db.close()


@app.post("/sets/{set_id}/tracks", status_code=201)
async def add_track_to_set(set_id: int, body: SetTrackAdd):
    db = await get_db()
    try:
        if not body.force:
            c = await db.execute(
                "SELECT id FROM set_tracks WHERE set_id = ? AND track_id = ?",
                [set_id, body.track_id],
            )
            if await c.fetchone():
                raise HTTPException(status_code=409, detail="already_in_set")
        c = await db.execute(
            "SELECT COALESCE(MAX(position), 0) + 1 FROM set_tracks WHERE set_id = ?", [set_id]
        )
        next_pos = (await c.fetchone())[0]
        # Fetch set and track notion_ids for Notion push
        c = await db.execute("SELECT notion_id FROM sets WHERE id = ?", [set_id])
        set_row = await c.fetchone()
        c = await db.execute("SELECT notion_id, name FROM tracks WHERE id = ?", [body.track_id])
        track_row = await c.fetchone()
        st_notion_id = None
        if set_row and set_row["notion_id"] and track_row:
            st_notion_id = await push_set_track_to_notion(
                set_row["notion_id"],
                track_row["notion_id"],
                next_pos,
                track_row["name"],
            )
        cursor = await db.execute(
            "INSERT INTO set_tracks (notion_id, set_id, track_id, position) VALUES (?, ?, ?, ?)",
            [st_notion_id, set_id, body.track_id, next_pos],
        )
        await db.commit()
        return {"id": cursor.lastrowid, "set_id": set_id, "track_id": body.track_id, "position": next_pos}
    finally:
        await db.close()


@app.put("/sets/{set_id}/tracks/order")
async def reorder_set_tracks(set_id: int, body: SetTrackOrder):
    db = await get_db()
    try:
        for i, set_track_id in enumerate(body.ordered_ids, 1):
            await db.execute(
                "UPDATE set_tracks SET position = ? WHERE id = ? AND set_id = ?",
                [i, set_track_id, set_id],
            )
        await db.commit()
        # Push position updates to Notion
        c = await db.execute(
            "SELECT id, notion_id, position FROM set_tracks WHERE set_id = ? AND notion_id IS NOT NULL",
            [set_id],
        )
        for row in await c.fetchall():
            await update_set_track_position_in_notion(row["notion_id"], row["position"])
        return {"ok": True}
    finally:
        await db.close()


@app.delete("/sets/{set_id}/tracks/{set_track_id}", status_code=204)
async def remove_from_set(set_id: int, set_track_id: int):
    db = await get_db()
    try:
        c = await db.execute(
            "SELECT notion_id FROM set_tracks WHERE id = ? AND set_id = ?", [set_track_id, set_id]
        )
        st_row = await c.fetchone()
        await db.execute(
            "DELETE FROM set_tracks WHERE id = ? AND set_id = ?", [set_track_id, set_id]
        )
        c = await db.execute(
            "SELECT id FROM set_tracks WHERE set_id = ? ORDER BY position", [set_id]
        )
        rows = await c.fetchall()
        for i, row in enumerate(rows, 1):
            await db.execute("UPDATE set_tracks SET position = ? WHERE id = ?", [i, row["id"]])
        await db.commit()
        if st_row and st_row["notion_id"]:
            await archive_set_track_in_notion(st_row["notion_id"])
    finally:
        await db.close()


# --- SPA static file serving (must be last) ---

if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        file = DIST_DIR / full_path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(DIST_DIR / "index.html")
