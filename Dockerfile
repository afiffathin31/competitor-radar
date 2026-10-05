FROM python:3.11-slim

WORKDIR /code

# Create non-root user required by Hugging Face Spaces (UID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONPATH=/code/backend

# Copy and install Python dependencies
COPY --chown=user ./backend/requirements.txt /code/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/backend/requirements.txt

# Copy backend code and prebuilt frontend assets
COPY --chown=user ./backend /code/backend
COPY --chown=user ./frontend/dist /code/frontend/dist

WORKDIR /code/backend

# Hugging Face Spaces expects traffic on port 7860
EXPOSE 7860

CMD ["python", "-m", "uvicorn", "server_app.main:app", "--host", "0.0.0.0", "--port", "7860"]
