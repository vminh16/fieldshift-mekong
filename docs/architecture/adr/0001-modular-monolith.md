# ADR-0001: Modular monolith with ports/adapters

**Status:** Accepted for starter architecture. **Date:** 2026-11-13.

## Context

Product needs one source of truth for field state, candidate feasibility, crop response, planning and decision evidence. Team scope does not justify service-level deployment complexity.

## Decision

Use one Python backend: transport API → application use cases → framework-agnostic domain; external NASA, crop response and persistence are behind domain ports. Frontend is a separate React app. Keep domain scientific logic server-side. Use a feature-first frontend.

## Consequences

+ Strong boundaries, easier tests and a single decision output to drive Digital Twin.
+ Forecast/model implementations can change behind stable contracts.
- Monolith needs disciplined imports and module ownership.
- Heavy ingestion/compute may later require separate worker processes (same codebase).

## Deferred

No Kafka, Kubernetes, microservices, feature store or RL platform until measurable demand.
