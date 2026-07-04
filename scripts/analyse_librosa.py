# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.4
#   kernelspec:
#     display_name: Grimoire Scripts
#     language: python
#     name: grimoire-scripts
# ---

# %% [markdown]
# # Grimoire — Librosa Feature Analysis
# Calibrates audio features on the 41 manually-tagged tracks to validate separability before running bulk tagging.

# %%
import sqlite3, json, warnings
from pathlib import Path
import numpy as np
import librosa
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

warnings.filterwarnings('ignore')
# %matplotlib inline
plt.rcParams.update({'figure.dpi': 130, 'axes.spines.top': False, 'axes.spines.right': False})

DB_PATH     = Path('/home/felipe/grimoire/backend/grimoire.db')
MUSIC_ROOT  = Path('/mnt/c/Users/afmsa/Music')
DURATION    = 90   # seconds to load per track — enough for steady state, fast enough to batch
SR          = 22050

# %% [markdown]
# ## 1 — Load labeled tracks and match to audio files

# %%
# Index every audio file in the Music folder by its lowercase stem
EXTS = {'.mp3', '.wav', '.flac', '.aif', '.aiff'}
file_index = {}
for p in MUSIC_ROOT.rglob('*'):
    if p.suffix.lower() in EXTS:
        file_index[p.stem.lower().strip()] = p
print(f'Indexed {len(file_index)} audio files')

# Load the 41 tagged tracks from SQLite
db = sqlite3.connect(str(DB_PATH))
db.row_factory = sqlite3.Row
tagged = db.execute(
    'SELECT id, name, artist, bpm, grain, masse_basse, role_set FROM tracks WHERE grain IS NOT NULL'
).fetchall()

# Match by name (exact then substring)
labeled = []
no_file = []
for t in tagged:
    key  = t['name'].lower().strip()
    path = file_index.get(key)
    if not path:
        hits = [p for stem, p in file_index.items() if key in stem or stem in key]
        path = hits[0] if hits else None
    if path:
        labeled.append({**dict(t), 'path': str(path)})
    else:
        no_file.append(t['name'])

print(f'Matched: {len(labeled)}/41   |   No file: {len(no_file)}')
if no_file:
    print('Missing:', no_file)


# %% [markdown]
# ## 2 — Feature extraction
#
# For each track we compute:
#
# | Feature | What it measures |
# |---|---|
# | `sub_ratio` | Energy in 20–80 Hz relative to total — sub-bass weight |
# | `bass_ratio` | Energy in 80–250 Hz — bass body |
# | `mid_ratio` | Energy in 250–2k Hz |
# | `perc_ratio` | RMS of percussive layer / total RMS — kick/punch |
# | `harm_ratio` | RMS of harmonic layer / total RMS — tonal content |
# | `centroid` | Spectral centre of mass — low=bassy, high=bright |
# | `flatness` | How noisy vs tonal (1=white noise, 0=pure tone) |
# | `zcr` | Zero-crossing rate — high=noisy/percussive |
# | `onset` | Mean onset strength — beat punch |
# | `contrast_low` | Spectral contrast in low band — peak vs valley depth |

# %%
def extract_features(path, duration=DURATION):
    y, sr = librosa.load(path, duration=duration, sr=SR)

    # ── Frequency-band energy ────────────────────────────────────────────────
    D     = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    total = D.mean() + 1e-10

    def band(lo, hi):
        mask = (freqs >= lo) & (freqs < hi)
        return D[mask].mean() / total if mask.any() else 0.0

    sub_r  = band(20,   80)     # sub-bass
    bass_r = band(80,  250)     # bass body
    mid_r  = band(250, 2000)    # mids
    high_r = band(2000, sr//2)  # highs

    # ── Harmonic / Percussive separation ────────────────────────────────────
    y_h, y_p = librosa.effects.hpss(y)
    rms_t = librosa.feature.rms(y=y).mean()   + 1e-10
    rms_p = librosa.feature.rms(y=y_p).mean() + 1e-10
    rms_h = librosa.feature.rms(y=y_h).mean() + 1e-10

    # ── Spectral shape ──────────────────────────────────────────────────────
    cent     = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
    flat     = float(librosa.feature.spectral_flatness(y=y).mean())
    zcr      = float(librosa.feature.zero_crossing_rate(y).mean())
    onset    = float(librosa.onset.onset_strength(y=y, sr=sr).mean())
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr).mean(axis=1)

    return {
        'sub_ratio':    sub_r,
        'bass_ratio':   bass_r,
        'mid_ratio':    mid_r,
        'high_ratio':   high_r,
        'perc_ratio':   float(rms_p / rms_t),
        'harm_ratio':   float(rms_h / rms_t),
        'centroid':     cent,
        'flatness':     flat,
        'zcr':          zcr,
        'onset':        onset,
        'contrast_low': float(contrast[0]),
        'contrast_mid': float(contrast[2]),
    }


