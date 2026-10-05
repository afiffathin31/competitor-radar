from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
from pydantic import BaseModel
import json
from app.core.database import get_session
from app.models.models import InternalApp, Project

router = APIRouter(prefix="/internal-app", tags=["internal-app"])

class FeatureItem(BaseModel):
    name: str
    description: str = ""

class ModuleItem(BaseModel):
    module_name: str
    features: List[FeatureItem] = []

class UserFlowItem(BaseModel):
    flow_name: str
    steps: List[str] = []
    notes: Optional[str] = ""

class InternalAppPayload(BaseModel):
    project_id: str
    app_name: str
    category: str = "General"
    description: Optional[str] = ""
    target_audience: Optional[str] = ""
    modules_features: List[ModuleItem] = []
    user_flows: List[UserFlowItem] = []

@router.get("/{project_id}")
def get_internal_app(project_id: str, session: Session = Depends(get_session)):
    app_record = session.exec(select(InternalApp).where(InternalApp.project_id == project_id)).first()
    if not app_record:
        return None
    
    try:
        modules = json.loads(app_record.modules_features_json)
    except Exception:
        modules = []

    try:
        flows = json.loads(app_record.user_flows_json)
    except Exception:
        flows = []

    return {
        "id": app_record.id,
        "project_id": app_record.project_id,
        "app_name": app_record.app_name,
        "category": app_record.category,
        "description": app_record.description,
        "target_audience": app_record.target_audience,
        "modules_features": modules,
        "user_flows": flows,
        "updated_at": app_record.updated_at
    }

@router.post("")
def save_internal_app(payload: InternalAppPayload, session: Session = Depends(get_session)):
    project = session.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    app_record = session.exec(select(InternalApp).where(InternalApp.project_id == payload.project_id)).first()
    
    modules_str = json.dumps([m.dict() for m in payload.modules_features], ensure_ascii=False)
    flows_str = json.dumps([f.dict() for f in payload.user_flows], ensure_ascii=False)

    if not app_record:
        app_record = InternalApp(
            project_id=payload.project_id,
            app_name=payload.app_name,
            category=payload.category,
            description=payload.description,
            target_audience=payload.target_audience,
            modules_features_json=modules_str,
            user_flows_json=flows_str,
            updated_at=datetime.now(timezone.utc)
        )
        session.add(app_record)
    else:
        app_record.app_name = payload.app_name
        app_record.category = payload.category
        app_record.description = payload.description
        app_record.target_audience = payload.target_audience
        app_record.modules_features_json = modules_str
        app_record.user_flows_json = flows_str
        app_record.updated_at = datetime.now(timezone.utc)
        session.add(app_record)

    session.commit()
    session.refresh(app_record)
    return {"status": "success", "message": "Profil aplikasi internal berhasil disimpan", "id": app_record.id}

@router.get("/export-json/{project_id}")
def export_internal_app_json(project_id: str, session: Session = Depends(get_session)):
    app_record = session.exec(select(InternalApp).where(InternalApp.project_id == project_id)).first()
    if not app_record:
        raise HTTPException(status_code=404, detail="Data aplikasi internal belum dibuat")

    return {
        "version": "1.0",
        "app_name": app_record.app_name,
        "category": app_record.category,
        "description": app_record.description,
        "target_audience": app_record.target_audience,
        "modules_features": json.loads(app_record.modules_features_json or "[]"),
        "user_flows": json.loads(app_record.user_flows_json or "[]")
    }
