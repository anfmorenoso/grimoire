"""
Push local DB changes to existing Notion pages (updates, not creates).
Reads all tracks that already have a notion_id and PATCHes each one.

Safe to re-run: checkpoint skips already-synced IDs.
Progress checkpointed to scripts/sync_updates_progress.json.

Usage:
    python scripts/sync_updates_to_notion.py
"""

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

import aiosqlite
from notion_sync import update_in_notion

DB_PATH   = Path(__file__).parent.parent / "backend" / "grimoire.db"
CHECKPOINT = Path(__file__).parent / "sync_updates_progress.json"
DELAY     = 0.4   # Notion rate limit: 3 req/s


def load_checkpoint() -> set[int]:
    if CHECKPOINT.exists():
        return set(json.loads(CHECKPOINT.read_text()))
    return set()


def save_checkpoint(done: set[int]):
    CHECKPOINT.write_text(json.dumps(sorted(done)))


async def fetch_tracks() -> list[dict]:
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        c = await db.execute(
            "SELECT * FROM tracks WHERE notion_id IS NOT NULL ORDER BY id"
        )
        rows = await c.fetchall()

    result = []
    for row in rows:
        d = dict(row)
        if d.get("sensations"):
            try:
                d["sensations"] = json.loads(d["sensations"])
            except Exception:
                d["sensations"] = []
        else:
            d["sensations"] = []
        # notes column stores layering hints from bulk_suggest
        if d.get("notes"):
            d["layering"] = d["notes"]
        result.append(d)
    return result


async def main():
    done = load_checkpoint()
    if done:
        print(f"Resuming — {len(done)} tracks already synced")

    tracks = await fetch_tracks()
    pending = [t for t in tracks if t["id"] not in done]
    total   = len(pending)

    if total == 0:
        print("All tracks already synced.")
        CHECKPOINT.unlink(missing_ok=True)
        return

    print(f"{total} tracks to update in Notion (est. {total * DELAY / 60:.1f} min)\n")

    ok = failed = 0
    for i, track in enumerate(pending, 1):
        label = f"{track['artist'] or ''} — {track['name']}"
        print(f"[{i:>4}/{total}] {label[:65]}", end=" ", flush=True)

        try:
            await update_in_notion(track["notion_id"], track)
            done.add(track["id"])
            save_checkpoint(done)
            ok += 1
            print("✓")
        except Exception as e:
            failed += 1
            print(f"✗  {e}")

        if i < total:
            time.sleep(DELAY)

    CHECKPOINT.unlink(missing_ok=True)
    print(f"\n✓ Done — {ok} updated, {failed} failed")


if __name__ == "__main__":
    asyncio.run(main())
