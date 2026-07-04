"""Notion ↔ SQLite sync layer."""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone

import aiosqlite
from notion_client import AsyncClient

from vocabulary import (
    GRAIN_MAP, GRAIN_REVERSE,
    SENSATIONS_MAP, SENSATIONS_REVERSE,
    MASSE_BASSE_MAP, MASSE_BASSE_REVERSE,
    ROLE_SET_MAP, ROLE_SET_REVERSE,
)


NOTION_VOCAB_MAP = {
    "grain": GRAIN_MAP,
    "sensations": SENSATIONS_MAP,
    "masse_basse": MASSE_BASSE_MAP,
    "role_set": ROLE_SET_MAP,
}


def _get_client() -> AsyncClient:
    return AsyncClient(auth=os.getenv("NOTION_TOKEN"))


def _get_sets_db_id() -> str:
    return os.getenv("NOTION_SETS_DB_ID", "")


def _get_set_tracks_db_id() -> str:
    return os.getenv("NOTION_SET_TRACKS_DB_ID", "")


def _sets_enabled() -> bool:
    return bool(_get_sets_db_id() and _get_set_tracks_db_id())


def _get_db_id() -> str:
    return os.getenv("NOTION_DATABASE_ID", "")


# --- Notion → our model ---

def _text(prop) -> str | None:
    parts = prop.get("rich_text", [])
    return "".join(p["plain_text"] for p in parts) or None


def _select(prop, reverse_map: dict) -> str | None:
    sel = prop.get("select")
    if not sel:
        return None
    return reverse_map.get(sel["name"])


def _multi_select(prop, reverse_map: dict) -> list[str]:
    return [
        reverse_map[o["name"]]
        for o in prop.get("multi_select", [])
        if o["name"] in reverse_map
    ]


def notion_page_to_dict(page: dict) -> dict:
    p = page["properties"]
    label_prop = p.get("Label", {})
    bpm_prop = p.get("BPM", {})
    year_prop = p.get("Year", {})
    grain_prop = p.get("Grain", {})
    sensations_prop = p.get("Sensations", {})
    masse_basse_prop = p.get("Masse Basse", {})
    role_set_prop = p.get("Role Set", {})
    url_prop = p.get("URL", {})
    downloaded_prop = p.get("Downloaded", {})
    hq_prop = p.get("HQ", {})
    collection_prop = p.get("Collection", {})
    return {
        "notion_id": page["id"],
        "name": "".join(t["plain_text"] for t in p["Name"]["title"]),
        "artist": _text(p["Artist"]) or "",
        "album": _text(p.get("Album", {"rich_text": []})),
        "label": label_prop["select"]["name"] if label_prop.get("select") else None,
        "year": year_prop.get("number"),
        "bpm": bpm_prop.get("number"),
        "key": _text(p.get("Key", {"rich_text": []})),
        "grain": _select(grain_prop, GRAIN_REVERSE),
        "sensations": _multi_select(sensations_prop, SENSATIONS_REVERSE),
        "masse_basse": _select(masse_basse_prop, MASSE_BASSE_REVERSE),
        "role_set": _select(role_set_prop, ROLE_SET_REVERSE),
        "url": url_prop.get("url"),
        "downloaded": downloaded_prop.get("checkbox", False),
        "hq_download": hq_prop.get("checkbox", False),
        "layering": _text(p.get("Layering", {"rich_text": []})),
        "collection": collection_prop["select"]["name"] if collection_prop.get("select") else None,
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "notion_updated_at": page.get("last_edited_time"),
    }


# --- our model → Notion properties ---

def dict_to_notion_properties(data: dict) -> dict:
    props = {}

    if "name" in data and data["name"] is not None:
        props["Name"] = {"title": [{"text": {"content": data["name"]}}]}
    if "artist" in data and data["artist"] is not None:
        props["Artist"] = {"rich_text": [{"text": {"content": data["artist"]}}]}
    if "album" in data:
        props["Album"] = {"rich_text": [{"text": {"content": data["album"] or ""}}]}
    if "label" in data:
        props["Label"] = {"select": {"name": data["label"]}} if data["label"] else {"select": None}
    if "year" in data:
        props["Year"] = {"number": data["year"]}
    if "bpm" in data:
        props["BPM"] = {"number": data["bpm"]}
    if "key" in data:
        props["Key"] = {"rich_text": [{"text": {"content": data["key"] or ""}}]}
    if "grain" in data:
        notion_val = GRAIN_MAP.get(data["grain"]) if data["grain"] else None
        props["Grain"] = {"select": {"name": notion_val}} if notion_val else {"select": None}
    if "sensations" in data:
        props["Sensations"] = {
            "multi_select": [{"name": SENSATIONS_MAP[s]} for s in (data["sensations"] or []) if s in SENSATIONS_MAP]
        }
    if "masse_basse" in data:
        notion_val = MASSE_BASSE_MAP.get(data["masse_basse"]) if data["masse_basse"] else None
        props["Masse Basse"] = {"select": {"name": notion_val}} if notion_val else {"select": None}
    if "role_set" in data:
        notion_val = ROLE_SET_MAP.get(data["role_set"]) if data["role_set"] else None
        props["Role Set"] = {"select": {"name": notion_val}} if notion_val else {"select": None}
    if "url" in data:
        props["URL"] = {"url": data["url"]}
    if "downloaded" in data:
        props["Downloaded"] = {"checkbox": bool(data["downloaded"])}
    if "hq_download" in data:
        props["HQ"] = {"checkbox": bool(data["hq_download"])}
    if "layering" in data and data["layering"]:
        props["Layering"] = {"rich_text": [{"text": {"content": data["layering"]}}]}
    if "collection" in data:
        props["Collection"] = {"select": {"name": data["collection"]}} if data["collection"] else {"select": None}

    return props


