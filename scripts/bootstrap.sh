#!/usr/bin/env bash
set -euo pipefail
python3.11 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -e './apps/api[dev]'
(cd apps/web && npm install --no-audit --no-fund)
cp -n .env.example .env || true
echo 'Bootstrap complete. Start: source .venv/bin/activate && make api-dev; in another terminal: make web-dev'
