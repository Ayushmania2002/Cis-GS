#!/usr/bin/env python3
"""
Create placeholder assets for Cis-GS if they don't exist.
Run this before building if you don't have logo/icon/banner files.
"""

import os
from pathlib import Path

def create_placeholder_images():
    """Create simple placeholder PNG images using PIL/Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        print("✓ Pillow found, creating placeholder images...")
    except ImportError:
        print("⚠️  Pillow not installed. Installing...")
        os.system("pip install Pillow")
        from PIL import Image, ImageDraw, ImageFont
    
    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)
    
    # ── 1. Logo (200x200) ────────────────────────────────────────────────────
    logo_path = assets_dir / "logo.png"
    if not logo_path.exists():
        print(f"Creating {logo_path}...")
        img = Image.new('RGB', (200, 200), color='#2E86AB')
        draw = ImageDraw.Draw(img)
        
        # Draw simple "Cis-GS" text
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        draw.text((100, 80), "Cis-GS", fill='white', anchor='mm', font=font)
        draw.text((100, 120), "v1.0", fill='#E0E0E0', anchor='mm', font=font)
        
        img.save(logo_path)
        print(f"  ✓ Created logo: {logo_path}")
    else:
        print(f"  ✓ Logo already exists: {logo_path}")
    
    # ── 2. Favicon (64x64) ───────────────────────────────────────────────────
    favicon_path = assets_dir / "favicon.png"
    if not favicon_path.exists():
        print(f"Creating {favicon_path}...")
        img = Image.new('RGB', (64, 64), color='#2E86AB')
        draw = ImageDraw.Draw(img)
        
        # Draw simple "C" for Cis-GS
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        draw.text((32, 32), "C", fill='white', anchor='mm', font=font)
        
        img.save(favicon_path)
        print(f"  ✓ Created favicon: {favicon_path}")
    else:
        print(f"  ✓ Favicon already exists: {favicon_path}")
    
    # ── 3. Banner (1920x1080) ────────────────────────────────────────────────
    banner_path = assets_dir / "banner.png"
    if not banner_path.exists():
        print(f"Creating {banner_path}...")
        img = Image.new('RGB', (1920, 1080), color='#F0F4F8')
        draw = ImageDraw.Draw(img)
        
        # Draw gradient-like effect (simple bands)
        for i in range(0, 1080, 10):
            color_val = int(240 + (i / 1080) * 15)
            draw.rectangle([0, i, 1920, i+10], fill=f'#{color_val:02x}{color_val:02x}{color_val:02x}')
        
        # Draw title
        try:
            font_large = ImageFont.truetype("arial.ttf", 120)
            font_small = ImageFont.truetype("arial.ttf", 60)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        draw.text((960, 400), "Cis-GS", fill='#2E86AB', anchor='mm', font=font_large)
        draw.text((960, 540), "Genome-wide Cis-element Scanner", 
                  fill='#555555', anchor='mm', font=font_small)
        
        img.save(banner_path)
        print(f"  ✓ Created banner: {banner_path}")
    else:
        print(f"  ✓ Banner already exists: {banner_path}")
    
    print("\n✅ All placeholder assets ready!")
    print(f"\nAssets folder: {assets_dir.absolute()}")
    print("You can replace these with your own images before building.\n")


if __name__ == '__main__':
    print("=" * 70)
    print("Cis-GS Asset Generator")
    print("=" * 70)
    print()
    
    create_placeholder_images()
