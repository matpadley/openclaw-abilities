"""
scheduler.py – Periodic job that checks for PDC tournaments starting today
and fires Signal notifications via the notifier module.

Uses APScheduler (``pip install apscheduler``).  The check interval is
controlled by the ``CHECK_INTERVAL_HOURS`` environment variable (default: 24).
"""

import logging
import os
from datetime import date

from apscheduler.schedulers.blocking import BlockingScheduler

from .notifier import send_notification
from .scraper import fetch_tournaments

logger = logging.getLogger(__name__)


def check_and_notify() -> None:
    """
    Fetch the PDC calendar and send a Signal message for every tournament
    whose start date matches today's date.
    """
    today = date.today()
    logger.info("Checking PDC calendar for tournaments starting on %s…", today)

    tournaments = fetch_tournaments()
    notified = 0
    for tournament in tournaments:
        if tournament["start_date"] == today:
            success = send_notification(tournament["name"])
            if success:
                notified += 1
                logger.info("Notified: %s", tournament["name"])

    if notified == 0:
        logger.info("No tournaments start today (%s).", today)


def run_scheduler() -> None:
    """
    Start the blocking APScheduler that calls :func:`check_and_notify`
    at a configurable interval.
    """
    interval_str = os.getenv("CHECK_INTERVAL_HOURS", "24")
    try:
        interval_hours = int(interval_str)
    except ValueError:
        logger.warning(
            "Invalid CHECK_INTERVAL_HOURS value %r; falling back to default of 24 hours.",
            interval_str,
        )
        interval_hours = 24

    scheduler = BlockingScheduler()
    scheduler.add_job(
        check_and_notify,
        trigger="interval",
        hours=interval_hours,
        id="pdc_darts_check",
        name="PDC Darts Tournament Check",
        replace_existing=True,
    )

    logger.info(
        "Scheduler started – checking every %d hour(s). Press Ctrl+C to stop.",
        interval_hours,
    )

    # Run once immediately on startup so we don't miss today's events.
    check_and_notify()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
