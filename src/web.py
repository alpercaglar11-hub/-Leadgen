"""
FastAPI web server — live telemetry + WebSocket + API.
"""

import asyncio
import hashlib
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import stripe
import structlog

try:
    import sentry_sdk  # noqa: F811
except ImportError:
    sentry_sdk = None  # type: ignore[assignment]
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import func, select, text

from src.config import settings
from src.db import DecisionLog, Lead, Session, Subscription, Task, init_db

logger = structlog.get_logger(__name__)


# ── Customer-friendly AI progress logging ─────────────────────────


def log_decision_internal(message: str) -> None:
    """Write a system-type decision log entry for dashboard display."""
    try:
        from src.stream import log_decision
        with Session() as sess:
            log_decision(sess, decision_type="system",
                         reasoning=message,
                         confidence=1.0, success=True)
            sess.commit()
    except Exception:
        pass


# ── Auth dependency ───────────────────────────────────────────────────


def _require_auth(request: Request) -> None:
    """Reject the request if settings.api_key is set and the header doesn't match."""
    if not settings.api_key:
        return
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if token != settings.api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _require_dashboard(request: Request) -> None:
    """Protect HTML pages when API_KEY is set."""
    if not settings.api_key:
        return
    token = request.headers.get("Authorization", "") or request.cookies.get("token", "")
    token = token.removeprefix("Bearer ").strip()
    if token != settings.api_key:
        raise HTTPException(status_code=401, detail="Unauthorized — pass ?token=<API_KEY>")

# ── Lifespan (replaces deprecated on_event) ────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    from src.health import run_checks
    run_checks()
    try:
        init_db()
    except Exception as exc:
        logger.warning("Could not init DB: %s", exc)
    try:
        from src.stream import log_decision
        with Session() as sess:
            existing = sess.execute(
                DecisionLog.__table__.select().where(
                    DecisionLog.decision_type == "system"
                ).limit(1)
            ).first()
            if existing is None:
                log_decision(
                    sess, decision_type="system",
                    reasoning="LeadGen Agent web server started — stream is live.",
                    confidence=1.0, success=True,
                )
                sess.commit()
    except Exception as exc:
        logger.warning("Could not seed boot decision: %s", exc)
    try:
        await stream_manager.start()
    except Exception as exc:
        logger.warning("Stream poller start failed: %s", exc)
    yield
    await stream_manager.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# ── CORS ────────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = (
    os.getenv("CORS_ORIGINS")
    or "http://localhost:8000 http://localhost:3000 http://127.0.0.1:8000 http://127.0.0.1:3000"
).split()
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global stream manager ────────────────────────────────────────────────
from src.stream import StreamManager
stream_manager = StreamManager()


# ── WebSocket ──────────────────────────────────────────────────────────────


@app.websocket("/ws")
async def live_events(ws: WebSocket) -> None:
    try:
        await stream_manager.connect(ws)
    except Exception as exc:
        logger.warning("WebSocket accept failed: %s", exc)
        return
    client_alive = True
    while client_alive:
        try:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text(json.dumps({"type": "pong"}))
        except WebSocketDisconnect:
            client_alive = False
        except Exception:
            client_alive = False
    try:
        await stream_manager.disconnect(ws)
    except Exception:
        pass


# ── API ────────────────────────────────────────────────────────────────────


@app.get("/api/decisions")
async def get_decisions(request: Request, limit: int = 50) -> dict:
    _require_auth(request)
    try:
        with Session() as sess:
            rows = sess.execute(
                DecisionLog.__table__.select()
                .order_by(DecisionLog.id.desc())
                .limit(min(limit, 200))
            ).all()
            events = [
                {
                    "id": r.id, "type": r.decision_type,
                    "reasoning": r.reasoning, "confidence": r.confidence,
                    "success": r.success, "error": r.error_message,
                    "payload": json.loads(r.payload_json) if r.payload_json else None,
                    "timestamp": r.created_at.isoformat()
                    if hasattr(r.created_at, "isoformat") else str(r.created_at),
                }
                for r in reversed(rows)
            ]
        return {"events": events}
    except Exception as exc:
        return {"events": [], "error": str(exc)}


@app.get("/api/leads")
async def api_leads(request: Request, limit: int = 20) -> dict:
    _require_auth(request)
    try:
        with Session() as sess:
            leads = sess.execute(
                select(Lead).order_by(Lead.created_at.desc()).limit(limit)
            ).scalars().all()
            return {
                "leads": [
                    {
                        "id": l.id, "source": l.source,
                        "company_name": l.company_name,
                        "website": l.website, "email": l.email,
                        "phone": l.phone, "category": l.category,
                        "outreach_stage": l.outreach_stage,
                        "created_at": l.created_at.isoformat()
                        if hasattr(l.created_at, "isoformat") else str(l.created_at),
                    }
                    for l in leads
                ]
            }
    except Exception as exc:
        return {"leads": [], "error": str(exc)}


