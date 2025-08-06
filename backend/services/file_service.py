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
from pdfminer.high_level import extract_text
import re
# Use our dedicated table extraction module.  This relies on Camelot
from backend.parsers.table_extractor import extract_tables

from backend.config import settings

from backend.models.file_asset import FileAsset
from backend.schemas.file_asset import FileAssetUpdate
from backend.utils.id import generate_id


class ParsedSchema(TypedDict, total=False):
    """Loose schema representation stored in the database."""

    part_number: str
    description: str
    package: str
    category: str
    parameters: dict[str, Any]
    ratings: dict[str, Any]
    # Structured tables extracted from the datasheet.  Each entry has a
    # ``table_type`` and ``rows`` property.  This field is optional and may
    # be omitted or an empty list if no tables were detected or extracted.
    tables: list[dict[str, Any]]


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
        """Return all persisted file assets."""
        result = await self.session.execute(select(FileAsset))
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

