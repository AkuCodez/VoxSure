"""Vercel entry point (lite mode). Vercel detects the FastAPI instance named `app` in this file.

All the real code lives in backend/app. On Vercel, VERCEL=1 is set, which switches the app to lite mode
(ONNX classifier + hosted Whisper + LLM translation); the website itself is served from the public/ folder.
Locally you can also run it with:  uvicorn server:app --port 8000
"""
from backend.app.main import app  # noqa: F401  (re-exported for the platform)
