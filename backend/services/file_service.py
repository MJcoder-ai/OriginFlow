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


class FileService:
    """Service layer for file asset CRUD."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_asset(self, data: dict) -> FileAsset:
        payload = dict(data)
        asset_id = payload.pop("id", generate_id("asset"))
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
    async def parse_datasheet(asset: FileAsset, session: AsyncSession) -> FileAsset:
        """Parse a PDF datasheet via AI if not already parsed."""
        if asset.parsed_at:
            return asset
        try:
            pdf_text = await asyncio.to_thread(extract_text, asset.local_path)
        except Exception as e:  # pragma: no cover - log error
            print(f"Error extracting text from {asset.filename}: {e}")
            return asset

        ai = AsyncOpenAI()
        prompt = (
            "You are an expert electronics assistant. Extract key specifications "
            "from the following component datasheet and return ONLY valid JSON:\n"
            '{"part_number":str,"description":str,"package":str,"category":str,'
            '"parameters":{str:str|float},"ratings":{str:str|float}}\n\n'
            f"Datasheet text (first 20,000 chars):\n---\n{pdf_text[:20_000]}\n---"
        )
        try:
            resp = await ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content
            asset.parsed_payload = json.loads(content)
            asset.parsed_at = datetime.now(timezone.utc)
            session.add(asset)
            await session.commit()
            await session.refresh(asset)
        except Exception as e:  # pragma: no cover - log error
            print(f"AI parsing failed for {asset.filename}: {e}")
        return asset

    @staticmethod
    async def update_asset(asset: FileAsset, update_data: FileAssetUpdate, session: AsyncSession) -> FileAsset:
        """Update parsed_payload and timestamp."""
        asset.parsed_payload = update_data.parsed_payload
        asset.parsed_at = datetime.now(timezone.utc)
        session.add(asset)
        await session.commit()
        await session.refresh(asset)
        return asset

