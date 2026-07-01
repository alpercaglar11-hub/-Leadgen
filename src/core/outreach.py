"""Cold email outreach module with SendGrid delivery and live telemetry."""

from __future__ import annotations

import json
import os
from typing import List

import structlog

import sendgrid
from sendgrid.helpers.mail import Content, Email, Mail, Personalization, Bcc

from src.config import settings
from src.db import Lead, Session
from src.stream import log_decision

logger = structlog.get_logger(__name__)


class OutreachResult:
    sent: int
    skipped: int
    failed: int
    errors: List[str]

    def __init__(self):
        self.sent = 0
        self.skipped = 0
        self.failed = 0
        self.errors = []


def _send_email(to_email: str, subject: str, body_text: str) -> tuple[bool, str | None]:
    """Send a single email via SendGrid. Returns (success, message_id_or_error)."""
    if not settings.sendgrid_api_key:
        logger.warning("SENDGRID_API_KEY not set — skipping real send")
        return False, "SendGrid not configured"

    sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
    mail = Mail(
        from_email=Email(settings.from_email, settings.from_name),
        subject=subject,
        plain_text_content=Content("text/plain", body_text),
    )
    p = Personalization()
    p.add_to(Email(to_email))
    mail.add_personalization(p)

    try:
        resp = sg.send(mail)
        msg_id = resp.headers.get("X-Message-Id") if resp.headers else None
        if resp.status_code in (200, 201, 202):
            return True, msg_id
        return False, f"HTTP {resp.status_code}"
    except Exception as exc:
        return False, str(exc)


def run_outreach(limit: int = 5, dry_run: bool = True) -> OutreachResult:
    """Fetch qualified leads and send personalized cold emails.

    *dry_run* logs but does not send.
    """
    result = OutreachResult()

    with Session() as sess:
        leads = sess.execute(
            Lead.__table__.select()
            .where(Lead.outreach_stage == "new")
            .order_by(Lead.created_at.asc())
            .limit(limit)
        ).all()

    with Session() as sess:
        log_decision(sess, decision_type="outreach",
                     reasoning=f"Initializing outreach pipeline: {len(leads)} leads loaded, dry_run={dry_run}, stage_filter='new'",
                     confidence=0.95, success=True,
                     payload={"limit": limit, "dry_run": dry_run, "lead_count": len(leads)})
        sess.commit()

    if not leads:
        with Session() as sess:
            log_decision(sess, decision_type="skip",
                         reasoning="No leads in 'new' stage — outreach queue is empty. Run scraper first.",
                         confidence=1.0, success=True)
            sess.commit()
        return result

    for row in leads:
        company = row.company_name or "there"
        website = row.website or ""

        if not website and not row.email:
            result.skipped += 1
            with Session() as sess:
                log_decision(sess, decision_type="skip",
                             reasoning=f"Skipping lead '{company}' (id={row.id}): missing website and email — cannot send outreach",
                             confidence=0.8, success=True,
                             payload={"lead_id": row.id, "company": company, "reason": "no_website_or_email"})
                sess.commit()
            continue

        subject = f"Quick question for {company}"
        body = f"""Hi {company} team,

I came across your work and was impressed by what you're building.

I specialize in helping businesses like yours generate more qualified leads through automated outreach — saving hours of manual work every week.

Would you be open to a quick chat this week to see if this could be a fit?

Best,
LeadGen Agent"""

        if dry_run:
            logger.info("[DRY RUN] Would email %s — %s", company, subject)
            with Session() as sess:
                log_decision(sess, decision_type="outreach",
                             reasoning=f"[DRY_RUN] Cold email generated for '{company}' (website={website or 'none'}): subject='{subject}' — would be sent to decision-maker",
                             confidence=0.9, success=True,
                             payload={"lead_id": row.id, "company": company, "website": website,
                                      "subject": subject[:80], "dry_run": True})
                sess.commit()
            result.sent += 1
        else:
            if not row.email:
                result.skipped += 1
                with Session() as sess:
                    log_decision(sess, decision_type="skip",
                                 reasoning=f"No email address for '{company}' — skipping real send",
                                 confidence=0.8, success=True,
                                 payload={"lead_id": row.id, "company": company})
                    sess.commit()
                continue
            ok, msg_id = _send_email(row.email, subject, body)
            if ok:
                with Session() as sess:
                    sess.execute(
                        Lead.__table__.update()
                        .where(Lead.id == row.id)
                        .values(outreach_stage="contacted", outreach_email_id=msg_id)
                    )
                    sess.commit()
                    log_decision(sess, decision_type="outreach",
                                 reasoning=f"Cold email dispatched via SendGrid to '{company}' ({row.email}): subject='{subject}', message_id={msg_id}",
                                 confidence=0.9, success=True,
                                 payload={"lead_id": row.id, "company": company, "email": row.email,
                                          "subject": subject[:80], "message_id": msg_id})
                    sess.commit()
                result.sent += 1
                logger.info("Sent email to %s <%s> — sg-id=%s", company, row.email, msg_id)
            else:
                result.failed += 1
                result.errors.append(f"{company}: {msg_id}")
                with Session() as sess:
                    log_decision(sess, decision_type="error",
                                 reasoning=f"SendGrid delivery failed for '{company}' ({row.email}): {msg_id}",
                                 confidence=0.0, success=False, error_message=msg_id,
                                 payload={"lead_id": row.id, "company": company, "email": row.email})
                    sess.commit()

    total = result.sent + result.skipped + result.failed
    rate = round(result.sent / total * 100, 1) if total > 0 else 0
    with Session() as sess:
        log_decision(sess, decision_type="outreach",
                     reasoning=f"Outreach cycle finished: {result.sent} sent, {result.skipped} skipped, {result.failed} errors. Success rate: {rate}%",
                     confidence=1.0 if result.failed == 0 else 0.5,
                     success=result.failed == 0,
                     payload={"sent": result.sent, "skipped": result.skipped,
                              "failed": result.failed, "success_rate": rate})
        sess.commit()

    return result
