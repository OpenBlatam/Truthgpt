"""
AI Viral Thumbnail Generator Module v5.0 (Powered by PIL / Pillow)
===================================================================
Generates high-CTR 9:16 vertical cover images with kinetic typography,
high contrast borders, and viral badge overlays for Instagram Reels, TikTok, and Shorts.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Tuple

try:
    from PIL import Image, ImageDraw, ImageFont  # type: ignore
    HAS_PIL = True
except (ImportError, ValueError):
    HAS_PIL = False

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CUSTOM EXCEPTIONS & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

class ThumbnailGenerationError(Exception):
    """Custom exception raised for thumbnail generation failures."""
    pass


class C:
    """Terminal ANSI Color Codes."""
    H = '\033[95m'; B = '\033[94m'; CY = '\033[96m'; G = '\033[92m'
    Y = '\033[93m'; R = '\033[91m'; E = '\033[0m'; BD = '\033[1m'
    DIM = '\033[2m'; W = '\033[97m'


# ═══════════════════════════════════════════════════════════════════════════
# VIRAL THUMBNAIL GENERATOR ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class ViralThumbnailGenerator:
    """
    Intelligent Vertical 9:16 Cover / Thumbnail Generator (Pillow / PIL).
    Creates high-converting cover images (cover.png) optimized for CTR.
    """

    @staticmethod
    def _safe_draw_text(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: str, fill: Tuple[int, int, int]) -> None:
        """Safely renders text with fallback ascii sanitization for PIL default fonts."""
        try:
            draw.text(xy, text, fill=fill)
        except (UnicodeEncodeError, Exception):
            clean_txt = "".join(c for c in text if ord(c) < 256)
            try:
                draw.text(xy, clean_txt, fill=fill)
            except Exception:
                pass

    @staticmethod
    def create_thumbnail(
        title: str,
        hook_score: int,
        output_path: str,
        canvas_size: Tuple[int, int] = (1080, 1920),
    ) -> str:
        """
        Creates a vertical 9:16 thumbnail image with gradient background, bold typography, and virality badge.

        Args:
            title: Headline string to overlay on cover.
            hook_score: Virality score (0-100).
            output_path: Destination PNG image filepath.
            canvas_size: Target image dimensions (width, height) tuple.

        Returns:
            str: Path to generated thumbnail image file.

        Raises:
            ThumbnailGenerationError: If image creation or saving fails.
        """
        w, h = canvas_size if isinstance(canvas_size, (tuple, list)) and len(canvas_size) == 2 else (1080, 1920)
        try:
            w, h = max(100, int(w)), max(100, int(h))
        except (ValueError, TypeError):
            w, h = 1080, 1920

        try:
            img = Image.new("RGB", (w, h), color=(15, 15, 25))
            draw = ImageDraw.Draw(img)

            # Draw dark gradient background
            for y in range(h):
                r = int(15 + (40 * y / h))
                g = int(15 + (10 * y / h))
                b = int(25 + (60 * y / h))
                draw.line([(0, y), (w, y)], fill=(r, g, b))

            # Top Hook Badge Box
            try:
                score = max(0, min(100, int(hook_score)))
            except (ValueError, TypeError):
                score = 90

            draw.rectangle([60, 120, 600, 220], fill=(255, 0, 85))
            ViralThumbnailGenerator._safe_draw_text(draw, (80, 145), f"HOOK VIRAL: {score}/100", fill=(255, 255, 255))

            # Main Kinetic Title Text Overlay
            clean_title = str(title or "VIDEO VIRAL").strip()
            lines = clean_title.upper().split()
            if not lines:
                lines = ["VIDEO", "VIRAL"]
            chunked = [" ".join(lines[i:i + 3]) for i in range(0, len(lines), 3)]

            start_y = 700
            for chunk in chunked[:3]:
                # Yellow bounding box for high contrast
                draw.rectangle([50, start_y, w - 50, start_y + 140], fill=(255, 220, 0))
                ViralThumbnailGenerator._safe_draw_text(draw, (70, start_y + 25), chunk, fill=(0, 0, 0))
                start_y += 170

            # Bottom Call To Action Badge
            draw.rectangle([100, h - 250, w - 100, h - 130], fill=(0, 255, 200))
            ViralThumbnailGenerator._safe_draw_text(draw, (180, h - 210), "MIRA EL VIDEO COMPLETO", fill=(0, 0, 0))

            out_file = Path(output_path).resolve()
            out_file.parent.mkdir(parents=True, exist_ok=True)
            img.save(str(out_file), "PNG")
            logger.debug("Successfully saved viral thumbnail to %s", out_file)
            return str(out_file)
        except Exception as e:
            logger.error("Failed to generate or save viral thumbnail image to '%s': %s", output_path, e)
            raise ThumbnailGenerationError(f"Failed to save thumbnail image to '{output_path}': {e}") from e
