#!/usr/bin/env python3
"""
Generates the custom SVG assets for the TwanstCodess GitHub profile.

Edit CONFIG / TOOLKIT / LOOP below, then run from this folder:

    pip install fonttools brotli uharfbuzz
    python3 generate.py

The SVGs are written to ../assets/. Fonts are subset and embedded inside
each SVG, so they look identical on every computer (GitHub blocks external
fonts inside SVG images).
"""
import utils.session
import base64
import io
import json
from html import escape
from pathlib import Path

import uharfbuzz as hb
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "assets"
CACHE = HERE / ".cache"

# --------------------------------------------------------------------------
# Content
# --------------------------------------------------------------------------
CONFIG = {
    "first_name": "Twana",
    "last_name": "Muhamad",
    "tagline": [
        "I build software, teach it to think, then try",
        "to break it before anyone else can.",
    ],
}

# Palette — three discipline colours carry meaning everywhere:
# amber = build (full-stack), violet = think (AI), red = break (bug hunting)
INK = "#161B36"
PANEL = "#20264A"
RULE = "#343C6E"
PAPER = "#F1F2FA"
MIST = "#9CA4CC"
BUILD = "#FFB547"
THINK = "#A790FF"
BREAK = "#FF5F5A"

ROLES = [
    ("build", BUILD, "Full-stack developer"),
    ("think", THINK, "AI developer"),
    ("break", BREAK, "Bug hunter"),
]

LOOP = [
    ("build", BUILD, "Build", "Full-stack developer",
     "Complete products from database to interface: web apps with Laravel, "
     "Vue and Angular, mobile apps with Flutter, desktop tools in C#."),
    ("think", THINK, "Think", "AI developer",
     "Features that learn and see: computer vision with OpenCV, "
     "machine-learning models in Python and assistants built on large "
     "language models."),
    ("break", BREAK, "Break", "Bug hunter",
     "Hunting vulnerabilities in web apps and APIs before attackers do, "
     "testing against the OWASP Top 10 and reporting through responsible "
     "disclosure."),
]
LOOP_RETURN = "Every bug I find makes the next build stronger."

# (name, simple-icons slug or None, fallback monogram)
TOOLKIT = [
    ("build", BUILD, "Build", "full-stack", [
        ("Languages", [
            ("JavaScript", "javascript"), ("TypeScript", "typescript"),
            ("PHP", "php"), ("C#", None, "C#"), ("C++", "cplusplus"),
            ("Java", "openjdk"), ("Dart", "dart"), ("Python", "python"),
            ("Ruby", "ruby"), ("Perl", "perl"),
        ]),
        ("Front end", [
            ("HTML5", "html5"), ("CSS3", "css"), ("Sass", "sass"),
            ("Tailwind CSS", "tailwindcss"), ("Bootstrap", "bootstrap"),
            ("Chakra UI", "chakraui"), ("MUI", "mui"), ("Vue.js", "vuedotjs"),
            ("Angular", "angular"), ("AngularJS", "angular"),
            ("jQuery", "jquery"), ("Chart.js", "chartdotjs"),
        ]),
        ("Back end", [
            ("Laravel", "laravel"), ("Meteor.js", "meteor"),
            ("Apache", "apache"),
        ]),
        ("Mobile & desktop", [
            ("Flutter", "flutter"), ("Xamarin", None, "Xa"),
        ]),
        ("Databases", [
            ("MySQL", "mysql"), ("MariaDB", "mariadb"), ("SQLite", "sqlite"),
            ("SQL Server", None, "SQL"),
        ]),
    ]),
    ("think", THINK, "Think", "AI", [
        ("Models", [
            ("Python", "python"), ("TensorFlow", "tensorflow"),
            ("PyTorch", "pytorch"), ("scikit-learn", "scikitlearn"),
            ("Jupyter", "jupyter"),
        ]),
        ("Vision & LLMs", [
            ("OpenCV", "opencv"), ("Hugging Face", "huggingface"),
            ("LangChain", "langchain"), ("OpenAI API", None, "AI"),
        ]),
    ]),
    ("break", BREAK, "Break", "security", [
        ("Recon & testing", [
            ("Kali Linux", "kalilinux"), ("Nmap", None, "Nm"),
            ("Burp Suite", "burpsuite"), ("Wireshark", "wireshark"),
            ("Metasploit", "metasploit"), ("OWASP Top 10", "owasp"),
        ]),
        ("Scripting & privacy", [
            ("Bash", "gnubash"), ("PowerShell", None, ">_"),
            ("Tor", "torproject"),
        ]),
    ]),
    ("tools", MIST, "Tools", "design & workflow", [
        ("Design", [
            ("Figma", "figma"), ("Adobe XD", None, "Xd"),
            ("Photoshop", None, "Ps"), ("Illustrator", None, "Ai"),
            ("Canva", None, "Ca"),
        ]),
        ("Workflow", [
            ("Git", "git"), ("Postman", "postman"), ("npm", "npm"),
            ("Yarn", "yarn"), ("Arduino", "arduino"),
        ]),
    ]),
]

