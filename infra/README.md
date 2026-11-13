# Infrastructure

`compose.yaml` starts development-only API + Web. No production database, queue or object store is initialized because application persistence has not been implemented. Do not deploy it publicly without auth, TLS, secret handling and logging controls. See `docs/operations/DEPLOYMENT.md`.
