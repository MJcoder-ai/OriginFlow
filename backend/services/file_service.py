# backend/services/file_service.py
"""Business logic for file uploads."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import asyncio
import json
from datetime import datetime, timezone
from openai import AsyncOpenAI
from pdfminer.high_level import extract_text

from backend.models.file_asset import FileAsset
from backend.schemas.file_asset import FileAssetUpdate
from backend.utils.id import generate_id


async def run_parsing_job(asset_id: str, session: AsyncSession, ai_client: AsyncOpenAI) -> None:
    """Background job that extracts text and parses a datasheet via AI."""
    asset = await FileService.get(session, asset_id)
    if not asset:
        return

    try:
        pdf_text = await asyncio.to_thread(extract_text, asset.local_path)
        if not pdf_text or len(pdf_text.strip()) < 100:
            raise ValueError("Low quality text extracted. Potential scanned document.")

        extractor_prompt = (
            "You are an expert electronics datasheet extractor. Analyze the text provided. "
            "First, find the part number. Second, find the main description. "
            "Third, find all key electrical parameters and their values. "
            "Fourth, find all absolute maximum ratings. "
            "Finally, assemble this into a single JSON object. Ensure all values are correctly typed as numbers or strings.\n\n"
            f"Datasheet text:\n---\n{pdf_text[:20_000]}\n---"
        )

        extractor_resp = await ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": extractor_prompt}],
            response_format={"type": "json_object"},
        )
        extracted_json_str = extractor_resp.choices[0].message.content

        validator_prompt = (
            "You are a validation AI. The following JSON was extracted from a component datasheet. "
            "Review it for correctness and adherence to the schema. "
            "Correct any obvious typos or formatting errors. Ensure values that should be numbers are not strings. "
            "Return ONLY the cleaned, validated JSON object. Do not add any commentary.\n\n"
            f"Input JSON:\n---\n{extracted_json_str}\n---"
        )

        validator_resp = await ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": validator_prompt}],
            response_format={"type": "json_object"},
        )
        final_payload = json.loads(validator_resp.choices[0].message.content)

        asset.parsed_payload = final_payload
        asset.parsing_status = "success"
        asset.parsed_at = datetime.now(timezone.utc)
    except Exception as e:  # pragma: no cover - log error
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
        # Mark datasheet as manually verified when saved via the UI
        asset.is_human_verified = True
        session.add(asset)
        await session.commit()
        await session.refresh(asset)
        return asset

