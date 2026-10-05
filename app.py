import sys
import os
from pathlib import Path

# ZeroGPU supervisor configuration for custom Uvicorn servers
try:
    import spaces
    @spaces.GPU
    def _zerogpu_probe():
        pass
    
    if hasattr(spaces, "_zerogpu_startup_report"):
        spaces._zerogpu_startup_report()
    elif hasattr(spaces, "zero") and hasattr(spaces.zero, "_zerogpu_startup_report"):
        spaces.zero._zerogpu_startup_report()
except Exception as e:
    print(f"ZeroGPU init note: {e}")

# Ensure backend directory is in sys.path
backend_path = Path(__file__).resolve().parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import gradio as gr
from server_app.main import app as fastapi_app

# Define Gradio interface
with gr.Blocks(title="Competitor Radar AI") as demo:
    gr.Markdown("### Competitor Radar AI\nSistem Intelijen Pasar & Riset Kompetitor Aplikasi Android.")
    gr.HTML('<p><a href="/" target="_self" style="display:inline-block;padding:10px 18px;background:#0d9488;color:white;border-radius:8px;text-decoration:none;font-weight:600;">Buka Dashboard Utama &rarr;</a></p>')

# Mount Gradio app under /gradio; fastapi_app continues serving / and /api
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

# Trigger startup report before binding port
try:
    import spaces
    if hasattr(spaces, "_zerogpu_startup_report"):
        spaces._zerogpu_startup_report()
except Exception:
    pass

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
