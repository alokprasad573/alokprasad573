"""
Customizable SVG generator for Alok Prasad's GitHub Profile visuals.

Usage:
    python scripts/generate_svgs.py
    python scripts/generate_svgs.py --only hero about
    python scripts/generate_svgs.py --raw-photos
    python scripts/generate_svgs.py --out custom/output/dir
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import config as cfg  # noqa: E402
from github_live import fetch_live_github_stats  # noqa: E402


# ==============================================================================
# HELPERS: Escaping, Font/Photo Loading, Typography Sizing, Line Wrapping
# ==============================================================================
def esc(text: object) -> str:
    """Escape text for safe inclusion inside SVG XML elements and attributes."""
    return xml_escape(str(text), {"'": "&apos;", '"': "&quot;"})


def estimate_text_px(text: str, font_size: float, mono: bool = False, letter_spacing: float = 0.0) -> float:
    """Approximate rendered text width in pixels for dynamic pill/card sizing."""
    n = len(text)
    if mono:
        return n * (font_size * 0.67 + letter_spacing)
    narrow = set("ijlItf1.,:;!|()[]/\\'\" ")
    wide = set("mwMWQGCDHO")
    total = 0.0
    for ch in text:
        if ch in narrow:
            total += font_size * 0.34
        elif ch in wide:
            total += font_size * 0.76
        else:
            total += font_size * 0.56
    return total + max(0, n - 1) * letter_spacing


def split_two_lines(items: list[str], max_chars: int = 44, sep: str = " · ") -> tuple[str, str]:
    """Split a list of tool names into two visually balanced separator lines."""
    joined = sep.join(items)
    if len(joined) <= max_chars or len(items) <= 2:
        mid = (len(items) + 1) // 2
        if len(items) > 1 and len(joined) > max_chars:
            return sep.join(items[:mid]), sep.join(items[mid:])
        return joined, ""

    best_idx = 1
    best_diff = 10**9
    for i in range(1, len(items)):
        l1 = sep.join(items[:i])
        l2 = sep.join(items[i:])
        diff = abs(len(l1) - len(l2))
        if len(l1) <= max_chars and len(l2) <= max_chars and diff < best_diff:
            best_diff = diff
            best_idx = i
    if best_diff == 10**9:
        best_idx = max(1, (len(items) + 1) // 2)
    return sep.join(items[:best_idx]), sep.join(items[best_idx:])


def load_fonts_css() -> str:
    fonts_path = REPO_ROOT / cfg.ASSETS["fonts_css"]
    if not fonts_path.exists():
        raise FileNotFoundError(
            f"Missing bundled font CSS at {fonts_path}. Keep scripts/assets/fonts_bundle.css intact."
        )
    return fonts_path.read_text(encoding="utf-8")


def resolve_image_uri(source_rel: str, thumb_rel: str | None = None, use_raw: bool = False) -> str:
    """
    Encode an image file as a base64 data URI.
    Uses bundled thumbnail unless missing, `--raw-photos` is passed, or user modified the source photo.
    """
    src_path = REPO_ROOT / source_rel
    chosen = src_path

    if not use_raw and thumb_rel:
        thumb_path = REPO_ROOT / thumb_rel
        if thumb_path.exists():
            if not src_path.exists() or src_path.stat().st_mtime <= thumb_path.stat().st_mtime:
                chosen = thumb_path

    if not chosen.exists():
        raise FileNotFoundError(f"Image asset not found: {chosen}")

    mime, _ = mimetypes.guess_type(chosen.name)
    if not mime:
        mime = "image/png"
    b64 = base64.b64encode(chosen.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def base_defs(ns: str, w: int, h: int, fonts_css: str, extra_css: str = "") -> str:
    """Shared tokenized CSS design system, atmospheric meshes, specular bevels & grids."""
    t = cfg.THEME
    return f"""    <style type="text/css"><![CDATA[
{fonts_css}
      svg {{
        --c-bg: {t['bg']};
        --c-bg-mid: {t['bg_mid']};
        --c-surface: {t['surface']};
        --c-surface-alt: {t['surface_alt']};
        --c-surface-deep: {t['surface_deep']};
        --c-border: {t['border']};
        --c-primary: {t['primary']};
        --c-secondary: {t['secondary']};
        --c-crimson: {t['crimson']};
        --c-crimson-soft: {t['crimson_soft']};
        --c-green: {t['green']};
        --c-text: {t['text']};
        --c-text-soft: {t['text_soft']};
        --c-muted: #B0C0DC;
        --c-muted-dim: #8DA2C5;
        --ease-cinematic: cubic-bezier(0.22, 1, 0.36, 1);
      }}
      .t-display {{
        font-family: 'Space Grotesk', system-ui, -apple-system, 'Segoe UI', sans-serif;
        text-rendering: geometricPrecision;
      }}
      .t-body {{
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
        text-rendering: optimizeLegibility;
      }}
      .t-mono {{
        font-family: 'JetBrains Mono', ui-monospace, 'Cascadia Mono', monospace;
        font-variant-numeric: tabular-nums;
      }}
      .c-muted {{ fill: var(--c-muted); }}
      .c-dim {{ fill: var(--c-muted-dim); }}
      @keyframes beacon-ring {{
        0% {{ transform: scale(0.95); opacity: 0.72; }}
        70% {{ transform: scale(1.95); opacity: 0; }}
        100% {{ transform: scale(1.95); opacity: 0; }}
      }}
      @keyframes status-breathe {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.55; }}
      }}
      .beacon-dot {{ animation: status-breathe 2.4s ease-in-out infinite; }}
      .beacon-halo {{ animation: beacon-ring 2.4s var(--ease-cinematic) infinite; }}
{extra_css}
      @media (prefers-reduced-motion: reduce) {{
        * {{ animation: none !important; transition: none !important; }}
        .beacon-halo {{ opacity: 0.25 !important; transform: none !important; }}
      }}
    ]]></style>
    <linearGradient id="{ns}-bg" x1="0" y1="0" x2="{w}" y2="{h}" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#050913"/>
      <stop offset="50%" stop-color="#0A1226"/>
      <stop offset="100%" stop-color="#060A15"/>
    </linearGradient>
    <radialGradient id="{ns}-glow-b" cx="14%" cy="16%" r="58%">
      <stop offset="0%" stop-color="{t['primary']}" stop-opacity="0.24"/>
      <stop offset="48%" stop-color="{t['primary']}" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="{t['primary']}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="{ns}-glow-r" cx="88%" cy="84%" r="54%">
      <stop offset="0%" stop-color="{t['crimson']}" stop-opacity="0.20"/>
      <stop offset="50%" stop-color="{t['crimson']}" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="{t['crimson']}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="{ns}-glow-c" cx="54%" cy="6%" r="48%">
      <stop offset="0%" stop-color="{t['secondary']}" stop-opacity="0.10"/>
      <stop offset="100%" stop-color="{t['secondary']}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="{ns}-glass" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#15233D" stop-opacity="0.92"/>
      <stop offset="55%" stop-color="#0E182B" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#09101E" stop-opacity="0.98"/>
    </linearGradient>
    <linearGradient id="{ns}-glass-alt" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#192946" stop-opacity="0.94"/>
      <stop offset="100%" stop-color="#0F1A2E" stop-opacity="0.96"/>
    </linearGradient>
    <linearGradient id="{ns}-spec-top" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="22%" stop-color="{t['secondary']}" stop-opacity="0.45"/>
      <stop offset="50%" stop-color="#FFFFFF" stop-opacity="0.34"/>
      <stop offset="78%" stop-color="{t['crimson_soft']}" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="{ns}-hairline" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{t['primary']}" stop-opacity="0"/>
      <stop offset="18%" stop-color="{t['primary']}" stop-opacity="0.82"/>
      <stop offset="50%" stop-color="{t['border']}" stop-opacity="0.95"/>
      <stop offset="82%" stop-color="{t['crimson']}" stop-opacity="0.78"/>
      <stop offset="100%" stop-color="{t['crimson']}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="{ns}-card-stroke" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{t['secondary']}" stop-opacity="0.72"/>
      <stop offset="48%" stop-color="{t['border']}" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="{t['crimson']}" stop-opacity="0.62"/>
    </linearGradient>
    <linearGradient id="{ns}-pill-stroke" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{t['primary']}" stop-opacity="0.65"/>
      <stop offset="55%" stop-color="{t['border']}" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="{t['crimson']}" stop-opacity="0.55"/>
    </linearGradient>
    <linearGradient id="{ns}-title-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#F8FAFF"/>
      <stop offset="65%" stop-color="#DCE8FF"/>
      <stop offset="100%" stop-color="{t['secondary']}"/>
    </linearGradient>
    <pattern id="{ns}-grid" width="48" height="48" patternUnits="userSpaceOnUse">
      <path d="M48 0H0V48" fill="none" stroke="{t['border']}" stroke-opacity="0.22" stroke-width="0.75"/>
      <circle cx="0" cy="0" r="1.15" fill="{t['secondary']}" fill-opacity="0.24"/>
      <circle cx="24" cy="24" r="0.85" fill="{t['border']}" fill-opacity="0.45"/>
    </pattern>
    <radialGradient id="{ns}-grid-mask-g" cx="50%" cy="50%" r="65%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="1"/>
      <stop offset="78%" stop-color="#FFFFFF" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0.12"/>
    </radialGradient>
    <mask id="{ns}-grid-mask">
      <rect width="{w}" height="{h}" fill="url(#{ns}-grid-mask-g)"/>
    </mask>"""


def shell_background(ns: str, w: int, h: int) -> str:
    t = cfg.THEME
    return f"""  <rect width="{w}" height="{h}" rx="18" fill="url(#{ns}-bg)"/>
  <rect width="{w}" height="{h}" rx="18" fill="url(#{ns}-grid)" mask="url(#{ns}-grid-mask)"/>
  <rect width="{w}" height="{h}" rx="18" fill="url(#{ns}-glow-b)"/>
  <rect width="{w}" height="{h}" rx="18" fill="url(#{ns}-glow-r)"/>
  <rect width="{w}" height="{h}" rx="18" fill="url(#{ns}-glow-c)"/>
  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="17" stroke="url(#{ns}-card-stroke)" stroke-width="1.5"/>
  <rect x="20" y="1" width="{w - 40}" height="1.2" rx="0.6" fill="url(#{ns}-spec-top)"/>
  <path d="M18 12V6C18 4.9 18.9 4 20 4H26" stroke="{t['primary']}" stroke-opacity="0.6" stroke-width="1.4" stroke-linecap="round"/>
  <path d="M{w - 26} 4H{w - 20}C{w - 18.9} 4 {w - 18} 4.9 {w - 18} 6V12" stroke="{t['crimson']}" stroke-opacity="0.6" stroke-width="1.4" stroke-linecap="round"/>"""


# ==============================================================================
# 1. HERO.SVG (1200x424)
# ==============================================================================
def build_role_css_and_nodes(roles: list[dict[str, str]]) -> tuple[str, str]:
    n = max(1, len(roles))
    if n == 1:
        r0 = roles[0]
        css = ""
        node = f'<text x="16" y="0" class="t-display" font-size="22" font-weight="600" fill="{esc(r0["color"])}">{esc(r0["text"])}</text>'
        return css, node

    dur = n * 3.0
    css_lines = []
    nodes = []
    seg = 100.0 / n
    for idx, role in enumerate(roles):
        cls = f"hero-r{idx + 1}"
        kf = f"hero-role-{idx + 1}"
        s = idx * seg
        e = (idx + 1) * seg
        if idx == 0:
            fade_end = max(s, e - 2.2)
            frame = (
                f"0%, {fade_end:.1f}% {{ opacity: 1; transform: translateY(0px); }} "
                f"{e:.1f}%, 97.5% {{ opacity: 0; transform: translateY(-4px); }} "
                f"100% {{ opacity: 1; transform: translateY(0px); }}"
            )
        else:
            on_start = min(99.0, s + 1.4)
            on_end = max(on_start, e - 2.2)
            frame = (
                f"0%, {max(0.0, s - 0.5):.1f}% {{ opacity: 0; transform: translateY(5px); }} "
                f"{on_start:.1f}%, {on_end:.1f}% {{ opacity: 1; transform: translateY(0px); }} "
                f"{min(100.0, e):.1f}%, 100% {{ opacity: 0; transform: translateY(-4px); }}"
            )
        css_lines.append(f"      @keyframes {kf} {{ {frame} }}")
        css_lines.append(f"      .{cls} {{ animation: {kf} {dur:.1f}s var(--ease-cinematic) infinite both; }}")
        init_op = "1" if idx == 0 else "0"
        nodes.append(
            f'    <text x="16" y="0" class="t-display {cls}" font-size="21.5" font-weight="600" fill="{esc(role["color"])}" opacity="{init_op}">{esc(role["text"])}</text>'
        )

    hidden_selectors = ", ".join(f".hero-r{i + 1}" for i in range(1, n))
    css_lines.append("      @media (prefers-reduced-motion: reduce) {")
    css_lines.append("        .hero-r1 { opacity: 1 !important; transform: none !important; }")
    css_lines.append(f"        {hidden_selectors} {{ opacity: 0 !important; }}")
    css_lines.append("      }")
    return "\n".join(css_lines), "\n".join(nodes)


def build_hero(fonts_css: str, use_raw: bool = False) -> str:
    t = cfg.THEME
    hcfg = cfg.HERO
    pcard = hcfg["portrait_card"]
    photo_uri = resolve_image_uri(cfg.ASSETS["hero_photo"], cfg.ASSETS["hero_photo_thumb"], use_raw=use_raw)

    degree_txt = hcfg["degree_badge"]
    degree_w = max(180, round(estimate_text_px(degree_txt, 11.5, mono=True, letter_spacing=0.8) + 48))
    loc_txt = hcfg["location_badge"]
    loc_x = 48 + degree_w + 12
    loc_w = max(84, round(estimate_text_px(loc_txt, 11.5, mono=True, letter_spacing=0.8) + 48))

    greet_txt = hcfg["greeting"]
    cursor_x = 48 + round(estimate_text_px(greet_txt, 18.0, mono=True, letter_spacing=1.2) + 10)

    role_css, role_nodes = build_role_css_and_nodes(hcfg["roles"])

    # Render all configured intro lines cleanly without truncation
    intro_list = hcfg["intro_lines"][:3]
    intro_start_y = 240 if len(intro_list) <= 2 else 234
    intro_step = 23 if len(intro_list) <= 2 else 20
    intro_xml = []
    for idx, line in enumerate(intro_list):
        iy = intro_start_y + idx * intro_step
        line_fill = "#C2D0E8" if idx < len(intro_list) - 1 else "#E2ECFF"
        intro_xml.append(
            f'  <text x="48" y="{iy}" class="t-body" font-size="14.5" font-weight="400" fill="{line_fill}">{esc(line)}</text>'
        )

    focus_xml = []
    focus_items = hcfg["focus_cards"][:3]
    total_focus_w = 676
    gap = 14
    card_w = (total_focus_w - gap * (max(1, len(focus_items)) - 1)) // max(1, len(focus_items))
    for i, fc in enumerate(focus_items):
        fx = i * (card_w + gap)
        delay = f"{0.12 * i:.2f}s"
        focus_xml.append(
            f'  <g class="hero-card-stagger" style="animation-delay:{delay}">\n'
            f'    <rect x="{fx}" y="0" width="{card_w}" height="48" rx="10" fill="url(#hero-glass-alt)" stroke="{t["border"]}" stroke-width="1.1"/>\n'
            f'    <line x1="{fx + 10}" y1="0.8" x2="{fx + card_w - 10}" y2="0.8" stroke="url(#hero-spec-top)" stroke-width="1"/>\n'
            f'    <rect x="{fx}" y="11" width="3" height="26" rx="1.5" fill="{esc(fc["color"])}"/>\n'
            f'    <text x="{fx + 14}" y="18" class="t-mono" font-size="9.5" font-weight="600" fill="{esc(fc["color"])}" letter-spacing="0.9">{esc(fc["label"])}</text>\n'
            f'    <text x="{fx + 14}" y="36" class="t-body" font-size="12" font-weight="600" fill="{t["text"]}">{esc(fc["title"])}</text>\n'
            f'  </g>'
        )

    extra_css = f"""      @keyframes hero-type {{ 0% {{ clip-path: inset(0 100% 0 0); }} 100% {{ clip-path: inset(0 0% 0 0); }} }}
      @keyframes hero-cursor-slide {{ 0% {{ transform: translateX(-110px); }} 100% {{ transform: translateX(0px); }} }}
      @keyframes hero-cursor {{ 0%, 48% {{ opacity: 1; }} 52%, 100% {{ opacity: 0.14; }} }}
      @keyframes hero-rise {{ 0% {{ transform: translateY(24px); opacity: 0.25; }} 100% {{ transform: translateY(0px); opacity: 1; }} }}
      @keyframes hero-card-in {{ 0% {{ transform: translateY(8px); opacity: 0.35; }} 100% {{ transform: translateY(0px); opacity: 1; }} }}
      @keyframes hero-portrait-in {{ 0% {{ transform: translateY(10px) scale(0.985); opacity: 0.45; }} 100% {{ transform: translateY(0px) scale(1); opacity: 1; }} }}
      @keyframes hero-sweep {{ 0% {{ transform: translateY(0px); opacity: 0; }} 12% {{ opacity: 0.55; }} 88% {{ opacity: 0.55; }} 100% {{ transform: translateY(412px); opacity: 0; }} }}
      @keyframes hero-glare {{ 0% {{ transform: translateX(-340px); }} 52%, 100% {{ transform: translateX(460px); }} }}
      .hero-greet {{ animation: hero-type 0.9s steps(10, end) both; }}
      .hero-cursor {{ animation: hero-cursor-slide 0.9s steps(10, end) both, hero-cursor 1.05s infinite; }}
      .hero-rise {{ animation: hero-rise 0.85s var(--ease-cinematic) both; }}
      .hero-card-stagger {{ animation: hero-card-in 0.75s var(--ease-cinematic) both; }}
      .hero-portrait {{ transform-origin: 964px 180px; animation: hero-portrait-in 0.9s var(--ease-cinematic) both; }}
      .hero-beam {{ animation: hero-sweep 6.8s linear infinite; }}
      .hero-sheen {{ animation: hero-glare 5.8s ease-in-out infinite; }}
{role_css}
      @media (prefers-reduced-motion: reduce) {{
        .hero-greet {{ clip-path: none !important; }}
        .hero-cursor {{ transform: none !important; opacity: 1 !important; }}
        .hero-beam, .hero-sheen {{ display: none; }}
      }}"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="424" viewBox="0 0 1200 424" fill="none" role="img" aria-label="{esc(hcfg['aria_label'])}">
  <defs>
{base_defs("hero", 1200, 424, fonts_css, extra_css)}
    <linearGradient id="hero-name-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{t['text']}"/>
      <stop offset="32%" stop-color="{t['text']}"/>
      <stop offset="50%" stop-color="{t['secondary']}"/>
      <stop offset="68%" stop-color="{t['text']}"/>
      <stop offset="100%" stop-color="{t['text']}"/>
      <animate attributeName="x1" values="-60%;100%;-60%" dur="6.5s" begin="0s" repeatCount="indefinite"/>
      <animate attributeName="x2" values="40%;200%;40%" dur="6.5s" begin="0s" repeatCount="indefinite"/>
    </linearGradient>
    <linearGradient id="hero-scan" x1="0" y1="0" x2="1200" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t['primary']}" stop-opacity="0"/>
      <stop offset="35%" stop-color="{t['primary']}" stop-opacity="0.30"/>
      <stop offset="50%" stop-color="{t['crimson']}" stop-opacity="0.38"/>
      <stop offset="65%" stop-color="{t['primary']}" stop-opacity="0.30"/>
      <stop offset="100%" stop-color="{t['primary']}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="hero-foil" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="44%" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="50%" stop-color="{t['secondary']}" stop-opacity="0.14"/>
      <stop offset="56%" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="hero-portrait-rim" cx="50%" cy="44%" r="55%">
      <stop offset="0%" stop-color="{t['primary']}" stop-opacity="0.34"/>
      <stop offset="56%" stop-color="{t['crimson']}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{t['bg']}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="hero-portrait-fade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{t['surface_deep']}" stop-opacity="0"/>
      <stop offset="58%" stop-color="{t['surface_deep']}" stop-opacity="0"/>
      <stop offset="100%" stop-color="{t['surface_deep']}" stop-opacity="0.97"/>
    </linearGradient>
    <clipPath id="hero-name-clip">
      <rect x="42" y="98" width="690" height="92"/>
    </clipPath>
    <clipPath id="hero-portrait-clip">
      <rect x="774" y="34" width="380" height="292" rx="12"/>
    </clipPath>
    <clipPath id="hero-card-clip">
      <rect x="764" y="22" width="400" height="380" rx="16"/>
    </clipPath>
  </defs>

