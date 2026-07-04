"""
Batch AI tagging — sends 20 tracks per API call instead of 1.
Per-collection context blocks sharpen accuracy for each playlist's vibe.
Includes layering_note in the output.

Usage:
    python scripts/bulk_suggest.py                              # all untagged tracks
    python scripts/bulk_suggest.py --collection "The Swamp > Psytech"
    python scripts/bulk_suggest.py --batch 15
    python scripts/bulk_suggest.py --limit 60
    python scripts/bulk_suggest.py --dry-run
"""

import asyncio
import json
import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

import os
import aiosqlite
import google.generativeai as genai
from vocabulary import FULL_WIKI

DB_PATH    = Path(__file__).parent.parent / "backend" / "grimoire.db"
CHECKPOINT = Path(__file__).parent / "bulk_suggest_progress.json"
LOG_FILE   = Path(__file__).parent / "bulk_suggest_log.jsonl"
DELAY      = 4.5
BATCH_SIZE = 20

# ── Vocabulary ────────────────────────────────────────────────────────────────

ALLOWED = {
    "grain":       ["minéral", "texture", "poussiéreux", "aquatique", "épuré", "saturé"],
    "sensations":  ["hypnotique", "mystérieux", "rituel", "organique", "acide", "amorphe", "cinématique", "nerveux"],
    "masse_basse": ["squelette", "léger", "lourd"],
    "role_set":    ["construction", "planage", "amorce", "peak_time"],
}

def _vocab_block() -> str:
    lines = []
    for category, entries in FULL_WIKI.items():
        lines.append(f"\n[{category.upper()}]")
        for e in entries:
            lines.append(f'  "{e.key}" — {e.description}')
    return "\n".join(lines)

VOCAB_BLOCK = _vocab_block()

# ── Per-collection context ────────────────────────────────────────────────────
# Each block is injected into the system prompt when --collection matches.
# Add new entries here as you expand to more playlists.

COLLECTION_CONTEXT: dict[str, str] = {

    "The Swamp > Psytech": """
COLLECTION : The Swamp > Psytech
Scène de référence : Mo:Dem Festival — The Swamp / Ozora — Pumpui Stage
BPM typique : 124–134.
Artistes représentatifs : Breger, David Phoenix, Scionaugh, Aaron King, Miles From Mars,
  Yuli Fershtat, Multi Tul, Fractal Joke, Unknown Concept, Nocide.
Son distinctif : psytechno sombre et cérémonial. Couches profondes et répétitives,
  modulations psychédéliques lentes, kick chirurgical mais pas agressif,
  atmosphères marécageuses ou caverneuses. Groove profond qui hypnotise sur la durée.
""",

    "The Swamp > Swampy Trance": """
COLLECTION : The Swamp > Swampy Trance
Scène de référence : Mo:Dem Festival — The Swamp (nuit avancée, cérémoniel)
BPM typique : 126–136.
Artistes représentatifs : Gorovich, ATIA, Waitz, Christie, Status Zero, Valise,
  Pire Meilleur, Tilman Riddelt, Underzone, Hotpretty.
Son distinctif : plus organique et narratif que le Psytech. Basses chaudes et profondes,
  textures organiques, structure répétitive qui construit une transe lente.
  Éléments tribal ou chamanique fréquents. Groove enveloppant, flottant.
""",

    "The Hive > Hive Vibes": """
COLLECTION : The Hive > Hive Vibes
Scène de référence : Mo:Dem Festival — The Hive / Ozora Main Stage (nuit)
BPM typique : 138–148.
Artistes représentatifs : Sourone, Ajja, Cezzers, Hypogeo, Jumpstreet, Libra, Lola Cerise,
  Rinkadink, Krumelur.
Son distinctif : psytrance nocturne, forest et twilight. Structures denses et chargées,
  sound design psychédélique hyper-détaillé, kick puissant, montées intenses.
  Énergie cinétique et mystique, éléments forestiers ou cosmiques.
""",

    "Bouncy Plane": """
COLLECTION : Bouncy Plane
BPM typique : 138–148.
Artistes représentatifs : Swart, Funk Tribu, MZA.
Son distinctif : trance psy accessible avec groove rebondissant et aérien.
  Entre trance planante et psytrance festive. Bassline rebondissante, mélodies aériennes,
  espace et légèreté dans le mix. Énergie positive, solaire ou cosmique — jamais brutale.
""",

    "Slightly Acid": """
COLLECTION : Slightly Acid
BPM typique : 128–138.
Son distinctif : acid techno ou techno à coloration acide. Ligne de basse 303 ou synth
  acide central, groove techno solide, modulations de filtre prononcées.
  Tension acide constante, atmosphère industrielle ou souterraine. Pas nécessairement brutal.
""",

    "Trance > Parchabounce": """
COLLECTION : Trance > Parchabounce
BPM typique : 140–150+.
Son distinctif : hard bounce festif et énergique. Kick très fort et rebondissant,
  énergie maximale, construction rapide. Son de rave direct et efficace —
  impact immédiat, efficacité dancefloor avant toute subtilité.
""",

    "Trance > Tranceomething else": """
COLLECTION : Trance > Tranceomething else
BPM typique : variable.
Son distinctif : trance qui ne rentre pas dans les autres sous-playlists —
  plus classique, expérimental, ou hybride. Analyser chaque morceau sur ses propres mérites.
""",

    "Trance > Trancy": """
COLLECTION : Trance > Trancy
Son distinctif : trance classique assumée — nappes larges, mélodies reconnaissables,
  énergie montante typique du genre.
""",

    "Trance > Acid Trance": """
COLLECTION : Trance > Acid Trance
Son distinctif : trance avec ligne acide centrale. Fusion entre énergie trance
  et tension acid techno.
""",
}

