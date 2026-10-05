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
css_file = "index-DQGFL0eV.css"
js_file = "index-D4PbbeRY.js"

if (dist_dir / "assets").exists():
    css_candidates = list((dist_dir / "assets").glob("*.css"))
    js_candidates = list((dist_dir / "assets").glob("*.js"))
    if css_candidates:
        css_file = css_candidates[0].name
    if js_candidates:
        js_file = js_candidates[0].name

react_html = f'''
<div id="root"></div>
<link rel="stylesheet" href="/static_assets/assets/{css_file}">
<script type="module" src="/static_assets/assets/{js_file}"></script>
'''

with gr.Blocks(title="Competitor Radar AI", css="""
body, .gradio-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
footer { display: none !important; }
""") as demo:
    probe_btn = gr.Button("ZeroGPU Probe", visible=False)
    probe_btn.click(fn=_gpu_probe, inputs=[], outputs=[])

    gr.HTML(react_html)

# Mount API routers onto demo.app with prefix="/api"
demo.app.include_router(projects.router, prefix="/api")
demo.app.include_router(internal_app.router, prefix="/api")
demo.app.include_router(competitors.router, prefix="/api")
demo.app.include_router(analysis.router, prefix="/api")
demo.app.include_router(exports.router, prefix="/api")
demo.app.include_router(api_settings.router, prefix="/api")

@demo.app.get("/api/health")
def health():
    return {"status": "ok", "service": "competitor-radar"}

# Mount frontend assets
if dist_dir.exists():
    demo.app.mount("/static_assets", StaticFiles(directory=str(dist_dir)), name="static_assets")

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        ssr_mode=False
    )
