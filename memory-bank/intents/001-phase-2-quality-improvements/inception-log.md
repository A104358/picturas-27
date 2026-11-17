---
intent: 001-phase-2-quality-improvements
created: 2026-11-14T17:10:27Z
updated: 2026-11-17T22:53:41Z
completed: null
status: in-progress
---

# Inception Log: Phase 2 Quality Improvements

## Overview

**Intent:** Improve two PictuRAS quality requirements through measured refactoring,
preserving existing image and video functionality.
**Type:** Refactoring.
**Team:** PL2-G4.
**Created:** 2026-11-14T17:10:27Z.

The user selected Create Intent in the Inception menu and asked to continue.
The Phase 2 context and Exercise 6 diagnosis inform initialization. The user has
not yet selected the two quality requirements or approved architectural changes
at initialization. The later individual decision validations are recorded below.
The user subsequently requested exploration of all candidates before a final pair
is selected with validation and agreement from the whole team.
The user has now explicitly requested recording agreement on QC-06 security/
end-to-end authorization + QC-05 performance efficiency/upload resource utilization.
The canonical record attributes the collectively communicated pair agreement to
that instruction; no separate nominal declarations or reviewed commit are invented.

## Artifacts Created

| Artifact | Status | File |
|----------|--------|------|
| Requirements | Pair QC-06 + QC-05 agreed as communicated by the user; detailed requirements/remaining targets pending | [requirements.md](requirements.md) |
| Quality exploration | Six directions/15 pairs compared; canonical pair agreement recorded with source and scope | [quality-exploration.md](quality-exploration.md) |
| Investigation plan | Protocols and feasibility assessment prepared for all six directions, including both usability scenarios | [investigation-plan.md](investigation-plan.md) |
| Exploration evidence | Source inventory, acknowledgement-order demonstration, 74 passing host video tests, 24 valid processor calls and two corrupt-input probes | [evidence/README.md](evidence/README.md) |
| Live findings | 13-service experiment; upload RSS, three processing batches, access matrix, progress and one worker recovery; discussion shortlist unapproved | [live-findings.md](live-findings.md) |
| Team review | Six-direction synthesis, recommended discussion pair, scope/metric proposals and decision questions prepared; human review pending | [team-review.md](team-review.md) |
| Updated decision rationale | Communicated November 16 choices preserved, undecided points explicit, final rationale and presentation answers completed | [Ideas 1/2](../../../docs/fase2-ideias-1-e-2.md) |
| Measurement specification | 60 metrics, methods, baseline values/limits, proposed minimums/targets and explicit pre-code gates; formal baseline incomplete | [Metrics and baseline](../../../docs/fase2-metricas-e-baseline.md) |
| WS authorization contract | WS-C1 A/WS-C2 A/WS-C3 A individually validated; rest proposed. D4 mTLS replaces asymmetric service JWT; certificate/pair lifecycle detailed for review; 10 verification cases not run | [Contract proposal](../../../docs/architecture/fase2-contrato-websocket.md) |
| WS/PKI/ACL source audit | Three synthetic key paths not ignored, six tracked legacy private-key paths and seven reviewed broad-copy build contexts; readonly planning evidence, not image/runtime testing | [Security planning audit](evidence/security-planning-audit-2026-11-16.json) |
| Operational security review | WS-C4 A/PKI-C2 B/PKI-C3 A individually validated; 16 pending batches, new CA/all certificates for withdrawal, isolated maintenance/restart. CRL recommendation superseded; testable runbook/controls prepared, not executed | [Queue/revocation contract](../../../docs/architecture/fase2-fila-ws-e-revogacao.md) |
| Operational criteria | PKI-C4 B/PKI-C5 A/OPS-C1 A individually validated; isolation 30/10 s, measured replacement/pilot milestone, full current/target channel matrix, actual mock mTLS and implemented/tested administrative reconciliation required. No runtime proof | [Operational criteria](../../../docs/architecture/fase2-criterios-operacionais-seguranca.md) |
| Remaining security selection — November 17 | SESS-C1 A/JWT-C1 A/LINK-C1 A/WS-C5 B individually communicated and technically confirmed; D8 revised, replay/capacity metrics separated and logical scenarios v1 fixed. Proof/physical corpus/implementation pending | [Sessions/identity/sharing/WS](../../../docs/architecture/fase2-sessoes-identidade-partilhas-ws.md) |
| Anonymous recovery procedure and case template | SESS-C1 A working proof/issuance/import specification and AR-01–AR-12 detailed; empty public case template. User says independent association evidence is unknown, so no case eligible/approved/issued by this review | [Procedure](../../../docs/architecture/fase2-recuperacao-anonima.md), [empty template](../../../docs/templates/anonymous-session-recovery-case.template.json) |
| Session transition inventory | Luís identified, both sets preserved. Isolated-copy counts: picturas 4 accounts/2 projects; experiment 13/10; originals hash-verified unchanged. Browser mappings/other computers and migration/source selection pending | [Inventory worksheet](../../../docs/architecture/fase2-inventario-sessoes.md) |
| New evidence audit | 14 successful uploads summarized, 23 security/control case records reviewed, fresh static source/certificate inventory; raw ARM results unchanged | [Raw evidence index](evidence/nfr-2026-11-16/README.md) |
| System Context | Not created | No artifact yet |
| Units | Not created | No artifact yet |
| Stories | Not created | No artifact yet |
| Bolt Plan | Not created | No artifact yet |

