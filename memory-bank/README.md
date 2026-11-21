# PictuRAS-27 specifications workspace

This workspace reuses the specs.md AI-DLC infrastructure from
`Fase1/picturas-27-extension` (version 0.1.74).
Inception is active for the first Phase 2 quality-improvement intent. The agreed
pair is QC-06 security/end-to-end authorization + QC-05 upload resource efficiency,
as communicated by the user. Detailed elicitation, remaining metric approvals and
the formal baseline remain incomplete. Individual identity/WS validations retain
their recorded scope and do not imply whole-team approval of all details.
The user corrected delivery to **27 November 2026**, superseding 20 November for
current planning. Team hours remain unknown.
Security coverage option A is individually validated: internal APIs use mTLS;
other channels require verified server TLS and service-specific least-privilege
credentials where applicable. Exact configuration/proof and session transition
remain open; prior JWT/WS decisions are preserved.
Construction has not started. The newly supplied teaching materials are organized
and resolved in [Exercise 6 Block 2](../docs/exercises/06-architectural-patterns/resolution-block-2.md)
and [Exercise 7](../docs/exercises/07-architectural-tactics/resolution.md), preserving
original sources, shared EV/H/ALT and canonical QS/CAND. This documentation work
does not select remaining upload options or complete formal baseline/human review.
Current security review: [WS queue, revocation and persistent connections](../docs/architecture/fase2-fila-ws-e-revogacao.md)
records individually validated WS-C4 A/PKI-C2 B/PKI-C3 A and a testable maintenance
procedure. Channel proof, PKI timing/emergency reconciliation remain open; no
implementation or measured compliance is inferred.
[Operational criteria](../docs/architecture/fase2-criterios-operacionais-seguranca.md)
record individually validated PKI-C4 B/PKI-C5 A/OPS-C1 A: isolation 30/10 s,
measured replacement/pilot planned by 23 November 18:00 UTC, current/target channel
proof and implemented/tested administrative recovery required. Runtime proof is
pending; this machine/Luís was selected as evaluation host on November 18 (since November 20 the official host is one team member's Mac, with the formal BF taken on November 21; Luís's runs are exploratory), while the
experimental configuration and physical load remain proposals.
The [November 17 remaining-security review](../docs/architecture/fase2-sessoes-identidade-partilhas-ws.md)
records SESS-C1 A/JWT-C1 A/LINK-C1 A/WS-C5 B individual selections with assistant
technical confirmation. D8/replay/capacity distinctions and logical scenarios v1
are fixed; concrete anonymous proof, physical corpus and emission controls still
need implementation/tests. No migration or deployed capability inferred.
[Anonymous recovery specification](../docs/architecture/fase2-recuperacao-anonima.md)
and an empty case template now detail eligibility, issuance/import and suspended
frontend bootstrap. Independent association evidence is unknown by user statement;
real cases remain pending, no tokens issued or recovery tool implemented.
Session transition: the user confirms local-only Docker Compose installations
administered by each member, no shared installation or external users. The
[inventory worksheet](../docs/architecture/fase2-inventario-sessoes.md) includes
one-host Docker metadata and isolated-copy account/project counts (picturas 4/2;
experiment 13/10). Luís is the administrator, both sets are preserved, and original
hashes remained unchanged. Other computers/browser mappings, migration and the
development source and experimental runtime configuration remain pending. The
evaluation host is now selected as this machine/Luís; neither retained dataset
was selected for evaluation. The [before/after evaluation plan](../docs/fase2-plano-avaliacao.md)
and empty templates specify proposed workloads, budgets, clocks and all 60 metric
criteria. The [plan review](../docs/fase2-revisao-plano-avaliacao.md) records
individual EVAL-B1/C1/R1/M1 A selection with conditions, disk floor ≥60 GiB and
U25 promoted to G. Only enumerated M1 criteria are covered, not all 60 values.
Calibration, physical freeze and remaining upload choices stay open. The
[upload decisions](../docs/architecture/fase2-upload-decisoes-pendentes.md)
now record individual UP-C1/C2/C3 A selection with conditions; the
[lifecycle proposal](../docs/architecture/fase2-upload-ciclo-vida.md) leaves UP-C4–C9
unselected and no implementation/support proof inferred. [Host metadata](intents/001-phase-2-quality-improvements/evidence/evaluation-host-2026-11-18.json)
is recorded, with no runtime campaign or final baseline completed.

- `intents/`: draft requirements and future units/stories.
- `bolts/`: future execution plans and artifacts.
- `standards/`: future project standards and decisions.
- `operations/`: future deployment and monitoring context.
- `project.yaml`: project type and workspace creation timestamp.

Templates and workflow definitions are in `../.specsmd/aidlc/`.
Editor integrations are in `../.codex/`, `../.claude/`, `../.github/`
and `../.agent/`; their presence does not activate an agent.
Phase 1 requirements, stories, bolts, standards and progress were not imported.
Project standards and story indexes have not been authored yet.

Current intent: [001-phase-2-quality-improvements](intents/001-phase-2-quality-improvements/requirements.md).
Agreed pair: QC-06 security/end-to-end authorization + QC-05 performance efficiency/upload resource utilization;
[collective agreement communicated by the user](intents/001-phase-2-quality-improvements/quality-exploration.md#decision-record--pair-agreement).
Progress: [inception log](intents/001-phase-2-quality-improvements/inception-log.md).
Options and team review: [quality exploration](intents/001-phase-2-quality-improvements/quality-exploration.md).
Measurement protocols: [investigation plan](intents/001-phase-2-quality-improvements/investigation-plan.md).
Preliminary results: [exploration evidence](intents/001-phase-2-quality-improvements/evidence/README.md).
Application measurements and team discussion: [live findings](intents/001-phase-2-quality-improvements/live-findings.md).
Current decision preparation: [team review packet](intents/001-phase-2-quality-improvements/team-review.md).
Latest communicated choices and rationale: [November 16 ideas 1/2](../docs/fase2-ideias-1-e-2.md).
Current metric definitions and initial values: [measurement plan](../docs/fase2-metricas-e-baseline.md).

Consult [AGENTS.md](../AGENTS.md), the [project README](../README.md) and the
[documentation index](../docs/README.md) for project context.
