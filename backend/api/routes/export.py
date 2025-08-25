from __future__ import annotations
from fastapi import APIRouter, Response
from io import StringIO, BytesIO
import csv, zipfile, json

router = APIRouter(tags=["export"])

def _csv(data: list[dict]) -> bytes:
    if not data: return b""
    out = StringIO()
    w = csv.DictWriter(out, fieldnames=sorted({k for d in data for k in d.keys()}))
    w.writeheader(); w.writerows(data)
    return out.getvalue().encode("utf-8")

@router.get("/export/{session_id}/bom.csv")
async def bom_csv(session_id: str):
    # Placeholder data - would integrate with ODL store
    bom = [{"item":"Inverter","qty":1,"cost":2000},{"item":"Module","qty":8,"cost":300}]
    return Response(content=_csv(bom), media_type="text/csv",
                    headers={"Content-Disposition":"attachment; filename=bom.csv"})

@router.get("/export/{session_id}/schedules.csv")
async def schedules_csv(session_id: str):
    # Placeholder data - would integrate with ODL store  
    routes = [{"bundle":"STR_1","len_m":15.2},{"bundle":"STR_2","len_m":14.8},{"bundle":"AC_TRUNK","len_m":18.0}]
    return Response(content=_csv(routes), media_type="text/csv",
                    headers={"Content-Disposition":"attachment; filename=schedules.csv"})

@router.get("/export/{session_id}/package.zip")
async def package_zip(session_id: str):
    # Placeholder data - would integrate with ODL store
    bom = [{"item":"Inverter","qty":1,"cost":2000},{"item":"Module","qty":8,"cost":300}]
    routes = [{"bundle":"STR_1","len_m":15.2},{"bundle":"STR_2","len_m":14.8},{"bundle":"AC_TRUNK","len_m":18.0}]
    mem = BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("bom.csv", _csv(bom))
        z.writestr("schedules.csv", _csv(routes))
        z.writestr("meta.json", json.dumps({"session_id": session_id, "export_time": "2024-01-01"}, indent=2))
        z.writestr("README.txt", "Exported by OriginFlow. Files: bom.csv, schedules.csv, meta.json")
    mem.seek(0)
    return Response(content=mem.read(), media_type="application/zip",
                    headers={"Content-Disposition":"attachment; filename=originflow_package.zip"})