from fastapi import APIRouter, HTTPException, Body

router = APIRouter(tags=["__test__"])


@router.get("/ok")
async def ok():
    return {"status": "ok"}


@router.get("/boom")
async def boom():
    raise HTTPException(status_code=500, detail="boom")


@router.post("/echo")
async def echo(payload: dict = Body(...)):
    """Return the payload for exercising size metrics."""
    return {"echo": payload}


@router.get("/crash")
async def crash():
    raise RuntimeError("crash")