## Summary

| Metric | Count |
|--------|-------|
| Detailed functional requirements generated | 0 |
| Candidate quality directions cataloged | 6 |
| Candidate pairs compared qualitatively | 15 |
| Quality requirements selected | 2 |
| Final requirement baselines established | 0 |
| New host video tests passed | 74 |
| Valid processor pilot calls, across host and container | 24 |
| Runtime application source files matched | 182 |
| Existing Node tests passed in live slice | 8 |
| Committed videos in authoritative normal run | 9 |
| Worker interruption/recovery scenarios observed | 1 |
| November 16 metric dimensions specified | 60 |
| First-group decisions explicitly validated by the user | 3 |
| Room access/removal decisions individually selected and technically confirmed | 2 |
| Periodic revalidation, cutoff/failure and active JWT expiry proposals individually validated | 3 |
| D4 change and WS-C1/WS-C2 choices individually validated | 3 |
| Units | 0 |
| Stories | 0 |
| Bolts planned | 0 |

## Units Breakdown

No units have been decomposed. Boundaries depend on the selected requirements.

## Decision Log

| Timestamp | Decision | Basis | Approval state |
|-----------|----------|-------|----------------|
| 2026-11-14T17:10:27Z | Initialize the first intent under `001-phase-2-quality-improvements`. | User selected Create Intent and requested continuation in the established Phase 2 context. | Initialization authorized; detailed scope and quality priorities remain open. |
| 2026-11-14T17:16:06Z | Explore all six directions and compare pairs before choosing two requirements; require explicit agreement from all four team members for selection. | User requested broad exploration followed by whole-team validation and agreement. | Exploration requested by the user; no final pair or individual team approvals recorded. |
| 2026-11-14T17:35:54Z | Continue all-direction exploration, record preliminary experiments and prepare bounded measurement protocols. | User selected continuation; confirmed delivery on 20 November. Application sources match the prior diagnosis. | Exploratory work authorized; no final pair, targets or team approvals inferred. |
| 2026-11-14T18:06:50Z | Record scoped application measurements and one controlled worker interruption; prepare an evidence-based discussion shortlist. | User selected live exploration after commit 24484b7. Source/data checks and acquisition corrections are documented. | Experiments complete within stated bounds; final pair and all four individual approvals remain pending. |
| 2026-11-14T18:19:23Z | Commit live evidence as 793df2e and prepare the team review packet. | User explicitly requested a commit followed by Option 1, results review and decision preparation. | Evidence commit and review preparation authorized; pair, thresholds and all four individual approvals remain pending. |
| 2026-11-16T14:12:19Z | Audit newly supplied idea documents/results, complete decision rationale and define measurement gates before code. | User explicitly warned that some decisions remain open and requested presentation/report explanations plus metrics, minimums, targets and initial values. | Documentation/evidence review authorized. No final approval inferred; no application refactoring or runtime fault/load rerun performed. |
| 2026-11-16T14:34:42Z | Record D3/JWT, D7 and D6.1 as explicitly validated by the user, including the session-transition prerequisite before HS256 renewal. | User selected all three A options and explicitly limited validation to their own position. | Individual validation recorded; no agreement of all four, no approval of D6.2 or remaining open decisions, and no construction readiness inferred. |
| 2026-11-16T14:43:28Z | Record D6.2 B + D6.3 A: per-entry projects consultation and active room-access withdrawal, preserving alternative authorization. | User selected the combination subject to technical confirmation; assistant agreed it is proportionate, with medium confidence and no measured complexity advantage claimed. | Individual choice recorded. Membership revalidation, cutoff bound, propagation/race handling and active-session expiry remain open; no whole-team or construction approval inferred. |
| 2026-11-16T15:05:43Z | Record explicit A/A/A validation with conditions and reconfirm D6.2 B; synchronize decision rationale, S06/S12/S21/F06 and WS measurement protocol. | User specified initial 1 s project-grouped queries with individual member/context decisions; acceptance ≤5 s/target ≤2 s, local deadline from query start bounded by JWT/permission; no renewal on failure/obsolete responses; effective denial removes immediately, no new joins during outage; JWT expiry terminates, frontend explicitly reconnects with valid JWT/fresh room authorization; preserve anonymous identity/projects. | Individual validation only. Experimental compliance/load and whole-team agreement pending. Events deferred; no asserted equal failure security or rarity of active expiry. Contract/timeout, ordering/races, batch limits, session transition/renewal and remaining decisions stay open. |
| 2026-11-16T15:12:33Z | Record the agreed pair: QC-06 security/end-to-end authorization + QC-05 performance efficiency/upload resource utilization; selected requirement count becomes 2. | User explicitly asked “Podes registar o acordo do par”, after the pair and the outstanding collective agreement had been identified. | Pair agreement recorded as communicated by the user for PL2-G4. No separate individual signatures/statements, meeting date or reviewed commit supplied. Detail validations remain individual; remaining decisions/metrics, formal baseline and full requirements/construction review remain pending. |
| 2026-11-16T15:23:20Z | Elaborate a reviewable WS contract and ask WS-C1/WS-C2 clarifying questions. | User selected Option 1 to specify authenticated calls, access contexts, batch limits and ordering/races. Source review confirms joins currently carry only project ID, no room authorization state and no client mTLS in projects. | Draft only: direct mTLS/user delegation vs gateway mediation and proposed 1 s total timeout/50 evaluations remain unselected. Payload/order design and 10 test cases are proposals, not human validation or executed tests. Agreed pair/previous conditions preserved; no application changes. |
| 2026-11-16T15:30:57Z | D4 selects mTLS for internal service authentication; mark HTTPS + asymmetric service JWT as superseded. Preserve D3 HS256 user JWT and gateway-issued RS256 identity. | User explicitly changes their earlier service-authentication choice and requests recording the substitution. The original choice/date was not previously documented as a dated validation here; its prior status is supplied by this message, not fabricated retrospectively. | Individual validation. Existing mTLS proposal is now explicitly selected; private-key protection, issuance/renewal and service-pair matrix elaborated for review. Infrastructure coverage and lifecycle parameters pending; no certificates generated, tests executed or app changes authorized. |
| 2026-11-16T15:30:57Z | Record WS-C1 A/WS-C2 A: direct mTLS with specific WS authentication/operation permissions and explicit user delegation; total initial timeout 1 s and 50 member/context evaluations per request. | User validates identity/expiry from connection JWT, projects permission authority, bounded concurrency/fair scheduling for multiple batches and no authorization extension on failures/retries; cutoff ≤5 s/target ≤2 s retained. | Individual validation only, no agreement attributed to other members. Configurable parameters subject to measurement, not demonstrated capacity. Rest of contract remains proposed; no tests run/application edits. |
| 2026-11-16T15:57:21Z | Record delivery scope option A: mTLS on internal APIs, verified server TLS elsewhere and service-specific least-privilege credentials where applicable. | User explicitly chose A for 27 November to focus on demonstrated authorization failures while preserving time for both quality requirements and their evaluation. | Individual validation only. Prior JWT/WS rules preserved; per-channel configuration, PKI parameters, session transition, remaining requirements and baseline remain incomplete. No application changes or runtime tests. |
| 2026-11-16T16:31:00Z | Record anonymous deployment/browser inventory as unknown and required before choosing session migration. | User asks whether all anonymous browsers are team-controlled or external users exist, with an inventory prerequisite if unknown. The repository supplies no deployment/client-control inventory; neither population can be inferred. | No external users or all-controlled-client assumption asserted. Inventory remains to perform with deployment/operator information; identity/project preservation and prior JWT/WS conditions unchanged. No migration selected, secret rotated, runtime inventory or application/data changes performed. |
| 2026-11-16T18:25:38Z | Record user-supplied local-only deployment context and prepare the session inventory worksheet. | User selected inventory preparation, then confirmed use only on team computers through Docker Compose, each member administering their own installation, no shared installation/external users and no formal environment list. Source reads confirm localStorage/session effects and lack of central session inventory. | Deployment-scope uncertainty resolved by user statement, not technical measurement. Fields, administrator roster, historical candidates and collection/exit criteria prepared; actual counts, browser associations and migration still pending. No Docker/DB/browser inventory, application changes, token renewal or key rotation performed. Prior pair/security/WS decisions preserved. |
| 2026-11-16T19:03:51Z | Collect read-only local Docker metadata and record stopped/retained PictuRAS data sets. | User requested continuation. Queries found 13 exited experiment containers/6 volumes and 8 `picturas` volumes/no matching containers; historical temporary Compose file absent. | Partial one-host metadata inventory only. No DB/volume contents/browser inspected, services started/stopped, credentials rotated or application/data changed. Identity/project counts remain NM; other computers, administrator mapping and retention/migration decisions pending. |
| 2026-11-16T19:18:54Z | Record Luís as this machine's administrator and preservation of both volume sets; collect account/project counts through isolated temporary database copies. | User explicitly requested preservation/counting without original-data changes and deferred development/evaluation installation selection. Counts: picturas 4 accounts (2 anonymous/2 free), 2 projects; experiment 13 free accounts, 10 projects. No anonymously owned projects in either set. | Original volumes mounted read-only, four file manifests unchanged before/after, temporary copies/databases removed and no temporary DB containers found afterwards. First copy attempt failed and was preserved as diagnostic, also with unchanged originals/cleanup. Counts are not migration tests, active sessions or storage-integrity verification; browser mapping/presets/other computers remain pending. No original app/database started, credentials rotated or source installation selected. |
| 2026-11-16T19:49:16Z | Record individual WS-C3 A, PKI-C1 A and ACL-C1 A with implementation/evaluation conditions. | User agrees to initial 4 global/1 per project/alternating batches/64 KiB; local CA 365 days, service certs 30 days, renew with 7 days remaining; whole-project deletion owner-only, editor retains media removal. | Keep parameters distinct from measured capacity: 4 simultaneous does not prove 4/s or a 20-project limit. Queue maximum/final corpus, certificate revocation and persistent connections remain open. Include administrator-run issuance/renewal script and checks in delivery, retaining 30 days/no background daemon. ACL is an explicit policy change, not an unequivocal inherited RF restriction. Individual validation only; no app/ignore/build changes or runtime tests. |
| 2026-11-16T19:49:16Z | Audit source protections and ACL/UI paths without runtime changes. | Three synthetic key paths not ignored, six tracked legacy key paths, seven reviewed contexts copying broadly without demonstrated private-key exclusion. DELETE currently accepts edit; only found frontend call is current-user project list. | No secret contents gathered, images built, certificates generated or rendered UI verified. Plan Git/context/image-layer marker checks, startup/offline renewal tests and disposable-project owner/editor/reader tests; preserve authorized account cleanup and both retained datasets. |
| 2026-11-16T20:12:29Z | Prepare concrete alternatives for the pending WS queue, certificate revocation and persistent-connection review. | User selected option 1 to close security details. Proposed WS-C4 A: 16 pending batches/process; PKI-C2 A: signed local CRL with proposed 30/7-day maintenance; PKI-C3 A: isolated maintenance/restart and verification before reopening. | Choices explicitly requested from the user and still pending; no validation attributed to anyone. Preserve prior JWT/WS/PKI/ACL choices. Official Node/OpenSSL documentation supports candidate instruments, not runtime capacity or universal per-channel support. No application changes, certificates, PKI implementation, Docker operations or new runtime tests. |
| 2026-11-16T20:14:36Z | Record individual WS-C4 A, PKI-C2 B and PKI-C3 A; supersede CRL recommendation and specify maintenance controls. | User explicitly selects 16 pending batches/latest pending plan without deadline reset; replace CA/all certificates for trust withdrawal; isolation/restart and complete WS → projects/projects → storage controls before reopen. | Whole-installation downtime/coordination acknowledged, not measured short. Normal expiry renewal may retain CA and does not itself revoke old leaf; immediate withdrawal uses B. Compromise isolates without waiting for jobs; partial update stays isolated. Require old-CA rejection/new handshake and old-connection/session invalidation. PKI deadline, channel proof and emergency reconciliation pending; no app/PKI implementation, runtime tests or collective detail approval. |
| 2026-11-16T20:30:06Z | Prepare PKI-C4/PKI-C5/OPS-C1 alternatives for operational criteria. | User selected option 1 after A/B/A. Recommend proposed isolation 30 s/target 10 s and prepared idle replacement 15 min/target 5 min; full channel coverage with manual browser evidence; administrative reconciliation without automatic replay. | Await individual choice; no metrics approved by association. Source review finds early image ack, non-awaited result callbacks, refund-before-version update and counters/day ambiguities. HTTP generative API classification flagged for explicit decision. Primary supplier docs do not prove deployed coverage; Mongo/Rabbit version links redirect. No application, Docker, credentials, volumes or runtime tests changed; no new whole-team approvals. |
| 2026-11-16T20:33:46Z | Record PKI-C4 B, PKI-C5 A and OPS-C1 A with user conditions. | Explicit user choices: isolation ≤30 s/target ≤10 s including persistent connections/consumers; replacement measured, not imposed 15/5 min. Full current/target channel matrix and browser with known trust/no bypass. Mock API mTLS effort/rollback; administrative tool/procedure implemented/tested by delivery or explicit limitation. | Individual validation only. Pilot planning milestone set to 23 November 18:00 Europe/Lisbon/UTC; environment/load/results still pending. Isolate incomplete failures without clock reset; failed replacement remains isolated. Preserve evidence, exclude indeterminate outputs and prevent repeat quota corrections. No auto-recovery claim; early ack remains defect. No application, Docker, credentials, volumes or new runtime tests changed; preliminary effort estimates not measured/team-approved. |
| 2026-11-17T11:33:22Z | Prepare remaining security alternatives after user selects option 1. | SESS-C1 A recommends assisted transition/7-day user JWT, JWT-C1 A scoped 30-second gateway identity without generic single-use guarantee, LINK-C1 A preserves old/new links until explicit revocation per RNF52, WS-C5 initial state/rate/bytes and D10 host/container proofs. | Choices requested, still pending; no new individual validation inferred. Replay/logout/session-revocation residuals explicit. Code also emits preview/progress into personal rooms and producer messages lack project context: include protected emission checks/payload migration in tests, not a claimed live leak. No app, secrets, browsers, Docker or original data changed; only source/PDF/primary-doc review and Markdown. |
| 2026-11-17T11:53:34Z | Record individual SESS-C1 A/JWT-C1 A/LINK-C1 A/WS-C5 B recommendations and assistant technical confirmation. | User asks to close these choices with conditions: assisted same-ID preservation/future anonymous reissue and actual proof/tool tests, 30 s admission-only contextual identity with accepted reuse residual, links until revocation and lower WS caps 512/4096. | Technical confirmation, not a literal validation statement invented for four members. RNF52 verified PDF p.27; D8 expiry preference deferred. S07 no longer claims zero contextual replay; excess caps are refusal tests, not fully admitted load. Logical scenarios v1 fixed (normal 50, fairness 510, many-project 200, limits/rates/bytes/personal events); physical corpus/proof/controls still pending. No app/secrets/browsers/Docker/data changes or new runtime tests. |
| 2026-11-17T22:48:42Z | Concretize anonymous recovery, administrative issuance and browser import under SESS-C1 A. | User selected option 2 and answered they do not yet know whether an independent reliable identity/browser association record exists. Prepare proof criteria, private case states, restricted issuer, private normal JWT delivery and server-validation-before-import with suspended frontend bootstrap. | Evidence existence unknown, not absent/present. No case proof/approval or token created. Direct bearer file is not single-use/refresh; expiry starts at issuance, deletion does not revoke. Existing root provider can register/validate before import; tabs/callbacks require explicit handling. Empty JSON template outside real data, 12 planned scenarios and preliminary effort/rollback specified; no app/browser/DB/Docker/secret/volume change or runtime tests. |

