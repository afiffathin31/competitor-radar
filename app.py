import sys
import os
from pathlib import Path

# ZeroGPU supervisor probe
try:
    import spaces
except ImportError:
    class _MockSpaces:
        def GPU(self, fn=None, duration=None):
            def decorator(f):
                return f
            return decorator(fn) if fn else decorator
    spaces = _MockSpaces()

@spaces.GPU
def _gpu_probe():
    return True

# Ensure backend directory is in sys.path
backend_path = Path(__file__).resolve().parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import gradio as gr
from server_app.main import app as fastapi_app

# Define Gradio interface with probe attached to event graph
with gr.Blocks(title="Competitor Radar AI") as demo:
    gr.Markdown("### Competitor Radar AI\nSistem Intelijen Pasar & Riset Kompetitor Aplikasi Android.")
    gr.HTML('<p><a href="/" style="display:inline-block;padding:10px 18px;background:#0d9488;color:white;border-radius:8px;text-decoration:none;font-weight:600;">Buka Dashboard Utama &rarr;</a></p>')
    
    # Required by ZeroGPU supervisor: connect @spaces.GPU function to Gradio graph
    probe_btn = gr.Button("ZeroGPU Probe", visible=False)
    probe_btn.click(fn=_gpu_probe, inputs=[], outputs=[])

# Mount Gradio app under /gradio; fastapi_app continues serving / and /api
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
