import os
import sys
import random
from pathlib import Path

import pytest
from PIL import Image

os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.parsers.image_extractor import extract_images  # noqa: E402


def _create_pdf_with_images(pdf_path: Path) -> None:
    """Create a PDF containing one large and one tiny image."""
    # Large noisy image so compression doesn't shrink it below the threshold
    big_bytes = bytes(random.getrandbits(8) for _ in range(200 * 200 * 3))
    big_img = Image.frombytes("RGB", (200, 200), big_bytes)
    small_img = Image.new("RGB", (10, 10), color="red")
    big_img.save(pdf_path, save_all=True, append_images=[small_img])


def test_extract_images_ignores_small(tmp_path: Path):
    pdf_file = tmp_path / "two_images.pdf"
    _create_pdf_with_images(pdf_file)
    images = extract_images(str(pdf_file))
    # Only the large image should be returned because the small one is <20 kB
    assert len(images) == 1
    img = images[0]
    assert img["width"] == 200 and img["height"] == 200
