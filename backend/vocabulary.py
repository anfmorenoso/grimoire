from dataclasses import dataclass


@dataclass
class VocabEntry:
    key: str           # internal key used in our system
    notion_value: str  # exact string stored in Notion select
    label: str         # short display label with emoji
    description: str   # full wiki description with emoji


# --- Grain ---

GRAIN_WIKI: list[VocabEntry] = [
    VocabEntry(
        key="aquatique",
        notion_value="Aquatique (Liquide / Profond)",
        label="💧 Aquatique",
        description=(
            "Sons fluides, nappes submersibles, effets de delay rappelant le "
            "ressac ou les grands fonds marins. Éléments qui coulent de manière "
            "fluide et continue. Caractéristique de la Deep Techno italienne."
        ),
    ),
    VocabEntry(
        key="poussiéreux",
        notion_value="Poussiéreux (Brume / Lo-Fi)",
        label="⏳ Poussiéreux",
        description=(
            "Présence d'un souffle analogique constant, d'une friture subtile "
            "ou d'échos granuleux. Donne l'impression d'un son vieilli par le "
            "temps, d'une cassette ou d'une brume épaisse."
        ),
    ),
    VocabEntry(
        key="texture",
        notion_value="Texture (Le Relief / Grain)",
        label="🪵 Texture",
        description=(
            "Son hautement tactile, granuleux, organique mais sec — cliquetis "
            "de bois, frottements de terre, bruits d'écorce. Texture forestière, "
            "terreuse et chamanique (Feral)."
        ),
    ),
    VocabEntry(
        key="minéral",
        notion_value="Minéral (Chirurgical / Acier)",
        label="💎 Minéral",
        description=(
            "Sound-design froid, tranchant comme du métal ou sculpté au laser. "
            "Aucune bavure, propreté clinique absolue. S'applique à l'architecture "
            "scandinave ou à la précision chirurgicale de la psygressive."
        ),
    ),
    VocabEntry(
        key="saturé",
        notion_value="Saturé (Corrosif / Distordu)",
        label="⚡ Saturé",
        description=(
            "Saturation organique ou industrielle évidente — distorsion assumée, "
            "grain corrosif qui érode agressivement les contours du son. Entre "
            "l'accident électrique et la décision esthétique radicale."
        ),
    ),
    VocabEntry(
        key="épuré",
        notion_value="Épuré (Le Vide Plein)",
        label="🕳️ Épuré",
        description=(
            "Absence presque totale de texture superficielle. Le vide spatial, "
            "une approche purement minimaliste où seuls les éléments rythmiques "
            "et les notes essentielles subsistent."
        ),
    ),
]

# --- Sensations ---

SENSATIONS_WIKI: list[VocabEntry] = [
    VocabEntry(
        key="hypnotique",
        notion_value="Hypnotique (L'Aspiration)",
        label="🌀 Hypnotique",
        description=(
            "Structure cyclique obsédante qui aspire l'attention du dancefloor. "
            "Les boucles varient de manière imperceptible pour créer une transe de "
            "focalisation pure."
        ),
    ),
    VocabEntry(
        key="mystérieux",
        notion_value="Mystérieux (Profond)",
        label="👁️ Mystérieux",
        description=(
            "Atmosphère sombre, introspective, teintée d'inconnu ou de paranoïa "
            "cinématographique. Évoque la surveillance, les ombres ou l'exploration "
            "nocturne."
        ),
    ),
    VocabEntry(
        key="rituel",
        notion_value="Rituel / Mental (La cérémonie)",
        label="🔮 Rituel / Mental",
        description=(
            "Percussions chamaniques, cloches métalliques lointaines, incantations. "
            "Le morceau est construit ou ressenti comme une cérémonie mystique ou "
            "sacrée au milieu des arbres."
        ),
    ),
    VocabEntry(
        key="organique",
        notion_value="Organique (Le Vivant)",
        label="🌿 Organique",
        description=(
            "Connexion forte avec la matière vivante, la nature, la moiteur des "
            "marécages. Le son donne l'impression de respirer, d'évoluer comme un "
            "biotope en mouvement."
        ),
    ),
    VocabEntry(
        key="acide",
        notion_value="Acide ( La distorsion mentale)",
        label="🧪 Acide",
        description=(
            "Modulations de filtres, résonances poussées et synthés qui grincent, "
            "liquides, squelches ou FX psychédéliques complexes qui altèrent et "
            "distordent la perception mentale."
        ),
    ),
    VocabEntry(
        key="amorphe",
        notion_value="Amorphe (Flou Artistique)",
        label="🌫️ Amorphe",
        description=(
            "Perte de repères géométriques ou rythmiques clairs. Les nappes "
            "s'étirent sans contours nets, créant un brouillard sonore où le temps "
            "semble se dissoudre."
        ),
    ),
    VocabEntry(
        key="cinématique",
        notion_value="Cinématique (L'Espace / Spatial)",
        label="🌌 Cinématique",
        description=(
            "Réverbérations monumentales, sound-design de science-fiction. "
            "Envolées spatiales ou textures tridimensionnelles qui ouvrent l'espace "
            "à 360° au-dessus d'un panorama infini."
        ),
    ),
    VocabEntry(
        key="nerveux",
        notion_value="Nerveux (Le Tranchant)",
        label="💥 Nerveux",
        description=(
            "Énergie saccadée, percussions incisives, lignes rythmiques en tension "
            "permanente. Le morceau rejette la progression fluide : il coupe, choque "
            "et tranche dans le mix."
        ),
    ),
]

