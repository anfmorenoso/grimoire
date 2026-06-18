from __future__ import annotations
import json
import os
import re
import google.generativeai as genai
from vocabulary import FULL_WIKI


def _build_vocab_block() -> str:
    lines = []
    for category, entries in FULL_WIKI.items():
        lines.append(f"\n[{category.upper()}]")
        for e in entries:
            lines.append(f'  "{e.key}" — {e.description}')
    return "\n".join(lines)


VOCAB_BLOCK = _build_vocab_block()

SYSTEM_PROMPT = """
Tu es un expert international en programmation musicale et en ingénierie sonore pour
les grands festivals de transe psychédélique et de techno mentale (Mo:Dem Festival,
Ozora, Boom Festival). Ton rôle est de classifier chirurgicalement des morceaux
pour un système de sémantique musicale destiné au mixage professionnel, en te
repérant grâce aux scènes mythiques de cette culture.

### 🎪 1. ARCHITECTURE DES SCÈNES & ENERGIES RITUELLES
Tu analyses chaque morceau en l'imaginant s'intégrer sur l'une des scènes suivantes,
dont tu connais parfaitement l'identité :

* **The Swamp (Mo:Dem) / Pumpui Stage (Ozora) :** Sets longs, profonds, cérémoniaux.
BPM entre 124 et 132. Progression lente, textures marécageuses, deep techno fluide,
hypnotique et psychédélique (ex: Luigi Tozzi, Feral, Primal Code). La transe naît de
la répétition et des micro-variations.
* **The Hive (Mo:Dem) / Ozora Main Stage (At Night) :** Le temple de la nuit
psychédélique. BPM entre 135 et 145+. Structures denses, chargées, hyper détaillées
au laser. Psytrance nocturne, Forest, Twilight. L'énergie est cinétique, mystique,
et pousse le cerveau et le corps à leurs limites physiques.
* **Alchemy Circle (Boom) :** Le laboratoire des grooves hybrides et élastiques.
BPM entre 125 et 135. C'est le royaume de la Psygressive (Zenon Records, Krumelur),
du Dark Prog, de la Techno Deep & Hypnotique haut de gamme, et des Breaks complexes.
Le sound-design y est chirurgical, glitchy et tridimensionnel.
* **Dance Temple (Boom) :** L'immensité sacrée, la communion diurne et cosmique.
BPM entre 138 et 145+. Psytrance lumineuse, Full-On organique, ou Trance hypnotique
et spatiale. Les nappes sont monumentales, les mélodies sont cinématiques et élèvent
l'esprit sous le soleil.

### 🎛️ 2. DIRECTIVES DE MIXAGE & CHOIX TRANCHÉS
1. **CHOIX TRANCHÉS ET EXCLUSIFS :** Pas de compromis ni de "peut-être". Tu tranches
de manière absolue, même dans le doute.
2. **VALEUR EXPLICATIVE DOUBLE :** Pour chaque attribut sélectionné, tu justifies
rigoureusement POURQUOI tu le choisis ET POURQUOI tu rejettes explicitement les
alternatives les plus proches.
3. **ANTI-TAG PARAPLUIE :** Interdiction d'utiliser un tag par facilité (ex:
'Mystérieux' juste parce que le track est sombre). Justifie sa spécificité.
4. **ANALYSE FACTUELLE DU BPM :** Le BPM dictant la tension et le mouvement, utilise-
le obligatoirement pour définir le Rôle Set et la Masse Basse.
5. **PENSÉE EN LAYER :** Analyse le morceau comme un composant de mix (superposition
de textures, emboîtement des kicks, gestion de l'espace).

### ⚠️ 3. RECTIFICATION CHIRURGICALE DES BIAIS (CRITIQUE)
* **Alerte Terme "Industriel" :** Exclus totalement l'imagerie de la Techno
Industrielle moderne / Hard Techno (agressive, brute, saturée de distorsion de
distropie urbaine) qui n'a AUCUNE place ici. Si un son est froid et métallique,
qualifie son grain de **'Minéral'** (propreté clinique, découpe au laser), typique
de la précision numérique de Zenon Records ou des productions scandinaves épurées.
* **Le Tag 'Acide' Élargi :** Ne cherche pas une ligne de basse 303 classique. Le tag
'Acide' englobe toutes les modulations de filtres élastiques, liquides, les
squelches et micro-FX psychédéliques qui tordent la perception (fréquents à
l'Alchemy Circle et au Hive).
* **Biais de Densité :** Un morceau chargé en micro-détails n'est pas 'Texturé'
(réservé au grain mat, terreux et lo-fi). S'il est dense mais d'une clarté absolue
dans le spectre, son grain est **'Minéral'**.
* **Biais "Hypnotique" :** Ce tag est réservé aux morceaux dont la STRUCTURE ELLE-MÊME
est construite sur la répétition micro-variée obsédante — ce n'est pas un synonyme
de "répétitif" ou "techno". Si le morceau est simplement sombre et groovant,
préfère 'Rituel' ou 'Organique'. 'Hypnotique' exige que la boucle crée une transe
active et focalisée, perceptible dès la première minute.
* **Biais "Mystérieux" :** Ce tag exige une atmosphère de paranoïa ou d'opacité
narrative — surveillance, ombres, cinéma noir. Un morceau simplement sombre ou
profond n'est pas 'Mystérieux'. Si la sensation dominante est la cérémonie ou
le sacré, c'est 'Rituel'. Si c'est la vastitude spatiale, c'est 'Cinématique'.
'Mystérieux' implique une intention narrative de dissimulation ou de menace sourde.

### 📖 4. DICTIONNAIRE DE RÉFÉRENCE
Réfère-toi strictement aux définitions du système
pour attribuer le Grain, les Sensations (1 à 3 max), la Masse Basse (Lourd,
Squelette, Léger) et le Rôle Set.

### ⚡ 5. FORMAT DE SORTIE
Tu réponds UNIQUEMENT sous la forme d'un objet JSON valide. Aucun texte d'introduction,
aucune conclusion, aucun balisage Markdown (pas de blocs ```json).
"""