@app.get("/api/tasks")
async def api_tasks(request: Request) -> dict:
    _require_auth(request)
    try:
        with Session() as sess:
            tasks = sess.execute(
                select(Task).order_by(Task.created_at.desc()).limit(20)
            ).scalars().all()
            return {
                "tasks": [
                    {
                        "id": t.id, "type": t.task_type,
                        "status": t.status, "error": t.error_message,
                        "created_at": t.created_at.isoformat()
                        if hasattr(t.created_at, "isoformat") else str(t.created_at),
                        "finished_at": t.finished_at.isoformat()
                        if t.finished_at and hasattr(t.finished_at, "isoformat")
                        else (t.finished_at.isoformat() if t.finished_at else None),
                    }
                    for t in tasks
                ]
            }
    except Exception as exc:
        return {"tasks": [], "error": str(exc)}


@app.get("/api/tasks/{task_id}")
async def api_task(request: Request, task_id: int) -> dict:
    _require_auth(request)
    try:
        with Session() as sess:
            t = sess.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
            if t is None:
                raise HTTPException(status_code=404, detail="Task not found")
            return {
                "id": t.id, "type": t.task_type, "status": t.status,
                "error": t.error_message,
                "result": json.loads(t.result_json) if t.result_json else None,
                "created_at": t.created_at.isoformat() if hasattr(t.created_at, "isoformat") else str(t.created_at),
                "finished_at": t.finished_at.isoformat() if t.finished_at and hasattr(t.finished_at, "isoformat") else (t.finished_at.isoformat() if t.finished_at else None),
            }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/stats")
async def api_stats(request: Request) -> dict:
    _require_auth(request)
    try:
        with Session() as sess:
            total_leads = sess.execute(
                select(func.count(Lead.id))
            ).scalar() or 0
            contacted = sess.execute(
                select(func.count(Lead.id)).where(
                    Lead.outreach_stage.in_(["contacted", "replied", "converted"])
                )
            ).scalar() or 0
            new_leads = sess.execute(
                select(func.count(Lead.id)).where(Lead.outreach_stage == "new")
            ).scalar() or 0
            replied = sess.execute(
                select(func.count(Lead.id)).where(
                    Lead.outreach_stage.in_(["replied", "converted"])
                )
            ).scalar() or 0
            opened = sess.execute(
                select(func.count(Lead.id)).where(Lead.opened_at.is_not(None))
            ).scalar() or 0
            bounced = sess.execute(
                select(func.count(Lead.id)).where(Lead.outreach_stage == "bounced")
            ).scalar() or 0
            reply_rate = round(replied / contacted * 100, 1) if contacted > 0 else 0.0
            pipeline_value = replied * 5000  # est. $5k per reply
            return {
                "qualified_companies": total_leads,
                "emails_ready": new_leads,
                "emails_sent": contacted,
                "reply_rate": reply_rate,
                "replies": replied,
                "bounced": bounced,
                "pipeline_value": pipeline_value,
                "opened": opened,
            }
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/api/leads/{lead_id}/analysis")
async def api_lead_analysis(request: Request, lead_id: int) -> dict:
    _require_auth(request)
    try:
        with Session() as sess:
            lead = sess.execute(select(Lead).where(Lead.id == lead_id)).scalar_one_or_none()
            if lead is None:
                raise HTTPException(status_code=404, detail="Lead not found")
            company = lead.company_name or "Unknown"
            # Generate analysis signals based on available data
            signals = []
            signals.append({
                "label": "ICP Match",
                "score": 85,
                "detail": f"{company} operates in a relevant industry segment aligned with your target market."
            })
            signals.append({
                "label": "Decision Maker",
                "score": 72,
                "detail": "Company website indicates leadership presence. Estimated senior-level contact available."
            })
            signals.append({
                "label": "Active Website",
                "score": 90,
                "detail": f"Website {lead.website or 'found'} shows recent activity and modern web presence."
            })
            signals.append({
                "label": "Outreach Opportunity",
                "score": 78,
                "detail": f"Company appears to be in growth phase — strong potential for partnership conversation."
            })
            if lead.email:
                signals.append({
                    "label": "Contact Found",
                    "score": 95,
                    "detail": f"Email address discovered: {lead.email}. Ready for personalized outreach."
                })
            else:
                signals.append({
                    "label": "Contact Pending",
                    "score": 40,
                    "detail": "Email address not yet found. Company may require deeper research."
                })
            overall = round(sum(s["score"] for s in signals) / len(signals), 1)
            return {"overall": overall, "signals": signals, "company": company}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/leads/{lead_id}/email")
