from fastapi import APIRouter, Depends
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, timezone
from backend.services.file_service import FileService, ParsedSchema
from sqlalchemy.ext.asyncio import AsyncSession
from ..deps import get_session
from openai import AsyncOpenAI
import json

router = APIRouter(prefix="/ai", tags=["ai"])

class ImproveRequest(BaseModel):
    file_id: UUID
    user_message: str
    current_payload: ParsedSchema

@router.post("/improve-datasheet", response_model=ParsedSchema)
async def improve_datasheet(
    req: ImproveRequest,
    session: AsyncSession = Depends(get_session),
) -> ParsedSchema:
    prompt = (
        "You are an expert electronics assistant.\n"
        "Here is the current extracted JSON from a component datasheet:\n"
        f"{json.dumps(req.current_payload, indent=2)}\n\n"
        f"User request: {req.user_message}\n"
        "Return ONLY the corrected JSON."
    )
    resp = await AsyncOpenAI().chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.2,
    )
    new_payload: ParsedSchema = json.loads(resp.choices[0].message.content)
    # persist
    asset = await FileService.get(session, req.file_id)
    asset.parsed_payload = new_payload
    asset.parsed_at = datetime.now(timezone.utc)
    await session.commit()
    return new_payload
