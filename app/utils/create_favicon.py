from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

def create_favicon():
    """Create favicon images in various sizes and a web manifest file."""
    try:
        # Create base image
        size = 512
        background_color = "#2563eb"  # Blue color matching our theme
        text_color = "#ffffff"  # White
        
        img = Image.new('RGB', (size, size), background_color)
        draw = ImageDraw.Draw(img)
        
        # Try to load a nicer font, with multiple fallbacks
        font = None
        font_size = int(size/2)
        font_options = [
            "arial.ttf", 
            "Arial.ttf",
            "segoeui.ttf",  # Windows font
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux font
            "/System/Library/Fonts/Helvetica.ttc"  # Mac font
        ]
        
        for font_name in font_options:
            try:
                font = ImageFont.truetype(font_name, size=font_size)
                break
            except (OSError, IOError):
                continue
                
        if font is None:
            font = ImageFont.load_default()
            logger.warning("Using default font as no system fonts were found")
        
        # Add 3D text effect
        text = "CDP"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (size - text_width) / 2
        y = (size - text_height) / 2
        
        # Add shadow effect
        shadow_color = "#1d4ed8"  # Slightly darker blue
        shadow_offset = int(size/50)
        draw.text((x+shadow_offset, y+shadow_offset), text, font=font, fill=shadow_color)
        draw.text((x, y), text, font=font, fill=text_color)
        
        # Save in different sizes with proper directory handling
        favicon_dir = Path(__file__).parent.parent / "static" / "favicon"
        favicon_dir.mkdir(parents=True, exist_ok=True)
        
        # Define sizes and save images
        sizes = {
            'favicon-16x16.png': (16, 16),
            'favicon-32x32.png': (32, 32),
            'apple-touch-icon.png': (180, 180),
            'android-chrome-192x192.png': (192, 192),
            'android-chrome-512x512.png': (512, 512),
            'favicon.ico': (48, 48)
        }
        
        for filename, dimensions in sizes.items():
            resized = img.resize(dimensions, Image.Resampling.LANCZOS)
            if filename.endswith('.ico'):
                resized = resized.convert("RGBA")
                resized.save(favicon_dir / filename, format="ICO")
            else:
                resized.save(favicon_dir / filename)
        
        # Create complete webmanifest
        manifest = {
            "name": "CDP Assistant",
            "short_name": "CDP",
            "description": "AI-powered assistant for Customer Data Platform documentation",
            "icons": [
                {"src": "/static/favicon/favicon-16x16.png", "sizes": "16x16", "type": "image/png"},
                {"src": "/static/favicon/favicon-32x32.png", "sizes": "32x32", "type": "image/png"},
                {"src": "/static/favicon/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"},
                {"src": "/static/favicon/android-chrome-192x192.png", "sizes": "192x192", "type": "image/png"},
                {"src": "/static/favicon/android-chrome-512x512.png", "sizes": "512x512", "type": "image/png"}
            ],
            "theme_color": "#2563eb",
            "background_color": "#ffffff",
            "display": "standalone",
            "start_url": "/",
            "orientation": "portrait"
        }
        
        with open(favicon_dir / 'site.webmanifest', 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
            
        logger.info("Favicon creation completed successfully")
        
    except Exception as e:
        logger.error(f"Error creating favicon: {str(e)}")
        _create_fallback_favicon(favicon_dir)

def _create_fallback_favicon(favicon_dir: Path):
    """Create a simple fallback favicon if the main process fails"""
    try:
        simple_img = Image.new('RGB', (32, 32), "#2563eb")
        favicon_dir.mkdir(parents=True, exist_ok=True)
        simple_img.save(favicon_dir / 'favicon-32x32.png')
        logger.info("Created fallback favicon")
    except Exception as e:
        logger.error(f"Failed to create fallback favicon: {str(e)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_favicon()
