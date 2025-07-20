from __future__ import annotations

import json
import asyncio
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, Depends
from pdfminer.high_level import extract_text
from openai import AsyncOpenAI

from ..deps import get_ai_client

router = APIRouter()

@router.post("/parse-datasheet")
async def parse_datasheet(
    file: UploadFile = File(...),
    ai_client: AsyncOpenAI = Depends(get_ai_client),
) -> dict:
    """Parse a PDF datasheet and return extracted fields."""
    pdf_text = await asyncio.to_thread(extract_text, file.file)
    extractor_prompt = (
        "You are an expert electronics datasheet extractor. "
        "Return a JSON object of the key fields.\n\n" + pdf_text[:20_000]
    )
    resp = await ai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": extractor_prompt}],
        response_format={"type": "json_object"},
    )
    payload = json.loads(resp.choices[0].message.content)
    return {"assetId": str(uuid4()), "fields": payload}
