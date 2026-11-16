---
intent: 001-phase-2-quality-improvements
created: 2026-11-14T17:10:27Z
updated: 2026-11-16T19:49:16Z
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

**Documentation verification for the A/A/A update:** diff whitespace check passed;
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
pending-queue maximum/final workload, certificate revocation/trust withdrawal,
persistent-connection rotation and infrastructure pair coverage; WS-C3 fixes initial
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
