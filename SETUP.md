# Car Maintenance App — Setup Guide

This guide walks you through everything you need to do to get the app running on your computer. No prior experience needed — just follow each step in order.

---

## Prerequisites

Before you begin, make sure you have:

- **Python 3.11 or newer** — download from [python.org](https://www.python.org/downloads/)
- **Git** (optional) — only needed if you want to use version control

---

## 1. Open the Project

Open a terminal window and navigate into the project folder:

```bash
cd path\to\19-Car-Maintenance
```

---

## 2. Create a Virtual Environment

A virtual environment keeps this project's Python packages separate from everything else on your computer.

```bash
python -m venv venv
venv\Scripts\activate
```

Your terminal prompt should now show `(venv)` at the start. Keep this active whenever you work on the project.

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs FastAPI, pyairtable, python-dotenv, and all other required packages.

---

## 4. Create Your .env File

The `.env` file holds environment settings. Copy the example file:

```bash
copy .env.example .env
```

(On Mac/Linux: `cp .env.example .env`)

Fill in your Airtable credentials:

```
APP_ENV=dev
APP_LOG_LEVEL=INFO
AIRTABLE_TOKEN=your_airtable_personal_access_token_here
AIRTABLE_BASE_ID_DEV=appXXXXXXXXXXXXXX
AIRTABLE_BASE_ID_PROD=appXXXXXXXXXXXXXX
```

Your Airtable token can be found at airtable.com → Account → Developer Hub → Personal access tokens.

---

## 5. Set Up the Owner's Manual Q&A Index

The "Ask the Owner's Manual" chat feature needs two things that are **not** included when you
clone or download this repo (they're intentionally excluded from version control):

1. **The manual PDF itself**, which must be placed at:
   ```
   reference/2021_mazda3_manual_en_optimized.pdf
   ```
   Get this file from whoever shared the project with you (e.g. a shared drive or direct
   copy) and put it at that exact path.

2. **The search index built from that PDF.** Once the PDF is in place, build it with:
   ```bash
   python scripts/build_manual_index.py
   ```
   This downloads a small local embedding model on first run and takes a couple of minutes.
   It writes its output to `data/manual_index/` (also not tracked in git — regenerate it
   here, on the server, or on any new machine rather than copying it around).

If you skip this step, the rest of the app works normally — only the manual Q&A chat feature
will return an error until the index is built.

---

## 6. Run the App

Make sure your virtual environment is still active (you should see `(venv)` in your terminal), then run:

```bash
python -m backend.main
```

Open your browser and go to:

```
http://localhost:8000
```

You should see the Car Maintenance dashboard.

---

## 7. First Use

- Your current mileage is tracked via Airtable — add an initial reading via the dashboard
- All maintenance tasks are stored in Airtable and ready to use
- Tasks will show as **Never Done** until you mark them complete for the first time
- Each time you mark a task done, it is automatically logged to the Airtable Maintenance Log table

---

## Troubleshooting

**"Module not found" error when starting**
You are probably running Python outside the virtual environment. Run `venv\Scripts\activate` first, then try again.

**Airtable errors on startup**
Check that your `.env` file has a valid `AIRTABLE_TOKEN` and `AIRTABLE_BASE_ID_DEV`. Tokens are found at airtable.com → Account → Developer Hub.