# --- Sync operations ---

async def _fetch_notion_pages() -> list[dict]:
    """Fetch all pages from Notion database."""
    notion = _get_client()
    db_id = _get_db_id()
    pages = []
    cursor = None
    try:
        while True:
            kwargs: dict = {"database_id": db_id, "page_size": 100}
            if cursor:
                kwargs["start_cursor"] = cursor
            response = await notion.databases.query(**kwargs)
            pages.extend(response["results"])
            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")
    finally:
        await notion.aclose()
    return pages


async def preview_sync(db: aiosqlite.Connection) -> dict:
    """Compare Notion with local DB without writing. Returns {new, updated}."""
    pages = await _fetch_notion_pages()
    new_tracks: list[dict] = []
    updated_tracks: list[dict] = []

    for page in pages:
        try:
            row = notion_page_to_dict(page)
            if not row["name"]:
                continue
            c = await db.execute(
                "SELECT id FROM tracks WHERE notion_id = ?", [row["notion_id"]]
            )
            existing = await c.fetchone()
            entry = {"name": row["name"], "artist": row["artist"]}
            if existing:
                updated_tracks.append(entry)
            else:
                new_tracks.append(entry)
        except Exception:
            continue

    return {"new": new_tracks, "updated": updated_tracks}


async def archive_in_notion(notion_id: str):
    """Soft-delete a Notion page (archived=True). Reversible from Notion UI."""
    notion = _get_client()
    try:
        await notion.pages.update(page_id=notion_id, archived=True)
    finally:
        await notion.aclose()


async def sync_from_notion(db: aiosqlite.Connection):
    """Pull all pages from Notion and upsert into local SQLite."""
    pages = await _fetch_notion_pages()

    upserted = 0
    for page in pages:
        try:
            row = notion_page_to_dict(page)
            if not row["name"]:
                continue
            await db.execute(
                """
                INSERT INTO tracks (notion_id, name, artist, album, label, year, bpm, key,
                    grain, sensations, masse_basse, role_set, url, downloaded, hq_download, layering, collection, synced_at, notion_updated_at)
                VALUES (:notion_id, :name, :artist, :album, :label, :year, :bpm, :key,
                    :grain, :sensations, :masse_basse, :role_set, :url, :downloaded, :hq_download, :layering, :collection, :synced_at, :notion_updated_at)
                ON CONFLICT(notion_id) DO UPDATE SET
                    name=excluded.name, artist=excluded.artist, album=excluded.album,
                    label=excluded.label, year=excluded.year, bpm=excluded.bpm, key=excluded.key,
                    grain=excluded.grain, sensations=excluded.sensations,
                    masse_basse=excluded.masse_basse, role_set=excluded.role_set,
                    url=excluded.url, downloaded=excluded.downloaded, hq_download=excluded.hq_download,
                    layering=COALESCE(excluded.layering, tracks.layering),
                    collection=COALESCE(excluded.collection, tracks.collection),
                    synced_at=excluded.synced_at,
                    notion_updated_at=excluded.notion_updated_at
                """,
                {**row, "sensations": json.dumps(row["sensations"], ensure_ascii=False)},
            )
            upserted += 1
        except Exception:
            continue

    await db.commit()
    return upserted


async def push_to_notion(data: dict) -> str:
    """Create a new page in Notion. Returns the new page ID."""
    notion = _get_client()
    try:
        page = await notion.pages.create(
            parent={"database_id": _get_db_id()},
            properties=dict_to_notion_properties(data),
        )
        return page["id"]
    finally:
        await notion.aclose()


async def update_in_notion(notion_id: str, data: dict):
    """Patch an existing Notion page."""
    notion = _get_client()
    try:
        await notion.pages.update(
            page_id=notion_id,
            properties=dict_to_notion_properties(data),
        )
    finally:
        await notion.aclose()


# --- Sets sync ---

_set_track_prop_names: dict | None = None


async def _get_set_track_props(notion: AsyncClient) -> dict:
    """Discover the relation property names in the Set Tracks DB by inspecting the schema.
    Notion auto-names relations after the target database, so we can't hardcode them."""
    global _set_track_prop_names
    if _set_track_prop_names:
        return _set_track_prop_names

    schema = await notion.databases.retrieve(database_id=_get_set_tracks_db_id())
    props = {"set": "Set", "track": "Track"}  # fallback defaults

    sets_id = _get_sets_db_id().replace("-", "")
    tracks_id = _get_db_id().replace("-", "")

    for name, prop in schema.get("properties", {}).items():
        if prop.get("type") != "relation":
            continue
        related = prop.get("relation", {}).get("database_id", "").replace("-", "")
        if related == sets_id:
            props["set"] = name
        elif related == tracks_id:
            props["track"] = name

    _set_track_prop_names = props
    return props


