"""
scraper.py – Fetches PDC tournament schedule from https://www.pdc.tv/calendar
and returns a list of upcoming tournaments with their start dates.
"""

import logging
import os
from datetime import date, datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

PDC_CALENDAR_URL = os.getenv("PDC_CALENDAR_URL", "https://www.pdc.tv/calendar")

# Selector priority list – the scraper tries each strategy in order so that it
# can survive minor site redesigns without requiring a code change.
_DATE_FORMATS = [
    "%d %B %Y",   # e.g. "01 January 2025"
    "%B %d, %Y",  # e.g. "January 01, 2025"
    "%d/%m/%Y",   # e.g. "01/01/2025"
    "%Y-%m-%d",   # ISO 8601
]


def _parse_date(raw: str) -> Optional[date]:
    """Try multiple date formats and return a ``date`` object, or *None*."""
    raw = raw.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    logger.warning("Could not parse date string: %r", raw)
    return None


def fetch_tournaments(url: str = PDC_CALENDAR_URL) -> list[dict]:
    """
    Scrape the PDC calendar page and return a list of tournament dicts::

        [{"name": "Grand Prix", "start_date": date(2025, 10, 6)}, ...]

    The function tries several CSS selectors in sequence so it is resilient to
    minor markup changes on the PDC website.
    """
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to fetch PDC calendar: %s", exc)
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    tournaments = _parse_tournaments(soup)

    if not tournaments:
        logger.warning(
            "No tournaments found – the PDC site structure may have changed."
        )
    return tournaments


def _parse_tournaments(soup: BeautifulSoup) -> list[dict]:
    """
    Extract tournament data from a BeautifulSoup document.

    Strategy 1 – structured ``<article>`` / ``<div>`` blocks with explicit
    date and title elements (modern PDC markup).

    Strategy 2 – fall back to any element whose class name contains
    ``"event"`` and look for sibling/child date text.
    """
    tournaments: list[dict] = []

    # ── Strategy 1: article / event-card style ──────────────────────────────
    for article in soup.select(
        "article.event, div.event-card, div.calendar-event, "
        "li.event, div.views-row"
    ):
        name = _extract_text(
            article,
            "h2, h3, h4, .event-title, .field--name-title, "
            ".views-field-title span.field-content",
        )
        date_raw = _extract_text(
            article,
            "time, .event-date, .date-display-single, "
            ".field--name-field-date, .views-field-field-date "
            "span.field-content",
        )

        # ``<time datetime="…">`` carries a machine-readable value.
        time_tag = article.find("time")
        if time_tag and time_tag.get("datetime"):
            dt_attr = str(time_tag["datetime"])
            date_raw = dt_attr[:10] if len(dt_attr) >= 10 else dt_attr

        parsed = _parse_date(date_raw) if date_raw else None
        if name and parsed:
            tournaments.append({"name": name.strip(), "start_date": parsed})

    if tournaments:
        return tournaments

    # ── Strategy 2: generic fallback ────────────────────────────────────────
    for el in soup.find_all(class_=lambda c: c and "event" in c.lower()):
        name_tag = el.find(["h2", "h3", "h4", "span", "a"])
        time_tag = el.find("time")
        if name_tag and time_tag:
            date_raw = time_tag.get("datetime", time_tag.get_text())[:10]
            parsed = _parse_date(date_raw)
            if name_tag.get_text() and parsed:
                tournaments.append(
                    {
                        "name": name_tag.get_text().strip(),
                        "start_date": parsed,
                    }
                )

    return tournaments


def _extract_text(parent: BeautifulSoup, selector: str) -> Optional[str]:
    """Return stripped text from the first matching element, or *None*."""
    el = parent.select_one(selector)
    return el.get_text(strip=True) if el else None