## Scope Changes

**Delivery coverage selected, 2026-11-16T15:57:21Z:** The user selected option A
for delivery on 27 November: mTLS on internal APIs including WS → projects, with
specific service/operation authorization; verified server TLS on other channels;
service-specific credentials and least privilege for MongoDB/RabbitMQ/S3 where
applicable. This resolves the coverage choice posed below without reopening D3,
D4 or the validated WS behavior. Universal mTLS is not required for this delivery.
Exact channel/version configuration, PKI parameters, session transition, remaining
metrics and formal baseline are still open. Documents were synchronized; no app,
Compose, credentials/certificates or measurements were changed. No additional
whole-team approval or construction readiness is inferred.

Session-source inspection found seven-day HS256 JWTs, no independent anonymous
recovery credential in the inspected schema/session paths, and frontend error
handling that replaces the current identity with a new anonymous one. The next
clarification concerns control of existing anonymous browsers, to design their
preservation before HS256 rotation. No migration or new renewal/lifetime policy
is inferred from choosing transport coverage.

**Deadline and resumed elicitation, 2026-11-16T15:51:14Z:** The user explicitly
corrected delivery to **27 November 2026** and selected option 1 after activating
the Inception Agent: continue requirements and close the detailed scope. Current
planning references are synchronized; original guidelines, measurements and dated
decisions are preserved. A clarification asks whether mandatory mTLS covers the
internal application APIs with separate TLS/credentials/permissions on other
channels, or all internal protocols. This is a pending scope choice, not an
accepted exclusion or a reversal of D4. No application, certificates, baseline or
construction artifacts were changed/generated. The full requirements set remains
unapproved and available team hours remain unknown.

