# Profile SVG Generator

Generates the five customizable profile SVG visuals inside [`assets/images/`](../assets/images):

- `hero.svg` — Hero identity card, cycling role headlines, focus strips, and framed portrait
- `about.svg` — Engineering thesis summary and 2×2 architectural discipline cards
- `technology.svg` — 6-domain stack matrix (counts & line breaks auto-computed from tool lists)
- `github-stats.svg` — Telemetry HUD with auto-scaled language distribution bars
- `connect.svg` — Collaboration banner pointing to the clickable links below

## Quick Start

Edit any text, colors, stats, roles, or tech lists in [`config.py`](./config.py), then run from the repository root:

```bash
python scripts/generate_svgs.py
```

## Useful Flags

```bash
# Regenerate only specific SVGs
python scripts/generate_svgs.py --only hero technology

# Embed full-resolution assets/id.png directly (useful if you replace id.png)
python scripts/generate_svgs.py --raw-photos

# Validate XML and layout without overwriting files
python scripts/generate_svgs.py --dry-run

# Write output to a test directory
python scripts/generate_svgs.py --out tmp_svgs
```

## Notes for Customization

- **Fonts & Thumbnails:** [`assets/`](./assets) bundles the WOFF2 `@font-face` rules and sized portrait thumbnails so the generator runs with Python standard library only (no `pip install` needed).
- **Updating Photos:** Replace `assets/id.png` or `assets/alok-developer-character.png` and re-run `python scripts/generate_svgs.py`; the script detects newer image files automatically.
- **GitHub Cache Busting:** After pushing updated SVGs, bump `?v=3` → `?v=4` on the image URLs in [`README.md`](../README.md) so GitHub's Camo image proxy fetches the fresh version immediately.
