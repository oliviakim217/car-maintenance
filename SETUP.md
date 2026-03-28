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

This installs FastAPI, openpyxl, python-dotenv, and all other required packages.

---

## 4. Create Your .env File

The `.env` file holds environment settings. Copy the example file:

```bash
copy .env.example .env
```

(On Mac/Linux: `cp .env.example .env`)

The defaults are fine as-is — no changes needed to get started:

```
APP_ENV=dev
APP_LOG_LEVEL=INFO
```

---

## 5. Run the App

Make sure your virtual environment is still active (you should see `(venv)` in your terminal), then run:

```bash
python server.py
```

Open your browser and go to:

```
http://localhost:8000
```

You should see the Car Maintenance dashboard.

---

## 6. First Use

- Your current mileage (40,000 km) is pre-loaded as the starting reading
- All 25 maintenance tasks from your Mazda 3 owner's manual are loaded and ready
- Tasks will show as **Never Done** until you mark them complete for the first time
- Each time you mark a task done, it is automatically logged to `data/maintenance_log.xlsx` — the file is created on first use

---

## Troubleshooting

**"Module not found" error when starting**
You are probably running Python outside the virtual environment. Run `venv\Scripts\activate` first, then try again.

**Excel log not appearing**
The file `data/maintenance_log.xlsx` is created automatically the first time you mark a task as done. If it doesn't appear, check that the `data/` folder exists and that you have write permissions to the project folder.
