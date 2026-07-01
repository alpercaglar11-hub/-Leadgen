"""Browser-based lead scraper using Kimi WebBridge CDP."""

from __future__ import annotations

import json
import re
import time
from typing import List

import structlog

from src.browser.kimi import KimiBrowser, BrowserError
from src.db import Lead, Session
from src.stream import log_decision

logger = structlog.get_logger(__name__)

SEARCH_URL = "https://www.google.com"


class ScrapedLead:
    company: str
    website: str | None
    snippet: str | None

    def __init__(self, company: str, website: str | None = None, snippet: str | None = None):
        self.company = company
        self.website = website
        self.snippet = snippet


def scrape_google(query: str, limit: int = 10) -> List[ScrapedLead]:
    """Search Google for *query* and extract organic result leads."""
    browser = KimiBrowser()
    if not browser.check_available():
        raise BrowserError("Kimi WebBridge is not available — is the daemon running?")

    results: List[ScrapedLead] = []

    with Session() as sess:
        log_decision(sess, decision_type="scrape",
                     reasoning=f"Starting scrape pipeline: query='{query}', target_source='google_search', max_results={limit}",
                     confidence=0.95, success=True,
                     payload={"query": query, "step": "start", "limit": limit, "source": "google"})
        sess.commit()

    # 1. Navigate
    logger.info("Navigating to Google", url=SEARCH_URL)
    browser.navigate(SEARCH_URL)
    time.sleep(1.5)

    with Session() as sess:
        log_decision(sess, decision_type="scrape",
                     reasoning=f"Navigated to google.com and focusing search input for query: '{query}'",
                     confidence=0.9, success=True,
                     payload={"query": query, "step": "navigate", "url": SEARCH_URL})
        sess.commit()

    # 2. Navigate directly to search results URL
    import urllib.parse
    search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&num={limit+5}"
    browser.navigate(search_url)
    time.sleep(3.0)

    with Session() as sess:
        log_decision(sess, decision_type="scrape",
                     reasoning=f"Submitted search '{query}' to Google. Waiting for results page to load.",
                     confidence=0.85, success=True,
                     payload={"query": query, "step": "search_submit"})
        sess.commit()

    # 3. Extract search results via JavaScript DOM evaluation
    try:
        js = """
        (function() {
            var items = [];
            var anchors = document.querySelectorAll('a[href^="http"]');
            var seen = {};
            anchors.forEach(function(a) {
                var href = a.href;
                var text = a.innerText || a.textContent || '';
                text = text.trim();
                if (!text || text.length < 3) return;
                var domain = href.replace(/https?:\\/\\//, '').replace(/www\./, '').split('/')[0].toLowerCase();
                if (seen[domain]) return;
                var skip = ['google.com','youtube.com','facebook.com','instagram.com','twitter.com',
                           'linkedin.com','wikipedia.org','maps.google.com','accounts.google.com',
                           'support.google.com','policies.google.com'];
                if (skip.indexOf(domain) !== -1) return;
                if (text.match(/sign in|sign up|login|register|subscribe|cookie|privacy|terms|maps|images|shopping/i)) return;
                seen[domain] = true;
                items.push({name: text.substring(0, 100), url: href});
            });
            return JSON.stringify(items);
        })();
        """
        raw_result = browser.evaluate(js)
    except BrowserError as exc:
        with Session() as sess:
            log_decision(sess, decision_type="error",
                         reasoning=f"Failed to extract search results via JS: {exc}",
                         confidence=0.0, success=False, error_message=str(exc),
                         payload={"query": query, "step": "extract"})
            sess.commit()
        return results

    try:
        raw_json = raw_result.get("value", "") if isinstance(raw_result, dict) else str(raw_result)
        all_results = json.loads(raw_json) if raw_json else []
    except (json.JSONDecodeError, TypeError) as exc:
        with Session() as sess:
            log_decision(sess, decision_type="error",
                         reasoning=f"Failed to parse search results JSON: {exc}",
                         confidence=0.0, success=False, error_message=str(exc),
                         payload={"query": query, "step": "parse"})
            sess.commit()
        return results

    seen_domains = set()
    for item in all_results:
        if len(results) >= limit:
            break
        name = item.get("name", "").strip()
        url = item.get("url", "").strip()
        if not name or not url:
            continue
        domain = _extract_domain(url)
        if not domain or domain in seen_domains:
            continue
        seen_domains.add(domain)
        results.append(ScrapedLead(company=name, website=url, snippet=name))

    domains_show = [l.website for l in results[:5] if l.website]
    domain_str = ", ".join(d.split("/")[2] if "//" in d else d for d in domains_show)
    if len(results) > 5:
        domain_str += f" … and {len(results)-5} more"
    with Session() as sess:
        log_decision(sess, decision_type="leads",
                     reasoning=f"Extracted {len(results)} company leads from search results for '{query}': {domain_str}",
                     confidence=0.85, success=True,
                     payload={"query": query, "count": len(results), "limit": limit,
                              "domains": [l.website for l in results if l.website]})
        sess.commit()

    logger.info("Parsed leads from search", count=len(results))
    return results


