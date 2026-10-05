import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import spaces
import gradio as gr
import uvicorn
from server_app.main import app as fastapi_app

# ZeroGPU probe to satisfy Hugging Face ZeroGPU supervisor
@spaces.GPU
def _gpu_probe():
    return True

with gr.Blocks(title="Competitor Radar AI - Gateway") as demo:
    gr.Markdown("# 📡 Competitor Radar AI ZeroGPU Gateway")
    probe_btn = gr.Button("ZeroGPU Probe", visible=False)
    probe_btn.click(fn=_gpu_probe, inputs=[], outputs=[])

# Mount Gradio demo onto the full-stack FastAPI app under /gradio
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