Selection now follows a broad exploration stage instead of requiring an immediate
pair choice. The agreed pair is now QC-06 + QC-05, recorded as communicated by the
user. Final implementation scope remains exactly two distinct quality requirements.
Detailed scope, formal evaluation and remaining decisions still need completion.
Initial source checks and bounded processor/helper
experiments are now recorded; they do not complete whole-system evaluation.
The live stage adds bounded candidate measurements and a successful early worker
restart scenario. No real Whisper, scaling, rendered-browser usability or measured
maintenance task is claimed. The dedicated stack is stopped with volumes retained.

## Ready for Construction

- [x] Intent initialized with known goal and scope.
- [x] Initial qualitative comparison and exploration protocols prepared.
- [x] Source revision rechecked and preliminary experiments recorded.
- [x] Scoped live measurements, acquisition corrections and discussion brief recorded.
- [x] Evidence committed and concrete team review packet prepared.
- [x] New idea documents audited; decision rationale and 60-metric specification prepared.
- [x] Individual validation recorded for D3/JWT, D7 and D6.1, with conditions intact.
- [x] D6.2 B + D6.3 A recorded; room-ticket proposal deferred with rationale.
- [x] A/A/A permanence conditions recorded, including individually validated 5 s/2 s criteria, initial 1 s grouped queries, bounded failure policy and explicit reconnection after JWT expiry.
- [x] D4 supersession and WS-C1 A/WS-C2 A conditions recorded; D3 functions retained, PKI/pair operational detail made explicit as a proposal.
- [x] WS-C3/PKI-C1/ACL-C1 individual choices and conditions recorded; source protection gaps audited, capacity correction explicit.
- [x] WS-C4 A/PKI-C2 B/PKI-C3 A individually validated; maintenance runbook/controls prepared and CRL recommendation superseded.
- [x] PKI-C4 B/PKI-C5 A/OPS-C1 A individually validated with pilot milestone, current/target channel matrix and actual implementation/test obligations.
- [x] SESS-C1 A/JWT-C1 A/LINK-C1 A/WS-C5 B individually communicated/technically confirmed; D8/replay/capacity distinctions and logical scenarios v1 recorded.
- [x] Anonymous proof/issuance/import working procedure and empty case template prepared; user evidence status recorded as unknown, not fabricated proof.
- [ ] Open architecture/compatibility decisions closed and applicable metric gates approved.
- [ ] Formal initial baseline completed for every mandatory metric or justified NA mechanism.
- [ ] Exploratory evidence and feasibility assessed with the team.
- [x] Pair agreement recorded for PL2-G4 as communicated by the user; QC-06 + QC-05 selected, without fabricated separate nominal approvals.
- [ ] Clarifying questions answered.
- [ ] Two quality requirements selected and quantitatively specified.
- [ ] Requirements reviewed by the user.
- [ ] System context defined.
- [ ] Units decomposed.
- [ ] Stories created for all units.
- [ ] Bolts planned.
- [ ] Artifacts reviewed and construction readiness confirmed.

