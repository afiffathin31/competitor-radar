import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import spaces
import gradio as gr
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from server_app.api.routers import projects, internal_app, competitors, analysis, exports, settings as api_settings
from server_app.core.database import init_db

# Initialize database schema on startup
try:
    init_db()
except Exception as db_err:
    print(f"Database init warning: {db_err}")

# Create dedicated FastAPI sub-app for all /api endpoints
api_app = FastAPI(title="Competitor Radar API")
api_app.include_router(projects.router)
api_app.include_router(internal_app.router)
api_app.include_router(competitors.router)
api_app.include_router(analysis.router)
api_app.include_router(exports.router)
api_app.include_router(api_settings.router)

@api_app.get("/health")
def health():
    return {"status": "ok", "service": "competitor-radar"}

# Dummy probe function to satisfy ZeroGPU supervisor
@spaces.GPU
def _gpu_probe():
    return True

# Build Gradio Blocks demo
with gr.Blocks(title="Competitor Radar AI") as demo:
    gr.Markdown("# 📡 Competitor Radar AI\nSistem Intelijen Pasar & Riset Kompetitor Aplikasi Android.")
    gr.HTML('<p style="margin-bottom:12px;"><a href="/app" style="display:inline-block;padding:12px 24px;background:#0d9488;color:white;border-radius:8px;text-decoration:none;font-weight:700;font-size:16px;box-shadow:0 4px 6px -1px rgba(13,148,136,0.3);">🚀 Buka Dashboard Aplikasi (Full Screen) &rarr;</a> <a href="/api/docs" target="_blank" style="margin-left:12px;display:inline-block;padding:12px 20px;background:#3b82f6;color:white;border-radius:8px;text-decoration:none;font-weight:600;">📚 API Documentation &rarr;</a></p>')
    gr.HTML('<iframe src="/app" style="width:100%; height:900px; border:1px solid #e2e8f0; border-radius:12px; box-shadow:0 10px 15px -3px rgba(0,0,0,0.1);"></iframe>')
    probe_btn = gr.Button("ZeroGPU Probe", visible=False)
    probe_btn.click(fn=_gpu_probe, inputs=[], outputs=[])

# Launch Gradio server (coordinating with ZeroGPU supervisor)
port = int(os.environ.get("PORT", 7860))
app, _, _ = demo.launch(
    server_name="0.0.0.0",
    server_port=port,
    prevent_thread_lock=True,
    show_error=True
)

# Mount REST API
app.mount("/api", api_app)

# Mount static React frontend
dist_dir = Path(__file__).resolve().parent / "frontend" / "dist"
if dist_dir.exists():
    if (dist_dir / "assets").exists():
        app.mount("/assets", StaticFiles(directory=dist_dir / "assets"), name="spa-assets")
        app.mount("/app/assets", StaticFiles(directory=dist_dir / "assets"), name="spa-sub-assets")

    @app.get("/app/{full_path:path}")
    async def serve_spa_path(full_path: str = ""):
        target_file = dist_dir / full_path
        if full_path and target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(dist_dir / "index.html")

    @app.get("/app")
    async def serve_spa_root():
        return FileResponse(dist_dir / "index.html")

print("Competitor Radar AI running successfully on Hugging Face Spaces!")
demo.block_thread()