# --- Masse Basse ---

MASSE_BASSE_WIKI: list[VocabEntry] = [
    VocabEntry(
        key="lourd",
        notion_value="Lourd / Brrr (La Masse)",
        label="🐘 Lourd / Brrr",
        description=(
            "Infrabasses massives, sub destructrice ou ligne de basse galopante "
            "(rolling) qui sature l'espace physique. Impact lourd et écrasant sur "
            "le sound-system."
        ),
    ),
    VocabEntry(
        key="squelette",
        notion_value="Squelette (Le Moteur)",
        label="🦴 Squelette",
        description=(
            "Kick mat, sec, rigide et focalisé. La sub reste strictement à sa place. "
            "Châssis mécanique épuré conçu pour rouler à pleine vitesse de manière "
            "chirurgicale."
        ),
    ),
    VocabEntry(
        key="léger",
        notion_value="Léger (La Peau / Tool)",
        label="🪶 Léger",
        description=(
            "Bas du spectre très discret, feutré ou lointain. Aucun impact physique "
            "lourd. Agit comme un outil d'habillage parfait pour le layering."
        ),
    ),
]

# --- Role Set ---

ROLE_SET_WIKI: list[VocabEntry] = [
    VocabEntry(
        key="amorce",
        notion_value="1. Amorce (Perplexe)",
        label="🌱 1. Amorce",
        description=(
            "Les 10-15 premières minutes du set. Sas de décompression, pose le "
            "décor mystique, capte les esprits à froid sans agression physique."
        ),
    ),
    VocabEntry(
        key="construction",
        notion_value="2. Construction (Mue)",
        label="🦎 2. Construction",
        description=(
            "20ème-45ème minute. Basse Squelette dominante, tension montante, "
            "hypnose des corps — opère la mue progressive vers l'intensité."
        ),
    ),
    VocabEntry(
        key="peak_time",
        notion_value="3. Peak Time (Lourdeur/Brrr)",
        label="🔥 3. Peak Time",
        description=(
            "Cœur du set. Énergie maximale, impact physique direct et massif, "
            "conçu pour emmener le dancefloor au point de rupture."
        ),
    ),
    VocabEntry(
        key="planage",
        notion_value="4. Planage Massif (Mi-Hauteur)",
        label="🦅 4. Planage Massif",
        description=(
            "Fin de set ou redescente post-tempête. Nappes monumentales, "
            "libération émotionnelle, lévitation sans fatiguer les corps."
        ),
    ),
]

# --- Lookup helpers ---

FULL_WIKI = {
    "grain": GRAIN_WIKI,
    "sensations": SENSATIONS_WIKI,
    "masse_basse": MASSE_BASSE_WIKI,
    "role_set": ROLE_SET_WIKI,
}

# key → notion_value
GRAIN_MAP = {e.key: e.notion_value for e in GRAIN_WIKI}
SENSATIONS_MAP = {e.key: e.notion_value for e in SENSATIONS_WIKI}
MASSE_BASSE_MAP = {e.key: e.notion_value for e in MASSE_BASSE_WIKI}
ROLE_SET_MAP = {e.key: e.notion_value for e in ROLE_SET_WIKI}

# notion_value → key (reverse lookups for sync)
GRAIN_REVERSE = {v: k for k, v in GRAIN_MAP.items()}
SENSATIONS_REVERSE = {v: k for k, v in SENSATIONS_MAP.items()}
MASSE_BASSE_REVERSE = {v: k for k, v in MASSE_BASSE_MAP.items()}
ROLE_SET_REVERSE = {v: k for k, v in ROLE_SET_MAP.items()}