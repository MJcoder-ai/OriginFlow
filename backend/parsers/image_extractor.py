"""Utilities for extracting images from PDF documents.

This module provides a single helper :func:`extract_images` which uses
:mod:`pypdf` to iterate over the pages of a PDF and yield embedded images.
Each image's raw bytes are loaded into :class:`PIL.Image` to determine its
pixel dimensions and other metadata.  Very small images (less than 20 kB)
are ignored to avoid icons and similar boilerplate graphics.

The function returns a list of dictionaries with the following keys::

    {
        "page": int,        # page number starting at 1
        "index": int,       # index of the image on that page
        "name": str,        # original name if provided by the PDF
        "extension": str,   # best guess file extension
        "mime": str,        # MIME type
        "width": int,       # pixel width
        "height": int,      # pixel height
        "data": bytes,      # raw image bytes
    }

The extracted data is suitable for saving to disk or further processing in
the parsing pipeline.
"""

from __future__ import annotations

from io import BytesIO
from typing import Dict, List
import logging

from pypdf import PdfReader
from PIL import Image

logger = logging.getLogger(__name__)

# Minimum number of bytes for an image to be considered.  This helps skip
# icons and other tiny graphics that are often embedded in datasheets.
MIN_BYTES = 20 * 1024


def _guess_extension(name: str | None, mime: str | None) -> str:
    """Return a best-guess file extension for an image.

    The extension is derived from the image name if present, otherwise from
    the MIME type.  Defaults to ``"png"`` if no information is available.
    """

    if name and "." in name:
        return name.rsplit(".", 1)[1].lower()
    if mime and "/" in mime:
        return mime.split("/", 1)[1].lower()
    return "png"


def extract_images(pdf_path: str) -> List[Dict]:
    """Extract embedded images from a PDF file.

    Args:
        pdf_path: Path to the PDF file on disk.

    Returns:
        A list of dictionaries with image metadata and raw bytes.  Images
        smaller than ``MIN_BYTES`` are filtered out.
    """

    results: List[Dict] = []
    try:
        reader = PdfReader(pdf_path)
    except Exception as exc:
        logger.debug("pypdf failed to read %s: %s", pdf_path, exc)
        return results

    for page_index, page in enumerate(reader.pages, start=1):
        try:
            images = getattr(page, "images", [])
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Failed to access images on page %d: %s", page_index, exc)
            continue
        for image_index, image_obj in enumerate(images, start=1):
            data = image_obj.data  # raw bytes
            if not data or len(data) < MIN_BYTES:
                continue
            name = getattr(image_obj, "name", None)
            mime = getattr(image_obj, "mime_type", None)
            ext = _guess_extension(name, mime)
            width = height = None
            try:
                with Image.open(BytesIO(data)) as im:
                    width, height = im.size
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("Pillow failed to read image on page %d: %s", page_index, exc)
            results.append(
                {
                    "page": page_index,
                    "index": image_index,
                    "name": name,
                    "extension": ext,
                    "mime": mime,
                    "width": width,
                    "height": height,
                    "data": data,
                }
            )
    return results
