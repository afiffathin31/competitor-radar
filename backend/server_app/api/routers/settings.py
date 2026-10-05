from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Dict, Any
from pydantic import BaseModel
import os
from server_app.core.database import get_session
from server_app.models.models import AppSetting
from server_app.core.config import settings

router = APIRouter(prefix="/settings", tags=["settings"])

class SettingsUpdate(BaseModel):
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    qwen_api_key: str = ""
    qwen_base_url: str = ""
    qwen_model: str = ""
    default_provider: str = "gemini"

def mask_key(k: str) -> str:
    if not k or len(k) < 6:
        return ""
    return k[:4] + "*" * (len(k) - 8) + k[-4:]

@router.get("")
def get_settings(session: Session = Depends(get_session)):
    def get_val(key_name: str, fallback_env: str) -> str:
        st = session.exec(select(AppSetting).where(AppSetting.key == key_name)).first()
        if st and st.value:
            return st.value
        return os.getenv(key_name, fallback_env)

    gemini_key = get_val("GEMINI_API_KEY", settings.GEMINI_API_KEY)
    openai_key = get_val("OPENAI_API_KEY", settings.OPENAI_API_KEY)
    claude_key = get_val("ANTHROPIC_API_KEY", settings.ANTHROPIC_API_KEY)
    qwen_key = get_val("QWEN_API_KEY", settings.QWEN_API_KEY)
    qwen_base_url = get_val("QWEN_BASE_URL", settings.QWEN_BASE_URL)
    qwen_model = get_val("QWEN_MODEL", settings.QWEN_MODEL)
    provider = get_val("DEFAULT_LLM_PROVIDER", settings.DEFAULT_LLM_PROVIDER)

    return {
        "gemini_api_key_masked": mask_key(gemini_key),
        "has_gemini": bool(gemini_key.strip()),
        "openai_api_key_masked": mask_key(openai_key),
        "has_openai": bool(openai_key.strip()),
        "anthropic_api_key_masked": mask_key(claude_key),
        "has_claude": bool(claude_key.strip()),
        "qwen_api_key_masked": mask_key(qwen_key),
        "has_qwen": bool(qwen_key.strip()),
        "qwen_base_url": qwen_base_url,
        "qwen_model": qwen_model,
        "default_provider": provider
    }

@router.post("")
def update_settings(payload: SettingsUpdate, session: Session = Depends(get_session)):
    def set_val(k: str, v: str):
        if v.strip():
            st = session.exec(select(AppSetting).where(AppSetting.key == k)).first()
            if not st:
                st = AppSetting(key=k, value=v.strip())
                session.add(st)
            else:
                st.value = v.strip()
                session.add(st)

    if payload.gemini_api_key:
        set_val("GEMINI_API_KEY", payload.gemini_api_key)
    if payload.openai_api_key:
        set_val("OPENAI_API_KEY", payload.openai_api_key)
    if payload.anthropic_api_key:
        set_val("ANTHROPIC_API_KEY", payload.anthropic_api_key)
    if payload.qwen_api_key:
        set_val("QWEN_API_KEY", payload.qwen_api_key)
    if payload.qwen_base_url:
        set_val("QWEN_BASE_URL", payload.qwen_base_url)
    if payload.qwen_model:
        set_val("QWEN_MODEL", payload.qwen_model)
    
    if payload.default_provider:
        set_val("DEFAULT_LLM_PROVIDER", payload.default_provider)

    session.commit()
    return {"status": "success", "message": "Pengaturan API Key dan provider berhasil disimpan"}
