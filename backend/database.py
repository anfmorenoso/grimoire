import json
import os
from pathlib import Path
import aiosqlite

DB_PATH = Path(os.environ.get("DB_PATH", str(Path(__file__).parent / "grimoire.db")))

CREATE_TRACKS_TABLE = """
CREATE TABLE IF NOT EXISTS tracks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    notion_id   TEXT UNIQUE,
    name        TEXT NOT NULL,
    artist      TEXT NOT NULL,
    album       TEXT,
    label       TEXT,
    year        INTEGER,
    bpm         INTEGER,
    key         TEXT,
    grain       TEXT,
    sensations  TEXT DEFAULT '[]',
    masse_basse TEXT,
    role_set    TEXT,
    url         TEXT,
    downloaded  INTEGER DEFAULT 0,
    hq_download INTEGER DEFAULT 0,
    notes       TEXT,
    layering    TEXT,
    synced_at        TEXT,
    notion_updated_at TEXT
)
"""

CREATE_SETS_TABLE = """
CREATE TABLE IF NOT EXISTS sets (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    notion_id  TEXT UNIQUE,
    name       TEXT NOT NULL,
    created_at INTEGER DEFAULT (unixepoch())
)
"""

CREATE_SET_TRACKS_TABLE = """
CREATE TABLE IF NOT EXISTS set_tracks (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    notion_id TEXT UNIQUE,
    set_id    INTEGER NOT NULL REFERENCES sets(id) ON DELETE CASCADE,
    track_id  INTEGER REFERENCES tracks(id) ON DELETE SET NULL,
    position  INTEGER NOT NULL
)
"""


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    return db


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(CREATE_TRACKS_TABLE)
        await db.execute(CREATE_SETS_TABLE)
        await db.execute(CREATE_SET_TRACKS_TABLE)
        for col_sql in [
            "ALTER TABLE tracks ADD COLUMN layering TEXT",
            "ALTER TABLE tracks ADD COLUMN year INTEGER",
            "ALTER TABLE tracks ADD COLUMN hq_download INTEGER DEFAULT 0",
            "ALTER TABLE tracks ADD COLUMN created_at INTEGER",
            "ALTER TABLE tracks ADD COLUMN notion_updated_at TEXT",
            "ALTER TABLE sets ADD COLUMN notion_id TEXT",
            "ALTER TABLE set_tracks ADD COLUMN notion_id TEXT",
        ]:
            try:
                await db.execute(col_sql)
            except Exception:
                pass  # column already exists
        # Normalize sensations JSON to unescaped Unicode so LIKE filters work.
        # json.dumps previously used ASCII escapes (e.g. é) which broke
        # accented-key filters like cinématique, mystérieux, etc.
        cursor = await db.execute("SELECT id, sensations FROM tracks WHERE sensations IS NOT NULL")
        rows = await cursor.fetchall()
        for row in rows:
            try:
                normalized = json.dumps(json.loads(row[1]), ensure_ascii=False)
                if normalized != row[1]:
                    await db.execute("UPDATE tracks SET sensations = ? WHERE id = ?", [normalized, row[0]])
            except Exception:
                pass
        await db.commit()


def row_to_dict(row: aiosqlite.Row) -> dict:
    d = dict(row)
    if d.get("sensations"):
        d["sensations"] = json.loads(d["sensations"])
    d["downloaded"] = bool(d.get("downloaded", 0))
    d["hq_download"] = bool(d.get("hq_download", 0))
    return d
