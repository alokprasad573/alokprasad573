"""
Customizable configuration for generating all SVG visuals in `assets/images/`.

Edit any text, color, metric, domain tool list, or image path below, then run:
    python scripts/generate_svgs.py
"""

from __future__ import annotations

# ------------------------------------------------------------------------------
# 1. PATHS (relative to repository root)
# ------------------------------------------------------------------------------
OUTPUT_DIR = "assets/images"

ASSETS = {
    "fonts_css": "scripts/assets/fonts_bundle.css",
    "hero_photo": "assets/id.png",
    "hero_photo_thumb": "scripts/assets/portrait_hero_520.png",
    "badge_photo": "assets/id.png",
    "badge_photo_thumb": "scripts/assets/portrait_badge_260.png",
    "connect_character": "assets/alok-developer-character.png",
}

# ------------------------------------------------------------------------------
# 2. COLOR PALETTE & THEME TOKENS
# ------------------------------------------------------------------------------
THEME = {
    "bg": "#070B16",
    "bg_mid": "#0A1124",
    "surface": "#101A2C",
    "surface_alt": "#142138",
    "surface_deep": "#0B1325",
    "border": "#25344D",
    "border_subtle": "#1E2D45",
    "primary": "#247BFF",
    "secondary": "#5EA0FF",
    "crimson": "#FF354F",
    "crimson_soft": "#FF6B7F",
    "green": "#22C55E",
    "text": "#F5F7FF",
    "text_soft": "#D2DCF0",
    "muted": "#9BA9C4",
    "muted_dim": "#7D8FAD",
}

# ------------------------------------------------------------------------------
# 3. HERO BANNER (`assets/images/hero.svg`)
# ------------------------------------------------------------------------------
HERO = {
    "aria_label": "Alok Prasad - Software Engineer, Computer Science Engineering, AI/ML",
    "degree_badge": "B.TECH COMPUTER SCIENCE · 2023–2027",
    "location_badge": "INDIA",
    "greeting": "Hello, I'm",
    "name": "ALOK PRASAD",
    # Supports 1 or more rotating headlines (keyframe timings scale automatically)
    "roles": [
        {"text": "Software Engineer | Full Stack Developer | AI/ML", "color": "#F5F7FF"},
        {"text": "Full-Stack Developer · Next.js, TypeScript & FastAPI", "color": "#5EA0FF"},
        {"text": "Applied Computer Vision · Browser ONNX & MediaPipe", "color": "#F5F7FF"},
        {"text": "Secure Software Systems · Cloud & Container Engineering", "color": "#FF6B7F"},
    ],
    "intro_lines": [
        "I design and build intelligent web software built for everyday use.",
        "Bridging clean software engineering with modern web frameworks and applied AI.",
        "Crafting reliable, AI-driven products from the ground up.",
    ],
    "focus_cards": [
        {"label": "FOCUS 01", "title": "On-Device CV & Edge ML", "color": "#5EA0FF"},
        {"label": "FOCUS 02", "title": "Security & RLS Boundaries", "color": "#FF6B7F"},
        {"label": "FOCUS 03", "title": "Typed Full-Stack Systems", "color": "#22C55E"},
    ],
    "footer_note": "RUNGTA COLLEGE OF ENGINEERING, BHILAI · 2023–2027 · B-127-ARCHIVE",
    "portrait_card": {
        "id_badge": "ID // ALOK-01",
        "status_badge": "ACTIVE",
        "meta_top_label": "CORE DOMAINS",
        "meta_top_value": "Full-Stack · AI/ML · Security",
        "meta_bottom_label": "PRIMARY STACK",
        "meta_bottom_value": "TypeScript · Python · Next.js",
    },
}

# ------------------------------------------------------------------------------
# 4. ABOUT BANNER (`assets/images/about.svg`)
# ------------------------------------------------------------------------------
# Supported card icon keys: "vision", "shield", "layers", "terminal", "cpu", "code"
ABOUT = {
    "aria_label": "About Alok Prasad - Core Engineering Approach and Architectural Focus",
    "eyebrow": "ENGINEERING APPROACH",
    "title_line_1": "Practical Systems.",
    "title_line_2": "Applied Intelligence.",
    "summary_lines": [
        "Designing full-stack software where browser-side",
        "ML meets explicit data boundaries, idempotent",
        "workflows, and verifiable test suites.",
    ],
    "spec_left": {
        "label": "DEGREE TRACK",
        "value": "B.Tech CSE",
        "color": "#F5F7FF",
    },
    "spec_right": {
        "label": "INSTITUTION · COHORT",
        "value": "Rungta COE · 2023–27",
        "color": "#FF6B7F",
    },
    "cards": [
        {
            "tag": "01 // CLIENT-SIDE VISION",
            "title": "In-Browser ML & Vision",
            "line1": "MediaPipe landmarks, ONNX Runtime Web & TF.js",
            "line2": "Raw imagery remains strictly in client RAM",
            "color": "#247BFF",
            "icon": "vision",
        },
        {
            "tag": "02 // SECURITY ENGINEERING",
            "title": "Tenant & Runtime Defense",
            "line1": "PostgreSQL 7-table RLS, SSRF socket IP pinning",
            "line2": "Argon2id hashing & EWMA + ML DDoS filters",
            "color": "#FF354F",
            "icon": "shield",
        },
        {
            "tag": "03 // PRODUCT ARCHITECTURE",
            "title": "Typed Full-Stack APIs",
            "line1": "Next.js App Router, React 19, FastAPI & Express",
            "line2": "Prisma, Mongoose, Supabase & Redis pipelines",
            "color": "#5EA0FF",
            "icon": "layers",
        },
        {
            "tag": "04 // CLOUD & VERIFICATION",
            "title": "Resilient Containers & CI",
            "line1": "AWS EC2 & S3, NGINX, Docker multi-stage builds",
            "line2": "Vitest boundaries, Playwright E2E & GH Actions",
            "color": "#22C55E",
            "icon": "terminal",
        },
    ],
}