async def _query_all(notion: AsyncClient, database_id: str) -> list[dict]:
    pages, cursor = [], None
    while True:
        kwargs: dict = {"database_id": database_id, "page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = await notion.databases.query(**kwargs)
        pages.extend(resp["results"])
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return pages


async def push_set_to_notion(name: str) -> str | None:
    if not _sets_enabled():
        return None
    notion = _get_client()
    try:
        page = await notion.pages.create(
            parent={"database_id": _get_sets_db_id()},
            properties={"Name": {"title": [{"text": {"content": name}}]}},
        )
        return page["id"]
    finally:
        await notion.aclose()


async def update_set_in_notion(notion_id: str, name: str):
    if not _sets_enabled():
        return
    notion = _get_client()
    try:
        await notion.pages.update(
            page_id=notion_id,
            properties={"Name": {"title": [{"text": {"content": name}}]}},
        )
    finally:
        await notion.aclose()


async def archive_set_in_notion(notion_id: str):
    if not _sets_enabled():
        return
    notion = _get_client()
    try:
        await notion.pages.update(page_id=notion_id, archived=True)
    finally:
        await notion.aclose()


async def push_set_track_to_notion(
    set_notion_id: str, track_notion_id: str | None, position: int, track_name: str
) -> str | None:
    if not _sets_enabled():
        return None
    notion = _get_client()
    try:
        prop_names = await _get_set_track_props(notion)
        props: dict = {
            "Name": {"title": [{"text": {"content": track_name}}]},
            "Position": {"number": position},
            prop_names["set"]: {"relation": [{"id": set_notion_id}]},
        }
        if track_notion_id:
            props[prop_names["track"]] = {"relation": [{"id": track_notion_id}]}
        page = await notion.pages.create(
            parent={"database_id": _get_set_tracks_db_id()},
            properties=props,
        )
        return page["id"]
    finally:
        await notion.aclose()


async def update_set_track_position_in_notion(notion_id: str, position: int):
    if not _sets_enabled():
        return
    notion = _get_client()
    try:
        await notion.pages.update(
            page_id=notion_id,
            properties={"Position": {"number": position}},
        )
    finally:
        await notion.aclose()


async def archive_set_track_in_notion(notion_id: str):
    if not _sets_enabled():
        return
    notion = _get_client()
    try:
        await notion.pages.update(page_id=notion_id, archived=True)
    finally:
        await notion.aclose()


async def sync_sets_from_notion(db: aiosqlite.Connection):
    """Pull Grimoire Sets + Grimoire Set Tracks from Notion into SQLite."""
    if not _sets_enabled():
        return
    notion = _get_client()
    try:
        # --- Sets ---
        set_pages = await _query_all(notion, _get_sets_db_id())
        for page in set_pages:
            if page.get("archived"):
                continue
            notion_id = page["id"]
            name = "".join(t["plain_text"] for t in page["properties"]["Name"]["title"]) or "Sans nom"
            created_at = int(
                datetime.fromisoformat(page["created_time"].replace("Z", "+00:00")).timestamp()
            )
            await db.execute(
                """INSERT INTO sets (notion_id, name, created_at) VALUES (?, ?, ?)
                   ON CONFLICT(notion_id) DO UPDATE SET name=excluded.name""",
                [notion_id, name, created_at],
            )

        # Build id maps for the join
        c = await db.execute("SELECT id, notion_id FROM sets WHERE notion_id IS NOT NULL")
        set_map = {row[1]: row[0] for row in await c.fetchall()}

        c = await db.execute("SELECT id, notion_id FROM tracks WHERE notion_id IS NOT NULL")
        track_map = {row[1]: row[0] for row in await c.fetchall()}

        # --- Set tracks ---
        prop_names = await _get_set_track_props(notion)
        st_pages = await _query_all(notion, _get_set_tracks_db_id())
        for page in st_pages:
            if page.get("archived"):
                continue
            notion_id = page["id"]
            props = page["properties"]

            set_relations = props.get(prop_names["set"], {}).get("relation", [])
            if not set_relations:
                continue
            set_id = set_map.get(set_relations[0]["id"])
            if set_id is None:
                continue

            track_relations = props.get(prop_names["track"], {}).get("relation", [])
            track_id = track_map.get(track_relations[0]["id"]) if track_relations else None
            position = props.get("Position", {}).get("number") or 0

            await db.execute(
                """INSERT INTO set_tracks (notion_id, set_id, track_id, position) VALUES (?, ?, ?, ?)
                   ON CONFLICT(notion_id) DO UPDATE SET
                       set_id=excluded.set_id,
                       track_id=excluded.track_id,
                       position=excluded.position""",
                [notion_id, set_id, track_id, position],
            )

        await db.commit()
    finally:
        await notion.aclose()
