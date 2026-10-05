import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

try:
    import spaces
except ImportError:  # local development: HF Spaces provides the real package
    class spaces:  # type: ignore
        @staticmethod
        def GPU(fn=None, **_kw):
            return fn if fn else (lambda f: f)
import gradio as gr
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from server_app.api.routers import projects, internal_app, competitors, analysis, exports, settings as api_settings
from server_app.core.database import init_db

try:
    init_db()
except Exception as db_err:
    print(f"Database init warning: {db_err}")


# ZeroGPU requires at least one @spaces.GPU function wired into the Blocks graph
@spaces.GPU
def _gpu_probe():
    return True


FULLSCREEN_CSS = """
html, body, .gradio-container, .main, .wrap, .contain { margin:0 !important; padding:0 !important; max-width:100% !important; }
footer { display:none !important; }
"""

with gr.Blocks(title="Competitor Radar AI", css=FULLSCREEN_CSS) as demo:
    probe_btn = gr.Button("ZeroGPU Probe", visible=False)
    probe_btn.click(fn=_gpu_probe, inputs=[], outputs=[])
    gr.HTML(
        '<iframe src="/static_assets/" title="Competitor Radar" '
        'style="position:fixed;inset:0;width:100vw;height:100vh;border:0;z-index:9999;background:#fff;"></iframe>'
    )

# Custom routes are registered on demo.app, and demo.app is passed to launch(_app=...)
# so Gradio 6 reuses it instead of creating a fresh app (which would drop these routes).
fastapi_app = demo.app

for r in (projects, internal_app, competitors, analysis, exports, api_settings):
    fastapi_app.include_router(r.router, prefix="/api")

@fastapi_app.get("/api/health")
def health():
    return {"status": "ok", "service": "competitor-radar"}

dist_dir = Path(__file__).resolve().parent / "frontend" / "dist"
if dist_dir.exists():
    fastapi_app.mount("/static_assets", StaticFiles(directory=str(dist_dir), html=True), name="static_assets")

if __name__ == "__main__":
    demo.launch(
        _app=fastapi_app,
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        ssr_mode=False,
        show_error=True,
    )
