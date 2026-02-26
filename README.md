# OpenClaw Abilities

Core ability logic and related tooling for the OpenClaw project.

## Overview

This repository hosts:

- Ability definitions and behavior rules
- Supporting scripts/utilities
- Project documentation and references

## Project Structure

```
abilities/
└── pdc_darts_notifications/   # PDC Darts tournament reminder via Signal
    ├── __init__.py
    ├── scraper.py             # Scrapes PDC calendar for tournament dates
    ├── notifier.py            # Sends Signal messages via REST API or CLI
    ├── scheduler.py           # APScheduler-based periodic check
    ├── main.py                # Entry point
    ├── requirements.txt       # Python dependencies
    ├── .env.example           # Configuration template
    └── tests/
        └── test_scraper.py    # Unit tests (scraper mocked)
README.md
```

---

## Ability: PDC Darts Notifications (`abilities/pdc_darts_notifications`)

Sends a Signal message on the day a PDC darts tournament starts.

### How it works

1. **Scraper** – Fetches `https://www.pdc.tv/calendar` with `requests` +
   `BeautifulSoup` and extracts tournament names and start dates.  Two
   selector strategies are tried in order so the scraper can adapt to minor
   site redesigns.
2. **Notifier** – Delivers a message like
   *"Reminder: The Grand Prix starts today!"* via either:
   - the [signal-cli REST API](https://github.com/bbernhard/signal-cli-rest-api)
     (`SIGNAL_MODE=rest`, default), or
   - a locally installed `signal-cli` binary (`SIGNAL_MODE=cli`).
3. **Scheduler** – An [APScheduler](https://apscheduler.readthedocs.io/)
   `BlockingScheduler` polls the calendar at a configurable interval
   (default every 24 hours).

### Prerequisites

- Python ≥ 3.10
- A registered Signal number and either:
  - A running [signal-cli REST API](https://github.com/bbernhard/signal-cli-rest-api) container, **or**
  - A locally installed [signal-cli](https://github.com/AsamK/signal-cli) binary

### Installation

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd openclaw-abilities

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r abilities/pdc_darts_notifications/requirements.txt

# 4. Configure environment variables
cp abilities/pdc_darts_notifications/.env.example .env
# Edit .env with your Signal numbers and preferred mode
```

### Configuration

Copy `.env.example` to `.env` (or set the variables in your environment):

| Variable | Default | Description |
|---|---|---|
| `SIGNAL_SENDER_NUMBER` | *(required)* | Registered Signal sender number (E.164) |
| `SIGNAL_RECIPIENT_NUMBER` | *(required)* | Recipient phone number (E.164) |
| `SIGNAL_MODE` | `rest` | `rest` – REST API · `cli` – local binary |
| `SIGNAL_REST_URL` | `http://localhost:8080` | Base URL of signal-cli REST API |
| `SIGNAL_CLI_PATH` | `signal-cli` | Path to local signal-cli binary |
| `CHECK_INTERVAL_HOURS` | `24` | How often (hours) to poll the PDC calendar |
| `LOG_LEVEL` | `INFO` | Python logging level |

### Running

**Persistent scheduler** (checks every `CHECK_INTERVAL_HOURS`):

```bash
python -m abilities.pdc_darts_notifications.main
```

**One-shot check** (useful with an external cron job):

```bash
python -m abilities.pdc_darts_notifications.main --once
```

**Example cron entry** (run daily at 08:00):

```cron
0 8 * * * /path/to/.venv/bin/python -m abilities.pdc_darts_notifications.main --once >> /var/log/pdc_darts.log 2>&1
```

### Running Tests

```bash
pip install pytest
pytest abilities/pdc_darts_notifications/tests/ -v
```

---

## Contributing

1. Create a feature branch.
2. Make focused changes.
3. Open a pull request with a clear description.

## License

Add your project license information here.