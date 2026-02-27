"""
test_scraper.py – Unit tests for the PDC tournament scraper.

All HTTP calls are mocked so these tests run fully offline.
"""

import importlib
import os
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
import requests
from bs4 import BeautifulSoup

import abilities.pdc_darts_notifications.scraper as scraper_module
from abilities.pdc_darts_notifications.scraper import (
    _parse_date,
    _parse_tournaments,
    fetch_tournaments,
)


# ── _parse_date ──────────────────────────────────────────────────────────────

class TestParseDate:
    def test_day_month_year(self):
        assert _parse_date("15 March 2025") == date(2025, 3, 15)

    def test_month_day_year(self):
        assert _parse_date("March 15, 2025") == date(2025, 3, 15)

    def test_slash_format(self):
        assert _parse_date("15/03/2025") == date(2025, 3, 15)

    def test_iso_format(self):
        assert _parse_date("2025-03-15") == date(2025, 3, 15)

    def test_with_leading_whitespace(self):
        assert _parse_date("  2025-03-15  ") == date(2025, 3, 15)

    def test_invalid_returns_none(self):
        assert _parse_date("not a date") is None

    def test_empty_string_returns_none(self):
        assert _parse_date("") is None


# ── _parse_tournaments ───────────────────────────────────────────────────────

class TestParseTournaments:
    def _soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")

    def test_strategy1_article_with_time_datetime(self):
        html = """
        <article class="event">
            <h2>Grand Prix</h2>
            <time datetime="2025-10-06">6 October 2025</time>
        </article>
        """
        tournaments = _parse_tournaments(self._soup(html))
        assert len(tournaments) == 1
        assert tournaments[0]["name"] == "Grand Prix"
        assert tournaments[0]["start_date"] == date(2025, 10, 6)

    def test_strategy1_multiple_events(self):
        html = """
        <article class="event">
            <h2>World Championship</h2>
            <time datetime="2025-12-19">19 December 2025</time>
        </article>
        <article class="event">
            <h2>Premier League</h2>
            <time datetime="2025-02-06">6 February 2025</time>
        </article>
        """
        tournaments = _parse_tournaments(self._soup(html))
        assert len(tournaments) == 2
        names = {t["name"] for t in tournaments}
        assert "World Championship" in names
        assert "Premier League" in names

    def test_strategy1_div_event_card(self):
        html = """
        <div class="event-card">
            <h3>Masters</h3>
            <time datetime="2025-02-01">1 February 2025</time>
        </div>
        """
        tournaments = _parse_tournaments(self._soup(html))
        assert len(tournaments) == 1
        assert tournaments[0]["name"] == "Masters"
        assert tournaments[0]["start_date"] == date(2025, 2, 1)

    def test_strategy2_fallback_generic_event_class(self):
        html = """
        <div class="my-event-item">
            <span>UK Open</span>
            <time datetime="2025-02-28">28 February 2025</time>
        </div>
        """
        tournaments = _parse_tournaments(self._soup(html))
        assert len(tournaments) == 1
        assert tournaments[0]["name"] == "UK Open"
        assert tournaments[0]["start_date"] == date(2025, 2, 28)

    def test_empty_page_returns_empty_list(self):
        html = "<html><body><p>No events</p></body></html>"
        tournaments = _parse_tournaments(self._soup(html))
        assert tournaments == []

    def test_event_missing_date_is_skipped(self):
        html = """
        <article class="event">
            <h2>Mystery Tournament</h2>
        </article>
        """
        tournaments = _parse_tournaments(self._soup(html))
        assert tournaments == []

    def test_event_missing_name_is_skipped(self):
        html = """
        <article class="event">
            <time datetime="2025-10-06">6 October 2025</time>
        </article>
        """
        tournaments = _parse_tournaments(self._soup(html))
        assert tournaments == []


# ── fetch_tournaments ────────────────────────────────────────────────────────

class TestFetchTournaments:
    def test_returns_parsed_tournaments_on_success(self):
        mock_html = """
        <article class="event">
            <h2>World Grand Prix</h2>
            <time datetime="2025-10-06">6 October 2025</time>
        </article>
        """
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.raise_for_status = MagicMock()

        with patch(
            "abilities.pdc_darts_notifications.scraper.requests.get",
            return_value=mock_response,
        ):
            result = fetch_tournaments()

        assert len(result) == 1
        assert result[0]["name"] == "World Grand Prix"
        assert result[0]["start_date"] == date(2025, 10, 6)

    def test_returns_empty_list_on_request_exception(self):
        with patch(
            "abilities.pdc_darts_notifications.scraper.requests.get",
            side_effect=requests.RequestException("timeout"),
        ):
            result = fetch_tournaments()

        assert result == []

    def test_accepts_custom_url(self):
        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.raise_for_status = MagicMock()

        with patch(
            "abilities.pdc_darts_notifications.scraper.requests.get",
            return_value=mock_response,
        ) as mock_get:
            fetch_tournaments(url="https://example.com/custom")
            mock_get.assert_called_once_with(
                "https://example.com/custom", timeout=15
            )

    def test_uses_env_var_url_by_default(self):
        with patch.dict("os.environ", {"PDC_CALENDAR_URL": "https://example.com/env-url"}):
            importlib.reload(scraper_module)
            assert scraper_module.PDC_CALENDAR_URL == "https://example.com/env-url"

        # Reload without the env var to restore state
        env_without_url = {k: v for k, v in os.environ.items() if k != "PDC_CALENDAR_URL"}
        with patch.dict("os.environ", env_without_url, clear=True):
            importlib.reload(scraper_module)

    def test_default_url_is_pdc_calendar(self):
        env_without_url = {k: v for k, v in os.environ.items() if k != "PDC_CALENDAR_URL"}
        with patch.dict("os.environ", env_without_url, clear=True):
            importlib.reload(scraper_module)
            assert scraper_module.PDC_CALENDAR_URL == "https://www.pdc.tv/calendar"