# %%
results = []
for i, t in enumerate(labeled):
    name = t['name'][:40]
    print(f'[{i+1:>2}/{len(labeled)}] {name:<42}', end=' ', flush=True)
    try:
        feats = extract_features(t['path'])
        results.append({**t, **feats})
        print('✓')
    except Exception as e:
        print(f'✗  {e}')

print(f'\nExtracted features for {len(results)}/{len(labeled)} tracks')

# %% [markdown]
# ## 3 — Masse Basse: visual separability

# %%
MASSE_COLORS = {'lourd': '#E05555', 'léger': '#45BDDB', 'squelette': '#9B72CF'}
MASSE_CATS   = ['lourd', 'léger', 'squelette']

features_plot = [
    ('sub_ratio',    'Sub-bass ratio\n(20–80 Hz / total)'),
    ('bass_ratio',   'Bass ratio\n(80–250 Hz / total)'),
    ('perc_ratio',   'Percussive ratio\n(kick / total RMS)'),
    ('centroid',     'Spectral centroid\n(Hz — low=bassy)'),
    ('onset',        'Onset strength\n(beat punch)'),
    ('contrast_low', 'Low-band contrast\n(peak vs valley depth)'),
]

fig, axes = plt.subplots(2, 3, figsize=(13, 7))
fig.suptitle('Masse Basse — Feature separability across 19 calibration tracks', fontsize=12, fontweight='bold', y=1.01)

for ax, (feat, label) in zip(axes.flat, features_plot):
    by_cat = {c: [r[feat] for r in results if r['masse_basse'] == c] for c in MASSE_CATS}
    vals   = [by_cat[c] for c in MASSE_CATS]

    bp = ax.boxplot(vals, patch_artist=True, tick_labels=MASSE_CATS,
                    medianprops={'color': 'white', 'linewidth': 2})
    for patch, cat in zip(bp['boxes'], MASSE_CATS):
        patch.set_facecolor(MASSE_COLORS[cat])
        patch.set_alpha(0.65)

    rng = np.random.default_rng(42)
    for j, (cat_vals, cat) in enumerate(zip(vals, MASSE_CATS)):
        jitter = rng.uniform(-0.1, 0.1, len(cat_vals))
        ax.scatter(np.array([j + 1] * len(cat_vals)) + jitter, cat_vals,
                   color=MASSE_COLORS[cat], s=35, zorder=5, edgecolors='white', linewidths=0.5)

    ax.set_title(label, fontsize=9)
    ax.grid(axis='y', alpha=0.25, linestyle='--')
    ax.tick_params(labelsize=8)