## Next Steps

**Anonymous-recovery documentation verification, 2026-11-17T22:53:41Z:**
12 documentation/template artifacts; empty JSON parses, remains template-only,
pending evidence/approval and not issued, with no credential fields or real IDs.
60 unique metric IDs, 10 existing WS cases and 12 distinct planned recovery cases
retained; canonical/catalog synchronization, 188 local file links, Markdown table
continuity and diff whitespace passed. These are static documentation checks,
not recovery, JWT, browser or runtime tests. No application/data changes, token
issuance, case approval or commit performed.

**Current anonymous-recovery detail:** the user states independent association
evidence is **unknown**. The [procedure](../../../docs/architecture/fase2-recuperacao-anonima.md)
and [empty case template](../../../docs/templates/anonymous-session-recovery-case.template.json)
now specify proof/eligibility, issuance/import, frontend bootstrap suspension,
error/ambiguity handling and AR-01–AR-12. Real cases remain pending evidence; no
issuance, browser inspection or migration is authorized/performed by this review.
Next obtain independent association evidence locally, then implement/test the
procedure after the required full requirements/baseline review; do not ask again
whether evidence is already known or infer it from the template/old JWT.

**Current November 17 selection:** SESS-C1 A/JWT-C1 A/LINK-C1 A/WS-C5 B are
individual recommendations technically confirmed by the assistant; do not ask again
which options were selected. The [contract/logical scenarios v1](../../../docs/architecture/fase2-sessoes-identidade-partilhas-ws.md)
updates D8, explicit replay residuals and normal-vs-refusal capacity assertions.
Next concretize independent anonymous proof/browser mappings and tested issuance/
import, complete physical scenario/manifest freeze and project-event emission
controls. Retain admitted-cap review if corpus needs >512/4096, all earlier gates
and the separate unfinished upload requirements. No migration or code authorization
is inferred; full requirements/baseline review remains incomplete.

