from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
import json
from app.core.database import get_session
from app.models.models import Competitor, Project, InternalApp
from app.services.scraper_playstore import PlayStoreScraper
from app.services.scraper_web import WebScraper
from app.services.analysis_engine import AnalysisEngine

router = APIRouter(prefix="/competitors", tags=["competitors"])

class CompetitorAutoDiscoverRequest(BaseModel):
    project_id: str
    query: Optional[str] = None
    limit: int = 3

class CompetitorCreate(BaseModel):
    project_id: str
    name: str
    playstore_package: str = ""
    website_url: str = ""
    extra_urls: List[str] = []

class CompetitorResponse(BaseModel):
    id: str
    project_id: str
    name: str
    playstore_package: str
    website_url: str
    extra_urls: List[str]

@router.get("/project/{project_id}", response_model=List[CompetitorResponse])
def get_competitors_by_project(project_id: str, session: Session = Depends(get_session)):
    comps = session.exec(select(Competitor).where(Competitor.project_id == project_id)).all()
    results = []
    for c in comps:
        try:
            extra = json.loads(c.extra_urls_json) if c.extra_urls_json else []
        except Exception:
            extra = []
        results.append(CompetitorResponse(
            id=c.id,
            project_id=c.project_id,
            name=c.name,
            playstore_package=c.playstore_package,
            website_url=c.website_url,
            extra_urls=extra
        ))
    return results

@router.post("", response_model=CompetitorResponse)
def add_competitor(data: CompetitorCreate, session: Session = Depends(get_session)):
    proj = session.get(Project, data.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    c = Competitor(
        project_id=data.project_id,
        name=data.name,
        playstore_package=data.playstore_package.strip(),
        website_url=data.website_url.strip(),
        extra_urls_json=json.dumps(data.extra_urls)
    )
    session.add(c)
    session.commit()
    session.refresh(c)
    return CompetitorResponse(
        id=c.id,
        project_id=c.project_id,
        name=c.name,
        playstore_package=c.playstore_package,
        website_url=c.website_url,
        extra_urls=data.extra_urls
    )

@router.delete("/{competitor_id}")
def delete_competitor(competitor_id: str, session: Session = Depends(get_session)):
    c = session.get(Competitor, competitor_id)
    if not c:
        raise HTTPException(status_code=404, detail="Kompetitor tidak ditemukan")
    session.delete(c)
    session.commit()
    return {"status": "success", "message": "Kompetitor berhasil dihapus"}

@router.delete("/project/{project_id}/all")
def clear_all_competitors(project_id: str, session: Session = Depends(get_session)):
    """
    Menghapus semua kompetitor dalam proyek ini sekaligus.
    """
    comps = session.exec(select(Competitor).where(Competitor.project_id == project_id)).all()
    count = len(comps)
    for c in comps:
        session.delete(c)
    session.commit()
    return {"status": "success", "message": f"{count} kompetitor berhasil dihapus"}

@router.get("/preview/playstore")
def preview_playstore(package_name: str):
    """
    Test scraping Play Store untuk memvalidasi package name sebelum disimpan.
    """
    if not package_name.strip():
        raise HTTPException(status_code=400, detail="Package name tidak boleh kosong")
    data = PlayStoreScraper.scrape_app_details(package_name.strip())
    return data

@router.get("/preview/website")
async def preview_website(url: str):
    """
    Test scraping website resmi untuk memvalidasi URL.
    """
    if not url.strip():
        raise HTTPException(status_code=400, detail="URL tidak boleh kosong")
    data = await WebScraper.scrape_url(url.strip())
    return data

@router.get("/discover-preview")
def discover_competitor_preview(
    project_id: str, 
    query: Optional[str] = None, 
    limit: int = 4, 
    session: Session = Depends(get_session)
):
    """
    Memberikan rekomendasi kompetitor Play Store berdasarkan aplikasi internal secara instan.
    """
    internal_app = session.exec(select(InternalApp).where(InternalApp.project_id == project_id)).first()
    queries = AnalysisEngine.determine_search_queries(internal_app, query)

    existing_comps = session.exec(select(Competitor).where(Competitor.project_id == project_id)).all()
    existing_pkgs = {c.playstore_package.strip().lower() for c in existing_comps if c.playstore_package}

    candidates = []
    seen = set(existing_pkgs)
    for q in queries:
        if len(candidates) >= limit:
            break
        hits = PlayStoreScraper.search_competitor_apps(q, n_hits=limit + 3)
        for h in hits:
            pkg = h["package_name"].lower()
            if pkg in seen:
                continue
            if internal_app and internal_app.app_name.lower() in h["title"].lower():
                continue
            seen.add(pkg)
            candidates.append(h)
            if len(candidates) >= limit:
                break

    return candidates

@router.post("/auto-discover", response_model=List[CompetitorResponse])
async def auto_discover_and_add(
    data: CompetitorAutoDiscoverRequest, 
    session: Session = Depends(get_session)
):
    """
    Mencari dan langsung menambahkan kompetitor Play Store ke dalam proyek.
    """
    internal_app = session.exec(select(InternalApp).where(InternalApp.project_id == data.project_id)).first()
    await AnalysisEngine.auto_discover_and_register_competitors(
        project_id=data.project_id,
        internal_app=internal_app,
        limit=data.limit,
        custom_keywords=data.query,
        session=session
    )

    comps = session.exec(select(Competitor).where(Competitor.project_id == data.project_id)).all()
    results = []
    for c in comps:
        try:
            extra = json.loads(c.extra_urls_json) if c.extra_urls_json else []
        except Exception:
            extra = []
        results.append(CompetitorResponse(
            id=c.id,
            project_id=c.project_id,
            name=c.name,
            playstore_package=c.playstore_package,
            website_url=c.website_url,
            extra_urls=extra
        ))
    return results
