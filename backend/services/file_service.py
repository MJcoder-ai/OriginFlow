# backend/services/file_service.py
"""Business logic for file uploads."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any
from typing_extensions import TypedDict

import asyncio
import json
from datetime import datetime, timezone
from openai import AsyncOpenAI
import re

# Optional heavy dependencies are imported lazily so tests can run without
# installing full PDF parsing stack.
try:  # pragma: no cover - import guard
    from pdfminer.high_level import extract_text  # type: ignore
except Exception:  # pragma: no cover - fallback when library missing
    def extract_text(*args, **kwargs):  # type: ignore
        raise RuntimeError("pdfminer is required for PDF text extraction")

try:  # pragma: no cover - import guard
    from backend.parsers.image_extractor import extract_images  # image extraction
except Exception:  # pragma: no cover - fallback when dependencies missing
    def extract_images(*args, **kwargs):  # type: ignore
        return []

# Use our dedicated table extraction module.  This relies on Camelot
from backend.parsers.table_extractor import extract_tables

from backend.config import settings

from backend.models.file_asset import FileAsset
from backend.schemas.file_asset import FileAssetUpdate
from backend.utils.id import generate_id
from pathlib import Path
from fastapi import UploadFile


class ParsedSchema(TypedDict, total=False):
    """Loose schema representation stored in the database."""

    part_number: str
    description: str
    package: str
    category: str
    parameters: dict[str, Any]
    ratings: dict[str, Any]
    # Series name for product families. Datasheets covering multiple variants
    # often describe them under a single family or series identifier. This
    # field captures that identifier when present.
    series_name: str
    # Extracted variants from a multi-product datasheet. Each variant is a dict with
    # its own attributes such as part_number, power and voltage. This list may be empty
    # for single-product datasheets.
    variants: list[dict[str, Any]]
    # Structured tables extracted from the datasheet.  Each entry has a
    # ``table_type`` and ``rows`` property.  This field is optional and may
    # be omitted or an empty list if no tables were detected or extracted.
    tables: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Category inference helper
# ---------------------------------------------------------------------------

# Many datasheets do not explicitly specify the component category.  When
# ``category`` or ``device_type`` is missing or set to "unknown", we use a
# simple heuristic to guess the category based on the extracted text,
# description and part number.  This improves lookup accuracy when the
# SystemDesignAgent needs to find a matching panel, inverter or battery.
def infer_category(data: dict[str, Any]) -> str:
    """Infer a component category from extracted datasheet fields.

    Args:
        data: The partially parsed extraction result.

    Returns:
        A string such as "panel", "inverter", "battery", "pump", or "unknown".
    """
    # Build a single lowercase string containing key textual fields.  We
    # deliberately include part number, name, description, and category, plus
    # any known parameters or specs, to search for indicative keywords.  The
    # check is order-agnostic and case-insensitive.
    text_parts: list[str] = []
    try:
        for field_name in ("part_number", "name", "description", "category"):
            val = data.get(field_name)
            if val:
                text_parts.append(str(val))
    except Exception:
        pass
    for key in ("parameters", "ratings", "specs"):
        try:
            val = data.get(key)
            if isinstance(val, dict):
                text_parts.append(" ".join(f"{k}:{v}" for k, v in val.items()))
        except Exception:
            pass
    combined = " ".join(text_parts).lower()
    def contains_any(words: list[str]) -> bool:
        return any(w in combined for w in words)
    # Panels: look for common PV module terms
    if contains_any(["panel", "module"]) or (contains_any(["solar"]) and not contains_any(["controller"])):
        return "panel"
    # Inverters: inverter, converter or charger keywords
    if contains_any(["inverter", "converter", "charger"]):
        return "inverter"
    # Batteries: battery, accumulator keywords
    if contains_any(["battery", "accumulator"]):
        return "battery"
    # Pumps: pumping keywords
    if contains_any(["pump", "water pump", "pumping"]):
        return "pump"
    # Unknown fallback
    return "unknown"


async def run_parsing_job(asset_id: str, session: AsyncSession, ai_client: AsyncOpenAI) -> None:
    """Background job that extracts text and parses a datasheet using multiple techniques."""
    asset = await FileService.get(session, asset_id)
    if not asset:
        return

    try:
        # Extract raw text using pdfminer first. Abort early if too little text was found.
        pdf_text: str = await asyncio.to_thread(extract_text, asset.local_path)
        if not pdf_text or len(pdf_text.strip()) < 100:
            raise ValueError("Low quality text extracted. Potential scanned document.")

        extraction_result: dict[str, Any] = {}
        parsed_tables: list[dict[str, Any]] = []

        # ------------------------------------------------------------------
        # Image extraction from PDF
        # ------------------------------------------------------------------
        # Attempt to extract images using pypdf.  Filter out very small images
        # (e.g. icons) based on raw data size.  Save each image to the
        # datasheet's upload directory and create a FileAsset entry for it.
        try:
            images = extract_images(asset.local_path)
        except Exception:
            images = []
        # Only consider images above 5 kB to avoid logos and icons
        min_bytes = 5 * 1024
        images = [img for img in images if img.get("data") and len(img["data"]) > min_bytes]
        # Directory to store extracted images
        save_dir = Path(asset.local_path).parent / "images"
        save_dir.mkdir(parents=True, exist_ok=True)
        extracted_assets: list[FileAsset] = []
        largest_pixels = 0
        largest_asset: FileAsset | None = None
        for img in images:
            page = img.get("page")
            index = img.get("index")
            ext = img.get("extension", "png")
            width = img.get("width")
            height = img.get("height")
            data_bytes: bytes = img.get("data", b"")  # type: ignore
            # Convert unsupported formats (e.g. JP2, TIFF) to JPEG for browser compatibility.
            # Allowed formats are JPEG/JPG and PNG. Others will be converted to JPEG.
            if ext.lower() not in ("jpg", "jpeg", "png"):
                try:
                    from PIL import Image  # type: ignore
                    import io  # type: ignore
                    with Image.open(io.BytesIO(data_bytes)) as im:
                        # Convert to RGB to avoid palette or alpha issues
                        rgb = im.convert("RGB")
                        buf = io.BytesIO()
                        rgb.save(buf, format="JPEG")
                        data_bytes = buf.getvalue()
                        ext = "jpg"
                        width, height = rgb.size
                except Exception:
                    # If conversion fails, keep original data and extension
                    pass
            filename = f"page{page}_img{index}.{ext}"
            file_id = generate_id("asset")
            file_path = save_dir / filename
            with file_path.open("wb") as f:
                f.write(data_bytes)
            url = f"/static/uploads/{asset.id}/images/{filename}"
            size = len(data_bytes)
            mime_map = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
            }
            mime = mime_map.get(ext.lower(), f"image/{ext.lower()}")
            new_img = FileAsset(
                id=file_id,
                filename=filename,
                mime=mime,
                size=size,
                url=url,
                parent_asset_id=asset.id,
                component_id=None,
                is_extracted=True,
                is_primary=False,
                width=width,
                height=height,
            )
            session.add(new_img)
            extracted_assets.append(new_img)
            try:
                if width and height and (width * height) > largest_pixels:
                    largest_pixels = width * height
                    largest_asset = new_img
            except Exception:
                pass
        # Mark largest as primary
        if largest_asset:
            largest_asset.is_primary = True
        elif extracted_assets:
            # Fallback: mark the first as primary
            extracted_assets[0].is_primary = True
        # Append image metadata to extraction_result for front-end consumption
        if extracted_assets:
            # Flush session to get IDs for new images
            await session.flush()
            extraction_result["images"] = [
                {
                    "id": img.id,
                    "url": img.url,
                    "width": img.width,
                    "height": img.height,
                    "primary": img.is_primary,
                }
                for img in extracted_assets
            ]

        # ------------------------------------------------------------------
        # Rule-based extraction via regex heuristics
        # ------------------------------------------------------------------
        if settings.use_rule_based:
            fields: dict[str, Any] = {}
            m = re.search(r"part\s*number[:\s]+([^\n]+)", pdf_text, re.IGNORECASE)
            if m:
                fields["part_number"] = m.group(1).strip()
            m = re.search(r"description[:\s]+([^\n]+)", pdf_text, re.IGNORECASE)
            if m:
                fields["description"] = m.group(1).strip()
            m = re.search(r"manufacturer[:\s]+([^\n]+)", pdf_text, re.IGNORECASE)
            if m:
                fields["manufacturer"] = m.group(1).strip()
            m = re.search(r"package[:\s]+([^\n]+)", pdf_text, re.IGNORECASE)
            if m:
                fields["package"] = m.group(1).strip()
            m = re.search(r"category[:\s]+([^\n]+)", pdf_text, re.IGNORECASE)
            if m:
                fields["category"] = m.group(1).strip()
            extraction_result.update(fields)

        # ------------------------------------------------------------------
        # Table extraction using Camelot
        # ------------------------------------------------------------------
        if settings.use_table_extraction:
            try:
                parsed_tables = extract_tables(asset.local_path)
                if parsed_tables:
                    extraction_result["tables"] = parsed_tables
            except Exception:
                extraction_result.setdefault("tables", [])

        # ------------------------------------------------------------------
        # AI-driven extraction combining text and tables
        # ------------------------------------------------------------------
        if settings.use_ai_extraction:
            prompt_parts = [
                "You are an expert electronics datasheet extractor. Read the text and extracted tables below and return a comprehensive JSON object with as many relevant fields as possible.",
                # Make mechanical_characteristics, packaging_configuration and warranty explicit objects.
                "The JSON should include keys like part_number, manufacturer, description, package, category, recommended_operating_conditions, electrical_parameters, absolute_maximum_ratings, pin_configuration, dimensions, safety_certifications, mechanical_characteristics, packaging_configuration, warranty, and any other relevant data you can infer. For mechanical_characteristics, extract an object with the keys: cell_type, number_of_cells, dimensions, weight, front_glass, frame, junction_box and output_cables. For packaging_configuration, extract an object with the keys: pallets_per_stack, pcs_per_pallet, pcs_per_stack and pcs_per_container. For warranty, extract an object with the keys: product_years and power_years.",
                "Ensure numbers are returned as numbers where appropriate and leave null or empty structures for missing fields.",
                "\n\nDatasheet text:\n---\n" + pdf_text[:20_000] + "\n---",
            ]
            if parsed_tables:
                # Convert parsed tables into markdown.  Include the table type as
                # a heading so the AI knows what each table represents.  Each
                # row is joined by pipes for readability.  Separate multiple
                # tables with blank lines.
                table_md_list: list[str] = []
                for tbl in parsed_tables:
                    rows = [" | ".join(cell.strip() for cell in row) for row in tbl.get("rows", [])]
                    header = f"**{tbl.get('table_type', 'unknown table')}**"
                    table_md_list.append(header + "\n" + "\n".join(rows))
                tables_md = "\n\nExtracted tables:\n---\n" + "\n\n".join(table_md_list) + "\n---"
                prompt_parts.append(tables_md)

            extractor_resp = await ai_client.chat.completions.create(
                model=settings.openai_model_router,
                messages=[{"role": "user", "content": "\n\n".join(prompt_parts)}],
                response_format={"type": "json_object"},
            )
            extracted_json_str = extractor_resp.choices[0].message.content
            validator_prompt = (
                "You are a validation AI. The following JSON was extracted from a component datasheet. "
                "Review it for correctness and adherence to the schema. "
                "Correct any obvious typos or formatting errors. Ensure values that should be numbers are numbers. "
                "Return ONLY the cleaned, validated JSON object. Do not add any commentary.\n\n"
                f"Input JSON:\n---\n{extracted_json_str}\n---"
            )
            validator_resp = await ai_client.chat.completions.create(
                model=settings.openai_model_router,
                messages=[{"role": "user", "content": validator_prompt}],
                response_format={"type": "json_object"},
            )
            ai_payload = json.loads(validator_resp.choices[0].message.content)
            extraction_result.update(ai_payload)

        # Infer a category when missing or unknown.  Some datasheets omit a
        # category or mislabel it as "unknown".  Use heuristic inference to
        # assign a sensible category (panel, inverter, battery, pump) based on
        # part number, description and specs.  See ``infer_category()`` for
        # details.  Only update when a non-unknown guess is returned.
        category_value = extraction_result.get("category") or extraction_result.get("device_type")
        if not category_value or (
            isinstance(category_value, str) and category_value.lower() == "unknown"
        ):
            guessed_cat = infer_category(extraction_result)
            if guessed_cat and guessed_cat != "unknown":
                extraction_result["category"] = guessed_cat

        # Persist success results
        asset.parsed_payload = extraction_result
        asset.parsing_status = "success"
        asset.parsed_at = datetime.now(timezone.utc)

        # ------------------------------------------------------------------
        # Phase 2: Datasheet Extraction & Library Augmentation
        #
        # When a datasheet is successfully parsed, automatically update
        # the master component library with the extracted metadata.  This
        # enrichment step creates or updates a ComponentMaster record based
        # on the part number and other fields found in the datasheet.  It
        # stores the full parsed JSON as the ``specs`` column and fills in
        # common fields (name, manufacturer, category, voltage, current,
        # power, ports, dependencies, layer_affinity, sub_elements) where
        # available.  Failures during this enrichment are swallowed so
        # they do not block the overall parsing pipeline.
        try:
            from backend.services.component_db_service import ComponentDBService
            from backend.schemas.component_master import ComponentMasterCreate

            # Instantiate the component DB service using the current session
            comp_service = ComponentDBService(session)

            # Extract common fields from the payload, falling back to
            # sensible defaults if keys are missing.  The extracted JSON
            # may use various naming conventions; try multiple keys.
            part_number = (
                extraction_result.get("part_number")
                or extraction_result.get("pn")
                or extraction_result.get("partNumber")
            )
            manufacturer = (
                extraction_result.get("manufacturer")
                or extraction_result.get("mfg")
                or extraction_result.get("maker")
            )
            # Use description as the human-friendly name when available.
            name = (
                extraction_result.get("description")
                or extraction_result.get("name")
                or part_number
                or "Unknown component"
            )
            category = (
                extraction_result.get("category")
                or extraction_result.get("device_type")
                or "unknown"
            )
            description = extraction_result.get("description")

            # Numerical fields may be nested; attempt to coerce to float if
            # present.  If parsing fails, default to None.
            def _to_float(value: Any) -> float | None:
                try:
                    if isinstance(value, (int, float)):
                        return float(value)
                    if isinstance(value, str):
                        return float(value.strip().split()[0])
                except Exception:
                    return None
                return None

            voltage = _to_float(
                extraction_result.get("voltage")
                or extraction_result.get("nominal_voltage")
            )
            current = _to_float(
                extraction_result.get("current")
                or extraction_result.get("nominal_current")
            )
            power = _to_float(
                extraction_result.get("power")
                or extraction_result.get("max_power")
                or extraction_result.get("rated_power")
            )

            # Optional complex fields
            ports = extraction_result.get("ports")
            dependencies = extraction_result.get("dependencies")
            layer_affinity = extraction_result.get("layer_affinity")
            sub_elements = extraction_result.get("sub_elements")
            series_name = extraction_result.get("series_name")
            variants = extraction_result.get("variants")

            # Proceed only if a part number was extracted; skip otherwise
            if part_number:
                existing = await comp_service.get_by_part_number(part_number)
                data = {
                    "part_number": part_number,
                    "name": name,
                    "manufacturer": manufacturer or "Unknown",
                    "category": category,
                    "description": description,
                    "voltage": voltage,
                    "current": current,
                    "power": power,
                    "specs": extraction_result,
                    "ports": ports,
                    "dependencies": dependencies,
                    "layer_affinity": layer_affinity,
                    "sub_elements": sub_elements,
                    "series_name": series_name,
                    "variants": variants,
                }
                # Remove keys with value None to respect default nullability
                data = {k: v for k, v in data.items() if v is not None}

                if existing:
                    # Update the existing record in-place
                    for key, value in data.items():
                        setattr(existing, key, value)
                    session.add(existing)
                    await session.commit()
                    await session.refresh(existing)
                else:
                    # Create a new record
                    create_obj = ComponentMasterCreate(**data)
                    await comp_service.create(create_obj)
        except Exception:
            # Swallow any errors during enrichment so that parsing continues
            pass
    except Exception as e:
        asset.parsing_status = "failed"
        asset.parsing_error = str(e)
    session.add(asset)
    await session.commit()


class FileService:
    """Service layer for file asset CRUD."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_asset(self, data: dict) -> FileAsset:
        payload = dict(data)
        asset_id = payload.pop("id", generate_id("asset"))
        payload["uploaded_at"] = datetime.now(timezone.utc)
        obj = FileAsset(id=asset_id, **payload)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def list_assets(self) -> list[FileAsset]:
        """Return only top-level PDF file assets.

        Child assets such as images use ``parent_asset_id`` to reference their
        parent datasheet and should not appear in the general file listing.
        """
        stmt = select(FileAsset).where(FileAsset.parent_asset_id.is_(None))
        stmt = stmt.where(FileAsset.mime == "application/pdf")
        result = await self.session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get(session: AsyncSession, asset_id: str) -> FileAsset | None:
        """Retrieve a single asset by ID."""
        return await session.get(FileAsset, asset_id)

    @staticmethod
    async def trigger_parsing(asset: FileAsset, session: AsyncSession) -> FileAsset:
        """Mark an asset as processing and persist."""
        if asset.parsing_status in {"processing", "success"}:
            return asset
        asset.parsing_status = "processing"
        asset.parsing_error = None
        session.add(asset)
        await session.commit()
        await session.refresh(asset)
        return asset

    @staticmethod
    async def parse_datasheet(
        asset: FileAsset, session: AsyncSession, ai_client: AsyncOpenAI
    ) -> FileAsset:
        """Synchronously parse a datasheet via AI (legacy)."""
        await run_parsing_job(asset.id, session, ai_client)
        await session.refresh(asset)
        return asset

    @staticmethod
    async def update_asset(asset: FileAsset, update_data: FileAssetUpdate, session: AsyncSession) -> FileAsset:
        """Update parsed payload and mark the asset as verified."""
        asset.parsed_payload = update_data.parsed_payload
        asset.parsed_at = datetime.now(timezone.utc)
        # Only update the human verification flag if explicitly supplied in the request.
        if update_data.is_human_verified is not None:
            asset.is_human_verified = update_data.is_human_verified
        session.add(asset)
        await session.commit()
        await session.refresh(asset)
        return asset

    # ------------------------------------------------------------------
    # Image management methods
    # ------------------------------------------------------------------
    async def list_images(self, asset_id: str) -> list[dict[str, Any]]:
        """Return all image assets linked to a datasheet via ``parent_asset_id``.

        Both images extracted from the PDF and those uploaded manually are
        returned.  The query filters on ``parent_asset_id`` so that images are
        associated with their parent datasheet rather than a schematic
        component.
        """
        stmt = select(FileAsset).where(FileAsset.parent_asset_id == asset_id)
        result = await self.session.execute(stmt)
        images_models = result.scalars().all()
        images: list[dict[str, Any]] = []
        for img in images_models:
            images.append(
                {
                    "id": img.id,
                    "filename": img.filename,
                    "url": img.url,
                    "is_primary": img.is_primary,
                    "is_extracted": img.is_extracted,
                    "width": img.width,
                    "height": img.height,
                }
            )
        return images

    async def upload_images(self, asset_id: str, files: list[UploadFile]) -> list[FileAsset]:
        """Upload one or more image files and associate them with a datasheet asset."""
        asset = await FileService.get(self.session, asset_id)
        if not asset:
            raise ValueError("Asset not found")
        # Directory under uploads/{asset_id}/images
        save_dir = Path(asset.local_path).parent / "images"
        save_dir.mkdir(parents=True, exist_ok=True)
        saved_assets: list[FileAsset] = []
        for upl in files:
            # Generate a new asset ID for each uploaded image
            img_id = generate_id("asset")
            filename = upl.filename
            file_path = save_dir / filename
            # Write the content
            content = await upl.read()
            with file_path.open("wb") as buf:
                buf.write(content)
            url = f"/static/uploads/{asset.id}/images/{filename}"
            size = len(content)
            # Determine content type and dimensions
            content_type = upl.content_type or "image/png"
            width = height = None
            try:
                from PIL import Image
                import io

                with Image.open(io.BytesIO(content)) as im:
                    width, height = im.size
            except Exception:
                pass
            new_asset = FileAsset(
                id=img_id,
                filename=filename,
                mime=content_type,
                size=size,
                url=url,
                parent_asset_id=asset.id,
                component_id=None,
                is_extracted=False,
                is_primary=False,
                width=width,
                height=height,
            )
            self.session.add(new_asset)
            saved_assets.append(new_asset)
        await self.session.commit()
        for img in saved_assets:
            await self.session.refresh(img)
        return saved_assets

    async def delete_image(self, asset_id: str, image_id: str) -> None:
        """Remove an image file associated with a datasheet and its record.

        If the deleted image was marked as primary, the largest remaining image
        (by pixel area) will be promoted to primary.
        """
        img = await FileService.get(self.session, image_id)
        if not img or img.parent_asset_id != asset_id:
            raise ValueError("Image not found or does not belong to this asset")
        was_primary = img.is_primary
        # Remove file from disk
        try:
            path = img.local_path
            if path.exists():  # type: ignore[attr-defined]
                path.unlink(missing_ok=True)  # type: ignore[attr-defined]
        except Exception:
            pass
        await self.session.delete(img)
        await self.session.commit()

        if was_primary:
            stmt = select(FileAsset).where(FileAsset.parent_asset_id == asset_id)
            result = await self.session.execute(stmt)
            remaining = result.scalars().all()
            largest = None
            largest_pixels = 0
            for im in remaining:
                try:
                    if im.width and im.height and (im.width * im.height) > largest_pixels:
                        largest_pixels = im.width * im.height
                        largest = im
                except Exception:
                    pass
            if largest:
                for im in remaining:
                    im.is_primary = im.id == largest.id
                    self.session.add(im)
                await self.session.commit()

    async def set_primary_image(self, asset_id: str, image_id: str) -> None:
        """Set a specific image as the primary thumbnail for a datasheet."""
        stmt = select(FileAsset).where(FileAsset.parent_asset_id == asset_id)
        result = await self.session.execute(stmt)
        imgs = result.scalars().all()
        target = None
        for img in imgs:
            if img.id == image_id:
                target = img
                img.is_primary = True
            else:
                img.is_primary = False
            self.session.add(img)
        if target is None:
            raise ValueError("Image not found")
        await self.session.commit()

