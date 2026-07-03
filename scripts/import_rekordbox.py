"""
Import tracks from a Rekordbox XML collection into the Grimoire SQLite database.

- BPM (AverageBpm) and key (Tonality) from Rekordbox always overwrite existing values
- Genre stored as-is from Rekordbox
- HQ detected from file path
- Playlist membership stored as "Folder > Playlist" (or just "Playlist" if at root)
- Duplicate detection: same name + artist (case-insensitive) → update, not re-insert

Usage:
    python scripts/import_rekordbox.py [path/to/rekordbox.xml]
"""

import asyncio
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import aiosqlite

# ── Configuration ──────────────────────────────────────────────────────────────
DEFAULT_XML = Path(__file__).parent / "data" / "collection.xml"
DB_PATH = Path(__file__).parent.parent / "backend" / "grimoire.db"
HQ_MARKER = "Good quality files"
SKIP_ARTISTS = {"rekordbox", "felipax", "rebik"}  # own mixes / loop samples
SKIP_GENRES  = {"loop samples"}
# ───────────────────────────────────────────────────────────────────────────────


def decode_location(location: str) -> str:
    path = location.replace("file://localhost/", "").replace("file:///", "")
    return urllib.parse.unquote(path)


def parse_playlists(root: ET.Element) -> dict[str, str]:
    """Return {track_id: 'Folder > Playlist'} for every track in the playlist tree."""
    memberships: dict[str, str] = {}

    def walk(node: ET.Element, parent_folder: str | None):
        node_type = node.get("Type")
        name = node.get("Name", "")

        if node_type == "0":  # folder
            folder = name if name != "ROOT" else None
            for child in node:
                walk(child, folder)

        elif node_type == "1":  # playlist
            label = f"{parent_folder} > {name}" if parent_folder else name
            for track_ref in node.findall("TRACK"):
                tid = track_ref.get("Key")
                if tid:
                    # A track can appear in multiple playlists — keep first occurrence
                    memberships.setdefault(tid, label)

    playlists_root = root.find("PLAYLISTS")
    if playlists_root is not None:
        for child in playlists_root:
            walk(child, None)

    return memberships


def parse_xml(xml_path) -> list[dict]:
    tree = ET.parse(str(xml_path))
    root = tree.getroot()

    collection = root.find("COLLECTION")
    if collection is None:
        raise ValueError("No <COLLECTION> element found — is this a valid rekordbox XML?")

    memberships = parse_playlists(root)

    tracks = []
    for t in collection.findall("TRACK"):
        name   = t.get("Name", "").strip()
        artist = t.get("Artist", "").strip()
        genre  = t.get("Genre", "").strip()
        if not name:
            continue
        if artist.lower() in SKIP_ARTISTS or genre.lower() in SKIP_GENRES:
            continue

        location = decode_location(t.get("Location", ""))
        if location.startswith("soundcloud:"):
            continue
        hq = HQ_MARKER.lower() in location.lower()

        bpm_raw = t.get("AverageBpm")  # AverageBpm is the analysed value
        try:
            bpm = round(float(bpm_raw)) if bpm_raw and float(bpm_raw) > 0 else None
        except ValueError:
            bpm = None

        year_raw = t.get("Year")
        try:
            year = int(year_raw) if year_raw and year_raw != "0" else None
        except ValueError:
            year = None

        track_id = t.get("TrackID", "")
        collection_label = memberships.get(track_id) or None

        tracks.append({
            "name": name,
            "artist": artist,
            "album": t.get("Album") or None,
            "label": t.get("Label") or None,
            "genre": t.get("Genre") or None,
            "year": year,
            "bpm": bpm,
            "key": t.get("Tonality") or None,
            "notes": t.get("Comments") or None,
            "downloaded": 1,
            "hq_download": 1 if hq else 0,
            "collection": collection_label,
        })

    return tracks


async def ensure_columns(db: aiosqlite.Connection):
    """Add new columns if they don't exist yet (safe to run repeatedly)."""
    for sql in [
        "ALTER TABLE tracks ADD COLUMN genre TEXT",
        "ALTER TABLE tracks ADD COLUMN collection TEXT",
    ]:
        try:
            await db.execute(sql)
        except Exception:
            pass  # column already exists


async def import_tracks(tracks: list[dict]) -> tuple[int, int]:
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        await ensure_columns(db)
        inserted = updated = 0

        for t in tracks:
            c = await db.execute(
                "SELECT id FROM tracks WHERE LOWER(name) = LOWER(?) AND LOWER(artist) = LOWER(?)",
                [t["name"], t["artist"]],
            )
            existing = await c.fetchone()

            if existing:
                await db.execute(
                    """UPDATE tracks
                       SET bpm = ?, key = ?, hq_download = ?, genre = ?, collection = ?
                       WHERE id = ?""",
                    [t["bpm"], t["key"], t["hq_download"], t["genre"], t["collection"],
                     existing["id"]],
                )
                updated += 1
            else:
                await db.execute(
                    """INSERT INTO tracks
                       (name, artist, album, label, genre, year, bpm, key, sensations,
                        downloaded, hq_download, notes, collection)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, '[]', ?, ?, ?, ?)""",
                    [
                        t["name"], t["artist"], t["album"], t["label"], t["genre"],
                        t["year"], t["bpm"], t["key"],
                        t["downloaded"], t["hq_download"], t["notes"], t["collection"],
                    ],
                )
                inserted += 1

        await db.commit()
        return inserted, updated


async def main():
    xml_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_XML

    print(f"Parsing {xml_path} ...")
    tracks = parse_xml(xml_path)
    hq_count = sum(1 for t in tracks if t["hq_download"])
    in_playlist = sum(1 for t in tracks if t["collection"])
    print(f"Found {len(tracks)} tracks — {hq_count} HQ, {len(tracks) - hq_count} LQ, "
          f"{in_playlist} in a playlist")

    print(f"Importing into {DB_PATH} ...")
    inserted, updated = await import_tracks(tracks)

    print(f"\n✓ Done — {inserted} inserted, {updated} updated (BPM / key / genre / collection)")


if __name__ == "__main__":
    asyncio.run(main())
