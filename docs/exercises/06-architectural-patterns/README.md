# Exercise 6 — Architectural patterns

[Documentation index](../../README.md) · **Team: PL2-G4** · **Blocks 1 and 2**

Read the [completed resolution](resolution.md) for the architectural diagnosis,
requirements mapping, evidence register and comparison of alternatives.

Continue with the [Block 2 resolution](resolution-block-2.md) for quality
trade-offs, six canonical scenarios and the two selected requirement candidates.
The [Exercise 7 resolution](../07-architectural-tactics/resolution.md) reuses
CAND-1/QS-01 and CAND-2/QS-02 for tactics and decisions. The evidence/hypothesis
registry stays in Block 1 §2.6; its November 18 update preserves the earlier rows
and matrix. Historical runs are distinct from today's documentation review.

## Assignment and supporting material

| Artifact | Purpose |
|----------|---------|
| [Assignment — Block 1, Portuguese](sources/RAS-exercicio_6_bloco1_SWdesign_PT.html) | Version 1.1: tasks 0–3 and expected results. |
| [Assignment — Block 2, Portuguese](sources/RAS-exercicio_6_bloco2_SWdesign_PT.html) | Version 1.1, November 4: tasks 4–5 and results 4–7. |
| [Original Block 2 template](sources/RAS-exercicio_6_bloco2_SWdesign_template_PT.md) | Version 1.1, preserved unfilled as supplied; the completed work is resolution-block-2.md. |
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
| [November 18 continuation sources](evidence/continuation-sources-2026-11-18.json) | Hashes of four newly organized originals and empty application diff from the Block 1 baseline. Static evidence only, no new workload. |
| [Continuation document checks](../07-architectural-tactics/evidence/verification-2026-11-18.md) | Previous registry/matrix preserved, scenarios transcribed exactly and new exercise content checked; academic review remains pending. |

With the application running, execute the script from the repository root:

```bash
docker exec -i picturas-projects-1 node < docs/exercises/06-architectural-patterns/evidence/preparacao.cjs
```

The script creates a dedicated free account and project and retains their results
for inspection. Its temporary local media are removed. This is a functional smoke
check, not a performance baseline.

The newly supplied Block 2 HTML links to the Block 1/support HTML in the same
sources directory. Original filenames and bytes are retained. The template
mentions a Markdown assignment filename; the actual supplied assignment is HTML
1.1, used explicitly in the resolution rather than inventing a missing source.