BASE_SYSTEM_PROMPT = """
Tu es un expert international en programmation musicale pour les grands festivals de
transe psychédélique et de techno mentale (Mo:Dem, Ozora, Boom).

Tu reçois une liste de morceaux en JSON et tu retournes un JSON array avec les tags
pour chacun. Pas de texte autour, uniquement le JSON array.

Valeurs strictement autorisées :
- grain      : {grain}
- sensations : {sensations} (choisis 1 à 3)
- masse_basse: {masse_basse}
- role_set   : {role_set}

Si tu ne peux vraiment pas déterminer un champ, mets null.
Ne invente pas de valeurs hors des listes ci-dessus.

Biais à éviter :
- "Minéral" = froid et précis comme un laser (Zenon Records), PAS industriel brutal
- "Hypnotique" = structure construite SUR la répétition micro-variée, pas juste sombre
- "Mystérieux" = paranoïa narrative, dissimulation — pas simplement profond ou sombre
- "Acide" = toute modulation de filtre élastique psychédélique, pas seulement une 303
- "Texturé" = lo-fi mat terreux, PAS dense et chirurgicalement clair

{{collection_block}}

{vocab}
""".strip()


def build_system_prompt(collection: str | None) -> str:
    block = COLLECTION_CONTEXT.get(collection or "", "")
    return BASE_SYSTEM_PROMPT.format(
        grain=ALLOWED["grain"],
        sensations=ALLOWED["sensations"],
        masse_basse=ALLOWED["masse_basse"],
        role_set=ALLOWED["role_set"],
        vocab=VOCAB_BLOCK,
    ).replace("{collection_block}", block.strip())


# ── Checkpoint ────────────────────────────────────────────────────────────────

def load_checkpoint() -> set[int]:
    if CHECKPOINT.exists():
        return set(json.loads(CHECKPOINT.read_text()))
    return set()

def save_checkpoint(done: set[int]):
    CHECKPOINT.write_text(json.dumps(sorted(done)))


# ── DB ────────────────────────────────────────────────────────────────────────

async def fetch_pending(done: set[int], collection: str | None = None) -> list[dict]:
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        if collection:
            c = await db.execute(
                "SELECT id, name, artist, label, bpm, key FROM tracks WHERE grain IS NULL AND collection = ? ORDER BY id",
                [collection],
            )
        else:
            c = await db.execute(
                "SELECT id, name, artist, label, bpm, key FROM tracks WHERE grain IS NULL ORDER BY id"
            )
        rows = await c.fetchall()
    return [dict(r) for r in rows if r["id"] not in done]


