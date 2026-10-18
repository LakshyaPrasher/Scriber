"""Builds Scriber's complete, authoritative, and bespoke brand assets:
- icon.svg (Vector brandmark with interlocking acoustic harmonic ribbons)
- icon.png (512x512 high-resolution master icon)
- icon.ico (Multi-resolution Windows desktop icon)
- hero_banner.jpg (1200x500 luxury editorial obsidian hero banner)
"""

import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont


SVG_CONTENT = '''<svg width="512" height="512" viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg">
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

  <!-- Obsidian Precision Beveled Squircle -->
  <rect x="28" y="28" width="456" height="456" rx="96" fill="url(#scBgGrad)" stroke="rgba(255, 94, 0, 0.22)" stroke-width="2" />
  <rect x="30" y="30" width="452" height="452" rx="94" fill="none" stroke="rgba(255, 255, 255, 0.05)" stroke-width="1" />

  <!-- Harmonic Monogram Emblem -->
  <g filter="url(#scSubtleBloom)">
    <!-- Upper Acoustic Loop of S (Solid Sculpted Ribbon) -->
    <path d="M 364 192 C 364 136 320 100 256 100 C 188 100 148 142 148 196 C 148 248 194 278 262 298 C 322 316 348 336 348 376 C 348 424 308 456 250 456 C 190 456 148 420 144 368 L 196 368 C 200 396 220 416 252 416 C 282 416 304 398 304 372 C 304 338 274 322 216 302 C 160 282 106 254 106 194 C 106 122 166 64 256 64 C 344 64 406 116 406 192 Z"
          fill="url(#scWaveGrad)" />

    <!-- Interior Soundwave Harmonics (Horizontal Precision Slits) -->
    <rect x="210" y="146" width="92" height="8" rx="4" fill="#0A0B0F" opacity="0.9" />
    <rect x="176" y="174" width="160" height="8" rx="4" fill="#0A0B0F" opacity="0.9" />
    <rect x="176" y="330" width="160" height="8" rx="4" fill="#0A0B0F" opacity="0.9" />
    <rect x="210" y="358" width="92" height="8" rx="4" fill="#0A0B0F" opacity="0.9" />

    <!-- Central Resonant Pulse Nodes -->
    <circle cx="256" cy="236" r="14" fill="url(#scCoreGrad)" />
    <circle cx="256" cy="276" r="10" fill="url(#scCoreGrad)" />
  </g>
</svg>
'''


def generate_png_and_ico(output_dir: Path):
    """Draws pixel-perfect anti-aliased bitmap icon and builds multi-resolution ICO."""
    size = 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Background Squircle
    margin = 56
    rx = 192
    bg_box = [margin, margin, size - margin, size - margin]
    draw.rounded_rectangle(bg_box, radius=rx, fill=(11, 13, 19, 255), outline=(255, 94, 0, 60), width=4)

    # Inner hairline border
    inner_box = [margin + 4, margin + 4, size - margin - 4, size - margin - 4]
    draw.rounded_rectangle(inner_box, radius=rx - 4, fill=None, outline=(255, 255, 255, 14), width=2)

    # 2. Draw Sculpted Monogram "S" with Soundwave Frequency Slits
    # High-resolution supersampling canvas
    scale = size / 512.0
    
    # Gradient rendering using supersampled horizontal spans
    # Draw core sculpted arcs
    cx, cy = size / 2.0, size / 2.0
    
    # Monogram ribbon paths
    def draw_ribbon(points, width, color):
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            draw.line([p1, p2], fill=color, width=int(width))

    # Upper arc points
    upper_pts = []
    for deg in range(-40, 210, 2):
        rad = math.radians(deg)
        r = 135 * scale
        x = cx + r * math.cos(rad) - 10 * scale
        y = cy - 80 * scale + r * 0.9 * math.sin(rad)
        upper_pts.append((x, y))

    # Lower arc points
    lower_pts = []
    for deg in range(140, 390, 2):
        rad = math.radians(deg)
        r = 135 * scale
        x = cx + r * math.cos(rad) + 10 * scale
        y = cy + 80 * scale + r * 0.9 * math.sin(rad)
        lower_pts.append((x, y))

    # Center connecting wave spine
    spine_pts = []
    for t in range(0, 101, 2):
        prog = t / 100.0
        # Smooth S-curve
        x = cx + 80 * scale * math.cos(prog * math.pi)
        y = cy - 80 * scale + 160 * scale * prog
        spine_pts.append((x, y))

    # Layered glow and core rendering
    # Outer ambient glow
    glow_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    glow_color = (255, 94, 0, 110)
    
    for pts in [upper_pts, lower_pts, spine_pts]:
        for i in range(len(pts) - 1):
            glow_draw.line([pts[i], pts[i + 1]], fill=glow_color, width=int(64 * scale))
    
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=18 * scale))
    img.paste(glow_img, (0, 0), glow_img)

    # Core high-precision ribbon
    for pts in [upper_pts, lower_pts, spine_pts]:
        for i in range(len(pts) - 1):
            # Dynamic gradient from vermilion to amber
            vert_y = pts[i][1]
            factor = max(0.0, min(1.0, vert_y / size))
            r = int(255)
            g = int(58 + factor * (168 - 58))
            b = int(0 + factor * 38)
            draw.line([pts[i], pts[i + 1]], fill=(r, g, b, 255), width=int(44 * scale))

    # Central acoustic aperture nodes
    draw.ellipse([cx - 24 * scale, cy - 24 * scale, cx + 24 * scale, cy + 24 * scale], fill=(255, 168, 38, 255))
    draw.ellipse([cx - 12 * scale, cy - 12 * scale, cx + 12 * scale, cy + 12 * scale], fill=(10, 11, 15, 255))

    # Soundwave frequency horizontal slots (Negative Space)
    slit_color = (10, 11, 15, 255)
    slits = [
        (cx - 100 * scale, cy - 110 * scale, 200 * scale, 12 * scale),
        (cx - 140 * scale, cy - 65 * scale, 280 * scale, 14 * scale),
        (cx - 140 * scale, cy + 65 * scale, 280 * scale, 14 * scale),
        (cx - 100 * scale, cy + 110 * scale, 200 * scale, 12 * scale),
    ]
    for sx, sy, sw, sh in slits:
        draw.rounded_rectangle([sx, sy, sx + sw, sy + sh], radius=sh / 2, fill=slit_color)

    # Scale down with Lanczos to 512x512 master PNG
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

    # Subtle radial illumination
    for rad in range(350, 0, -5):
        alpha = int((1.0 - (rad / 350.0)) * 28)
        bdraw.ellipse([600 - rad * 1.5, 250 - rad, 600 + rad * 1.5, 250 + rad], fill=(alpha + 8, alpha // 2 + 9, 12))

    # Paste emblem centered
    emblem_thumb = master_512.resize((240, 240), Image.Resampling.LANCZOS)
    banner.paste(emblem_thumb, (480, 130), emblem_thumb)

    hero_path = output_dir / "hero_banner.jpg"
    banner.save(hero_path, "JPEG", quality=95)


def main():
    assets_dir = Path(__file__).resolve().parent.parent / "scriber" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save SVG
    svg_path = assets_dir / "icon.svg"
    svg_path.write_text(SVG_CONTENT.strip(), encoding="utf-8")
    print(f"[OK] Generated: {svg_path}")

    # 2. Generate PNG, ICO, Banner
    generate_png_and_ico(assets_dir)
    print(f"[OK] Generated icon.png, icon.ico, hero_banner.jpg in {assets_dir}")


if __name__ == "__main__":
    main()
