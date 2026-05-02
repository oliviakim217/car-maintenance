# Car Maintenance Tracker

A personal web app for tracking scheduled maintenance on a 2021 Mazda 3. Displays all maintenance tasks with their current status (due, upcoming, or OK) based on current mileage and date. Tasks are stored in Airtable.

## Features

- Dashboard showing all maintenance tasks sorted by urgency
- Tasks grouped into time buckets: Overdue, Due Soon, Upcoming, OK
- Mark tasks as done, with automatic logging to Airtable
- Mileage tracking with manual odometer readings

## Tech Stack

- **Backend:** Python 3.12, FastAPI
- **Frontend:** HTML/CSS/JS (served by FastAPI)
- **Storage:** Airtable (Tasks, Mileage, Maintenance Log tables)
- **Config:** YAML (`configs/dev/` and `configs/prod/`)

## Setup

See [SETUP.md](SETUP.md) for full setup instructions.

Quick start:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your Airtable credentials
python -m backend.main
```

Open `http://localhost:8000` in your browser.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `APP_ENV` | `dev` or `prod` |
| `APP_LOG_LEVEL` | Logging level (default: `INFO`) |
| `AIRTABLE_TOKEN` | Airtable personal access token |
| `AIRTABLE_BASE_ID_DEV` | Airtable base ID for dev environment |
| `AIRTABLE_BASE_ID_PROD` | Airtable base ID for prod environment |

## Project Structure

```
backend/
  config/       # Config loader
  modules/      # Feature modules (schedule, mileage)
  routes/       # API endpoints
  services/     # Airtable service
  main.py       # Entry point
configs/
  dev/          # Dev YAML config
  prod/         # Prod YAML config
scripts/        # One-off utility scripts (e.g. seed_airtable.py)
tests/
```
