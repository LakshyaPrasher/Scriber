"""Builds Scriber's complete, authoritative, and bespoke brand assets:
- icon.svg (Mathematically symmetrical vector brandmark with sculpted acoustic ribbon)
- icon.png (512x512 high-resolution master icon with Lanczos antialiasing)
- icon.ico (Multi-resolution Windows desktop icon)
- hero_banner.jpg (1200x500 luxury editorial obsidian hero banner)
"""

import math
import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


SYMMETRIC_SVG_CONTENT = '''<svg width="512" height="512" viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <!-- Deep Obsidian Canvas -->
    <linearGradient id="scBgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#12151D" />
      <stop offset="50%" stop-color="#0A0B0F" />
      <stop offset="100%" stop-color="#050608" />
    </linearGradient>

    <!-- Vibrant Tangerine-Vermilion to Amber-Gold Gradient -->
    <linearGradient id="scWaveGrad" x1="15%" y1="10%" x2="85%" y2="90%">
      <stop offset="0%" stop-color="#FF3800" />
      <stop offset="45%" stop-color="#FF5E00" />
      <stop offset="80%" stop-color="#FFA826" />
      <stop offset="100%" stop-color="#FFC043" />
    </linearGradient>

    <!-- Accent Acoustic Core Gradient -->
    <linearGradient id="scCoreGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFA826" />
      <stop offset="100%" stop-color="#FF5E00" />
    </linearGradient>

    <!-- Precision Hairline Glow -->
    <filter id="scSubtleBloom" x="-15%" y="-15%" width="130%" height="130%">
      <feGaussianBlur stdDeviation="6" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Obsidian Precision Beveled Squircle (100% Symmetrical) -->
  <rect x="28" y="28" width="456" height="456" rx="96" fill="url(#scBgGrad)" stroke="rgba(255, 94, 0, 0.22)" stroke-width="2" />
  <rect x="30" y="30" width="452" height="452" rx="94" fill="none" stroke="rgba(255, 255, 255, 0.05)" stroke-width="1" />

  <!-- Symmetrical Harmonic Monogram Emblem -->
  <g filter="url(#scSubtleBloom)">
    <!-- Continuous Symmetrical Sculpted Ribbon S -->
    <path d="M 364 196 C 364 126 316 76 256 76 C 196 76 148 126 148 184 C 148 268 364 244 364 328 C 364 386 316 436 256 436 C 196 436 148 386 148 316 L 204 316 C 204 362 228 380 256 380 C 284 380 308 362 308 328 C 308 276 204 236 204 184 C 204 150 228 132 256 132 C 284 132 308 150 308 196 Z"
          fill="url(#scWaveGrad)" />
  </g>
</svg>
'''


def eval_cubic_bezier(p0, p1, p2, p3, steps=60):
    """Evaluates points along a cubic Bezier curve."""
    pts = []
    for i in range(steps + 1):
        t = i / float(steps)
        u = 1.0 - t
        x = u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0]
        y = u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]
        pts.append((x, y))
    return pts


