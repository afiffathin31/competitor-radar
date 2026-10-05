from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.core.database import get_session
from app.models.models import Project, InternalApp, Competitor, AnalysisReport

router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    title: str
    category: str = "E-Commerce / FinTech"
    description: Optional[str] = ""

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None

class ProjectRead(BaseModel):
    id: str
    title: str
    category: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    competitors_count: int = 0
    has_internal_app: bool = False
    has_report: bool = False

@router.get("", response_model=List[ProjectRead])
def list_projects(session: Session = Depends(get_session)):
    projects = session.exec(select(Project).order_by(Project.created_at.desc())).all()
    results = []
    for p in projects:
        comp_count = len(session.exec(select(Competitor).where(Competitor.project_id == p.id)).all())
        has_internal = session.exec(select(InternalApp).where(InternalApp.project_id == p.id)).first() is not None
        has_rep = session.exec(select(AnalysisReport).where(AnalysisReport.project_id == p.id)).first() is not None
        results.append(ProjectRead(
            id=p.id,
            title=p.title,
            category=p.category,
            description=p.description,
            created_at=p.created_at,
            updated_at=p.updated_at,
            competitors_count=comp_count,
            has_internal_app=has_internal,
            has_report=has_rep
        ))
    return results

@router.post("", response_model=Project)
def create_project(data: ProjectCreate, session: Session = Depends(get_session)):
    proj = Project(
        title=data.title,
        category=data.category,
        description=data.description
    )
    session.add(proj)
    session.commit()
    session.refresh(proj)
    return proj

@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str, session: Session = Depends(get_session)):
    proj = session.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")
    return proj

@router.patch("/{project_id}", response_model=Project)
def update_project(project_id: str, data: ProjectUpdate, session: Session = Depends(get_session)):
    proj = session.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")
    if data.title is not None:
        proj.title = data.title.strip()
    if data.category is not None:
        proj.category = data.category.strip()
    if data.description is not None:
        proj.description = data.description.strip()
    session.add(proj)
    session.commit()
    session.refresh(proj)
    return proj

@router.delete("/{project_id}")
def delete_project(project_id: str, session: Session = Depends(get_session)):
    proj = session.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")
    session.delete(proj)
    session.commit()
    return {"status": "success", "message": "Proyek berhasil dihapus"}
