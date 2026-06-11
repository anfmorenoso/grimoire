"""Spotify track metadata lookup via Client Credentials (no user auth needed)."""
from __future__ import annotations
import logging
import os
import re
import httpx

log = logging.getLogger(__name__)


def _label_from_copyrights(copyrights: list[dict]) -> str | None:
    """Extract record label from Spotify copyright list."""
    preferred = [c for c in copyrights if c.get("type") == "P"]
    entry = preferred[0] if preferred else (copyrights[0] if copyrights else None)
    if not entry:
        return None
    text = entry.get("text", "").strip()
    # strip copyright symbol / letter prefix: (C), (P), ©, ℗
    text = re.sub(r"^\(?\s*[CP©℗]\s*\)?\s*", "", text)
    # strip leading year
    text = re.sub(r"^\d{4}\s*", "", text)
    # take only the first label entity (before comma / long qualifier)
    text = text.split(",")[0].strip()
    return text or None

# Spotify key integer → Camelot notation (key_int, mode: 1=major 0=minor)
_CAMELOT: dict[tuple[int, int], str] = {
    (0, 1): "8B", (0, 0): "5A",
    (1, 1): "3B", (1, 0): "12A",
    (2, 1): "10B", (2, 0): "7A",
    (3, 1): "5B", (3, 0): "2A",
    (4, 1): "12B", (4, 0): "9A",
    (5, 1): "7B", (5, 0): "4A",
    (6, 1): "2B", (6, 0): "11A",
    (7, 1): "9B", (7, 0): "6A",
    (8, 1): "4B", (8, 0): "1A",
    (9, 1): "11B", (9, 0): "8A",
    (10, 1): "6B", (10, 0): "3A",
    (11, 1): "1B", (11, 0): "10A",
}


def _extract_track_id(url: str) -> str | None:
    match = re.search(r"spotify\.com(?:/intl-[a-z]+)?/track/([A-Za-z0-9]+)", url)
    return match.group(1) if match else None


async def get_spotify_token() -> str:
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def _fetch_audio_features(track_id: str, token: str) -> dict[str, object]:
    """Returns {bpm, key} where key is Camelot notation or None."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.spotify.com/v1/audio-features/{track_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 403:
                log.warning(
                    "audio-features blocked (403) — Spotify deprecated this endpoint "
                    "for apps created after Nov 2024. BPM/key will be null."
                )
                return {"bpm": None, "key": None}
            if resp.status_code != 200:
                log.warning("audio-features %s → HTTP %s: %s", track_id, resp.status_code, resp.text[:200])
                return {"bpm": None, "key": None}
            data = resp.json()
    except Exception as e:
        log.warning("audio-features exception: %s", e)
        return {"bpm": None, "key": None}

    bpm = round(data["tempo"]) if data.get("tempo") else None
    key_int = data.get("key", -1)
    mode = data.get("mode", -1)
    camelot = _CAMELOT.get((key_int, mode)) if key_int != -1 and mode != -1 else None
    return {"bpm": bpm, "key": camelot}


async def lookup_spotify_track(url: str) -> dict | None:
    track_id = _extract_track_id(url)
    if not track_id:
        return None

    try:
        token = await get_spotify_token()
    except Exception:
        return None

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.spotify.com/v1/tracks/{track_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
    except Exception:
        return None

    artists = ", ".join(a["name"] for a in data["artists"])
    label = None

    album_id = data["album"]["id"]
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.spotify.com/v1/albums/{album_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                album_data = resp.json()
                label = album_data.get("label") or _label_from_copyrights(
                    album_data.get("copyrights", [])
                )
            else:
                log.warning("album %s → HTTP %s: %s", album_id, resp.status_code, resp.text[:200])
    except Exception as e:
        log.warning("album fetch exception: %s", e)

    image_url = None
    if data["album"]["images"]:
        image_url = data["album"]["images"][0]["url"]

    release_date = data["album"].get("release_date", "") or ""
    year = int(release_date[:4]) if len(release_date) >= 4 and release_date[:4].isdigit() else None

    audio = await _fetch_audio_features(track_id, token)

    return {
        "name": data["name"],
        "artist": artists,
        "label": label,
        "year": year,
        "url": url,
        "image_url": image_url,
        "bpm": audio["bpm"],
        "key": audio["key"],
    }