legend = [mpatches.Patch(color=MASSE_COLORS[c], label=c, alpha=0.75) for c in MASSE_CATS]
fig.legend(handles=legend, loc='lower center', ncol=3, fontsize=9, frameon=False, bbox_to_anchor=(0.5, -0.03))
plt.tight_layout()
plt.savefig('masse_basse_features.png', dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## 4 — Grain: visual separability

# %%
GRAIN_COLORS = {
    'minéral':    '#7EC8E3',
    'aquatique':  '#45BDDB',
    'poussiéreux':'#C8A86B',
    'texture':    '#A87BC8',
    'épuré':      '#7BC87B',
    'saturé':     '#E07B7B',
}
grain_cats_present = sorted({r['grain'] for r in results})

features_grain = [
    ('flatness',     'Spectral flatness\n(noisy vs tonal)'),
    ('centroid',     'Spectral centroid\n(brightness)'),
    ('zcr',          'Zero-crossing rate\n(noise proxy)'),
    ('harm_ratio',   'Harmonic ratio\n(tonal content)'),
    ('contrast_mid', 'Mid-band contrast\n(texture depth)'),
    ('high_ratio',   'High-freq ratio\n(air / sparkle)'),
]

fig, axes = plt.subplots(2, 3, figsize=(13, 7))
fig.suptitle('Grain — Feature separability across 19 calibration tracks', fontsize=12, fontweight='bold', y=1.01)

for ax, (feat, label) in zip(axes.flat, features_grain):
    by_cat  = {c: [r[feat] for r in results if r['grain'] == c] for c in grain_cats_present}
    vals    = [by_cat.get(c, []) for c in grain_cats_present]
    present = [(c, v) for c, v in zip(grain_cats_present, vals) if v]

    bp = ax.boxplot([v for _, v in present], patch_artist=True,
                    tick_labels=[c for c, _ in present],
                    medianprops={'color': 'white', 'linewidth': 2})
    for patch, (cat, _) in zip(bp['boxes'], present):
        patch.set_facecolor(GRAIN_COLORS.get(cat, '#999'))
        patch.set_alpha(0.65)

    rng = np.random.default_rng(42)
    for j, (cat, cat_vals) in enumerate(present):
        jitter = rng.uniform(-0.1, 0.1, len(cat_vals))
        ax.scatter(np.array([j + 1] * len(cat_vals)) + jitter, cat_vals,
                   color=GRAIN_COLORS.get(cat, '#999'), s=35, zorder=5,
                   edgecolors='white', linewidths=0.5)

    ax.set_title(label, fontsize=9)
    ax.tick_params(axis='x', labelsize=7, rotation=15)
    ax.grid(axis='y', alpha=0.25, linestyle='--')

legend = [mpatches.Patch(color=GRAIN_COLORS.get(c, '#999'), label=c, alpha=0.75) for c in grain_cats_present]
fig.legend(handles=legend, loc='lower center', ncol=len(grain_cats_present),
           fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.03))
plt.tight_layout()
plt.savefig('grain_features.png', dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## 5 — Classification: can we predict masse_basse from audio alone?

# %%
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import LeaveOneOut
from sklearn.pipeline import make_pipeline

FEAT_NAMES = ['sub_ratio', 'bass_ratio', 'perc_ratio', 'centroid',
              'flatness', 'zcr', 'onset', 'contrast_low', 'harm_ratio']

X       = np.array([[r[f] for f in FEAT_NAMES] for r in results])
y_masse = [r['masse_basse'] for r in results]
y_grain = [r['grain'] for r in results]

le_m = LabelEncoder(); y_m = le_m.fit_transform(y_masse)
le_g = LabelEncoder(); y_g = le_g.fit_transform(y_grain)

def loo_accuracy(X, y, clf):
    loo = LeaveOneOut()
    correct = sum(
        clf.fit(X[tr], y[tr]).predict(X[te]) == y[te]
        for tr, te in loo.split(X)
    )
    return correct / len(y)

# Decision Tree (max_depth=3 keeps it human-readable)
dt   = DecisionTreeClassifier(max_depth=3, random_state=42)
knn  = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=3))

print('=== Leave-One-Out accuracy ===')
for name, clf, y_enc in [
    ('Decision Tree  → masse_basse', dt,  y_m),
    ('k-NN (k=3)     → masse_basse', knn, y_m),
    ('Decision Tree  → grain',       dt,  y_g),
    ('k-NN (k=3)     → grain',       knn, y_g),
]:
    acc = loo_accuracy(X, y_enc, clf)
    bar = '█' * int(acc * 20)
    print(f'  {name}:  {bar:<20}  {acc*100:.0f}%  ({int(acc*len(y_enc))}/{len(y_enc)})')

print()
dt.fit(X, y_m)
print('Decision Tree rules for masse_basse:')
print(export_text(dt, feature_names=FEAT_NAMES))

