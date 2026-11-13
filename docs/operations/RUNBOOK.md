# Development runbook

1. Start API (`make api-dev`) and Web (`make web-dev`) in separate terminals, or use Docker Compose.
2. `curl -fsS http://localhost:8000/v1/health` must show `mode: scaffold`.
3. If Web shows `offline`, confirm API process, CORS_ORIGINS and VITE_API_BASE_URL.
4. Unit tests: `make test`; YAML/catalog: `make config-check`; docs: http://localhost:8000/docs.
5. Planned NASA adapters are not connected. Do not diagnose missing recommendation functionality as an API data outage; the planning endpoint intentionally returns 501.
6. Do not log location coordinates, personal details, tokens or raw farmer inputs as diagnostics.

Production runbook (metrics, backups, incident steps, model rollback, token rotation) remains to be authored when services are implemented.
