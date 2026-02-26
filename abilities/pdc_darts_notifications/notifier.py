"""
notifier.py – Sends Signal messages via the Signal CLI REST API or local
signal-cli binary.

The notifier supports two modes, controlled by the ``SIGNAL_MODE`` env var:

* ``"rest"``  (default) – calls the signal-cli REST API at ``SIGNAL_REST_URL``
* ``"cli"``   – shells out to the ``signal-cli`` binary at ``SIGNAL_CLI_PATH``
"""

import logging
import os
import subprocess

import requests

logger = logging.getLogger(__name__)


def send_notification(tournament_name: str) -> bool:
    """
    Send a Signal message for the given *tournament_name*.

    Returns ``True`` on success, ``False`` on failure.
    """
    message = f"Reminder: The {tournament_name} starts today!"
    mode = os.getenv("SIGNAL_MODE", "rest").lower()

    if mode == "cli":
        return _send_via_cli(message)
    return _send_via_rest(message)


# ── REST helper ──────────────────────────────────────────────────────────────

def _send_via_rest(message: str) -> bool:
    """POST to the signal-cli REST API (https://github.com/bbernhard/signal-cli-rest-api)."""
    sender = os.getenv("SIGNAL_SENDER_NUMBER")
    recipient = os.getenv("SIGNAL_RECIPIENT_NUMBER")
    base_url = os.getenv("SIGNAL_REST_URL", "http://localhost:8080")

    if not sender or not recipient:
        logger.error(
            "SIGNAL_SENDER_NUMBER and SIGNAL_RECIPIENT_NUMBER must be set."
        )
        return False

    url = f"{base_url}/v2/send"
    payload = {
        "message": message,
        "number": sender,
        "recipients": [recipient],
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("Signal message sent via REST API: %r", message)
        return True
    except requests.RequestException as exc:
        logger.error("Failed to send Signal message via REST: %s", exc)
        return False


# ── CLI helper ───────────────────────────────────────────────────────────────

def _send_via_cli(message: str) -> bool:
    """Shell out to the local signal-cli binary."""
    sender = os.getenv("SIGNAL_SENDER_NUMBER")
    recipient = os.getenv("SIGNAL_RECIPIENT_NUMBER")
    cli_path = os.getenv("SIGNAL_CLI_PATH", "signal-cli")

    if not sender or not recipient:
        logger.error(
            "SIGNAL_SENDER_NUMBER and SIGNAL_RECIPIENT_NUMBER must be set."
        )
        return False

    cmd = [
        cli_path,
        "-u", sender,
        "send",
        "-m", message,
        recipient,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(
                "signal-cli exited with code %d: %s",
                result.returncode,
                result.stderr,
            )
            return False
        logger.info("Signal message sent via CLI: %r", message)
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        logger.error("Failed to run signal-cli: %s", exc)
        return False
