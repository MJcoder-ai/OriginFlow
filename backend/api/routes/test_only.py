from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["__test__"])


@router.get("/ok")
async def ok():
    return {"status": "ok"}


@router.get("/boom")
async def boom():
    raise HTTPException(status_code=500, detail="boom")