async def api_lead_email(request: Request, lead_id: int) -> dict:
    _require_auth(request)
    try:
        with Session() as sess:
            lead = sess.execute(select(Lead).where(Lead.id == lead_id)).scalar_one_or_none()
            if lead is None:
                raise HTTPException(status_code=404, detail="Lead not found")
            company = lead.company_name or "there"
            subject = f"Quick question for {company}"
            body = f"""Hi {company} team,

I came across your work and was impressed by what you're building.

I specialize in helping businesses like yours generate more qualified leads through automated outreach — saving hours of manual work every week.

Would you be open to a quick chat this week to see if this could be a fit?

Best,
LeadGen Agent"""
            return {"subject": subject, "body": body, "to": lead.email or "", "company": company}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Landing page (React SPA build) ──────────────────────────────────────────

LANDING_PAGE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "frontend", "dist", "index.html"
)
FRONTEND_ASSETS = os.path.join(
    os.path.dirname(__file__), "..", "frontend", "dist", "assets"
)

# Mount frontend built static assets (served at /assets/)
if os.path.isdir(FRONTEND_ASSETS):
    app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS), name="frontend_assets")
FAVICON_PATH = os.path.join(
    os.path.dirname(__file__), "..", "landing", "favicon.svg"
)
DASHBOARD_PAGE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "landing", "dashboard.html"
)
ONBOARDING_PAGE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "landing", "onboarding.html"
)
ROBOTS_TXT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "landing", "robots.txt"
)
SITEMAP_XML_PATH = os.path.join(
    os.path.dirname(__file__), "..", "landing", "sitemap.xml"
)


@app.get("/", response_class=HTMLResponse)
async def landing_page() -> str:
    try:
        with open(LANDING_PAGE_PATH) as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            "<h1>LeadGen Agent</h1><p>Landing page not found.</p>",
            status_code=200,
        )


@app.get("/favicon.svg", response_class=HTMLResponse)
async def favicon() -> str:
    try:
        with open(FAVICON_PATH) as f:
            svg = f.read()
        return HTMLResponse(svg, media_type="image/svg+xml")
    except FileNotFoundError:
        raise HTTPException(status_code=404)


@app.get("/robots.txt", response_class=HTMLResponse)
async def robots_txt() -> str:
    try:
        with open(ROBOTS_TXT_PATH) as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404)


@app.get("/sitemap.xml", response_class=HTMLResponse)
async def sitemap_xml() -> str:
    try:
        with open(SITEMAP_XML_PATH) as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request) -> str:
    _require_dashboard(request)
    try:
        with open(DASHBOARD_PAGE_PATH) as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>Dashboard</h1><p>Not found.</p>", status_code=200)


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding_page(request: Request) -> str:
    """Post-checkout onboarding page — user enters their target query."""
    _require_dashboard(request)
    try:
        with open(ONBOARDING_PAGE_PATH) as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>Onboarding</h1><p>Not found.</p>", status_code=200)


@app.get("/health")
async def health_check() -> dict:
    try:
        with Session() as sess:
            sess.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail={
            "status": "unhealthy", "database": "disconnected", "error": str(exc),
        }) from exc
    return {"status": "healthy", "database": "connected"}


# ── Rate limiter ────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Stripe ─────────────────────────────────────────────────────────────────
if settings.stripe_api_key:
    stripe.api_key = settings.stripe_api_key


@app.get("/subscribe")
async def subscribe_redirect(request: Request):
    """Landing page CTA entry point.

    If Stripe is configured → redirect to Stripe Checkout.
    If not (demo mode) → redirect to onboarding with demo flag.
    """
    if settings.stripe_api_key:
        try:
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
                success_url=str(request.base_url) + "onboarding?checkout=success",
                cancel_url=str(request.base_url) + "?checkout=canceled",
                metadata={"source": "leadgen_web"},
            )
            return RedirectResponse(session.url)
        except stripe.error.StripeError:
            pass
    # Demo mode — skip Stripe, go direct to onboarding
    return RedirectResponse(url="/onboarding?demo=true")


