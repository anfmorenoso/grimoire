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
    notes       TEXT,
    layering    TEXT,
    synced_at   TEXT,
    created_at  INTEGER DEFAULT (unixepoch())
)
"""


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TRACKS_TABLE)
        for col_sql in [
            "ALTER TABLE tracks ADD COLUMN layering TEXT",
            "ALTER TABLE tracks ADD COLUMN year INTEGER",
            "ALTER TABLE tracks ADD COLUMN created_at INTEGER DEFAULT (unixepoch())",
        ]:
            try:
                await db.execute(col_sql)
            except Exception:
                pass  # column already exists
        await db.commit()


def row_to_dict(row: aiosqlite.Row) -> dict:
    d = dict(row)
    if d.get("sensations"):
        d["sensations"] = json.loads(d["sensations"])
    d["downloaded"] = bool(d.get("downloaded", 0))
    return d
