# LeadGen — Find 100 qualified leads while you sleep

## Product
LeadGen is an autonomous B2B lead generation agent. Users set a target query (e.g. "Digital agencies in Berlin"), and the agent searches Google via browser automation, extracts company info, and sends personalized cold emails — all on autopilot.

**Pricing:** $99/month (up to 500 leads/month) — Stripe Checkout subscription.

## What's built
- **Landing page** — Hero: "Find 100 qualified leads while you sleep", pricing $99/month, CTA → /subscribe
- **Onboarding flow** — After payment at `/onboarding`, user enters their target query, system starts scraping automatically with live status
- **Live dashboard** — Real-time WebSocket telemetry showing every agent decision
- **Stripe subscription** — $99/month Checkout, webhook signature verification, subscription lifecycle management
- **Browser automation** — Kimi WebBridge Chrome automation for Google scraping
- **SendGrid outreach** — Personalized cold email pipeline with per-lead company context
- **Rate limiting** (slowapi) — /subscribe: 10/dk, /webhook: 20/dk
- **GET /health** endpoint (DB connection check, 200/503)
- **Structured logging** (structlog) — JSON output, ISO timestamps
- **Sentry integration** — Error tracking, traces_sample_rate=0.1
- **Fail-fast env validation** — Production blocks startup if STRIPE_API_KEY or SENDGRID_API_KEY is missing
- **Decision log cleanup** — 90-day retention, automatic cleanup at each agent cycle
- **PostgreSQL backup** — Daily pg_dump + 7-day retention
- **Agent orchestrator** — `python -m src.cli run` runs cleanup → scrape → outreach cycle
- **Deploy script** — Ubuntu 24.04 (DigitalOcean): Docker + Nginx + certbot SSL + cron
- **34/34 tests passing** (30 original + 4 fail-fast env validation)

## Stack
Python, FastAPI, SQLAlchemy, Alembic, Docker, PostgreSQL 16, slowapi, structlog, sentry-sdk, Stripe, SendGrid

## Repository structure
```
├── deploy.sh                 # One-command deploy (Ubuntu 24.04, DigitalOcean)
├── docker-compose.yml        # db + web + agent + backup services
├── Dockerfile                # Python 3.12-slim
├── requirements.txt          # Pinned Python dependencies
├── pyproject.toml            # Pytest config + setuptools
├── .env.example              # Template env file
├── scripts/
│   └── backup.sh             # pg_dump + 7-day pruning
├── src/
│   ├── __init__.py           # Sentry init, structlog config
│   ├── config.py             # Pydantic Settings + fail-fast validation
│   ├── web.py                # FastAPI app, Stripe, WebSocket, API, /onboarding
│   ├── cli.py                # Click CLI: scrape, outreach, status, init-db, run
│   ├── health.py             # Startup health checks (DB, browser)
│   ├── stream.py             # WebSocket streaming engine, decision logging
│   ├── db/                   # SQLAlchemy models (Lead, DecisionLog, Task, Subscription)
│   ├── core/
│   │   ├── orchestrator.py   # Agent cycle runner + decision log cleanup
│   │   ├── outreach.py       # SendGrid cold email pipeline
│   │   └── scraper.py        # Kimi WebBridge Chrome scraping
│   ├── browser/kimi.py       # Kimi WebBridge WebSocket provider
│   └── tasks/                # Background task definitions
├── tests/
│   ├── test_db.py            # Model tests + fail-fast validation tests
│   └── test_routes.py        # API integration tests (TestClient)
├── migrations/               # Alembic migration scripts
└── landing/                  # HTML pages
    ├── index.html            # LeadGen landing page
    ├── onboarding.html       # Post-payment onboarding + query entry
    └── dashboard.html        # Live WebSocket telemetry dashboard
```

## User flow
1. User visits landing page → clicks "Start Free Trial"
2. Stripe Checkout ($99/month, 14-day trial)
3. Redirected to `/onboarding` — user enters target query
4. Agent starts scraping immediately with live status updates
5. User can monitor progress on the live dashboard at `/dashboard`

## Services (docker-compose)
| Service | Port | Purpose |
|---------|------|---------|
| `db` | 5432 | PostgreSQL 16 |
| `web` | 8000 | FastAPI + landing page + dashboard + onboarding |
| `agent` | — | On-demand agent cycle (profile: manual) |
| `backup` | — | Daily pg_dump at 03:00 UTC |

## Important commands
```bash
# Run tests
.venv/bin/python3 -m pytest -v

# Run agent cycle (cleanup → scrape → outreach)
.venv/bin/python3 -m src.cli run

# Scrape leads
.venv/bin/python3 -m src.cli scrape "Digital Agencies in Europe"

# Send outreach (dry-run by default)
.venv/bin/python3 -m src.cli outreach --no-dry-run

# Start web server (dev)
.venv/bin/uvicorn src.web:app --reload --port 8000

# Full deploy
sudo DB_PASSWORD=... ./deploy.sh leadgen.example.com
```

## Next step
Deploy to DigitalOcean once GitHub Student Pack is active:
```
sudo ./deploy.sh your-domain.com
```
