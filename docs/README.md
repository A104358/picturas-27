# PictuRAS documentation

Academic requirements, architectural references, course material and exercise
deliverables. For application setup and usage, see the [project README](../README.md).

Start with the [Exercise 6 resolution](exercises/06-architectural-patterns/resolution.md)
or its [artifact index](exercises/06-architectural-patterns/README.md).

For Phase 2 planning, see the [comparison of six quality directions and team
decision record](../memory-bank/intents/001-phase-2-quality-improvements/quality-exploration.md).
The [investigation plan](../memory-bank/intents/001-phase-2-quality-improvements/investigation-plan.md)
defines measurement protocols; the [evidence index](../memory-bank/intents/001-phase-2-quality-improvements/evidence/README.md)
records preliminary runs and reproduction commands.
The [live findings and decision brief](../memory-bank/intents/001-phase-2-quality-improvements/live-findings.md)
summarize the scoped application measurements and provisional discussion pairs.
The [team review packet](../memory-bank/intents/001-phase-2-quality-improvements/team-review.md)
consolidates the recommendation, alternative pairs and scope/measurement proposals
for agreement by all four members.

## Phase 2 decisions and measurement plan

The following Portuguese documents are the current working material for the
team's report and presentation. Choices explicitly marked open remain undecided.
The agreed pair is security/end-to-end authorization and performance efficiency/
upload resource utilization; the [agreement record](../memory-bank/intents/001-phase-2-quality-improvements/quality-exploration.md#decision-record--pair-agreement)
identifies the user's instruction as its source. Detailed decisions and metrics
retain their recorded approval states.

The current planning deadline is **27 November 2026**, corrected by the user.
Individually validated security coverage is option A: mTLS on internal APIs,
verified server TLS on other channels, and service-specific least-privilege
credentials where applicable. Exact configuration and experimental proof remain
pending; prior JWT/WS decisions are preserved.

| Document | Purpose |
|----------|---------|
| [Ideas 1 and 2, choices and rationale](fase2-ideias-1-e-2.md) | Communicated choices, unresolved questions, alternatives, risks and presentation answers. The final section is the canonical decision rationale. |
| [Metrics, acceptance criteria and baseline](fase2-metricas-e-baseline.md) | 60 metrics, existing values, proposed minimums/targets and individually validated WS criteria (≤5 s/≤2 s, initial 1 s revalidation), with pending experimental proof and pre-implementation gates. |
| [WebSocket authorization contract](architecture/fase2-contrato-websocket.md) | WS-C1/C2/C3/C4 A individually validated and WS-C5 B individually selected/technically confirmed: direct mTLS/delegation, total 1 s, 50 evaluations, 4 global/1 per project/64 KiB and alternating batches; 16 pending batches; 512 connections/4096 contexts; physical workload and implementation proof pending. Remaining contract proposed; no tests run. |
| [Session transition inventory](architecture/fase2-inventario-sessoes.md) | Luís identified; both volume sets preserved. Isolated-copy counts: picturas 4 accounts/2 projects, experiment 13/10; original hashes unchanged. Browser mappings, other computers, migration and source selection pending. |
| [WS queue and certificate withdrawal](architecture/fase2-fila-ws-e-revogacao.md) | WS-C4 A/PKI-C2 B/PKI-C3 A individually validated: 16 pending batches, new CA/all certificates for withdrawal and isolated maintenance/restart; testable runbook, costs, failure policy and pending channel/timing proof. |
| [Operational security criteria](architecture/fase2-criterios-operacionais-seguranca.md) | PKI-C4 B/PKI-C5 A/OPS-C1 A individually validated: isolation 30/10 s, measured replacement and pilot planned by 23 November 18:00 UTC; current/target channels, mock mTLS effort/rollback and implemented/tested administrative reconciliation required. Runtime results pending. |
| [Sessions, internal identity, sharing and WS contract](architecture/fase2-sessoes-identidade-partilhas-ws.md) | November 17 A/A/A/B individually selected and technically confirmed: assisted preservation/renewal, scoped 30 s identity with reuse residual, indefinite links and WS 512/4096 caps. Logical normal/saturation scenarios v1 fixed; anonymous proof, physical corpus and controls/tests pending. |
| [Anonymous recovery and issuance/import](architecture/fase2-recuperacao-anonima.md) | Detailed SESS-C1 A procedure and AR-01–AR-12: independent proof, administrative issuer, private bearer file and validation-before-import with suspended bootstrap. User says association evidence is unknown; real cases pending, no tool implemented or token issued. |
| [Empty anonymous-recovery case template](templates/anonymous-session-recovery-case.template.json) | Public credential-free template only. Complete a private copy outside Git; empty evidence/template status never authorizes issuance. |
| [Upgrade catalog](../memory-bank/intents/001-phase-2-quality-improvements/upgrade-ideas.md) | Broader 19-idea catalog and the original ARM pilot context; qualitative scores are not team approval. |
| [November 16 evidence audit](../memory-bank/intents/001-phase-2-quality-improvements/evidence/nfr-2026-11-16/README.md) | Original raw results, reproducibility limits and links to the derived audit. |

## Reference documents

| Topic | Document | Period / purpose |
|-------|----------|------------------|
| Requirements | [Base requirements](requirements/doc-ext-requisitos.pdf) | 2025/2026, Phase 1: images, presets, AI assistance and sharing. |
| Requirements | [Video extension requirements](requirements/doc-ext-requisitos-2627.pdf) | 2026/2027, Phase 1, PL1-G4: video MVP and quality requirements. |
| Architecture | [Base architectural solution](architecture/doc-sol-arquitetural.pdf) | 2025/2026, Phase 2: the architecture inherited by the video extension. |
| Guidelines | [Phase 2 guidelines, version 1](guidelines/fase-2-guidelines-1.pdf) | 2026/2027: improve two non-functional requirements through refactoring. |
| Lectures | [Lecture 11 — Architectural Styles](lectures/RAS-slidesEN-11-ARCH-Styles.pdf) | Course slides, October 2021: architectural styles and their constraints. |

## Exercises

| Exercise | Deliverable | Supporting artifacts |
|----------|-------------|----------------------|
| 6 — Architectural patterns, Block 1 | [Resolution — PL2-G4](exercises/06-architectural-patterns/resolution.md) | [Assignment, support material, diagrams and evidence](exercises/06-architectural-patterns/README.md) |

## Folder layout

```text
docs/
├── README.md
├── requirements/                    # Base and video requirements
├── architecture/                    # Architectural reference reports
├── guidelines/                      # Project phase instructions
├── lectures/                        # Course slides
└── exercises/
    └── 06-architectural-patterns/
        ├── README.md                # Exercise artifact index
        ├── resolution.md            # Completed Block 1 report
        ├── sources/                 # Original assignment and support HTML
        ├── diagrams/                # PlantUML sources and SVG renderings
        └── evidence/                # Reproduction script and execution record
```

Keep shared reference material in its topic folder and exercise-specific work
inside the corresponding exercise directory. Retain original reference filenames
and update relative links when moving artifacts.