**A/A/A/B selection verification, 2026-11-17T12:06:37Z:** 60 metric IDs,
10 WS cases and 13 logical scenario groups v1 retained; canonical/catalog slices,
D8 persistence and selected 512/4096 caps consistent. Replay residual separate
from rejected-profile assertions; fairness arithmetic and excess-cap refusal
checked. All 174 local file links, table continuity and diff whitespace passed.
Only Markdown changed; no runtime tests, migration or application/data changes.

**November 17 proposal verification, 2026-11-17T11:37:33Z:** 60 metric IDs,
10 WS cases and catalog synchronization retained; 174 local file links, Markdown
table continuity and diff whitespace passed. New choices remain proposals; only
Markdown changed. No application/data changes, runtime tests, browser inspection
or commit were performed.

**Latest criteria result:** PKI-C4 B/PKI-C5 A/OPS-C1 A are individually validated.
The [criteria contract](../../../docs/architecture/fase2-criterios-operacionais-seguranca.md)
records isolation 30/10 s and incomplete-isolation behavior, the pilot milestone
**23 November 18:00 UTC**, mandatory environment/load/duration/results, full current/
target channel coverage, browser checks, mock mTLS effort/rollback and implemented/
tested administrative reconciliation by delivery or an explicit capability limitation.
Do not ask again which options were selected. Next select pilot installation/load,
complete concrete isolation/termination/tooling and verification in the later
implementation/evaluation phase, and close remaining WS/session/upload requirements
and baseline before construction. No execution or installation choice inferred.

