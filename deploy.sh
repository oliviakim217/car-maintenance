#!/usr/bin/env bash
# VM deploy script for the car-maintenance FastAPI app.
# Run manually first (`./deploy.sh` from /opt/car-maintenance) to verify it
# works before GitHub Actions calls it automatically. See
# references — .github/workflows/deploy.yml invokes this over SSH.
set -euo pipefail

APP_DIR="${DEPLOY_APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
BRANCH="${DEPLOY_BRANCH:-main}"
SYSTEMD_SERVICE="${SYSTEMD_SERVICE:-car-maintenance.service}"

log() {
    printf '[deploy] %s\n' "$1"
}

fail() {
    printf '[deploy] ERROR: %s\n' "$1" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"
}

require_command git
require_command sudo

cd "${APP_DIR}"

if [[ ! -f "${APP_DIR}/venv/bin/activate" ]]; then
    fail "No venv found at ${APP_DIR}/venv — create it once with: python3 -m venv venv"
fi

if [[ ! -f "${APP_DIR}/.env" ]]; then
    fail "No .env found at ${APP_DIR}/.env — create it once from .env.example"
fi

log "Fetching latest code from origin/${BRANCH}"
git fetch origin "${BRANCH}"
git reset --hard "origin/${BRANCH}"

log "Installing dependencies"
# shellcheck disable=SC1091
source "${APP_DIR}/venv/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

log "Restarting ${SYSTEMD_SERVICE}"
sudo systemctl restart "${SYSTEMD_SERVICE}"

log "Deployment completed successfully"
