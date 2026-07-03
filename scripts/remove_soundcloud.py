"""
Archive SoundCloud tracks in Notion and delete them from the local DB.

Usage:
    python scripts/remove_soundcloud.py [--dry-run]
"""

import asyncio
import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

import os
import httpx
import aiosqlite

DB_PATH = Path(__file__).parent.parent / "backend" / "grimoire.db"

# All confirmed SoundCloud track IDs
SC_IDS = [
    753, 754, 755, 757, 758, 759, 760, 761, 762, 763,
    765, 766, 767, 768, 769, 771, 772, 773, 774, 775,
    783, 785, 786, 787, 788, 789, 790, 791,
    914, 915, 916, 917, 918, 919, 920,
    921, 922, 923, 924, 926,
]


async def archive_notion_page(client: httpx.AsyncClient, notion_id: str) -> bool:
    token = os.getenv("NOTION_TOKEN")
    resp = await client.patch(
        f"https://api.notion.com/v1/pages/{notion_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        },
        json={"archived": True},
    )
    return resp.status_code == 200


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        placeholders = ",".join("?" * len(SC_IDS))
        c = await db.execute(
            f"SELECT id, name, artist, notion_id FROM tracks WHERE id IN ({placeholders}) ORDER BY id",
            SC_IDS,
        )
        rows = await c.fetchall()

    print(f"Found {len(rows)} SoundCloud tracks to remove")
    if args.dry_run:
        for r in rows:
            print(f"  [{r['id']:>5}]  {(r['artist'] or '')[:25]:<25} — {r['name'][:45]}")
        print("\n(dry-run — no changes made)")
        return

    archived = 0
    failed = []

    async with httpx.AsyncClient(timeout=10) as client:
        async with aiosqlite.connect(str(DB_PATH)) as db:
            for r in rows:
                notion_id = r["notion_id"]
                label = f"{r['artist'] or ''} — {r['name']}"

                if notion_id:
                    ok = await archive_notion_page(client, notion_id)
                    if ok:
                        archived += 1
                        print(f"  archived [{r['id']:>5}] {label[:60]}")
                    else:
                        failed.append(r["id"])
                        print(f"  FAILED   [{r['id']:>5}] {label[:60]}")
                    time.sleep(0.4)

                await db.execute("DELETE FROM tracks WHERE id = ?", [r["id"]])

            await db.commit()

    total = len(rows)
    print(f"\n✓ Deleted {total} tracks from DB")
    print(f"  Notion archived: {archived}, failed: {len(failed)}")
    if failed:
        print(f"  Failed IDs (still deleted from DB): {failed}")


if __name__ == "__main__":
    asyncio.run(main())
