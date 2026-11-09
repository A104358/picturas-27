# Exercise 6 — Architectural patterns

[Documentation index](../../README.md) · **Team: PL2-G4** · **Block 1**

Read the [completed resolution](resolution.md) for the architectural diagnosis,
requirements mapping, evidence register and comparison of alternatives.

## Assignment and supporting material

| Artifact | Purpose |
|----------|---------|
| [Assignment — Block 1, Portuguese](sources/RAS-exercicio_6_bloco1_SWdesign_PT.html) | Version 1.1: tasks 0–3 and expected results. |
| [Architectural patterns support document](sources/RAS_support_doc_architectural_patterns_PT.html) | Pattern catalog used in the analysis. |
| [Shared reference documents](../../README.md#reference-documents) | Requirements PDFs, architectural report, Phase 2 guidelines and lecture slides. |

## Diagrams

| Diagram | View | Editable source |
|---------|------|-----------------|
| Global architecture and video path | [SVG](diagrams/arquitetura_global_plantuml.svg) | [PlantUML](diagrams/arquitetura_global.puml) |
| Complete mixed-media processing request | [SVG](diagrams/sequencia_processamento.svg) | [PlantUML](diagrams/sequencia_processamento.puml) |

## Evidence and reproduction

| Artifact | Purpose |
|----------|---------|
| [Execution record — 2026-11-09](evidence/validacao-2026-11-09.txt) | Environment, source hashes, existing test results, API checks and limitations. Historical command paths are preserved and the current path is stated at the top. |
| [Preparation script](evidence/preparacao.cjs) | Reproduces the mixed image/video project, processing, frame extraction and ZIP checks through nginx and the API Gateway. |

With the application running, execute the script from the repository root:

```bash
docker exec -i picturas-projects-1 node < docs/exercises/06-architectural-patterns/evidence/preparacao.cjs
```

The script creates a dedicated free account and project and retains their results
for inspection. Its temporary local media are removed. This is a functional smoke
check, not a performance baseline.
