"""Generates simple SVG product images (so the demo looks populated offline)."""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "app" / "static" / "images"
ITEMS = [
    ("laptop", "💻", "#2563eb", "#38bdf8"), ("gaming-laptop", "🎮", "#7c3aed", "#f43f5e"),
    ("smartphone", "📱", "#0891b2", "#22d3ee"), ("smartphone-lite", "📲", "#059669", "#34d399"),
    ("headphones", "🎧", "#db2777", "#f472b6"), ("earbuds", "🎵", "#ea580c", "#fb923c"),
    ("smartwatch", "⌚", "#4f46e5", "#818cf8"), ("fitband", "🏃", "#0d9488", "#5eead4"),
    ("keyboard", "⌨️", "#334155", "#64748b"), ("mouse", "🖱️", "#b45309", "#fbbf24"),
    ("usb-hub", "🔌", "#475569", "#94a3b8"), ("backpack", "🎒", "#be123c", "#fb7185"),
    ("placeholder", "🛒", "#64748b", "#cbd5e1"),
]
TPL = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient></defs>
<rect width="400" height="300" fill="url(#g)"/>
<text x="200" y="185" font-size="110" text-anchor="middle">{e}</text></svg>"""

OUT.mkdir(parents=True, exist_ok=True)
for name, emoji, a, b in ITEMS:
    (OUT / f"{name}.svg").write_text(TPL.format(a=a, b=b, e=emoji), encoding="utf-8")
print("Images created:", len(ITEMS))
