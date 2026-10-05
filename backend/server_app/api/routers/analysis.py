from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import json
from server_app.core.database import get_session
from server_app.models.models import (
    AnalysisReport, FeatureGapItem, FlowComparisonItem, 
    CompetitorOverviewItem, Project, InternalApp, Competitor
)
from server_app.services.analysis_engine import AnalysisEngine

router = APIRouter(prefix="/analysis", tags=["analysis"])

class RunAnalysisRequest(BaseModel):
    project_id: str
    provider: str = "gemini"
    auto_discover: bool = True
    discover_limit: int = 3
    custom_keywords: Optional[str] = None

def format_report_response(report: AnalysisReport, session: Session) -> Dict[str, Any]:
    project = session.get(Project, report.project_id)
    gaps = session.exec(select(FeatureGapItem).where(FeatureGapItem.report_id == report.id)).all()
    flows = session.exec(select(FlowComparisonItem).where(FlowComparisonItem.report_id == report.id)).all()
    overviews = session.exec(select(CompetitorOverviewItem).where(CompetitorOverviewItem.report_id == report.id)).all()

    formatted_gaps = []
    for g in gaps:
        try:
            sources = json.loads(g.official_sources_json) if g.official_sources_json else []
        except Exception:
            sources = []
        formatted_gaps.append({
            "id": g.id,
            "competitor_name": g.competitor_name,
            "feature_name": g.feature_name,
            "category": g.category,
            "internal_status": g.internal_status,
            "innovation_highlight": g.innovation_highlight,
            "impact_score": g.impact_score,
            "effort_score": g.effort_score,
            "official_sources": sources
        })

    formatted_flows = []
    for f in flows:
        formatted_flows.append({
            "id": f.id,
            "flow_name": f.flow_name,
            "internal_steps": f.internal_steps,
            "competitor_detected_flow": f.competitor_detected_flow,
            "friction_points": f.friction_points,
            "simplification_recommendation": f.simplification_recommendation
        })

    formatted_overviews = []
    for o in overviews:
        try:
            strengths = json.loads(o.key_strengths_json) if o.key_strengths_json else []
        except Exception:
            strengths = []
        try:
            weaknesses = json.loads(o.key_weaknesses_json) if o.key_weaknesses_json else []
        except Exception:
            weaknesses = []

        formatted_overviews.append({
            "id": o.id,
            "competitor_name": o.competitor_name,
            "playstore_score": o.playstore_score,
            "ratings_count": o.ratings_count,
            "key_strengths": strengths,
            "key_weaknesses": weaknesses,
            "playstore_url": o.playstore_url,
            "website_url": o.website_url
        })

    # Ambil info internal app
    internal_app = session.exec(select(InternalApp).where(InternalApp.project_id == report.project_id)).first()
    internal_app_data = None
    if internal_app:
        try:
            mods = json.loads(internal_app.modules_features_json) if internal_app.modules_features_json else []
        except Exception:
            mods = []
        try:
            flows = json.loads(internal_app.user_flows_json) if internal_app.user_flows_json else []
        except Exception:
            flows = []
        internal_app_data = {
            "app_name": internal_app.app_name,
            "category": internal_app.category,
            "description": internal_app.description,
            "target_audience": internal_app.target_audience,
            "modules_features": mods,
            "user_flows": flows
        }

    # Ambil info kompetitor proyek
    comps = session.exec(select(Competitor).where(Competitor.project_id == report.project_id)).all()
    competitors_data = []
    for c in comps:
        competitors_data.append({
            "name": c.name,
            "playstore_package": c.playstore_package,
            "website_url": c.website_url
        })

    return {
        "id": report.id,
        "project_id": report.project_id,
        "project_title": project.title if project else "Project",
        "project_category": project.category if project else "General",
        "project_description": project.description if project else "",
        "internal_app": internal_app_data,
        "competitors": competitors_data,
        "summary": report.summary,
        "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "feature_gaps": formatted_gaps,
        "flow_comparisons": formatted_flows,
        "competitor_overviews": formatted_overviews
    }

@router.post("/run")
async def run_analysis(data: RunAnalysisRequest, session: Session = Depends(get_session)):
    try:
        report = await AnalysisEngine.run_project_analysis(
            project_id=data.project_id,
            provider=data.provider,
            session=session,
            auto_discover=data.auto_discover,
            discover_limit=data.discover_limit,
            custom_keywords=data.custom_keywords
        )
        return format_report_response(report, session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/project/{project_id}/latest")
def get_latest_project_analysis(project_id: str, session: Session = Depends(get_session)):
    report = session.exec(
        select(AnalysisReport)
        .where(AnalysisReport.project_id == project_id)
        .order_by(AnalysisReport.created_at.desc())
    ).first()

    if not report:
        return None

    return format_report_response(report, session)

@router.patch("/feature-gap/{gap_id}")
def update_gap_status(gap_id: str, payload: Dict[str, Any], session: Session = Depends(get_session)):
    gap = session.get(FeatureGapItem, gap_id)
    if not gap:
        raise HTTPException(status_code=404, detail="Item gap fitur tidak ditemukan")

    if "internal_status" in payload:
        gap.internal_status = payload["internal_status"]
    if "impact_score" in payload:
        gap.impact_score = int(payload["impact_score"])
    if "effort_score" in payload:
        gap.effort_score = int(payload["effort_score"])

    session.add(gap)
    session.commit()
    return {"status": "success", "message": "Status gap berhasil diperbarui"}

@router.delete("/project/{project_id}")
def delete_project_analyses(project_id: str, session: Session = Depends(get_session)):
    """
    Menghapus seluruh riwayat laporan riset untuk proyek ini (Reset Laporan).
    """
    reports = session.exec(select(AnalysisReport).where(AnalysisReport.project_id == project_id)).all()
    for r in reports:
        gaps = session.exec(select(FeatureGapItem).where(FeatureGapItem.report_id == r.id)).all()
        for g in gaps:
            session.delete(g)
        flows = session.exec(select(FlowComparisonItem).where(FlowComparisonItem.report_id == r.id)).all()
        for f in flows:
            session.delete(f)
        overviews = session.exec(select(CompetitorOverviewItem).where(CompetitorOverviewItem.report_id == r.id)).all()
        for o in overviews:
            session.delete(o)
        session.delete(r)
    session.commit()
    return {"status": "success", "message": f"{len(reports)} riwayat laporan berhasil dihapus"}