**B/A/A documentation verification, 2026-11-16T20:42:28Z:** 60 metric IDs and
10 WS cases retained; catalog synchronized; 43 channel-matrix rows (including an
explicit pending topology row), 19 broker principals and 6 database/backup pairs
checked. Pilot Lisbon/UTC milestone verified; 156 local file links and table
continuity passed. Only Markdown changed; no runtime tests or implementation.

**Earlier operational result:** WS-C4 A/PKI-C2 B/PKI-C3 A are individually validated.
The [operational contract](../../../docs/architecture/fase2-fila-ws-e-revogacao.md)
specifies queue replacement/deadlines and a testable maintenance/CA-withdrawal
procedure. Next close the PKI operational deadline, per-channel/version checks,
concrete emergency reconciliation, WS state/abuse limits and final workload; do not
ask again which A/B option was selected. Prior session preservation/retention and
formal baseline gates remain. No runtime verification or application work inferred.

**Later A/B/A review verification:** 60 metric IDs and 10 WS scenarios retained,
catalog synchronized, 137 local file links resolved and Markdown table continuity
checked. Only Markdown documentation changed; no runtime checks or commit created.

**Earlier A/A/A verification record:** diff whitespace check passed;
60 unique metric IDs retained (24 security/26 upload/10 guards), 10 WS scenarios,
ideas 1/2 catalog synchronized and 171 local file links resolved. Static audit
JSON verified. Changes are confined to documentation/planning evidence; these
checks do not execute the future WS/PKI/ACL scenarios or establish a formal baseline.

