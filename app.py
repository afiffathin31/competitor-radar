import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import spaces
import gradio as gr
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from server_app.api.routers import projects, internal_app, competitors, analysis, exports, settings as api_settings
from server_app.core.database import init_db

try:
    init_db()
except Exception as db_err:
    print(f"Database init warning: {db_err}")

# ZeroGPU Probe
@spaces.GPU
def _gpu_probe():
    return True

dist_dir = Path(__file__).resolve().parent / "frontend" / "dist"

with gr.Blocks(title="Competitor Radar AI", css="""
body, .gradio-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
footer { display: none !important; }
""") as demo:
    probe_btn = gr.Button("ZeroGPU Probe", visible=False)
    probe_btn.click(fn=_gpu_probe, inputs=[], outputs=[])

    # Full screen overlay of the React frontend
    gr.HTML('<iframe src="/app/" style="position:fixed; top:0; left:0; width:100vw; height:100vh; border:none; z-index:9999;"></iframe>')

# Mount API routers directly onto demo.app
demo.app.include_router(projects.router, prefix="/api")
demo.app.include_router(internal_app.router, prefix="/api")
demo.app.include_router(competitors.router, prefix="/api")
demo.app.include_router(analysis.router, prefix="/api")
demo.app.include_router(exports.router, prefix="/api")
demo.app.include_router(api_settings.router, prefix="/api")

@demo.app.get("/api/health")
def health():
    return {"status": "ok", "service": "competitor-radar"}

# Serve frontend static assets under /app/ and /assets/
if dist_dir.exists():
    demo.app.mount("/app", StaticFiles(directory=str(dist_dir), html=True), name="app")
    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        demo.app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

@demo.app.get("/app")
def redirect_app():
    return RedirectResponse(url="/app/")

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        ssr_mode=False
    )