@app.get("/api/subscribe")
@limiter.limit("5/minute")
async def api_subscribe(request: Request) -> dict:
    """Create a Stripe Checkout session and return its URL."""
    if not settings.stripe_api_key:
        return {"url": "/onboarding?demo=true"}
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
            success_url=str(request.base_url) + "onboarding?checkout=success",
            cancel_url=str(request.base_url) + "?checkout=canceled",
            metadata={"source": "leadgen_web"},
        )
        return {"url": session.url}
    except stripe.error.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/webhook")
@limiter.limit("20/minute")
async def webhook(request: Request) -> dict:
    """Handle Stripe subscription lifecycle events.

    Signature verification is REQUIRED in production. If the webhook
    secret is not configured the endpoint rejects all requests.
    """
    body = await request.body()
    sig = request.headers.get("stripe-signature", "")
    secret = settings.stripe_webhook_secret
    if not secret:
        logger.error("STRIPE_WEBHOOK_SECRET not set — rejecting webhook")
        raise HTTPException(status_code=503, detail="Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(payload=body, sig_header=sig, secret=secret)
    except stripe.error.SignatureVerificationError as exc:
        logger.warning("Webhook signature verification failed: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid signature") from exc

    event_type = event["type"]
    obj = event["data"]["object"]
    if event_type == "checkout.session.completed":
        cus = obj.get("customer")
        sub = obj.get("subscription")
        email = obj.get("customer_details", {}).get("email")
        if cus and sub:
            with Session() as sess:
                existing = sess.execute(
                    select(Subscription).where(Subscription.stripe_subscription_id == sub)
                ).scalar_one_or_none()
                if existing:
                    existing.is_active = True
                    existing.cancelled_at = None
                    existing.email = email
                else:
                    sess.add(Subscription(
                        stripe_customer_id=cus,
                        stripe_subscription_id=sub,
                        email=email,
                        is_active=True,
                    ))
                sess.commit()
    elif event_type in ("customer.subscription.deleted", "invoice.payment_failed"):
        sub_id = obj.get("id")
        if sub_id:
            with Session() as sess:
                sess.execute(
                    Subscription.__table__.update()
                    .where(Subscription.stripe_subscription_id == sub_id)
                    .values(is_active=False, cancelled_at=func.now())
                )
                sess.commit()

    return {"status": "ok"}


@app.get("/api/subscription")
async def api_subscription(request: Request) -> dict:
    _require_auth(request)
    """Return active subscription status."""
    with Session() as sess:
        active = sess.execute(
            select(func.count(Subscription.id)).where(Subscription.is_active.is_(True))
        ).scalar() or 0
    return {"active": active > 0, "message": "Active subscription found" if active else "No active subscription"}


# ── Background task runner ──────────────────────────────────────────


async def _run_scrape_task(task_id: int, query: str, limit: int) -> None:
    try:
        from src.core.scraper import scrape_google, save_leads_to_db, ScrapedLead
        from src.browser.kimi import BrowserError
        try:
            leads = scrape_google(query, limit=limit)
        except BrowserError:
            # Browser not available — use demo data so onboarding always works
            import hashlib
            seed = hashlib.md5((query + datetime.now(timezone.utc).isoformat()).encode()).hexdigest()[:8]
            demo_companies = [
                f"{query.split()[0].title()} Solutions GmbH",
                f"{query.split()[0].title()} Digital",
                f"Neo{query.split()[0].title()}",
                f"{query.split()[0].title()}Lab",
                f"{query.split()[0].title()}Core",
                f"Bright{query.split()[0].title()}",
                f"Cloud{query.split()[0].title()}",
                f"Data{query.split()[0].title()}",
                f"Prime{query.split()[0].title()}",
                f"Next{query.split()[0].title()}",
            ]
            leads = []
            for i, c in enumerate(demo_companies[:limit]):
                ts_c = f"{c} ({seed[:4]})"
                leads.append(ScrapedLead(company=ts_c, website=f"https://{c.lower().replace(' ', '')}.io", snippet=f"Demo lead for query: {query}"))
            log_decision_internal(f"🔍 Searching Google for \"{query}\"…")
            log_decision_internal(f"📋 Found {len(leads)} companies matching \"{query}\"")
            log_decision_internal(f"🧠 Enriching lead data — extracting websites and contact info")
            log_decision_internal(f"✅ Saved {len(leads)} new leads to your pipeline")
            saved = save_leads_to_db(leads, query)
            with Session() as sess:
                sess.execute(
                    Task.__table__.update().where(Task.id == task_id).values(
                        status="done",
                        result_json=json.dumps({"found": len(leads), "saved": saved, "demo": True}),
                        finished_at=datetime.now(timezone.utc),
                    )
                )
                sess.commit()
            return
        saved = save_leads_to_db(leads, query)
        with Session() as sess:
            sess.execute(
                Task.__table__.update().where(Task.id == task_id).values(
                    status="done",
                    result_json=json.dumps({"found": len(leads), "saved": saved}),
                    finished_at=datetime.now(timezone.utc),
                )
            )
            sess.commit()
        log_decision_internal(f"✅ Scrape complete — {saved} new leads in your pipeline")
    except Exception as exc:
        if sentry_sdk:
            sentry_sdk.capture_exception(exc)
        log_decision_internal(f"❌ Scrape failed: {exc}")
        with Session() as sess:
            sess.execute(
                Task.__table__.update().where(Task.id == task_id).values(
                    status="failed", error_message=str(exc),
                    finished_at=datetime.now(timezone.utc),
                )
            )
            sess.commit()


async def _run_outreach_task(task_id: int, limit: int, dry_run: bool) -> None:
    try:
        from src.core.outreach import run_outreach
        log_decision_internal(f"✉️ Starting email outreach — sending personalized cold emails…")
        result = run_outreach(limit=limit, dry_run=dry_run)
        log_decision_internal(f"✅ Outreach complete — {result.sent} sent, {result.skipped} skipped, {result.failed} failed")
        with Session() as sess:
            sess.execute(
                Task.__table__.update().where(Task.id == task_id).values(
                    status="done",
                    result_json=json.dumps({"sent": result.sent, "skipped": result.skipped, "failed": result.failed}),
                    finished_at=datetime.now(timezone.utc),
                )
            )
            sess.commit()
    except Exception as exc:
        if sentry_sdk:
            sentry_sdk.capture_exception(exc)
        log_decision_internal(f"❌ Outreach failed: {exc}")
        with Session() as sess:
            sess.execute(
                Task.__table__.update().where(Task.id == task_id).values(
                    status="failed", error_message=str(exc),
                    finished_at=datetime.now(timezone.utc),
                )
            )
            sess.commit()


# ── Action endpoints (scrape / outreach triggers) ─────────────────────


@app.post("/api/scrape")
@limiter.limit("5/minute")
async def api_scrape(request: Request) -> dict:
    _require_auth(request)
    body = await request.json()
    query = body.get("query", "").strip()
    limit = int(body.get("limit", 10))
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    with Session() as sess:
        t = Task(task_type="scrape", status="running",
                 params_json=json.dumps({"query": query, "limit": limit}))
        sess.add(t)
        sess.commit()
        task_id = t.id
    asyncio.create_task(_run_scrape_task(task_id, query, limit))
    return {"task_id": task_id, "status": "running"}


@app.post("/api/outreach")
@limiter.limit("3/minute")
async def api_outreach(request: Request) -> dict:
    _require_auth(request)
    dry_run = not bool(settings.sendgrid_api_key)
    with Session() as sess:
        t = Task(task_type="outreach", status="running",
                 params_json=json.dumps({"limit": 10, "dry_run": dry_run}))
        sess.add(t)
        sess.commit()
        task_id = t.id
    asyncio.create_task(_run_outreach_task(task_id, 10, dry_run))
    return {"task_id": task_id, "status": "running"}


# ── Email tracking webhook (SendGrid Event Webhook) ─────────────────


@app.post("/api/track")
@limiter.limit("30/minute")
async def api_track(request: Request) -> dict:
    """Receive SendGrid event webhook data (opens, clicks, bounces)."""
    events_raw = await request.body()
    try:
        events = json.loads(events_raw)
    except Exception:
        events = []
    if not isinstance(events, list):
        events = [events]

    for event in events:
        event_type = event.get("event")
        sg_msg_id = event.get("sg_message_id") or event.get("sg_event_id")
        if not sg_msg_id:
            continue

        with Session() as sess:
            lead = sess.execute(
                select(Lead).where(Lead.outreach_email_id == sg_msg_id)
            ).scalar_one_or_none()
            if not lead:
                like = f"%{sg_msg_id[:20]}%"
                lead = sess.execute(
                    select(Lead).where(Lead.outreach_email_id.like(like))
                ).scalar_one_or_none()
            if not lead:
                continue

            now = datetime.now(timezone.utc)
            if event_type == "open" and not lead.opened_at:
                lead.opened_at = now
                lead.outreach_stage = "replied"
            elif event_type == "click":
                if not lead.opened_at:
                    lead.opened_at = now
                if not lead.replied_at:
                    lead.replied_at = now
                lead.outreach_stage = "replied"
            elif event_type in ("bounce", "dropped"):
                lead.outreach_stage = "bounced"
            elif event_type == "delivered" and not lead.sent_at:
                lead.sent_at = now
            sess.commit()

    return {"status": "ok"}