BUTTONS = [
    ("btn-youtube", "YouTube", "youtube"),
    ("btn-tiktok", "TikTok", "tiktok"),
    ("btn-instagram", "Instagram", "instagram"),
    ("btn-facebook", "Facebook", "facebook"),
]

# --------------------------------------------------------------------------
# Fonts
# --------------------------------------------------------------------------
BRICOLAGE = HERE / "fonts" / "BricolageGrotesque[opsz,wdth,wght].ttf"
MARTIAN = HERE / "fonts" / "MartianMono[wdth,wght].ttf"
FONT_SPECS = {
    "display": (BRICOLAGE, dict(opsz=96, wdth=75, wght=800), 800),
    "semi": (BRICOLAGE, dict(opsz=14, wdth=100, wght=600), 600),
    "text": (BRICOLAGE, dict(opsz=14, wdth=100, wght=400), 400),
    "mono": (MARTIAN, dict(wdth=87.5, wght=600), 600),
}
STATIC, HBFONT, UPEM = {}, {}, {}


def load_fonts():
    CACHE.mkdir(exist_ok=True)
    for key, (src, axes, _) in FONT_SPECS.items():
        path = CACHE / f"{key}.ttf"
        if not path.exists():
            vf = TTFont(src)
            instancer.instantiateVariableFont(vf, axes, inplace=True)
            vf.save(path)
        STATIC[key] = path
        face = hb.Face(hb.Blob.from_file_path(str(path)))
        HBFONT[key] = hb.Font(face)
        UPEM[key] = face.upem


def measure(font, s, size):
    buf = hb.Buffer()
    buf.add_str(s)
    buf.guess_segment_properties()
    hb.shape(HBFONT[font], buf, {"kern": True, "liga": True})
    return sum(p.x_advance for p in buf.glyph_positions) * size / UPEM[font]


