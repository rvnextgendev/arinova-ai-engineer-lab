# Skill Studio — presentation notes

## Slide 1: Why skills
Shared AI runtime, explicit business capability contracts, independent tests.

## Slide 2: Architecture
Browser → FastAPI → reviewed registry → permission check → handler → existing RAG or fixed SQL → result and telemetry.

## Slide 3: Live demonstration
Upload synthetic policy PDF; select HR Policy; execute; inspect retrieval; switch to Database Health; inspect traces.

## Slide 4: Extensibility
Add SKILL.md, register reviewed Python handler, define permissions and tests. Instructions are documentation in v1, not dynamically loaded into model prompts.

## Slide 5: Governance
Local demo identity only. No arbitrary SQL or dynamic script execution. Production authentication, signed packages, automatic routing, schema validation, sandboxing and tenant-scoped telemetry remain future work.

## Slide 6: Automotive pilot
Evidence retrieval only; complete DTC section extraction and vehicle metadata filtering are not implemented.
