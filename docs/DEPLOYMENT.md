# Deployment (Hugging Face Spaces, Docker)

Why this host: Whisper + DistilBERT need ~1.5-2 GB RAM; typical 512 MB free web tiers cannot run both, while Spaces'
free CPU tier (16 GB) can. The app is one container on one HTTPS origin, so Vercel is not needed. If you prefer Vercel for the
frontend, build it with `VITE_API_BASE=https://<backend>` and set `CORS_ORIGINS` on the backend.

**Status: not yet deployed.** Complete the steps below, then run the smoke test and add the URL to the README and report.

## Steps

1. Create a Hugging Face account → **New Space** → SDK **Docker**, hardware **CPU basic (free)**, visibility **Public**.
2. In the repo: `git lfs install` (the model file is tracked by LFS via `.gitattributes`).
3. `git remote add space https://huggingface.co/spaces/<user>/<space-name>` and `git push space main`
   (authenticate with a write token via `huggingface-cli login`; never commit the token).
4. The Space builds `Dockerfile` (≈10 min the first time: builds the frontend, installs CPU torch, bakes in the Whisper weights).
5. Optional: Space **Settings → Variables and secrets**: `DATABASE_URL` for managed PostgreSQL (otherwise SQLite on
   ephemeral disk; correction memory resets on restart, which is documented behaviour).
6. Open `https://<user>-<space-name>.hf.space` in a fresh browser.

## Smoke test (record results in the report)

- [ ] `/api/v1/health` returns `status: ok` with `asr_ready` and `intent_ready` true
- [ ] Typed "When does the library open?" → answer
- [ ] "When does it open?" → clarification buttons
- [ ] Mic permission prompt appears only after pressing the button; speak a question → transcript → answer
- [ ] "What's the weather?" → out-of-scope fallback
- [ ] Settings → memory opt-in, remember a correction, delete it

Free Spaces sleep after inactivity; the first request may take a minute to wake. Note this when sharing the link.