async def apply_batch(db: aiosqlite.Connection, results: list[dict]):
    for r in results:
        track_id = r.get("id")
        if not track_id:
            continue

        sets, values = [], []

        for col in ("grain", "masse_basse", "role_set"):
            val = r.get(col)
            if val and val in ALLOWED[col]:
                sets.append(f"{col} = ?")
                values.append(val)

        sensations = r.get("sensations") or []
        if isinstance(sensations, str):
            sensations = [sensations]
        sensations = [s for s in sensations if s in ALLOWED["sensations"]]
        if sensations:
            sets.append("sensations = ?")
            values.append(json.dumps(sensations))

        if r.get("bpm_estimate"):
            sets.append("bpm = COALESCE(bpm, ?)")
            values.append(r["bpm_estimate"])

        if r.get("layering_note"):
            sets.append("notes = COALESCE(notes, ?)")
            values.append(r["layering_note"])

        if sets:
            values.append(track_id)
            await db.execute(f"UPDATE tracks SET {', '.join(sets)} WHERE id = ?", values)

    await db.commit()


# ── LLM batch call ────────────────────────────────────────────────────────────

async def tag_batch(tracks: list[dict], system_prompt: str) -> list[dict]:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(
        model_name="gemini-3.1-flash-lite",
        system_instruction=system_prompt,
        generation_config={"response_mime_type": "application/json"},
    )

    payload = [
        {
            "id":     t["id"],
            "name":   t["name"],
            "artist": t["artist"] or "",
            **({"label": t["label"]} if t.get("label") else {}),
            **({"bpm":   t["bpm"]}   if t.get("bpm")   else {}),
            **({"key":   t["key"]}   if t.get("key")   else {}),
        }
        for t in tracks
    ]

    prompt = f"""Tague ces {len(tracks)} morceaux.

Input:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Réponds avec un JSON array, un objet par morceau :
[{{
  "id": <id>,
  "grain": "...",
  "sensations": [...],
  "masse_basse": "...",
  "role_set": "...",
  "bpm_estimate": <int ou null>,
  "layering_note": "1-2 phrases : description sonore + conseil de placement dans un mix"
}}, ...]"""

    response = await model.generate_content_async(prompt)
    text = response.text.strip().lstrip("```json").lstrip("```").rstrip("```")
    return json.loads(text)


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch",      type=int, default=BATCH_SIZE)
    parser.add_argument("--limit",      type=int, default=None)
    parser.add_argument("--collection", type=str, default=None)
    parser.add_argument("--dry-run",    action="store_true")
    args = parser.parse_args()

    system_prompt = build_system_prompt(args.collection)

    if args.collection and args.collection in COLLECTION_CONTEXT:
        print(f"Using collection-specific prompt for: {args.collection}")
    elif args.collection:
        print(f"⚠  No specific prompt for '{args.collection}' — using base prompt")

    done    = load_checkpoint()
    pending = await fetch_pending(done, collection=args.collection)
    if args.limit:
        pending = pending[:args.limit]

    if not pending:
        print("Nothing to tag — all tracks already have grain set.")
        CHECKPOINT.unlink(missing_ok=True)
        return

    batches = [pending[i:i + args.batch] for i in range(0, len(pending), args.batch)]

    if done:
        print(f"Resuming — {len(done)} tracks already tagged")
    print(f"{len(pending)} tracks · {len(batches)} batches of {args.batch} · est. {len(batches) * DELAY / 60:.1f} min\n")

    async with aiosqlite.connect(str(DB_PATH)) as db:
        for b_idx, batch in enumerate(batches, 1):
            names = ", ".join(f"{t['artist']} — {t['name']}" for t in batch[:2])
            print(f"[batch {b_idx:>2}/{len(batches)}] {names[:80]}…", end=" ", flush=True)

            if args.dry_run:
                print("(dry-run)")
                continue

            try:
                results = await tag_batch(batch, system_prompt)
                await apply_batch(db, results)

                for t in batch:
                    done.add(t["id"])
                save_checkpoint(done)

                LOG_FILE.open("a").write(
                    json.dumps({"batch": b_idx, "collection": args.collection, "results": results}, ensure_ascii=False) + "\n"
                )

                tagged = sum(1 for r in results if r.get("grain"))
                print(f"✓  {tagged}/{len(batch)} tagged")

            except Exception as e:
                print(f"✗  {e}")

            if b_idx < len(batches):
                time.sleep(DELAY)

    remaining = len(await fetch_pending(done))
    print(f"\n✓ Done — {len(done)} total processed, {remaining} still pending")
    if remaining == 0:
        CHECKPOINT.unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(main())
