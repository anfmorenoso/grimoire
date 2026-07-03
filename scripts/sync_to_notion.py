"""
Push all local tracks without a Notion ID to Notion, then save the notion_id back.
Safe to re-run: skips tracks that already have a notion_id.
Progress is checkpointed to sync_progress.json so it resumes after interruption.

Usage:
    python scripts/sync_to_notion.py
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# Reuse backend helpers
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

import aiosqlite
from notion_sync import push_to_notion

DB_PATH = Path(__file__).parent.parent / "backend" / "grimoire.db"
CHECKPOINT = Path(__file__).parent / "sync_progress.json"
DELAY = 1.0  # seconds between Notion API calls — raise if you hit rate limits


def load_checkpoint() -> set[int]:
    if CHECKPOINT.exists():
        return set(json.loads(CHECKPOINT.read_text()))
    return set()


def save_checkpoint(done: set[int]):
    CHECKPOINT.write_text(json.dumps(sorted(done)))


async def fetch_pending(done: set[int]) -> list[dict]:
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        c = await db.execute(
            "SELECT * FROM tracks WHERE notion_id IS NULL ORDER BY id"
        )
        rows = await c.fetchall()

    result = []
    for row in rows:
        d = dict(row)
        if d["id"] in done:
            continue
        if d.get("sensations"):
            import json as _json
            try:
                d["sensations"] = _json.loads(d["sensations"])
            except Exception:
                d["sensations"] = []
        else:
            d["sensations"] = []
        result.append(d)
    return result


async def main():
    done = load_checkpoint()
    if done:
        print(f"Resuming — {len(done)} tracks already synced in previous run")

    pending = await fetch_pending(done)
    total = len(pending)

    if total == 0:
        print("Nothing to sync — all tracks already have a Notion ID.")
        CHECKPOINT.unlink(missing_ok=True)
        return

    print(f"{total} tracks to push to Notion (delay: {DELAY}s between calls)\n")

    async with aiosqlite.connect(str(DB_PATH)) as db:
        for i, track in enumerate(pending, 1):
            label = f"{track['artist']} — {track['name']}" if track["artist"] else track["name"]
            print(f"[{i:>4}/{total}] {label[:60]}", end=" ", flush=True)
            try:
                notion_id = await push_to_notion(track)
                await db.execute(
                    "UPDATE tracks SET notion_id = ? WHERE id = ?",
                    [notion_id, track["id"]],
                )
                await db.commit()
                done.add(track["id"])
                save_checkpoint(done)
                print("✓")
            except Exception as e:
                print(f"✗  {e}")

            if i < total:
                time.sleep(DELAY)

    CHECKPOINT.unlink(missing_ok=True)
    print(f"\n✓ Done — {len(done)} tracks synced to Notion")


if __name__ == "__main__":
    asyncio.run(main())
