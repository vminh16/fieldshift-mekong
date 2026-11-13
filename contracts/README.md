# API contract

`openapi.json` is **generated from FastAPI routes** via:

```bash
make contracts
```

CI checks that the file matches the current API (`--check`). Do not edit it by hand. Routes are currently scaffold-only and are **not proof of Planning Engine implementation**. The future `DecisionPackage` must follow `docs/architecture/SOLUTION_DESIGN.md`.
