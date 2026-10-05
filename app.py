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
custom_css = """
body, .gradio-container {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
}
footer {
    display: none !important;
}
"""

with gr.Blocks(title="Competitor Radar AI", css=custom_css) as demo:
    gr.HTML('''
    <div style="height: 100vh; width: 100%; display: flex; flex-direction: column; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <div style="background: #0f172a; color: white; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b;">
            <div style="font-weight: 700; font-size: 16px; display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 18px;">📡</span> Competitor Radar AI
            </div>
            <div style="display: flex; gap: 10px;">
                <a href="/app/" target="_blank" style="padding: 6px 14px; background: #0d9488; color: white; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 600;">🚀 Buka Layar Penuh &rarr;</a>
                <a href="/api/docs" target="_blank" style="padding: 6px 14px; background: #334155; color: white; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 600;">📚 API Docs</a>
            </div>
        </div>
        <iframe src="/app/" style="flex: 1; width: 100%; border: none;"></iframe>
    </div>
    ''')
    probe_btn = gr.Button("ZeroGPU Probe", visible=False)
    probe_btn.click(fn=_gpu_probe, inputs=[], outputs=[])

# Mount /api onto demo.app BEFORE launch!
demo.app.mount("/api", api_app)

# Mount /app for static React frontend onto demo.app BEFORE launch!
dist_dir = Path(__file__).resolve().parent / "frontend" / "dist"
if dist_dir.exists():
    demo.app.mount("/app", StaticFiles(directory=str(dist_dir), html=True), name="app")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        ssr_mode=False,
        prevent_thread_lock=False,
        show_error=True
    )
