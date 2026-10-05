from datetime import datetime, timezone
from typing import Optional, List, Any
import uuid
from sqlmodel import SQLModel, Field, Column
import sqlalchemy as sa
import json

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class AppSetting(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    key: str = Field(index=True, unique=True)
    value: str

class Project(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    title: str
    category: str = "General"
    description: Optional[str] = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

class InternalApp(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    project_id: str = Field(index=True)
    app_name: str
    category: str = "General"
    description: Optional[str] = ""
    target_audience: Optional[str] = ""
    # JSON-encoded string for structured modules & features
    modules_features_json: str = Field(default="[]")
    # JSON-encoded string for user flows
    user_flows_json: str = Field(default="[]")
    updated_at: datetime = Field(default_factory=utc_now)

class Competitor(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    project_id: str = Field(index=True)
    name: str
    playstore_package: str = ""
    website_url: str = ""
    extra_urls_json: str = Field(default="[]")
    created_at: datetime = Field(default_factory=utc_now)

class AnalysisReport(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    project_id: str = Field(index=True)
    competitor_ids_json: str = Field(default="[]")
    summary: str = ""
    created_at: datetime = Field(default_factory=utc_now)

class FeatureGapItem(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    report_id: str = Field(index=True)
    competitor_name: str
    feature_name: str
    category: str = "General"
    # Status: 'Belum Diadaptasi' | 'Sebagian Diadaptasi' | 'Sudah Setara' | 'Aplikasi Kita Unggul'
    internal_status: str = "Belum Diadaptasi"
    innovation_highlight: str = ""
    impact_score: int = 5  # 1-10
    effort_score: int = 5  # 1-10
    # JSON list of {title: str, url: str, type: str, quote: str}
    official_sources_json: str = Field(default="[]")

class FlowComparisonItem(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    report_id: str = Field(index=True)
    flow_name: str
    internal_steps: str
    competitor_detected_flow: str
    friction_points: str
    simplification_recommendation: str

class CompetitorOverviewItem(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    report_id: str = Field(index=True)
    competitor_name: str
    playstore_score: float = 0.0
    ratings_count: int = 0
    key_strengths_json: str = Field(default="[]")
    key_weaknesses_json: str = Field(default="[]")
    playstore_url: str = ""
    website_url: str = ""
