# Plan — feature/remove-sensation-bias

**Goal:** The LLM over-assigns "hypnotique" and "mystérieux" to most tracks. Add an explicit anti-bias rule to the system prompt so the model only picks them when they are genuinely the strongest fit.

---

## Context

`backend/llm.py` has a `SYSTEM_PROMPT` with a section `### ⚠️ 3. RECTIFICATION CHIRURGICALE DES BIAIS` that already corrects for "Industriel" and "Acide" misuse. The same pattern needs to be applied to "Hypnotique" and "Mystérieux".

The definitions in `vocabulary.py`:
- **Hypnotique**: "Structure cyclique obsédante qui aspire l'attention… boucles varient de manière imperceptible pour créer une transe de focalisation pure." → requires very specific looping architecture, not just any repetitive track.
- **Mystérieux**: "Atmosphère sombre, introspective, teintée d'inconnu ou de paranoïa cinématographique… surveillance, ombres, exploration nocturne." → requires genuinely noir/paranoid atmosphere, not just darkness.

---

## Implementation

### 1. Add two bias-correction bullets to `SYSTEM_PROMPT` in `backend/llm.py`

Inside the existing `### ⚠️ 3. RECTIFICATION CHIRURGICALE DES BIAIS` block, append:

```
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
```

### 2. Verify with test cases

In `backend/tests/test_llm.py`, add mocked response assertions for tracks that previously returned hypnotique/mystérieux incorrectly and now return alternative sensations.

---

## Files to touch

| File | Change |
|------|--------|
| `backend/llm.py` | Add two bullets to `SYSTEM_PROMPT` bias section |
| `backend/tests/test_llm.py` | Add regression test cases |

---

## Testing

Fire a few real `/suggest` calls against known tracks that were incorrectly tagged (e.g. any track that previously returned `["hypnotique", "mystérieux"]` as its only sensations). Confirm the model now returns more specific alternatives.

> Keep a list of 3–5 track names + expected sensations here as a reference after testing.
