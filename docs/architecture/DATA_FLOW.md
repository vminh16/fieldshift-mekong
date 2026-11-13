# Data flow and ownership

```text
NASA / Local / Field inputs
   -> Ingestion adapters (metadata, provenance, quality)
   -> FieldState + ScenarioSet (typed outlook)
   -> Candidate Generator + Feasibility
   -> Crop–Soil Response (candidate × scenario -> outcome + trajectory)
   -> Rotation Planner (risk-aware shortlist + baseline)
   -> DecisionPackage immutable snapshot
   -> API -> Web comparison, Digital Twin viewer, what-if
```

- FieldProfile (input) is not FieldState (estimate at `as_of`).
- NASA historical replay ≠ calibrated seasonal forecast.
- Scenario outcome is modeled conditional result, not observed yield.
- Twin UI never creates or modifies scientific outputs.
- Persist `as_of`, availability/issue timestamps, crop/rule/model versions and input hashes for reproducibility.

See [Solution Design](SOLUTION_DESIGN.md) sections 5–10.
