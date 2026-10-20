# Deployment (Hugging Face Spaces, Docker)

Why this host: the app needs about 3-4 GB RAM (Whisper `small` + translation model + DistilBERT). Typical 512 MB free web tiers cannot run it,
while a Space's free CPU tier (16 GB) can. One container serves the API and the web app on one HTTPS origin.

**Status: not yet deployed.** The Docker image has **not been built** anywhere yet (Docker is not installed on the development machine), so the
first build may need a fix. Everything below is what to do and what to expect.

## 1. One-time setup
1. Create an account at `huggingface.co`.
2. **New Space** → SDK **Docker** → hardware **CPU basic (free)** → visibility **Public** → create it (empty).
3. **Settings → Access Tokens** → create a token with **Write** access. Keep it private; never paste it into chat or code.
4. Install Git LFS from `git-lfs.com`, then run `git lfs install` once.

## 2. Secrets (Space → Settings → Variables and secrets)
Add as **Secrets** (never commit them). For non-campus "ask anything" answers use ONE of:
* Gemini / Groq / OpenRouter: `GENERAL_PROVIDER=openai_compat`, `GENERAL_API_KEY`, `GENERAL_BASE_URL`, `GENERAL_MODEL`, `GENERAL_PROVIDER_NAME`
  (same values as in your local `.env`; run `setup_ai.ps1` to see the format).
* Claude: `ANTHROPIC_API_KEY`.

Without them the app still works; non-campus questions get the standard "outside what I can help with" reply.
Optional variables: `GENERAL_DAILY_CAP` (default 300 AI answers per day across all users), `DATABASE_URL` (managed PostgreSQL; otherwise SQLite on ephemeral
disk, so correction memory resets on restart), and `WHISPER_MODEL=base` if the free CPU is too slow for `small` (faster, less accurate).

## 3. Upload
Preview first (uploads nothing):
```powershell
cd D:\VoxSure
.\deploy_hf.ps1 -Space yourname/spacename -DryRun
```
Then deploy (asks you to type YES; when Git asks for credentials, username = your Hugging Face username, password = your write token):
```powershell
.\deploy_hf.ps1 -Space yourname/spacename
```
The script builds a clean one-commit snapshot of the tracked files (so your project history is untouched) with the right Git LFS rules
(model weights and images), then pushes it to the Space.

## 4. What to expect
* The first build is long: it builds the web app, installs CPU PyTorch, downloads Whisper `small`, and downloads and converts the 2.4 GB translation model.
  Watch the build log on the Space page. If the build fails, send me the last lines of the log.
* Live URL: `https://<yourname>-<spacename>.hf.space`. Free Spaces sleep after inactivity; the first request wakes them (about a minute).
* Speed on the free 2-vCPU CPU will be slower than on a laptop with spare cores (speech transcription especially).

## 5. Smoke test on the live URL (record the results in the report)
- [ ] `/api/v1/health` shows `status: ok`, `asr_multilingual: true`, `translation_ready: true`, and `general_ready: true` if you set AI secrets
- [ ] Settings → **Models in use** matches what you expect
- [ ] Typed "When does the library open?" → answer from the knowledge base
- [ ] Typed "Can I get a receipt?" → targeted clarification buttons
- [ ] Typed "What is the capital of France?" → AI-generated answer (if secrets set)
- [ ] A Spanish question → Spanish reply; a Hindi question → Hindi reply
- [ ] Microphone: permission prompt appears only after pressing the button; speak → transcript → answer
- [ ] Evaluation page loads (`/#/evaluation`)
- [ ] Record the links: `.\set_links.ps1 -Live https://yourname-spacename.hf.space -Repo https://github.com/you/repo` (updates README and report), then commit
