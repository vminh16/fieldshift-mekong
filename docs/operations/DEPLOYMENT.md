# Deployment topology

Current Compose file is **local development**, not a production deployment blueprint.

Future deployment boundaries: one web frontend, one FastAPI backend, optional worker process from same codebase, persistent PostgreSQL + object store if required. Keep NASA ingestion outside synchronous request path when latency warrants.

Production prerequisites: authentication/authorization and farmer data isolation; secret management; TLS; versioned model/config artifacts; backups and tested restores; monitoring, tracing and alerting; migration strategy; security scans; deployment approvals + rollback; NASA and local dataset licenses.

`.github/workflows/deploy.yml` currently **builds containers on manual trigger**, does not publish or deploy anywhere.
