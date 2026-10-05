from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse, HTMLResponse
from sqlmodel import Session
from server_app.core.database import get_session
from server_app.models.models import AnalysisReport
from server_app.api.routers.analysis import format_report_response
from server_app.services.exporter import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])

@router.get("/{report_id}/excel")
def download_excel(report_id: str, session: Session = Depends(get_session)):
    report = session.get(AnalysisReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")

    data = format_report_response(report, session)
    stream = ExportService.export_excel(data)
    
    filename = f"competitor_gap_report_{report.project_id[:8]}.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/{report_id}/csv")
def download_csv(report_id: str, session: Session = Depends(get_session)):
    report = session.get(AnalysisReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")

    data = format_report_response(report, session)
    csv_text = ExportService.export_csv(data)
    
    filename = f"competitor_gaps_{report.project_id[:8]}.csv"
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/{report_id}/markdown")
def download_markdown(report_id: str, session: Session = Depends(get_session)):
    report = session.get(AnalysisReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")

    data = format_report_response(report, session)
    md_text = ExportService.export_markdown(data)
    
    filename = f"competitor_analysis_{report.project_id[:8]}.md"
    return Response(
        content=md_text,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/{report_id}/pdf")
def download_pdf(report_id: str, session: Session = Depends(get_session)):
    """
    Mengunduh laporan lengkap dalam format file PDF (.pdf).
    """
    report = session.get(AnalysisReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")

    data = format_report_response(report, session)
    pdf_stream = ExportService.export_pdf(data)
    
    filename = f"Laporan_Riset_Kompetitor_{report.project_id[:8]}.pdf"
    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/{report_id}/html", response_class=HTMLResponse)
@router.get("/{report_id}/print", response_class=HTMLResponse)
def view_printable_html(report_id: str, session: Session = Depends(get_session)):
    """
    Menampilkan pratinjau laporan cetak interaktif (Print View) siap simpan ke PDF.
    """
    report = session.get(AnalysisReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")

    data = format_report_response(report, session)
    html_content = ExportService.export_html(data)
    return HTMLResponse(content=html_content)
