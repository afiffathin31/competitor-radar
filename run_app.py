import sys
import os
from pathlib import Path

# Ensure backend directory is in sys.path
backend_path = Path(__file__).resolve().parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import gradio as gr
from app.main import app as fastapi_app

# Define a minimal Gradio interface to ensure complete compatibility with Gradio SDK
with gr.Blocks(title="Competitor Radar AI") as demo:
    gr.Markdown("### Competitor Radar AI\nSistem Intelijen Pasar & Riset Kompetitor Aplikasi Android.")
    gr.HTML('<p><a href="/" style="display:inline-block;padding:10px 18px;background:#0d9488;color:white;border-radius:8px;text-decoration:none;font-weight:600;">Buka Dashboard Utama &rarr;</a></p>')


# Mount Gradio app under /gradio; fastapi_app continues serving / and /api
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("run_app:app", host="0.0.0.0", port=port, reload=False)