def save_leads_to_db(leads: List[ScrapedLead], query: str) -> int:
    """Save scraped leads to the database and return count saved."""
    saved = 0
    with Session() as sess:
        for lead in leads:
            existing = sess.execute(
                Lead.__table__.select().where(Lead.company_name == lead.company)
            ).first()
            if existing:
                continue
            sess.add(Lead(
                source="google",
                company_name=lead.company,
                website=lead.website,
                raw_data=json.dumps({"snippet": lead.snippet, "query": query}),
            ))
            saved += 1

        log_decision(sess, decision_type="leads",
                     reasoning=f"Persisted {saved} new leads to database (skipped {len(leads)-saved} duplicates) for query: '{query}'",
                     confidence=0.95, success=True,
                     payload={"query": query, "saved": saved, "duplicates": len(leads)-saved, "total_found": len(leads)})
        sess.commit()
    return saved


# ── Parsing helpers ───────────────────────────────────────────────────────


def _extract_links_from_tree(node) -> list[dict]:
    """Walk the CDP accessibility tree and collect navigable links."""
    links = []
    if not isinstance(node, dict):
        return links

    role = (node.get("role") or {}).get("value", "")
    name = (node.get("name") or {}).get("value", "")
    url = ""
    for child in node.get("children", []):
        url = url or _extract_url_from_node(child)

    if role == "link" and name and url:
        links.append({"name": name, "url": url})

    for child in node.get("children", []):
        sub = _extract_links_from_tree(child)
        for s in sub:
            if not s.get("url") and url:
                s["url"] = url
        links.extend(sub)

    return links


def _extract_url_from_node(node: dict) -> str:
    """Recursively find a URL attribute in a CDP tree node."""
    if not isinstance(node, dict):
        return ""
    val = node.get("value", "")
    if isinstance(val, str) and val.startswith("http"):
        return val
    for child in node.get("children", []):
        result = _extract_url_from_node(child)
        if result:
            return result
    return ""


def _extract_domain(url: str) -> str | None:
    m = re.search(r"https?://([^/]+)", url)
    if m:
        return m.group(1).replace("www.", "").lower()
    return None


def _is_not_company_result(name: str, domain: str, url: str) -> bool:
    """Filter out non-company results."""
    skip_domains = {
        "google.com", "youtube.com", "facebook.com", "instagram.com",
        "twitter.com", "linkedin.com", "pinterest.com", "reddit.com",
        "wikipedia.org", "translate.google.com", "maps.google.com",
        "shopping.google.com", "news.google.com",
    }
    skip_patterns = {"translate", "sign in", "sign up", "login", "register",
                     "subscribe", "cookie", "privacy", "terms", "maps",
                     "images", "shopping", "sponsored"}
    d = domain.lower().replace("www.", "")
    if d in skip_domains:
        return True
    name_l = name.lower()
    for pat in skip_patterns:
        if pat in name_l:
            return True
    return False