{shell_background("hero", 1200, 424)}
  <rect x="0" y="0" width="600" height="3" rx="1.5" fill="{t['primary']}"/>
  <rect x="600" y="0" width="600" height="3" rx="1.5" fill="{t['crimson']}"/>
  <rect class="hero-beam" x="12" y="4" width="1176" height="2" fill="url(#hero-scan)"/>

  <!-- Top Metadata Row -->
  <g transform="translate(48, 28)">
    <rect x="0" y="0" width="{degree_w}" height="30" rx="15" fill="url(#hero-glass-alt)" stroke="url(#hero-pill-stroke)" stroke-width="1.1"/>
    <circle class="beacon-halo" cx="16" cy="15" r="4.5" fill="{t['green']}" style="transform-origin:16px 15px"/>
    <circle class="beacon-dot" cx="16" cy="15" r="4.2" fill="{t['green']}"/>
    <text x="29" y="19" class="t-mono" font-size="11.5" font-weight="600" fill="{t['text']}" letter-spacing="0.8">{esc(degree_txt)}</text>
  </g>
  <g transform="translate({loc_x}, 28)">
    <rect x="0" y="0" width="{loc_w}" height="30" rx="15" fill="url(#hero-glass-alt)" stroke="{t['border']}" stroke-width="1.1"/>
    <path d="M18 10.5C15.5 10.5 13.5 12.4 13.5 14.8C13.5 17.9 18 22 18 22C18 22 22.5 17.9 22.5 14.8C22.5 12.4 20.5 10.5 18 10.5Z" stroke="{t['crimson_soft']}" stroke-width="1.5" fill="none"/>
    <circle cx="18" cy="14.6" r="1.6" fill="{t['crimson_soft']}"/>
    <text x="32" y="19" class="t-mono" font-size="11.5" font-weight="600" fill="#B8C7E0" letter-spacing="0.8">{esc(loc_txt)}</text>
  </g>
  <g transform="translate(686, 34)">
    <path d="M0 18L8 0H13L5 18H0ZM14 18L22 0H27L19 18H14ZM28 18L36 0H41L33 18H28Z" fill="{t['crimson']}"/>
  </g>

  <!-- Typed Greeting & Volumetric Display Name -->
  <text x="48" y="92" class="t-mono hero-greet" font-size="18" font-weight="600" fill="{t['secondary']}" letter-spacing="1.2">{esc(greet_txt)}</text>
  <rect class="hero-cursor" x="{cursor_x}" y="77" width="9" height="18" rx="1.5" fill="{t['crimson']}"/>

  <g clip-path="url(#hero-name-clip)">
    <text x="46" y="164" class="t-display hero-rise" font-size="66" font-weight="700" fill="{t['primary']}" fill-opacity="0.24" letter-spacing="-1.2">{esc(hcfg['name'])}</text>
    <text x="46" y="162" class="t-display hero-rise" font-size="66" font-weight="700" fill="url(#hero-name-grad)" letter-spacing="-1.2">{esc(hcfg['name'])}</text>
  </g>

  <!-- Cycling Role Headlines -->
  <g transform="translate(48, 204)">
    <rect x="0" y="-17" width="4" height="23" rx="2" fill="url(#hero-card-stroke)"/>
{role_nodes}
  </g>

  <!-- Positioning Statement (renders all configured lines) -->
{chr(10).join(intro_xml)}

  <!-- Architectural Focus Strip -->
  <line x1="48" y1="302" x2="724" y2="302" stroke="url(#hero-hairline)" stroke-width="1.1"/>
  <g transform="translate(48, 316)">
{chr(10).join(focus_xml)}
  </g>

  <!-- Location & Institution Footer -->
  <text x="48" y="394" class="t-mono c-dim" font-size="11" letter-spacing="0.4">{esc(hcfg['footer_note'])}</text>

  <!-- Right Column: Frosted Optical Portrait Card -->
  <g>
    <rect x="764" y="22" width="400" height="380" rx="16" fill="url(#hero-glass)" stroke="url(#hero-card-stroke)" stroke-width="1.5"/>
    <line x1="784" y1="23" x2="1144" y2="23" stroke="url(#hero-spec-top)" stroke-width="1"/>
    <circle cx="964" cy="172" r="144" fill="url(#hero-portrait-rim)"/>

    <g clip-path="url(#hero-portrait-clip)" class="hero-portrait">
      <image href="{photo_uri}" x="822" y="42" width="284" height="330" preserveAspectRatio="xMidYMin meet"/>
      <rect x="774" y="220" width="380" height="112" fill="url(#hero-portrait-fade)"/>
    </g>

    <g clip-path="url(#hero-card-clip)">
      <polygon class="hero-sheen" points="764,22 848,22 764,402 680,402" fill="url(#hero-foil)"/>
    </g>

    <path d="M778 48V36H790" stroke="{t['primary']}" stroke-width="2" stroke-linecap="round"/>
    <path d="M1138 36H1150V48" stroke="{t['crimson']}" stroke-width="2" stroke-linecap="round"/>
    <path d="M778 378V390H790" stroke="{t['border']}" stroke-width="2" stroke-linecap="round"/>
    <path d="M1138 390H1150V378" stroke="{t['border']}" stroke-width="2" stroke-linecap="round"/>

    <rect x="784" y="38" width="136" height="22" rx="6" fill="{t['bg']}" fill-opacity="0.86" stroke="{t['border']}" stroke-width="1"/>
    <text x="794" y="53" class="t-mono" font-size="10" font-weight="600" fill="{t['secondary']}" letter-spacing="1.0">{esc(pcard['id_badge'])}</text>

    <rect x="1032" y="38" width="114" height="22" rx="6" fill="{t['bg']}" fill-opacity="0.86" stroke="{t['border']}" stroke-width="1"/>
    <circle class="beacon-halo" cx="1044" cy="49" r="3.5" fill="{t['green']}" style="transform-origin:1044px 49px"/>
    <circle class="beacon-dot" cx="1044" cy="49" r="3.5" fill="{t['green']}"/>
    <text x="1054" y="53" class="t-mono" font-size="10" font-weight="600" fill="{t['text']}">{esc(pcard['status_badge'])}</text>

    <rect x="778" y="314" width="372" height="74" rx="12" fill="{t['surface']}" fill-opacity="0.94" stroke="{t['border']}" stroke-width="1.1"/>
    <line x1="792" y1="314.8" x2="1136" y2="314.8" stroke="url(#hero-spec-top)" stroke-width="0.9"/>
    <text x="794" y="338" class="t-mono c-dim" font-size="10">{esc(pcard['meta_top_label'])}</text>
    <text x="1134" y="338" text-anchor="end" class="t-mono" font-size="11" font-weight="600" fill="{t['text']}">{esc(pcard['meta_top_value'])}</text>
    <line x1="794" y1="350" x2="1134" y2="350" stroke="url(#hero-hairline)" stroke-width="1"/>
    <text x="794" y="372" class="t-mono c-dim" font-size="10">{esc(pcard['meta_bottom_label'])}</text>
    <text x="1134" y="372" text-anchor="end" class="t-mono" font-size="11" font-weight="600" fill="{t['secondary']}">{esc(pcard['meta_bottom_value'])}</text>
  </g>