print('\nFeature importances (masse_basse):')
for name, imp in sorted(zip(FEAT_NAMES, dt.feature_importances_), key=lambda x: -x[1]):
    bar = '█' * int(imp * 30)
    print(f'  {name:18}  {bar:<30}  {imp:.3f}')

# %% [markdown]
# ## 6 — Per-track summary table

# %%
# Predict masse_basse for each track and flag mismatches
dt.fit(X, y_m)
preds = le_m.inverse_transform(dt.predict(X))

print(f"{'Track':<36} {'Human':10} {'Pred':10} {'sub_r':6} {'bass_r':6} {'perc_r':6} {'centroid':9}")
print('─' * 90)
for r, pred in sorted(zip(results, preds), key=lambda x: x[0]['masse_basse']):
    flag = '' if r['masse_basse'] == pred else '  ← DIFF'
    print(f"{r['name'][:35]:<36} {r['masse_basse']:10} {pred:10} "
          f"{r['sub_ratio']:.3f}  {r['bass_ratio']:.3f}  "
          f"{r['perc_ratio']:.3f}  {r['centroid']:8.0f}{flag}")

# %% [markdown]
# ## 7 — Radar chart: average feature profile per masse_basse category

# %%
RADAR_FEATS = ['sub_ratio', 'bass_ratio', 'perc_ratio', 'centroid', 'onset', 'flatness', 'harm_ratio']
RADAR_LABELS = ['Sub-bass', 'Bass body', 'Percussive', 'Brightness', 'Onset punch', 'Flatness', 'Harmonic']

scaler = StandardScaler()
X_scaled = scaler.fit_transform(np.array([[r[f] for f in RADAR_FEATS] for r in results]))

# Clip to [-2, 2] and shift to [0, 1] for radar
X_norm = (np.clip(X_scaled, -2, 2) + 2) / 4

N = len(RADAR_FEATS)
angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]

fig, axes = plt.subplots(1, 3, figsize=(13, 4), subplot_kw={'polar': True})
fig.suptitle('Masse Basse — Average audio profile per category', fontsize=11, fontweight='bold')

for ax, cat in zip(axes, MASSE_CATS):
    idxs = [i for i, r in enumerate(results) if r['masse_basse'] == cat]
    mean_vals = X_norm[idxs].mean(axis=0).tolist()
    mean_vals += mean_vals[:1]

    color = MASSE_COLORS[cat]
    ax.plot(angles, mean_vals, color=color, linewidth=2)
    ax.fill(angles, mean_vals, color=color, alpha=0.25)

    # Individual tracks (lighter)
    for idx in idxs:
        vals = X_norm[idx].tolist() + [X_norm[idx][0]]
        ax.plot(angles, vals, color=color, linewidth=0.6, alpha=0.4)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(RADAR_LABELS, size=7)
    ax.set_yticks([])
    ax.set_title(f'{cat}  (n={len(idxs)})', color=color, fontweight='bold', pad=12)

plt.tight_layout()
plt.savefig('masse_basse_radar.png', dpi=150, bbox_inches='tight')
plt.show()

# %% [markdown]
# ## 8 — Threshold summary: what values define each category?
#
# Outputs concrete thresholds you can paste into `bulk_suggest.py` as the deterministic classifier.

# %%
key_feats = ['sub_ratio', 'bass_ratio', 'perc_ratio', 'centroid']
print('=== Calibrated thresholds per masse_basse category ===')
print(f"{'Feature':<15}  {'lourd':>22}  {'léger':>22}  {'squelette':>22}")
print('─' * 85)
for feat in key_feats:
    row = {}
    for cat in MASSE_CATS:
        vals = [r[feat] for r in results if r['masse_basse'] == cat]
        if vals:
            row[cat] = f'{np.mean(vals):.4f}  [{np.min(vals):.3f}–{np.max(vals):.3f}]'
        else:
            row[cat] = 'n/a'
    print(f"{feat:<15}  {row.get('lourd','n/a'):>22}  {row.get('léger','n/a'):>22}  {row.get('squelette','n/a'):>22}")

print()
print('Counts per category:')
for cat in MASSE_CATS:
    n = sum(1 for r in results if r['masse_basse'] == cat)
    print(f'  {cat:12} {n} tracks')
