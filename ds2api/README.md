# ds2api Local Setup

This folder follows the Docker/GHCR deployment style from `CJackHwang/ds2api`.

## Files

- `docker-compose.yml`: runs `ghcr.io/cjackhwang/ds2api:latest`.
- `.env.example`: ds2api container settings.
- `config.example.json`: safe template for API keys and DeepSeek accounts.
- `config.json`: local secret file, ignored by Git.

## Setup

```powershell
cd ds2api
Copy-Item .env.example .env
Copy-Item config.example.json config.json
```

Edit `config.json` locally:

- keep `keys[0]` aligned with root `.env` `DEEPSEEK_API_KEY`
- set your real DeepSeek account in `accounts`

Start:

```powershell
docker compose up -d
docker compose logs -f
```

Health/API checks:

```powershell
Invoke-WebRequest http://127.0.0.1:5001/healthz -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:5001/v1/models -UseBasicParsing
```

Root project `.env` should point to:

```env
DEEPSEEK_BASE_URL=http://127.0.0.1:5001
DEEPSEEK_API_KEY=ds2api-local-key
```

If you prefer the upstream default host port `6011`, set `DS2API_HOST_PORT=6011` in this folder's `.env` and update root `.env` to `DEEPSEEK_BASE_URL=http://127.0.0.1:6011`.