</svg>"""


# ==============================================================================
# 2. ABOUT.SVG (1200x344)
# ==============================================================================
def about_icon_markup(kind: str, color: str) -> str:
    t = cfg.THEME
    icons = {
        "vision": f'<path d="M12 18C15.5 13 21.5 13 25 18C21.5 23 15.5 23 12 18Z" stroke="{esc(color)}" stroke-width="1.6" fill="none"/><circle cx="18.5" cy="18" r="2.3" fill="{t["secondary"]}"/>',
        "shield": f'<path d="M18.5 11.5L24.5 14V18.5C24.5 21.9 21.9 24.4 18.5 25.5C15.1 24.4 12.5 21.9 12.5 18.5V14L18.5 11.5Z" stroke="{esc(color)}" stroke-width="1.6" fill="none"/><path d="M16.2 18.5L17.8 20.1L21 16.9" stroke="{t["crimson_soft"]}" stroke-width="1.5" stroke-linecap="round"/>',
        "layers": f'<path d="M18.5 12L25 15.5L18.5 19L12 15.5L18.5 12Z" stroke="{esc(color)}" stroke-width="1.5" fill="none"/><path d="M12 18.8L18.5 22.3L25 18.8" stroke="{t["primary"]}" stroke-width="1.5" stroke-linecap="round"/><path d="M12 22L18.5 25.5L25 22" stroke="{esc(color)}" stroke-width="1.5" stroke-linecap="round"/>',
        "terminal": f'<rect x="12" y="13" width="13" height="10" rx="2.5" stroke="{esc(color)}" stroke-width="1.5" fill="none"/><path d="M15 16.5L17 18.2L15 20" stroke="{esc(color)}" stroke-width="1.4" stroke-linecap="round"/><path d="M19 20H22" stroke="{esc(color)}" stroke-width="1.4" stroke-linecap="round"/>',
        "cpu": f'<rect x="14" y="13.5" width="9" height="9" rx="1.5" stroke="{esc(color)}" stroke-width="1.5" fill="none"/><path d="M16.5 11.5V13.5M20.5 11.5V13.5M16.5 22.5V24.5M20.5 22.5V24.5M12 16H14M12 20H14M23 16H25M23 20H25" stroke="{esc(color)}" stroke-width="1.3" stroke-linecap="round"/>',
        "code": f'<path d="M16 14.5L12.5 18L16 21.5M21 14.5L24.5 18L21 21.5M19.5 13.5L17.5 22.5" stroke="{esc(color)}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
    }
    return icons.get(kind, icons["terminal"])


def build_about(fonts_css: str) -> str:
    t = cfg.THEME
    acfg = cfg.ABOUT

    extra_css = """      @keyframes ab-flow { 0% { stroke-dashoffset: 36; } 100% { stroke-dashoffset: 0; } }
      @keyframes ab-card-rise { 0% { transform: translateY(8px); opacity: 0.4; } 100% { transform: translateY(0px); opacity: 1; }}
      .ab-flow { stroke-dasharray: 5 4; animation: ab-flow 2.8s linear infinite; }
      .ab-card-anim { animation: ab-card-rise 0.75s var(--ease-cinematic) both; }"""

    eyebrow_w = max(160, round(estimate_text_px(acfg["eyebrow"], 10.0, mono=True, letter_spacing=0.9) + 46))
    coords = [(464, 24), (830, 24), (464, 184), (830, 184)]
    cards_xml = []
    for idx, ((cx0, cy0), card) in enumerate(zip(coords, acfg["cards"][:4])):
        col = card["color"]
        icon_inner = about_icon_markup(card.get("icon", "terminal"), col)
        delay = f"{0.10 * idx:.2f}s"
        cards_xml.append(
            f'  <g transform="translate({cx0}, {cy0})">\n'
            f'    <g class="ab-card-anim" style="animation-delay:{delay}">\n'
            f'      <rect x="0" y="0" width="346" height="136" rx="14" fill="url(#about-glass)" stroke="{t["border"]}" stroke-width="1.2"/>\n'
            f'      <line x1="16" y1="0.8" x2="330" y2="0.8" stroke="url(#about-spec-top)" stroke-width="1"/>\n'
            f'      <rect x="0" y="18" width="3.5" height="100" rx="1.75" fill="{esc(col)}"/>\n'
            f'      <rect x="16" y="14" width="36" height="36" rx="10" fill="{t["surface_deep"]}" stroke="{esc(col)}" stroke-opacity="0.45" stroke-width="1.1"/>\n'
            f'      <circle cx="34" cy="32" r="14" fill="{esc(col)}" fill-opacity="0.08"/>\n'
            f'      <g transform="translate(15.5, 14)">{icon_inner}</g>\n'
            f'      <text x="64" y="27" class="t-mono" font-size="10" font-weight="600" fill="{esc(col)}" letter-spacing="0.9">{esc(card["tag"])}</text>\n'
            f'      <text x="64" y="46" class="t-display" font-size="15.5" font-weight="700" fill="{t["text"]}">{esc(card["title"])}</text>\n'
            f'      <line x1="16" y1="64" x2="328" y2="64" stroke="url(#about-hairline)" stroke-width="0.9"/>\n'
            f'      <text x="16" y="86" class="t-body" font-size="12.5" fill="#DCE6F8">{esc(card["line1"])}</text>\n'
            f'      <text x="16" y="109" class="t-mono c-dim" font-size="11">{esc(card["line2"])}</text>\n'
            f'    </g>\n'
            f'  </g>'
        )

    summary = acfg["summary_lines"]
    s1 = summary[0] if len(summary) > 0 else ""
    s2 = summary[1] if len(summary) > 1 else ""
    s3 = summary[2] if len(summary) > 2 else ""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="344" viewBox="0 0 1200 344" fill="none" role="img" aria-label="{esc(acfg['aria_label'])}">
  <defs>
{base_defs("about", 1200, 344, fonts_css, extra_css)}
    <linearGradient id="about-accent-text" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{t['secondary']}"/>
      <stop offset="65%" stop-color="#8BC0FF"/>
      <stop offset="100%" stop-color="{t['crimson_soft']}"/>
    </linearGradient>
  </defs>

{shell_background("about", 1200, 344)}

  <!-- Left Panel: Engineering Thesis & Academic Profile -->
  <rect x="24" y="24" width="420" height="296" rx="14" fill="url(#about-glass)" stroke="url(#about-card-stroke)" stroke-width="1.3"/>
  <line x1="40" y1="24.8" x2="428" y2="24.8" stroke="url(#about-spec-top)" stroke-width="1"/>

  <rect x="46" y="44" width="{eyebrow_w}" height="24" rx="7" fill="{t['bg']}" stroke="url(#about-pill-stroke)" stroke-width="1"/>
  <circle class="beacon-halo" cx="60" cy="56" r="3.5" fill="{t['primary']}" style="transform-origin:60px 56px"/>
  <circle class="beacon-dot" cx="60" cy="56" r="3.5" fill="{t['primary']}"/>
  <text x="72" y="60" class="t-mono" font-size="10" font-weight="600" fill="{t['secondary']}" letter-spacing="0.9">{esc(acfg['eyebrow'])}</text>

  <text x="46" y="104" class="t-display" font-size="25.5" font-weight="700" fill="url(#about-title-grad)">{esc(acfg['title_line_1'])}</text>
  <text x="46" y="135" class="t-display" font-size="25.5" font-weight="700" fill="url(#about-accent-text)">{esc(acfg['title_line_2'])}</text>

  <text x="46" y="169" class="t-body c-muted" font-size="13">{esc(s1)}</text>
  <text x="46" y="189" class="t-body c-muted" font-size="13">{esc(s2)}</text>
  <text x="46" y="209" class="t-body c-muted" font-size="13">{esc(s3)}</text>

  <line x1="46" y1="229" x2="422" y2="229" stroke="url(#about-hairline)" stroke-width="1"/>

  <rect x="46" y="245" width="180" height="56" rx="10" fill="url(#about-glass-alt)" stroke="{t['border']}" stroke-width="1"/>
  <line x1="56" y1="245.8" x2="216" y2="245.8" stroke="url(#about-spec-top)" stroke-width="0.8"/>
  <text x="58" y="264" class="t-mono c-dim" font-size="9.5">{esc(acfg['spec_left']['label'])}</text>
  <text x="58" y="286" class="t-display" font-size="13.5" font-weight="700" fill="{esc(acfg['spec_left']['color'])}">{esc(acfg['spec_left']['value'])}</text>

  <rect x="238" y="245" width="184" height="56" rx="10" fill="url(#about-glass-alt)" stroke="{t['border']}" stroke-width="1"/>
  <line x1="248" y1="245.8" x2="412" y2="245.8" stroke="url(#about-spec-top)" stroke-width="0.8"/>
  <text x="250" y="264" class="t-mono c-dim" font-size="9.5">{esc(acfg['spec_right']['label'])}</text>
  <text x="250" y="286" class="t-display" font-size="13.5" font-weight="700" fill="{esc(acfg['spec_right']['color'])}">{esc(acfg['spec_right']['value'])}</text>

  <path class="ab-flow" d="M444 92H464M444 252H464" stroke="{t['primary']}" stroke-opacity="0.65" stroke-width="1.6"/>

  <!-- Right 2x2 Architectural Practice Grid -->
{chr(10).join(cards_xml)}
</svg>"""