def generate_png_and_ico(output_dir: Path):
    """Draws pixel-perfect anti-aliased bitmap icon and builds multi-resolution ICO."""
    size = 1024
    scale = size / 512.0
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Background Squircle
    margin = int(28 * scale)
    rx = int(96 * scale)
    bg_box = [margin, margin, size - margin, size - margin]
    draw.rounded_rectangle(bg_box, radius=rx, fill=(10, 12, 17, 255), outline=(255, 94, 0, 65), width=int(3 * scale))

    # Inner hairline border
    inner_box = [margin + 3, margin + 3, size - margin - 3, size - margin - 3]
    draw.rounded_rectangle(inner_box, radius=rx - 3, fill=None, outline=(255, 255, 255, 12), width=int(1.5 * scale))

    # 2. Build full polygon matching the exact cubic Beziers of the SVG
    bezier_segments = [
        # Segment 1: (364, 196) -> C(364, 126), C(316, 76) -> P(256, 76)
        ((364, 196), (364, 126), (316, 76), (256, 76)),
        # Segment 2: (256, 76) -> C(196, 76), C(148, 126) -> P(148, 184)
        ((256, 76), (196, 76), (148, 126), (148, 184)),
        # Segment 3 (waist): (148, 184) -> C(148, 268), C(364, 244) -> P(364, 328)
        ((148, 184), (148, 268), (364, 244), (364, 328)),
        # Segment 4: (364, 328) -> C(364, 386), C(316, 436) -> P(256, 436)
        ((364, 328), (364, 386), (316, 436), (256, 436)),
        # Segment 5: (256, 436) -> C(196, 436), C(148, 386) -> P(148, 316)
        ((256, 436), (196, 436), (148, 386), (148, 316)),
        # Segment 6 (inner bottom): (204, 316) -> C(204, 362), C(228, 380) -> P(256, 380)
        ((204, 316), (204, 362), (228, 380), (256, 380)),
        # Segment 7: (256, 380) -> C(284, 380), C(308, 362) -> P(308, 328)
        ((256, 380), (284, 380), (308, 362), (308, 328)),
        # Segment 8 (inner waist): (308, 328) -> C(308, 276), C(204, 236) -> P(204, 184)
        ((308, 328), (308, 276), (204, 236), (204, 184)),
        # Segment 9 (inner top): (204, 184) -> C(204, 150), C(228, 132) -> P(256, 132)
        ((204, 184), (204, 150), (228, 132), (256, 132)),
        # Segment 10: (256, 132) -> C(284, 132), C(308, 150) -> P(308, 196)
        ((256, 132), (284, 132), (308, 150), (308, 196)),
    ]

    # Evaluate polygon points in sequence
    polygon_points = []
    # Segments 1-5 (outer)
    for seg in bezier_segments[:5]:
        pts = eval_cubic_bezier(seg[0], seg[1], seg[2], seg[3], steps=80)
        polygon_points.extend(pts[:-1])
    # Add bottom terminal cap point (204, 316)
    polygon_points.append((204, 316))
    # Segments 6-10 (inner)
    for seg in bezier_segments[5:]:
        pts = eval_cubic_bezier(seg[0], seg[1], seg[2], seg[3], steps=80)
        polygon_points.extend(pts[:-1])
    # Connects back to (364, 196) automatically
    scaled_polygon = [(p[0] * scale, p[1] * scale) for p in polygon_points]

    # 3. Ambient bloom / glow layer
    glow_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    glow_draw.polygon(scaled_polygon, fill=(255, 94, 0, 120))
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=20 * scale))
    img.paste(glow_img, (0, 0), glow_img)

    # 4. Fill Ribbon with Vermilion to Amber Gradient
    # Render horizontal gradient onto a mask
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.polygon(scaled_polygon, fill=255)

    grad_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(grad_img)
    for y in range(size):
        factor = y / float(size)
        r = int(255)
        g = int(56 + factor * (168 - 56))
        b = int(factor * 38)
        grad_draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
    img.paste(grad_img, (0, 0), mask)

    # 5. Scale down with Lanczos to 512x512 master PNG
    master_512 = img.resize((512, 512), Image.Resampling.LANCZOS)
    png_path = output_dir / "icon.png"
    master_512.save(png_path, "PNG", optimize=True)

    # Multi-resolution ICO (16, 24, 32, 48, 64, 128, 256)
    ico_path = output_dir / "icon.ico"
    master_512.save(
        ico_path,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )

    # Hero Banner (1200x500 Dark Editorial Obsidian Banner)
    banner_w, banner_h = 1200, 500
    banner = Image.new("RGB", (banner_w, banner_h), (8, 9, 12))
    bdraw = ImageDraw.Draw(banner)

    # Subtle radial illumination centered
    for rad in range(350, 0, -5):
        alpha = int((1.0 - (rad / 350.0)) * 26)
        bdraw.ellipse([600 - rad * 1.5, 250 - rad, 600 + rad * 1.5, 250 + rad], fill=(alpha + 8, alpha // 2 + 9, 12))

    # Paste emblem centered
    emblem_thumb = master_512.resize((240, 240), Image.Resampling.LANCZOS)
    banner.paste(emblem_thumb, (480, 130), emblem_thumb)

    hero_path = output_dir / "hero_banner.jpg"
    banner.save(hero_path, "JPEG", quality=95)


def main():
    assets_dir = Path(__file__).resolve().parent.parent / "scriber" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save Symmetrical SVG
    svg_path = assets_dir / "icon.svg"
    svg_path.write_text(SYMMETRIC_SVG_CONTENT.strip(), encoding="utf-8")
    print(f"[OK] Generated Symmetrical SVG: {svg_path}")

    # 2. Generate PNG, ICO, Banner
    generate_png_and_ico(assets_dir)
    print(f"[OK] Generated Symmetrical icon.png, icon.ico, hero_banner.jpg in {assets_dir}")


if __name__ == "__main__":
    main()