def wrap(font, s, size, width):
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if measure(font, trial, size) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def font_face(key, chars):
    f = TTFont(STATIC[key])
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]
    opts.hinting = False
    opts.desubroutinize = True
    sub = subset.Subsetter(opts)
    sub.populate(unicodes={ord(c) for c in chars} | {32})
    sub.subset(f)
    f.flavor = "woff2"
    bio = io.BytesIO()
    f.save(bio)
    b64 = base64.b64encode(bio.getvalue()).decode()
    return (f"@font-face{{font-family:'tw-{key}';"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")


FALLBACK = {
    "display": "'Segoe UI',system-ui,sans-serif",
    "semi": "'Segoe UI',system-ui,sans-serif",
    "text": "'Segoe UI',system-ui,sans-serif",
    "mono": "ui-monospace,Consolas,Menlo,monospace",
}

ICONS = json.loads((HERE / "icons.json").read_text())


# --------------------------------------------------------------------------
# SVG helpers
# --------------------------------------------------------------------------
def mix(c1, c2, t):
    """Blend c1 into c2 by t (0 = c2, 1 = c1)."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * t + y * (1 - t)):02X}" for x, y in zip(a, b))


def pts(points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


class Doc:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.parts, self.defs, self.css = [], [], []
        self.chars = {k: set() for k in FONT_SPECS}

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, font, size, fill, anchor="start", attrs="", cls=""):
        self.chars[font].update(s)
        klass = f"f-{font} {cls}".strip()
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" class="{klass}" '
                 f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
                 f'{attrs}>{escape(s)}</text>')

    def icon(self, slug, x, y, size, fill, attrs=""):
        p = ICONS[slug]["path"]
        self.add(f'<path transform="translate({x:.1f} {y:.1f}) '
                 f'scale({size / 24:.4f})" d="{p}" fill="{fill}" {attrs}/>')

    def monogram(self, label, x, y, size, color):
        self.add(f'<rect x="{x + .75:.1f}" y="{y + .75:.1f}" width="{size - 1.5:.1f}" '
                 f'height="{size - 1.5:.1f}" rx="4" fill="none" stroke="{color}" '
                 f'stroke-width="1.5"/>')
        fs = size * (.38 if len(label) > 2 else .44)
        self.text(x + size / 2, y + size / 2 + fs * .36, label, "mono", fs,
                  color, "middle")

    def glyph(self, kind, cx, cy, s, color):
        """Discipline marks: square = build, circle = think, crosshair = break."""
        if kind == "build":
            self.add(f'<rect x="{cx - s / 2:.1f}" y="{cy - s / 2:.1f}" '
                     f'width="{s:.1f}" height="{s:.1f}" rx="{s * .18:.1f}" fill="{color}"/>')
        elif kind == "think":
            self.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{s / 2:.1f}" fill="{color}"/>')
        elif kind == "break":
            r, sw = s * .36, max(1.5, s * .11)
            self.add(f'<g stroke="{color}" stroke-width="{sw:.1f}" stroke-linecap="round" fill="none">'
                     f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}"/>'
                     f'<path d="M{cx:.1f} {cy - s / 2:.1f}V{cy - r * .45:.1f}'
                     f'M{cx:.1f} {cy + r * .45:.1f}V{cy + s / 2:.1f}'
                     f'M{cx - s / 2:.1f} {cy:.1f}H{cx - r * .45:.1f}'
                     f'M{cx + r * .45:.1f} {cy:.1f}H{cx + s / 2:.1f}"/></g>'
                     f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{sw * .9:.1f}" fill="{color}"/>')
        else:
            self.add(f'<rect x="{cx - s / 2:.1f}" y="{cy - s / 2:.1f}" width="{s:.1f}" '
                     f'height="{s:.1f}" rx="{s * .18:.1f}" fill="none" stroke="{color}" '
                     f'stroke-width="{max(1.5, s * .12):.1f}"/>')

    def render(self, path):
        faces = "".join(font_face(k, c) for k, c in self.chars.items() if c)
        classes = "".join(
            f".f-{k}{{font-family:'tw-{k}',{FALLBACK[k]};font-weight:{FONT_SPECS[k][2]}}}"
            for k in FONT_SPECS)
        css = faces + classes + "".join(self.css)
        css += "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
               f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{escape(self.title)}">'
               f'<title>{escape(self.title)}</title>'
               f'<defs><style>{css}</style>{"".join(self.defs)}</defs>'
               + "".join(self.parts) + "</svg>")
        path.write_text(svg, encoding="utf-8")
        print(f"  {path.name:<20} {len(svg) / 1024:6.1f} KB")


# --------------------------------------------------------------------------
# Hero: name + an exploded isometric system stack being security-scanned
# --------------------------------------------------------------------------
S = 200  # flat design space mapped onto each plate's top face


def plate_matrix(cx, cy, w, h):
    return f"matrix({w / S:.4f} {h / S:.4f} {-w / S:.4f} {h / S:.4f} {cx:.1f} {cy - h:.1f})"


def plate_content(kind, c):
    ns = 'vector-effect="non-scaling-stroke"'
    if kind == "interface":
        return (f'<rect x="28" y="28" width="144" height="144" rx="12" fill="none" stroke="{c}" stroke-width="1.4" {ns}/>'
                f'<line x1="28" y1="58" x2="172" y2="58" stroke="{c}" stroke-width="1.2" {ns}/>'
                + "".join(f'<circle cx="{x}" cy="43" r="4.5" fill="{c}"/>' for x in (46, 61, 76))
                + f'<rect x="46" y="74" width="108" height="36" rx="6" fill="{c}" fill-opacity=".2"/>'
                f'<rect x="46" y="122" width="72" height="9" rx="4.5" fill="{c}" fill-opacity=".55"/>'
                f'<rect x="46" y="138" width="96" height="9" rx="4.5" fill="{c}" fill-opacity=".3"/>'
                f'<rect x="120" y="152" width="34" height="12" rx="6" fill="{c}"/>')
    if kind == "api":
        out = ""
        for i, (a, b) in enumerate([(30, 92), (38, 74), (30, 100), (42, 66)]):
            y = 40 + i * 34
            out += (f'<rect x="34" y="{y}" width="{a}" height="16" rx="8" fill="{c}" fill-opacity=".9"/>'
                    f'<rect x="{34 + a + 10}" y="{y + 4}" width="{b}" height="8" rx="4" fill="{c}" fill-opacity=".35"/>')
        return out
    if kind == "model":
        layers = [(48, [62, 100, 138]), (100, [44, 81, 119, 156]), (152, [80, 120])]
        out = ""
        for (x1, ys1), (x2, ys2) in zip(layers, layers[1:]):
            for y1 in ys1:
                for y2 in ys2:
                    out += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-opacity=".38" stroke-width="1" {ns}/>'
        for x, ys in layers:
            for y in ys:
                out += (f'<circle cx="{x}" cy="{y}" r="8" fill="{PANEL}" stroke="{c}" stroke-width="1.4" {ns}/>'
                        f'<circle cx="{x}" cy="{y}" r="3.2" fill="{c}"/>')
        return out
    if kind == "data":
        out = (f'<rect x="30" y="30" width="140" height="140" rx="10" fill="none" stroke="{c}" stroke-width="1.4" {ns}/>'
               f'<path d="M30 58H170V40a10 10 0 0 0-10-10H40a10 10 0 0 0-10 10Z" fill="{c}" fill-opacity=".22"/>')
        for y in (58, 86, 114, 142):
            out += f'<line x1="30" y1="{y}" x2="170" y2="{y}" stroke="{c}" stroke-opacity=".5" stroke-width="1" {ns}/>'
        out += f'<line x1="78" y1="30" x2="78" y2="170" stroke="{c}" stroke-opacity=".5" stroke-width="1" {ns}/>'
        return out
    return ""


def hero():
    W, H = 1200, 520
    title = (f"{CONFIG['first_name']} {CONFIG['last_name']}: full-stack developer, "
             f"AI developer and bug hunter. " + " ".join(CONFIG["tagline"]))
    d = Doc(W, H, title)
    cx, w, h, t = 885, 140, 70, 12
    stack = [  # top to bottom
        ("interface", BUILD, "Interface", 90),
        ("api", BUILD, "API", 198),
        ("model", THINK, "Model", 306),
        ("data", BUILD, "Data", 414),
    ]
    api_cy = 198
    scan_from, scan_to, dur = 45, 460, 6.5
    lock = (api_cy - scan_from) / (scan_to - scan_from)

    d.defs.append(
        '<pattern id="iso" width="60" height="30" patternUnits="userSpaceOnUse" x="15" y="0">'
        f'<path d="M0 15L30 0L60 15L30 30Z" fill="none" stroke="{RULE}" stroke-width="1"/></pattern>'
        f'<radialGradient id="fadeg" cx="{cx}" cy="260" r="360" gradientUnits="userSpaceOnUse">'
        '<stop offset="0" stop-color="#fff" stop-opacity=".55"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
        f'<mask id="fade"><rect width="{W}" height="{H}" fill="url(#fadeg)"/></mask>'
        f'<clipPath id="card"><rect width="{W}" height="{H}" rx="24"/></clipPath>')

    p1, p2 = lock - .03, lock + .02
    d.css.append(
        f".scan{{animation:scan {dur}s linear infinite;opacity:0}}"
        f"@keyframes scan{{0%{{transform:translateY({scan_from}px);opacity:0}}"
        f"6%{{opacity:1}}90%{{opacity:1}}100%{{transform:translateY({scan_to}px);opacity:0}}}}"
        f".lock{{animation:lock {dur}s linear infinite}}"
        f"@keyframes lock{{0%,{p1 * 100:.1f}%{{opacity:0}}{p2 * 100:.1f}%,94%{{opacity:1}}100%{{opacity:0}}}}"
        f".flash{{animation:flash {dur}s linear infinite;opacity:0}}"
        f"@keyframes flash{{0%,{p1 * 100:.1f}%{{opacity:0}}{p2 * 100:.1f}%{{opacity:1}}"
        f"{(p2 + .12) * 100:.1f}%,100%{{opacity:.45}}}}"
        ".spin{transform-box:fill-box;transform-origin:center;animation:spin 14s linear infinite}"
        "@keyframes spin{to{transform:rotate(360deg)}}")

    d.add(f'<rect width="{W}" height="{H}" rx="24" fill="{INK}"/>')
    d.add(f'<g clip-path="url(#card)"><rect x="560" width="{W - 560}" height="{H}" '
          f'fill="url(#iso)" mask="url(#fade)"/></g>')

    # Plates, bottom first so upper plates sit on top
    for kind, color, label, cy in reversed(stack):
        T, R, B, L = (cx, cy - h), (cx + w, cy), (cx, cy + h), (cx - w, cy)
        left = [L, B, (B[0], B[1] + t), (L[0], L[1] + t)]
        right = [B, R, (R[0], R[1] + t), (B[0], B[1] + t)]
        d.add(f'<polygon points="{pts(left)}" fill="{mix(color, INK, .26)}" '
              f'stroke="{color}" stroke-opacity=".6" stroke-width="1"/>')
        d.add(f'<polygon points="{pts(right)}" fill="{mix(color, INK, .14)}" '
              f'stroke="{color}" stroke-opacity=".6" stroke-width="1"/>')
        d.add(f'<polygon points="{pts([T, R, B, L])}" fill="{PANEL}" stroke="{color}" '
              f'stroke-width="1.5" stroke-linejoin="round"/>')
        d.add(f'<g transform="{plate_matrix(cx, cy, w, h)}">{plate_content(kind, color)}</g>')
        if kind == "api":
            # red edge flash when the scan locks on, and the crosshair on the bug
            d.add(f'<polygon class="flash" points="{pts([T, R, B, L])}" fill="{BREAK}" '
                  f'fill-opacity=".08" stroke="{BREAK}" stroke-width="2" stroke-linejoin="round"/>')
            ns = 'vector-effect="non-scaling-stroke"'
            d.add(f'<g transform="{plate_matrix(cx, cy, w, h)}"><g class="lock">'
                  f'<g class="spin"><circle cx="122" cy="100" r="34" fill="none" stroke="{BREAK}" '
                  f'stroke-width="2" stroke-dasharray="14 8" {ns}/></g>'
                  f'<circle cx="122" cy="100" r="18" fill="none" stroke="{BREAK}" stroke-width="1.5" {ns}/>'
                  f'<path d="M122 52V76M122 124V148M74 100H98M146 100H170" stroke="{BREAK}" '
                  f'stroke-width="2" stroke-linecap="round" {ns}/>'
                  f'<circle cx="122" cy="100" r="5" fill="{BREAK}"/></g></g>')
        # label
        lx = cx + w + 26
        d.add(f'<line x1="{cx + w + 8}" y1="{cy}" x2="{cx + w + 18}" y2="{cy}" '
              f'stroke="{RULE}" stroke-width="1.5"/>')
        d.text(lx, cy + 6, label, "semi", 17, MIST)
        if kind == "api":
            d.text(lx, cy + 30, "IDOR found", "mono", 12, BREAK, cls="lock")

    # scan plane sweeping the stack
    sw, sh = w + 22, h + 11
    d.add(f'<g class="scan"><polygon points="{pts([(cx, -sh), (cx + sw, 0), (cx, sh), (cx - sw, 0)])}" '
          f'fill="{BREAK}" fill-opacity=".07" stroke="{BREAK}" stroke-width="1.5" '
          f'stroke-linejoin="round"/></g>')

    # Left: name, roles legend, tagline
    x0 = 72
    d.text(x0, 182, CONFIG["first_name"], "display", 116, PAPER, attrs='letter-spacing="-1"')
    d.text(x0, 288, CONFIG["last_name"], "display", 116, PAPER, attrs='letter-spacing="-1"')
    x = x0 + 2
    for kind, color, label in ROLES:
        d.glyph(kind, x + 8, 343, 15 if kind != "break" else 19, color)
        d.text(x + 26, 350, label, "semi", 20, PAPER)
        x += 26 + measure("semi", label, 20) + 30
    for i, line in enumerate(CONFIG["tagline"]):
        d.text(x0, 404 + i * 32, line, "text", 22, MIST)
    d.render(OUT / "hero.svg")


# --------------------------------------------------------------------------
# Loop: build -> think -> break -> back to build
# --------------------------------------------------------------------------
def loop():
    W, H = 1200, 470
    d = Doc(W, H, "How I work: build as a full-stack developer, think as an AI developer, "
                  "break as a bug hunter. " + LOOP_RETURN)
    d.add(f'<rect width="{W}" height="{H}" rx="24" fill="{INK}"/>')
    d.defs.append(f'<marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="9" '
                  f'markerHeight="9" orient="auto-start-reverse"><path d="M1 1L9 5L1 9" '
                  f'fill="none" stroke="{MIST}" stroke-width="1.6" stroke-linecap="round" '
                  f'stroke-linejoin="round"/></marker>')
    xs, colw = [72, 462, 852], 300
    title_y = 150
    for i, (kind, color, title, role, desc) in enumerate(LOOP):
        x = xs[i]
        d.glyph(kind, x + 14, 80, 26 if kind != "break" else 32, color)
        d.text(x, title_y, title, "display", 60, PAPER, attrs='letter-spacing="-.5"')
        d.text(x, title_y + 40, role, "semi", 21, color)
        for j, line in enumerate(wrap("text", desc, 19, colw)):
            d.text(x, title_y + 82 + j * 29, line, "text", 19, MIST)
        if i < 2:
            tw = measure("display", title, 60)
            ax1, ax2, ay = x + tw + 22, xs[i + 1] - 22, title_y - 20
            d.add(f'<line x1="{ax1:.1f}" y1="{ay}" x2="{ax2:.1f}" y2="{ay}" stroke="{RULE}" '
                  f'stroke-width="2" stroke-dasharray="2 7" stroke-linecap="round"/>')
            d.add(f'<line x1="{ax2 - 2:.1f}" y1="{ay}" x2="{ax2:.1f}" y2="{ay}" stroke="{MIST}" '
                  f'stroke-width="2" marker-end="url(#ah)"/>')
    # return path from Break back to Build
    y1, y2, r = 392, 426, 14
    xa, xb = xs[2] + 14, xs[0] + 14
    d.add(f'<path d="M{xa} {y1}V{y2 - r}q0 {r} {-r} {r}H{xb + r}q{-r} 0 {-r} {-r}V{y1 + 4}" '
          f'fill="none" stroke="{RULE}" stroke-width="2" stroke-dasharray="2 7" '
          f'stroke-linecap="round"/>')
    d.add(f'<line x1="{xb}" y1="{y1 + 6}" x2="{xb}" y2="{y1 + 2}" stroke="{MIST}" '
          f'stroke-width="2" marker-end="url(#ah)"/>')
    tw = measure("semi", LOOP_RETURN, 18)
    mid = (xa + xb) / 2
    d.add(f'<rect x="{mid - tw / 2 - 16:.1f}" y="{y2 - 14}" width="{tw + 32:.1f}" height="28" '
          f'fill="{INK}"/>')
    d.text(mid, y2 + 6, LOOP_RETURN, "semi", 18, MIST, "middle")
    d.render(OUT / "loop.svg")


# --------------------------------------------------------------------------
# Toolkit
# --------------------------------------------------------------------------
def toolkit():
    W = 1200
    pad, sub_x, chip_x0, chip_x1 = 64, 272, 448, 1140
    ch, gap, row_gap = 40, 8, 10
    rows = []  # pre-layout
    y = 72
    layout = []
    for gi, (kind, color, gname, gnote, subs) in enumerate(TOOLKIT):
        g_top = y
        for sname, items in subs:
            x, line_y = chip_x0, y
            chips = []
            for item in items:
                name, slug = item[0], item[1]
                cw = 13 + 18 + 10 + measure("semi", name, 17) + 16
                if x + cw > chip_x1 and x > chip_x0:
                    x, line_y = chip_x0, line_y + ch + row_gap
                chips.append((x, line_y, cw, item))
                x += cw + gap
            layout.append(("sub", sname, y, chips, color))
            y = line_y + ch + 22
        layout.append(("group", (kind, color, gname, gnote), g_top, None, None))
        y += 26
        if gi < len(TOOLKIT) - 1:
            layout.append(("rule", None, y - 24, None, None))
            y += 22
    H = int(y + 20)
    d = Doc(W, H, "Toolkit: " + "; ".join(
        f"{g[2]}: " + ", ".join(i[0] for _, items in g[4] for i in items) for g in TOOLKIT))
    d.add(f'<rect width="{W}" height="{H}" rx="24" fill="{INK}"/>')
    for typ, a, y, chips, color in layout:
        if typ == "rule":
            d.add(f'<line x1="{pad}" y1="{y}" x2="{W - pad}" y2="{y}" stroke="{RULE}" stroke-width="1"/>')
        elif typ == "group":
            kind, gcolor, gname, gnote = a
            d.glyph(kind, pad + 9, y + 17, 17 if kind != "break" else 21, gcolor)
            d.text(pad + 30, y + 30, gname, "display", 38, PAPER)
            d.text(pad + 30, y + 56, gnote, "text", 17, MIST)
        else:
            d.text(sub_x, y + 26, a, "semi", 17, MIST)
            for x, cy, cw, item in chips:
                name, slug = item[0], item[1]
                d.add(f'<rect x="{x:.1f}" y="{cy}" width="{cw:.1f}" height="{ch}" rx="9" '
                      f'fill="{PANEL}" stroke="{RULE}" stroke-width="1"/>')
                if slug:
                    d.icon(slug, x + 13, cy + 11, 18, color)
                else:
                    d.monogram(item[2], x + 12, cy + 10, 20, color)
                d.text(x + 41, cy + 26, name, "semi", 17, PAPER)
    d.render(OUT / "toolkit.svg")


# --------------------------------------------------------------------------
# Link buttons
# --------------------------------------------------------------------------
def button(fname, label, slug, bg, fg, stroke):
    h, size = 52, 20
    w = round(20 + size + 12 + measure("semi", label, 17) + 22)
    d = Doc(w, h, label)
    d.add(f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="13" fill="{bg}" '
          f'stroke="{stroke}"/>')
    d.icon(slug, 20, (h - size) / 2, size, fg)
    d.text(20 + size + 12, h / 2 + 6, label, "semi", 17, fg)
    d.render(OUT / f"{fname}.svg")


def main():
    OUT.mkdir(exist_ok=True)
    load_fonts()
    print("Writing assets:")
    hero()
    loop()
    toolkit()
    for fname, label, slug in BUTTONS:
        button(fname, label, slug, PANEL, PAPER, RULE)
    button("btn-coffee", "Buy me a coffee", "buymeacoffee", BUILD, INK, BUILD)


if __name__ == "__main__":
    main()