For session transition, use the inventory worksheet: local-only/no-external-user
scope is supplied; Luís is responsible for this machine and both volume sets must
be preserved. One-host metadata and isolated-copy account/project counts are now
recorded, with unchanged original hashes. Complete browser profiles/associations,
any additional retained data and the other administrators' installation inventories.
Development/evaluation-source selection remains explicitly deferred by the user.
Keep historical experiment environments distinct. Review the resulting gaps before
choosing transition/renewal, preserving identity/projects and not relying solely on
the old JWT. Independent upload/certificate/measurement elicitation can continue.

Continue the exploration procedure in [quality-exploration.md](quality-exploration.md):
first review the November 16 [decision rationale](../../../docs/fase2-ideias-1-e-2.md#justificação-das-decisões)
and [measurement gates](../../../docs/fase2-metricas-e-baseline.md). Preserve open
decisions, approve applicable metrics and complete the formal baseline before code.
The first three A options, D6.2 B/D6.3 A and the subsequent A/A/A permanence
conditions are individually validated. Revalidation is initially every 1 s, grouped
by project with individual context decisions; cutoff acceptance ≤5 s/target ≤2 s,
bounded failure policy and termination at JWT expiry are selected, not measured.
WS-C1 A/WS-C2 A now validate direct mTLS/explicit delegation and initial total
timeout 1 s/50 evaluations, with limited concurrency/fair scheduling; D4 replaces
asymmetric service JWT. Next review remaining payload/context/order/race design,
final workload/state-abuse limits, PKI timing/emergency reconciliation and
infrastructure pair coverage; WS-C4 A fixes 16 pending batches, PKI-C2 B chooses
new CA/all certificates for withdrawal and PKI-C3 A fixes isolated maintenance
and restart with post-maintenance controls; WS-C3 fixes initial
4 global/1 per project/64 KiB, PKI-C1 fixes 365/30/7 days with administrator-run
script in delivery, and ACL-C1 owner-only whole-project deletion. All are individually
selected, not implemented or measured; close session transition/renewal before HS256 renewal
and the remaining upload/measurement details. Agree the scenarios and demonstrate
the criteria experimentally. The QC-06 + QC-05 pair agreement is now recorded as
communicated by the user. Do not reopen selection by default or extend that
agreement to all detailed decisions, remaining numerical targets or readiness.
The November 14 team packet is historical preparation for the narrower scope;
the new decision document takes precedence for the communicated preferences.

Use the [historical team packet](team-review.md), [live findings](live-findings.md)
and current decision rationale to complete the agreed pair's detailed scope and
remaining resource/target decisions. Collect evidence only where needed for the
final protocol or unresolved choices. Bind both requirements to comparable
initial/final measurements. Detailed requirements review still precedes
architecture decomposition or construction.

## Dependencies

Requirement selection precedes decomposition and architectural commitment.
Initial measurements must precede any refactoring of the measured paths.
