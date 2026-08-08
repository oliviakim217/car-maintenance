# Car Maintenance App — Overview

## What It Does

A personal web app for tracking and staying on top of car maintenance for a 2021 Mazda 3.

Instead of manually remembering when things are due, the app tracks your mileage over time and tells you which maintenance tasks are coming up — colour-coded by urgency. When something gets done, you log it and the schedule resets automatically.

### Core Features

- **Mileage tracking** — Enter your odometer reading manually, or take a photo of your dashboard and let AI read it for you
- **Maintenance schedule** — See all tasks (oil change, tyre rotation, brake fluid, etc.) with a status: overdue, due soon, or all good
- **Mark as done** — Log completed services with date, km, and notes; the schedule updates immediately
- **Estimated mileage** — Even between manual readings, the app estimates your current km based on your average daily driving (10 km on weekdays, 40 km on weekends)

---

## How It Was Built

This is a learning project built to explore modern web app development and AI integration.

### Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI |
| Frontend | Vanilla HTML/CSS/JavaScript (no framework) |
| Data storage | Airtable (cloud spreadsheet with REST API) |
| AI | Claude Haiku (Anthropic) — used for reading odometer from photos |
| Deployment | Docker, hosted on Render |
| Version control | GitHub |

### Architecture

The backend follows a layered structure:

```
Routes → Service/Module → Airtable API
```

- **Routes** handle HTTP requests and nothing else
- **Modules** contain the business logic (mileage estimation, schedule calculation)
- **Services** handle all external calls (Airtable, Claude AI)
- **Config** lives in YAML files, with secrets in environment variables

### AI Integration

The "Take a Photo" feature uses Claude Haiku's vision capability. When you upload a dashboard photo, the image is sent to Claude with a prompt asking it to read the odometer. Claude returns the number, the app validates it looks plausible, and asks you to confirm before saving. No photo is stored — it's used once and discarded.

---

## Who Built It

Built by Olivia as a personal learning project, with the goals of:
- Learning how to build a production-quality Python web app
- Understanding how to integrate AI into a real feature
- Practising software engineering fundamentals (config-driven design, input validation, structured logging, version control)
