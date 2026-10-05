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
from fastapi.responses import RedirectResponse
import uvicorn

from server_app.api.routers import projects, internal_app, competitors, analysis, exports, settings as api_settings
from server_app.core.database import init_db

# Initialize database schema on startup
try:
    init_db()
except Exception as db_err:
    print(f"Database init warning: {db_err}")

# ZeroGPU Probe
@spaces.GPU
def _gpu_probe():
    return True

# Explicitly notify ZeroGPU supervisor of startup completion
try:
    if hasattr(spaces, "_zerogpu_startup_report"):
        spaces._zerogpu_startup_report()
    elif hasattr(spaces, "zero") and hasattr(spaces.zero, "_zerogpu_startup_report"):
        spaces.zero._zerogpu_startup_report()
except Exception as err:
    print(f"ZeroGPU report note: {err}")

# 1. Main FastAPI App
app = FastAPI(title="Competitor Radar AI")

# Mount API routers
app.include_router(projects.router, prefix="/api")
app.include_router(internal_app.router, prefix="/api")
app.include_router(competitors.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(exports.router, prefix="/api")
app.include_router(api_settings.router, prefix="/api")

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "competitor-radar"}

# 2. Static React Frontend
dist_dir = Path(__file__).resolve().parent / "frontend" / "dist"
if dist_dir.exists():
    app.mount("/app", StaticFiles(directory=str(dist_dir), html=True), name="app")

@app.get("/")
def root():
    return RedirectResponse(url="/app/")

@app.get("/app")
def app_redirect():
    return RedirectResponse(url="/app/")

# 3. Mount Gradio probe onto FastAPI
with gr.Blocks(title="Competitor Radar AI - GPU Gateway") as demo:
    probe_btn = gr.Button("ZeroGPU Probe", visible=False)
    probe_btn.click(fn=_gpu_probe, inputs=[], outputs=[])

app = gr.mount_gradio_app(app, demo, path="/gradio")

# 4. Run native Uvicorn server on port 7860
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
