"""
Report API - Araştırma raporlarını farklı formatlarda indirme endpoint'leri.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from backend.app.services.report_generator import ReportGenerator
from typing import List
import os

router = APIRouter()
report_gen = ReportGenerator()

class ReportRequest(BaseModel):
    research_result: dict
    formats: List[str] = ["md", "html", "json"]

@router.post("/save")
async def save_report(request: ReportRequest):
    """Araştırma sonuçlarını belirtilen formatlarda kaydeder."""
    saved = report_gen.save_report(request.research_result, request.formats)
    return {"status": "success", "saved_files": saved}

@router.get("/download/{filename}")
async def download_report(filename: str):
    """Kaydedilmiş bir raporu indirir."""
    file_path = f"reports/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Rapor bulunamadı.")
    return FileResponse(file_path, filename=filename)

@router.post("/preview/html")
async def preview_html(research_result: dict):
    """Anlık HTML içeriği döndürür (kaydetmez)."""
    html = report_gen.generate_html(research_result)
    return Response(content=html, media_type="text/html")

@router.post("/preview/markdown")
async def preview_markdown(research_result: dict):
    """Anlık Markdown içeriği döndürür (kaydetmez)."""
    md = report_gen.generate_markdown(research_result)
    return Response(content=md, media_type="text/plain")
