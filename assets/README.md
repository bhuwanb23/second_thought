# Assets

Generated, not hand-drawn. Regenerate everything with:

```bash
python3 scripts/make_assets.py        # logo, icon, cards
python3 scripts/make_diagrams.py      # the four story diagrams
python3 scripts/make_diagrams_tech.py # the three system diagrams
python3 scripts/make_asset_index.py   # this folder's index and README
```

Palette and type scale live in `scripts/asset_kit.py`, so every asset matches the product page: ink `#14181f`, paper `#f6f7f9`, and one colour per verdict — offer `#0f7b4f`, defer `#8a5a00`, decline `#8c2f39`.

SVG is the source of truth; PNG is rasterised at 1.6–3x with cairosvg. Nothing here loads a font or an image from the network.

| Asset | Kind | Where it is used |
|---|---|---|
| `app-icon` | app | 512 square. Avatars, store listings, Devpost upload. |
| `devpost-thumbnail` | card | 1280x720 listing thumbnail. Upload this one to Devpost. |
| `diagram-ai-boundary` | diagram | Why the model cannot decide anything. |
| `diagram-architecture` | diagram | Four layers, one boundary, zero dependencies. |
| `diagram-clusters` | diagram | Where the idea sits in a field of 549 repos. |
| `diagram-defer` | diagram | The hero path: invoice on payday, ship on payment. |
| `diagram-flow` | diagram | The decision in one read: month + purchase, projection, floor test, three outcomes. |
| `diagram-gate` | diagram | Why a tampered approval cannot move money. |
| `diagram-verdicts` | diagram | The same $249 across three months, with the real copy. |
| `favicon` | app | 256 square. Source for the tab icon. |
| `logo-mark-on-paper` | logo | The mark on a paper tile, for grid layouts. |
| `logo-mark` | logo | The mark alone. |
| `logo-mono-white` | logo | Reversed lockup for dark backgrounds. |
| `logo-primary-transparent` | logo | Same lockup with no background, for white pages. |
| `logo-primary` | logo | The lockup on paper. READMEs, slides, the video's title card. |
| `logo-wordmark-only` | logo | Name only, where the mark is already present. |
| `og-card` | card | 1200x630 link preview for social and chat. |

Open `index.html` to look at the whole set at once.