# ==============================================================================
# 3. TECHNOLOGY.SVG (1200x360)
# ==============================================================================
def build_technology(fonts_css: str) -> str:
    t = cfg.THEME
    tcfg = cfg.TECHNOLOGY
    domains = tcfg["domains"][:6]

    extra_css = """      @keyframes tech-dash { 0% { stroke-dashoffset: 60; } 100% { stroke-dashoffset: 0; } }
      @keyframes tech-rise { 0% { transform: translateY(6px); opacity: 0.45; } 100% { transform: translateY(0px); opacity: 1; } }
      .tech-bus { stroke-dasharray: 7 5; animation: tech-dash 2.8s linear infinite; }
      .tech-card { animation: tech-rise 0.7s var(--ease-cinematic) both; }"""

    total_tools = sum(len(d["items"]) for d in domains)
    summary_text = f"{len(domains)} DOMAINS · {total_tools} {tcfg['summary_suffix']}"
    summary_w = max(200, round(estimate_text_px(summary_text, 10.5, mono=True, letter_spacing=0.8) + 36))
    summary_x = 1166 - summary_w

    slots = [(34, 94), (418, 94), (802, 94), (34, 218), (418, 218), (802, 218)]
    cards_xml = []
    for idx, ((cx0, cy0), dom) in enumerate(zip(slots, domains)):
        items = dom["items"]
        count_str = str(len(items))
        if dom.get("caption"):
            line1 = " · ".join(items)
            line2 = dom["caption"]
        else:
            line1, line2 = split_two_lines(items, max_chars=44)
        col = dom["color"]
        delay = f"{0.08 * idx:.2f}s"
        cards_xml.append(
            f'  <g transform="translate({cx0}, {cy0})">\n'
            f'    <g class="tech-card" style="animation-delay:{delay}">\n'
            f'      <rect x="0" y="0" width="364" height="108" rx="12" fill="url(#tech-glass)" stroke="{t["border"]}" stroke-width="1.2"/>\n'
            f'      <line x1="14" y1="0.8" x2="350" y2="0.8" stroke="url(#tech-spec-top)" stroke-width="1"/>\n'
            f'      <rect x="0" y="16" width="3.5" height="76" rx="1.75" fill="{esc(col)}"/>\n'
            f'      <text x="16" y="28" class="t-mono" font-size="11" font-weight="600" fill="{esc(col)}" letter-spacing="0.9">{esc(dom["tag"])}</text>\n'
            f'      <rect x="312" y="13" width="38" height="21" rx="6" fill="{t["bg"]}" stroke="{esc(col)}" stroke-opacity="0.4" stroke-width="1"/>\n'
            f'      <text x="331" y="27" text-anchor="middle" class="t-mono" font-size="10.5" font-weight="600" fill="{t["text"]}">{esc(count_str)}</text>\n'
            f'      <line x1="16" y1="42" x2="348" y2="42" stroke="url(#tech-hairline)" stroke-width="0.9"/>\n'
            f'      <text x="16" y="65" class="t-body" font-size="12.5" font-weight="600" fill="{t["text"]}">{esc(line1)}</text>\n'
            f'      <text x="16" y="88" class="t-body c-muted" font-size="12">{esc(line2)}</text>\n'
            f'    </g>\n'
            f'  </g>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="360" viewBox="0 0 1200 360" fill="none" role="img" aria-label="{esc(tcfg['aria_label'])}">
  <defs>
{base_defs("tech", 1200, 360, fonts_css, extra_css)}
  </defs>

{shell_background("tech", 1200, 360)}

  <!-- Header -->
  <circle class="beacon-halo" cx="42" cy="40" r="4.5" fill="{t['primary']}" style="transform-origin:42px 40px"/>
  <circle class="beacon-dot" cx="42" cy="40" r="4" fill="{t['primary']}"/>
  <text x="56" y="44" class="t-mono" font-size="11.5" font-weight="600" fill="{t['secondary']}" letter-spacing="1.1">{esc(tcfg['eyebrow'])}</text>

  <rect x="{summary_x}" y="27" width="{summary_w}" height="26" rx="8" fill="url(#tech-glass-alt)" stroke="url(#tech-pill-stroke)" stroke-width="1.1"/>
  <text x="{summary_x + summary_w // 2}" y="44" text-anchor="middle" class="t-mono" font-size="10.5" font-weight="600" fill="{t['text']}" letter-spacing="0.8">{esc(summary_text)}</text>

  <text x="34" y="75" class="t-display" font-size="18.5" font-weight="700" fill="url(#tech-title-grad)">{esc(tcfg['subtitle'])}</text>

  <!-- Animated Bus Connectors -->
  <path class="tech-bus" d="M398 148H418M782 148H802M398 272H418M782 272H802" stroke="{t['primary']}" stroke-opacity="0.72" stroke-width="1.8"/>
  <path class="tech-bus" d="M216 202V218M600 202V218M984 202V218" stroke="{t['crimson']}" stroke-opacity="0.58" stroke-width="1.6"/>

{chr(10).join(cards_xml)}

  <line x1="34" y1="340" x2="1166" y2="340" stroke="url(#tech-hairline)" stroke-width="1" opacity="0.6"/>
</svg>"""


# ==============================================================================
# 4. GITHUB-STATS.SVG (1200x372) — Hanging Lanyard Pendulum ID + Telemetry HUD
# ==============================================================================
def build_github_stats(
    fonts_css: str,
    use_raw: bool = False,
    stats_override: dict | None = None,
) -> str:
    t = cfg.THEME
    gcfg = stats_override or cfg.GITHUB_STATS
    prof = gcfg["profile"]
    photo_uri = resolve_image_uri(cfg.ASSETS["badge_photo"], cfg.ASSETS["badge_photo_thumb"], use_raw=use_raw)

    extra_css = """      @keyframes gs-drop {
        0% { transform: translateY(-24px); opacity: 0.35; }
        100% { transform: translateY(0px); opacity: 1; }
      }
      @keyframes gs-settle {
        0% { transform: rotate(4.8deg); }
        22% { transform: rotate(-3.6deg); }
        44% { transform: rotate(2.5deg); }
        66% { transform: rotate(-1.7deg); }
        84% { transform: rotate(1.2deg); }
        100% { transform: rotate(0deg); }
      }
      @keyframes gs-pendulum {
        0% { transform: rotate(0deg); }
        25% { transform: rotate(1.8deg); }
        75% { transform: rotate(-1.8deg); }
        100% { transform: rotate(0deg); }
      }
      @keyframes gs-grow { 0% { transform: scaleX(0.12); } 100% { transform: scaleX(1); } }
      @keyframes gs-glare { 0% { transform: translateX(-380px); } 56%, 100% { transform: translateX(460px); } }
      .gs-drop { animation: gs-drop 0.95s var(--ease-cinematic) 1 both; }
      .gs-settle { transform-origin: 204px 10px; animation: gs-settle 3.2s ease-out 1 both; }
      .gs-swing { transform-origin: 204px 10px; animation: gs-pendulum 5.2s ease-in-out 3.2s infinite both; }
      .gs-bar { transform-origin: 428px 190px; animation: gs-grow 1s var(--ease-cinematic) 1 both; }
      .gs-glare { animation: gs-glare 5.2s ease-in-out infinite; }
      @media (prefers-reduced-motion: reduce) {
        .gs-drop, .gs-settle, .gs-swing { transform: none !important; opacity: 1 !important; }
        .gs-glare { display: none; }
      }"""

    # Procedural crisp vector barcode across bottom of hanging ID badge
    bars_w = [3, 1, 2, 4, 1, 2, 1, 3, 2, 1, 4, 2, 1, 3, 1, 2, 2, 4, 1, 2, 3, 1, 2, 1, 3]
    bx = 58
    barcode_rects = []
    for bw in bars_w:
        barcode_rects.append(
            f'<rect x="{bx}" y="317" width="{bw}" height="15" rx="0.6" fill="#9BA9C4" fill-opacity="0.78"/>'
        )
        bx += bw + 3

    # Compute stacked proportional segments summing cleanly to 724px
    langs = gcfg["languages"][:5]
    total_coded = max(1, sum(lang["count"] for lang in langs))
    bar_total_w = 724
    seg_x = 428
    stacked_rects = []
    used_w = 0
    for idx, lang in enumerate(langs):
        if idx == len(langs) - 1:
            seg_w = max(0, bar_total_w - used_w)
        else:
            seg_w = round(bar_total_w * (lang["count"] / total_coded))
            used_w += seg_w
        stacked_rects.append(f'<rect x="{seg_x}" y="184" width="{seg_w}" height="14" fill="{esc(lang["color"])}"/>')
        seg_x += seg_w

    # 2-column individual language breakdown rows inside 724px right content width
    lang_cards = []
    for idx, lang in enumerate(langs):
        col_idx = 0 if idx < 3 else 1
        row_idx = idx if idx < 3 else idx - 3
        lx = 428 if col_idx == 0 else 806
        ly = 218 + row_idx * 34
        pct = f"{(lang['count'] / total_coded) * 100:.1f}%"
        fill_w = max(8, min(102, round(122 * (lang["count"] / total_coded))))
        lang_cards.append(
            f'  <circle cx="{lx + 6}" cy="{ly + 8}" r="7" fill="{esc(lang["color"])}" fill-opacity="0.16"/>\n'
            f'  <circle cx="{lx + 6}" cy="{ly + 8}" r="4.2" fill="{esc(lang["color"])}"/>\n'
            f'  <text x="{lx + 19}" y="{ly + 12}" class="t-body" font-size="12" font-weight="600" fill="{t["text"]}">{esc(lang["name"])}</text>\n'
            f'  <rect x="{lx + 168}" y="{ly + 4.5}" width="102" height="7" rx="3.5" fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="0.8"/>\n'
            f'  <rect x="{lx + 168}" y="{ly + 4.5}" width="{fill_w}" height="7" rx="3.5" fill="{esc(lang["color"])}"/>\n'
            f'  <text x="{lx + 346}" y="{ly + 12}" text-anchor="end" class="t-mono c-muted" font-size="11">{lang["count"]} ({pct})</text>'
        )

    lang_cards.append(
        f'  <rect x="806" y="280" width="346" height="30" rx="8" fill="url(#gstats-glass-alt)" stroke="{t["border"]}" stroke-width="1"/>\n'
        f'  <line x1="818" y1="280.8" x2="1140" y2="280.8" stroke="url(#gstats-spec-top)" stroke-width="0.8"/>\n'
        f'  <text x="820" y="299" class="t-mono c-dim" font-size="10">{esc(gcfg["coverage_label"])}</text>\n'
        f'  <text x="1140" y="299" text-anchor="end" class="t-mono" font-size="11" font-weight="600" fill="{t["secondary"]}">{total_coded} / {gcfg["total_repos"]} REPOS</text>'
    )

    # Repo total boxes inside hanging ID card (3 tiles across 292px: x=58..350)
    repo_boxes_xml = []
    for i, rb in enumerate(gcfg["repo_totals"][:3]):
        rx0 = 58 + i * 100
        col = rb["color"]
        repo_boxes_xml.append(
            f'        <rect x="{rx0}" y="236" width="92" height="52" rx="9" fill="url(#gstats-glass-alt)" stroke="{t["border"]}" stroke-width="1"/>\n'
            f'        <rect x="{rx0 + 10}" y="236" width="24" height="2" rx="1" fill="{esc(col)}"/>\n'
            f'        <text x="{rx0 + 10}" y="253" class="t-mono c-dim" font-size="8.5" letter-spacing="0.4">{esc(rb["label"])}</text>\n'
            f'        <text x="{rx0 + 10}" y="278" class="t-display" font-size="20" font-weight="700" fill="{esc(col)}">{esc(rb["value"])}</text>'
        )

    # KPI Bento strip on right card (5 boxes across 724px)
    kpis = gcfg["kpis"][:5]
    kpi_gap = 10
    kpi_w = (724 - kpi_gap * (max(1, len(kpis)) - 1)) // max(1, len(kpis))
    kpi_xml = []
    for i, kp in enumerate(kpis):
        kx = 428 + i * (kpi_w + kpi_gap)
        col = kp["color"]
        kpi_xml.append(
            f'  <rect x="{kx}" y="74" width="{kpi_w}" height="70" rx="10" fill="url(#gstats-glass-alt)" stroke="{t["border"]}" stroke-width="1.1"/>\n'
            f'  <line x1="{kx + 10}" y1="74.8" x2="{kx + kpi_w - 10}" y2="74.8" stroke="url(#gstats-spec-top)" stroke-width="0.9"/>\n'
            f'  <rect x="{kx + 14}" y="74" width="32" height="2.5" rx="1.25" fill="{esc(col)}"/>\n'
            f'  <text x="{kx + 14}" y="97" class="t-mono c-dim" font-size="9.5" letter-spacing="0.6">{esc(kp["label"])}</text>\n'
            f'  <text x="{kx + 14}" y="128" class="t-display" font-size="24" font-weight="700" fill="{esc(col)}">{esc(kp["value"])}</text>'
        )

    snap_w = max(124, round(estimate_text_px(prof["snapshot_label"], 9.0, mono=True) + 20))
    status_w = max(106, round(estimate_text_px(gcfg["status_badge"], 10.0, mono=True) + 38))
    status_x = 1152 - status_w

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="372" viewBox="0 0 1200 372" fill="none" role="img" aria-label="{esc(gcfg['aria_label'])}">
  <defs>
{base_defs("gstats", 1200, 372, fonts_css, extra_css)}
    <linearGradient id="gstats-bar-gloss" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.28"/>
      <stop offset="55%" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0.20"/>
    </linearGradient>
    <linearGradient id="gstats-clasp" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#475569"/>
      <stop offset="35%" stop-color="#CBD5E1"/>
      <stop offset="70%" stop-color="#64748B"/>
      <stop offset="100%" stop-color="#334155"/>
    </linearGradient>
    <linearGradient id="gstats-foil" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="44%" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="50%" stop-color="{t['secondary']}" stop-opacity="0.16"/>
      <stop offset="56%" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="gs-badge-clip">
      <rect x="40" y="60" width="328" height="290" rx="16"/>
    </clipPath>
    <clipPath id="gs-photo-clip">
      <rect x="58" y="92" width="102" height="122" rx="10"/>
    </clipPath>
    <clipPath id="gs-stack-clip">
      <rect x="428" y="184" width="724" height="14" rx="7"/>
    </clipPath>
  </defs>

{shell_background("gstats", 1200, 372)}

  <!-- Left Panel: Hanging Lanyard Pendulum Developer ID Badge -->
  <g class="gs-drop">
    <g class="gs-settle">
      <g class="gs-swing">
        <!-- Lanyard Strap & Metallic Swivel Clasp -->
        <rect x="184" y="0" width="40" height="34" fill="#132038"/>
        <rect x="188" y="0" width="4" height="34" fill="{t['primary']}"/>
        <rect x="216" y="0" width="4" height="34" fill="{t['crimson']}"/>
        <line x1="204" y1="2" x2="204" y2="30" stroke="{t['border']}" stroke-dasharray="2 2" stroke-width="1"/>
        <rect x="176" y="30" width="56" height="16" rx="5" fill="url(#gstats-clasp)" stroke="#94A3B8" stroke-width="1.1"/>
        <rect x="192" y="44" width="24" height="16" rx="4" fill="#334155" stroke="#94A3B8" stroke-width="1"/>

        <!-- Badge Card Body -->
        <rect x="40" y="60" width="328" height="290" rx="16" fill="url(#gstats-glass)" stroke="url(#gstats-card-stroke)" stroke-width="1.5"/>
        <line x1="56" y1="60.8" x2="352" y2="60.8" stroke="url(#gstats-spec-top)" stroke-width="1"/>
        <rect x="180" y="71" width="48" height="8" rx="4" fill="{t['bg']}" stroke="{t['border']}" stroke-width="1"/>

        <!-- Framed Portrait -->
        <rect x="58" y="92" width="102" height="122" rx="10" fill="{t['bg']}" stroke="url(#gstats-card-stroke)" stroke-width="1.2"/>
        <g clip-path="url(#gs-photo-clip)">
          <image href="{photo_uri}" x="58" y="94" width="102" height="120" preserveAspectRatio="xMidYMin slice"/>
        </g>

        <!-- EMV Chip & Header Metadata -->
        <rect x="174" y="92" width="32" height="22" rx="5" fill="#D4AF37" fill-opacity="0.22" stroke="#EAB308" stroke-width="1"/>
        <path d="M174 103H206M190 92V114" stroke="#EAB308" stroke-opacity="0.7" stroke-width="0.9"/>
        <text x="215" y="106" class="t-mono" font-size="9.5" font-weight="600" fill="{t['secondary']}" letter-spacing="0.6">{esc(prof['eyebrow'])}</text>

        <text x="174" y="137" class="t-display" font-size="19.5" font-weight="700" fill="url(#gstats-title-grad)">{esc(prof['name'])}</text>
        <text x="174" y="156" class="t-mono" font-size="11" fill="{t['crimson_soft']}">{esc(prof['handle'])}</text>
        <text x="174" y="174" class="t-body c-muted" font-size="11">{esc(prof['location'])}</text>
        <rect x="174" y="186" width="{snap_w}" height="22" rx="6" fill="{t['bg']}" stroke="{t['border']}" stroke-width="1"/>
        <text x="{174 + snap_w // 2}" y="200.5" text-anchor="middle" class="t-mono c-dim" font-size="9">{esc(prof['snapshot_label'])}</text>

        <line x1="58" y1="225" x2="350" y2="225" stroke="url(#gstats-hairline)" stroke-width="1"/>

{chr(10).join(repo_boxes_xml)}

        <text x="58" y="305" class="t-mono c-dim" font-size="9">{esc(prof['cohort_note'])}</text>
        {"".join(barcode_rects)}
        <text x="350" y="328" text-anchor="end" class="t-mono c-dim" font-size="10">B127-ALOK</text>

        <!-- Foil Light Sweep Across Swinging ID Card -->
        <g clip-path="url(#gs-badge-clip)">
          <polygon class="gs-glare" points="40,60 120,60 40,350 -40,350" fill="url(#gstats-foil)"/>
        </g>
      </g>
    </g>
  </g>

  <!-- Right Panel: Telemetry Matrix & Language Proportions -->
  <rect x="404" y="24" width="772" height="324" rx="14" fill="url(#gstats-glass)" stroke="{t['border']}" stroke-width="1.2"/>
  <line x1="420" y1="24.8" x2="1160" y2="24.8" stroke="url(#gstats-spec-top)" stroke-width="1"/>

  <text x="428" y="54" class="t-mono" font-size="11.5" font-weight="600" fill="{t['secondary']}" letter-spacing="1.1">{esc(gcfg['right_header'])}</text>
  <rect x="{status_x}" y="37" width="{status_w}" height="24" rx="7" fill="{t['bg']}" stroke="{t['border']}" stroke-width="1"/>
  <circle class="beacon-halo" cx="{status_x + 14}" cy="49" r="3.5" fill="{t['green']}" style="transform-origin:{status_x + 14}px 49px"/>
  <circle class="beacon-dot" cx="{status_x + 14}" cy="49" r="3.5" fill="{t['green']}"/>
  <text x="{status_x + 24}" y="53" class="t-mono" font-size="10" font-weight="600" fill="{t['green']}">{esc(gcfg['status_badge'])}</text>

{chr(10).join(kpi_xml)}

  <text x="428" y="172" class="t-mono c-muted" font-size="10.5" font-weight="600" letter-spacing="0.9">PRIMARY LANGUAGE DISTRIBUTION ({total_coded} CODED REPOS)</text>
  <rect x="428" y="184" width="724" height="14" rx="7" fill="{t['bg']}" stroke="{t['border']}" stroke-width="0.8"/>
  <g clip-path="url(#gs-stack-clip)" class="gs-bar">
    {"".join(stacked_rects)}
    <rect x="428" y="184" width="724" height="14" fill="url(#gstats-bar-gloss)"/>
  </g>

{chr(10).join(lang_cards)}
</svg>"""


# ==============================================================================
# 5. CONNECT.SVG (1200x268)
# ==============================================================================
def build_connect(fonts_css: str) -> str:
    t = cfg.THEME
    ccfg = cfg.CONNECT
    char_uri = resolve_image_uri(cfg.ASSETS["connect_character"], use_raw=True)

    extra_css = """      @keyframes conn-enter { 0% { transform: translateX(-12px); opacity: 0.4; } 100% { transform: translateX(0px); opacity: 1; } }
      @keyframes conn-wave { 0%, 100% { opacity: 0.25; transform: translateX(0px); } 50% { opacity: 1; transform: translateX(2px); } }
      @keyframes conn-drop { 0%, 100% { transform: translateY(0px); opacity: 0.7; } 50% { transform: translateY(4px); opacity: 1; } }
      .conn-char { animation: conn-enter 0.85s var(--ease-cinematic) both; }
      .conn-w1 { animation: conn-wave 2.4s ease-in-out infinite; }
      .conn-w2 { animation: conn-wave 2.4s 0.35s ease-in-out infinite; }
      .conn-w3 { animation: conn-wave 2.4s 0.7s ease-in-out infinite; }
      .conn-down { animation: conn-drop 2s ease-in-out infinite; }"""

    badge_txt = ccfg["character_badge"]
    badge_w = min(224, max(132, round(estimate_text_px(badge_txt, 10.0, mono=True, letter_spacing=0.8) + 28)))
    badge_x = 148 - badge_w // 2
    status_w = max(160, round(estimate_text_px(ccfg["status_badge"], 10.0, mono=True, letter_spacing=0.8) + 46))
    p1 = ccfg["pitch_lines"][0] if len(ccfg["pitch_lines"]) > 0 else ""
    p2 = ccfg["pitch_lines"][1] if len(ccfg["pitch_lines"]) > 1 else ""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="268" viewBox="0 0 1200 268" fill="none" role="img" aria-label="{esc(ccfg['aria_label'])}">
  <defs>
{base_defs("conn", 1200, 268, fonts_css, extra_css)}
    <radialGradient id="conn-char-halo" cx="50%" cy="48%" r="54%">
      <stop offset="0%" stop-color="{t['primary']}" stop-opacity="0.34"/>
      <stop offset="55%" stop-color="{t['crimson']}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{t['bg']}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="conn-floor-fade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{t['bg']}" stop-opacity="0"/>
      <stop offset="70%" stop-color="{t['bg']}" stop-opacity="0"/>
      <stop offset="100%" stop-color="{t['bg']}" stop-opacity="0.96"/>
    </linearGradient>
    <clipPath id="conn-char-clip">
      <rect x="24" y="20" width="248" height="228" rx="14"/>
    </clipPath>
  </defs>

{shell_background("conn", 1200, 268)}

  <!-- Left Developer Illustration -->
  <rect x="24" y="20" width="248" height="228" rx="14" fill="url(#conn-glass)" stroke="url(#conn-card-stroke)" stroke-width="1.3"/>
  <line x1="38" y1="20.8" x2="258" y2="20.8" stroke="url(#conn-spec-top)" stroke-width="1"/>
  <circle cx="148" cy="132" r="108" fill="url(#conn-char-halo)"/>
  <g clip-path="url(#conn-char-clip)" class="conn-char">
    <image href="{char_uri}" x="38" y="28" width="220" height="214" preserveAspectRatio="xMidYMid meet"/>
    <rect x="24" y="164" width="248" height="84" fill="url(#conn-floor-fade)"/>
  </g>
  <rect x="{badge_x}" y="214" width="{badge_w}" height="22" rx="6" fill="{t['bg']}" fill-opacity="0.92" stroke="url(#conn-pill-stroke)" stroke-width="1"/>
  <text x="148" y="229" text-anchor="middle" class="t-mono" font-size="10" font-weight="600" fill="{t['secondary']}" letter-spacing="0.8">{esc(badge_txt)}</text>

  <!-- Pointing Directional Signal Chevrons -->
  <g transform="translate(286, 116)">
    <path class="conn-w1" d="M0 0L9 16L0 32" stroke="{t['primary']}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    <path class="conn-w2" d="M10 0L19 16L10 32" stroke="{t['secondary']}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    <path class="conn-w3" d="M20 0L29 16L20 32" stroke="{t['crimson']}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  </g>

  <!-- Right Invitation Panel -->
  <rect x="330" y="20" width="846" height="228" rx="14" fill="url(#conn-glass)" stroke="{t['border']}" stroke-width="1.2"/>
  <line x1="348" y1="20.8" x2="1158" y2="20.8" stroke="url(#conn-spec-top)" stroke-width="1"/>

  <rect x="358" y="42" width="{status_w}" height="24" rx="7" fill="{t['bg']}" stroke="{t['border']}" stroke-width="1"/>
  <circle class="beacon-halo" cx="372" cy="54" r="3.5" fill="{t['green']}" style="transform-origin:372px 54px"/>
  <circle class="beacon-dot" cx="372" cy="54" r="3.5" fill="{t['green']}"/>
  <text x="384" y="58" class="t-mono" font-size="10" font-weight="600" fill="{t['green']}" letter-spacing="0.8">{esc(ccfg['status_badge'])}</text>

  <text x="1146" y="58" text-anchor="end" class="t-mono c-dim" font-size="10.5">{esc(ccfg['location_text'])}</text>

  <text x="358" y="102" class="t-display" font-size="30" font-weight="700" fill="url(#conn-title-grad)">{esc(ccfg['headline'])}</text>
  <text x="358" y="132" class="t-body c-muted" font-size="14.5">{esc(p1)}</text>
  <text x="358" y="153" class="t-body c-muted" font-size="14.5">{esc(p2)}</text>

  <line x1="358" y1="173" x2="1146" y2="173" stroke="url(#conn-hairline)" stroke-width="1"/>

  <text x="358" y="199" class="t-mono" font-size="11" font-weight="600" fill="{t['secondary']}" letter-spacing="0.9">{esc(ccfg['domains_line'])}</text>

  <g class="conn-down">
    <path d="M358 215L364 222L370 215" stroke="{t['crimson']}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
  <text x="380" y="223" class="t-mono c-dim" font-size="10.5" letter-spacing="0.6">{esc(ccfg['cta_hint'])}</text>
</svg>"""


# ==============================================================================
# CLI ENTRYPOINT & VALIDATION
# ==============================================================================
BUILDERS = {
    "hero": ("hero.svg", lambda fcss, raw, _stats: build_hero(fcss, use_raw=raw)),
    "about": ("about.svg", lambda fcss, raw, _stats: build_about(fcss)),
    "technology": ("technology.svg", lambda fcss, raw, _stats: build_technology(fcss)),
    "github-stats": ("github-stats.svg", lambda fcss, raw, stats: build_github_stats(fcss, use_raw=raw, stats_override=stats)),
    "connect": ("connect.svg", lambda fcss, raw, _stats: build_connect(fcss)),
}


def validate_svg(svg_text: str, filename: str) -> None:
    stripped = svg_text.replace("http://www.w3.org/2000/svg", "")
    if "http://" in stripped or "https://" in stripped:
        raise ValueError(f"{filename} contains an external URL; keep fonts/images self-contained.")
    ET.fromstring(svg_text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate customizable SVG banners for assets/images/.")
    parser.add_argument(
        "--only",
        nargs="+",
        choices=list(BUILDERS.keys()),
        help="Generate only selected SVGs (default: all 5).",
    )
    parser.add_argument(
        "--out",
        default=cfg.OUTPUT_DIR,
        help=f"Output directory relative to repo root or absolute (default: {cfg.OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--raw-photos",
        action="store_true",
        help="Embed full-resolution assets/id.png instead of compressed thumbnails.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip live GitHub API fetching and use static values in config.py.",
    )
    parser.add_argument(
        "--username",
        default=None,
        help="Override GitHub username when fetching live telemetry.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render and XML-validate SVGs in memory without writing files.",
    )
    args = parser.parse_args()

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir

    targets = args.only or list(BUILDERS.keys())
    fonts_css = load_fonts_css()

    live_stats = None
    if "github-stats" in targets and not args.offline:
        live_stats, synced = fetch_live_github_stats(cfg.GITHUB_STATS, args.username)
        if synced:
            print(
                f"Synced live GitHub metrics for {live_stats['profile']['handle']}: "
                f"{live_stats['total_repos']} repos, {live_stats['kpis'][0]['value']} contribs, "
                f"{live_stats['kpis'][1]['value']} commits, {live_stats['kpis'][3]['value']} streak"
            )
        else:
            print("Using static GITHUB_STATS values from config.py (live fetch unavailable).")

    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    for key in targets:
        filename, builder = BUILDERS[key]
        svg_text = builder(fonts_css, args.raw_photos, live_stats)
        validate_svg(svg_text, filename)
        if args.dry_run:
            print(f"[dry-run] {filename}: {len(svg_text):,} bytes (XML OK)")
        else:
            dest = out_dir / filename
            dest.write_text(svg_text, encoding="utf-8", newline="\n")
            print(f"Generated {dest.relative_to(REPO_ROOT)}: {len(svg_text):,} bytes (XML OK)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
