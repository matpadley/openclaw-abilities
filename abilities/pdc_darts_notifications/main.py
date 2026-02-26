"""
main.py – Entry point for the PDC Darts Notifications ability.

Usage
-----
Run once (check today and exit)::

    python -m abilities.pdc_darts_notifications.main --once

Run the persistent scheduler (keeps running until interrupted)::

    python -m abilities.pdc_darts_notifications.main
"""

import argparse
import logging
import os

from dotenv import load_dotenv

from .scheduler import check_and_notify, run_scheduler

# Load environment variables from a .env file if present.
load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PDC Darts Notifications – send Signal alerts for upcoming tournaments."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Check for today's tournaments once and exit (useful for cron jobs).",
    )
    args = parser.parse_args()

    if args.once:
        logger.info("Running one-shot check…")
        check_and_notify()
    else:
        run_scheduler()


if __name__ == "__main__":
    main()