# ------------------------------------------------------------------------------
# 5. TECHNOLOGY ARCHITECTURE BANNER (`assets/images/technology.svg`)
# ------------------------------------------------------------------------------
# Tool counts per card and the top summary badge ("6 DOMAINS · N VERIFIED TOOLS")
# are calculated automatically from the items lists below.
TECHNOLOGY = {
    "aria_label": "Technology Architecture Blueprint - 6 Domains and Verified Tools",
    "eyebrow": "TECH STACK // PRODUCTION ARCHITECTURE MATRIX",
    "subtitle": "End-to-End Engineering Layers Across Repositories",
    "summary_suffix": "VERIFIED TOOLS",
    "domains": [
        {
            "tag": "01 · PROGRAMMING",
            "color": "#247BFF",
            "items": ["JavaScript", "Python", "TypeScript", "C++"],
            "caption": "Core web, systems & ML runtimes",
        },
        {
            "tag": "02 · FRONTEND",
            "color": "#5EA0FF",
            "items": ["React", "Next.js", "Tailwind CSS", "HTML5", "Lucide React", "Google Fonts", "Vercel"],
            "caption": None,
        },
        {
            "tag": "03 · BACKEND & API",
            "color": "#22C55E",
            "items": ["Node.js", "Express.js", "FastAPI", "NGINX", "EJS", "Clerk", "Nodemon", "Render", "AWS EC2"],
            "caption": None,
        },
        {
            "tag": "04 · DATABASE",
            "color": "#6CAE3E",
            "items": ["PostgreSQL", "Prisma", "Supabase", "AWS S3", "MongoDB", "Mongoose", "Redis"],
            "caption": None,
        },
        {
            "tag": "05 · DEVOPS & QA",
            "color": "#F5F7FF",
            "items": ["Docker", "GitHub Actions", "Linux", "Git", "GitHub", "Jest"],
            "caption": None,
        },
        {
            "tag": "06 · AI / ML & CV",
            "color": "#FF354F",
            "items": ["PyTorch", "TensorFlow", "ONNX Runtime", "MediaPipe", "scikit-learn", "LangChain", "Pandas", "NumPy"],
            "caption": None,
        },
    ],
}

# ------------------------------------------------------------------------------
# 6. GITHUB STATS BANNER (`assets/images/github-stats.svg`)
# ------------------------------------------------------------------------------
# Stacked proportional bar widths & percentages are computed dynamically from
# the language repo counts below.
GITHUB_STATS = {
    "aria_label": "GitHub Telemetry Command HUD for alokprasad573",
    "profile": {
        "eyebrow": "GITHUB // VERIFIED",
        "name": "ALOK PRASAD",
        "handle": "@alokprasad573",
        "location": "Bhilai, India",
        "snapshot_label": "SNAPSHOT · 2026-11-26",
        "cohort_note": "COMPUTER SCIENCE ENG. · B.TECH 2023–2027",
    },
    "right_header": "GITHUB ANALYTICS // ACTIVITY TELEMETRY",
    "status_badge": "API VERIFIED",
    "total_repos": 69,
    "repo_totals": [
        {"label": "REPOS", "value": "69", "color": "#F5F7FF"},
        {"label": "ORIGINAL", "value": "67", "color": "#5EA0FF"},
        {"label": "STARS", "value": "9", "color": "#22C55E"},
    ],
    "kpis": [
        {"label": "CONTRIBUTIONS", "value": "1,255", "color": "#F5F7FF"},
        {"label": "1Y COMMITS", "value": "353", "color": "#5EA0FF"},
        {"label": "PULL REQUESTS", "value": "23", "color": "#22C55E"},
        {"label": "CUR. STREAK", "value": "7d", "color": "#FF6B7F"},
        {"label": "BEST STREAK", "value": "16d", "color": "#F5F7FF"},
    ],
    "languages": [
        {"name": "JavaScript", "count": 18, "color": "#F7DF1E"},
        {"name": "Jupyter Notebook", "count": 16, "color": "#F37626"},
        {"name": "Python", "count": 11, "color": "#3776AB"},
        {"name": "TypeScript", "count": 8, "color": "#247BFF"},
        {"name": "EJS / HTML / Kotlin", "count": 10, "color": "#FF6B7F"},
    ],
    "coverage_label": "CODED ARCHIVE COVERAGE",
}

# ------------------------------------------------------------------------------
# 7. CONNECT BANNER (`assets/images/connect.svg`)
# ------------------------------------------------------------------------------
CONNECT = {
    "aria_label": "Connect with Alok Prasad - Collaboration & Engineering Inquiries",
    "character_badge": "CONNECT WITH ME ALOK",
    "status_badge": "OPEN TO SWE & AI/ML ROLES",
    "location_text": "BHILAI, INDIA · B.TECH 2023–2027",
    "headline": "Let's Build Practical Software Systems",
    "pitch_lines": [
        "Available for software engineering internships, applied AI/ML & computer vision",
        "pipelines, and resilient full-stack security architectures.",
    ],
    "domains_line": "DOMAINS: FULL-STACK WEB · APPLIED CV / ML · SECURITY SYSTEMS",
    "cta_hint": "CHOOSE A VERIFIED CHANNEL BELOW: GITHUB · LINKEDIN · INSTAGRAM · EMAIL · PORTFOLIO",
}
