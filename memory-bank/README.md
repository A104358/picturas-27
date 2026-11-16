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
Construction has not started.
Current security review: [WS queue, revocation and persistent connections](../docs/architecture/fase2-fila-ws-e-revogacao.md)
records individually validated WS-C4 A/PKI-C2 B/PKI-C3 A and a testable maintenance
procedure. Channel proof, PKI timing/emergency reconciliation remain open; no
implementation or measured compliance is inferred.
[Operational criteria](../docs/architecture/fase2-criterios-operacionais-seguranca.md)
record individually validated PKI-C4 B/PKI-C5 A/OPS-C1 A: isolation 30/10 s,
measured replacement/pilot planned by 23 November 18:00 UTC, current/target channel
proof and implemented/tested administrative recovery required. Runtime proof is
pending; installation/load not selected.
Session transition: the user confirms local-only Docker Compose installations
administered by each member, no shared installation or external users. The
[inventory worksheet](../docs/architecture/fase2-inventario-sessoes.md) includes
one-host Docker metadata and isolated-copy account/project counts (picturas 4/2;
experiment 13/10). Luís is the administrator, both sets are preserved, and original
hashes remained unchanged. Other computers/browser mappings, migration and the
development/evaluation installation choice remain pending.

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