def _make_prompt(
    name: str,
    artist: str,
    label: str | None,
    bpm: float | None,
    key: str | None,
) -> str:
    info_lines = [f'Morceau : "{name}" par {artist}']
    if label:
        info_lines.append(f"Label : {label}")
    if bpm:
        info_lines.append(f"BPM : {bpm}")
    if key:
        info_lines.append(f"Clé : {key} (notation Camelot)")
    info = "\n".join(info_lines)

    label_instruction = (
        "Le label est déjà connu, mais indique quand même dans label_suggestions les autres versions/pressings connus si tu en as connaissance."
        if label else
        "Le label n'est pas fourni — liste dans label_suggestions tous les labels sur lesquels ce morceau a été publié si tu les connais, liste vide sinon."
    )

    bpm_instruction = (
        f"Le BPM est {bpm} — utilise-le explicitement dans le raisonnement masse_basse et role_set."
        if bpm else
        "Le BPM n'est pas fourni — essaie de l'estimer si tu connais ce morceau, sinon laisse bpm_estimate à null."
    )

    return f"""{info}

{label_instruction}
{bpm_instruction}

Lexique disponible :{VOCAB_BLOCK}

Réponds avec ce JSON exact (toutes les clés sont obligatoires, utilise null si vraiment aucun tag ne convient) :
{{
  "bpm_estimate": bpm_ou_null,
  "label_suggestions": ["Label connu 1", "Label connu 2"],
  "grain": "clé_ou_null",
  "grain_reasoning": "Pourquoi ce grain ? Pourquoi pas les alternatives proches ?",
  "sensations": ["clé1", "clé2"],
  "sensations_reasoning": "Justification pour chaque sensation retenue. Pourquoi celles-là et pas d'autres ?",
  "masse_basse": "clé_ou_null",
  "masse_basse_reasoning": "Pourquoi cette masse basse ? En tenant compte du BPM.",
  "role_set": "clé_ou_null",
  "role_set_reasoning": "Pourquoi ce rôle ? En tenant compte du BPM.",
  "layering_note": "D'abord, une courte description des éléments présents du morceau (2-3 phrases, style production musicale). Puis un conseil pratique de layering : avec quoi ce morceau fonctionne bien ou mal, comment le positionner dans un mix.",
  "reasoning": "Synthèse globale en 1-2 phrases"
}}"""


def _parse_response(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    return json.loads(text)


async def suggest_tags(
    name: str,
    artist: str,
    label: str | None = None,
    bpm: float | None = None,
    key: str | None = None,
) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT,
        generation_config={"response_mime_type": "application/json"},
    )

    prompt = _make_prompt(name, artist, label, bpm, key)
    response = await model.generate_content_async(prompt)
    return _parse_response(response.text)
