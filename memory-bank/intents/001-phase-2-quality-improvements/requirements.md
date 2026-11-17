---
intent: 001-phase-2-quality-improvements
phase: inception
status: draft
created: 2026-11-14T17:10:27Z
updated: 2026-11-17T22:48:42Z
---

# Requirements: Phase 2 Quality Improvements

## Intent Overview

Improve two distinct non-functional requirements of PictuRAS through refactoring,
preserving existing image and video behavior. Use the architectural diagnosis from
Exercise 6 as the starting evidence and evaluate each improvement separately with
reproducible measurements before and after implementation.

**Type:** Refactoring of an existing full-stack application.
**Team:** PL2-G4.
**Planning state:** Detailed requirements are being elicited; the complete set has
not been approved. The pair is agreed: **QC-06 security, end-to-end authorization,
and QC-05 performance efficiency, upload resource utilization**. The user requested
recording the pair agreement in this conversation; the canonical collective record
is in [quality exploration](quality-exploration.md#decision-record--pair-agreement).
Partial individual architecture validations are recorded below.
The user requested exploration of all six candidate directions before
selection, followed by explicit agreement from all four team members. The
[quality exploration](quality-exploration.md) records the comparison, investigation
protocols and agreement provenance. This draft is not a completed requirements
specification.

The [investigation plan](investigation-plan.md) and [evidence index](evidence/README.md)
now include renewed source checks, an acknowledgement-order demonstration,
74 passing host video tests and processor-only pilots. Final requirement baselines
and overall numerical acceptance remain pending; later individual validations of
specific WS criteria are recorded below.

The subsequent [live findings](live-findings.md) add candidate measurements from
an isolated 13-service deployment: upload RSS, three video batches, Socket.IO
progress, internal access tests and one worker-recovery scenario. These results
originally supported a provisional shortlist. The pair has since been agreed as
recorded below; this does not approve all quantitative targets or implementation details.

The [team review packet](team-review.md) now consolidates all six directions,
the recommended discussion pair QC-05 + QC-06, proposed boundaries and numerical
options. Its proposed percentages and zero-bypass criterion are unapproved
engineering proposals. Pair agreement selects two requirements and does not
approve these numerical options or replace the later full requirements review.

## Pair Agreement

**Recorded:** 2026-11-16T15:12:33Z. **Team:** PL2-G4.
**Source:** The user explicitly requested: “Podes registar o acordo do par”, after
the conversation identified the pair and the outstanding whole-team agreement.
Record this as the pair agreement communicated by the user for the team. No
individual signatures, meeting date, separately reviewed commit or additional
statements by the other members have been supplied or fabricated.

1. **QC-06 — Security: end-to-end authorization.** Verify identity and effective
   permissions at the gateway, services, storage and WebSocket boundaries in the
   selected scope; confidentiality, integrity and authenticity are the relevant
   ISO/IEC 25010:2011 subcharacteristics.
2. **QC-05 — Performance efficiency: upload resource utilization.** Bound memory
   consumption along the upload path and prevent large valid uploads from causing
   resource exhaustion/service failure, preserving supported behavior. Time
   behavior and functional correctness are guardrails.

The rationale is the observed authorization weaknesses and high upload memory/OOM,
with separate measurements and user impact. Detailed evidence and rejected
alternatives remain linked in the canonical record. Agreement is on this pair and
its stated improvement areas; architecture details, remaining metric proposals,
formal baseline and full requirements review retain their existing states. Earlier
individual validations remain individual; no construction readiness is inferred.

## November 16 Scope Clarification

The user supplied an expanded [idea catalog](upgrade-ideas.md) and
[ideas 1/2 decision document](../../../docs/fase2-ideias-1-e-2.md), explicitly stating
that not all decisions have been made. The new text communicates preferences for
layered authorization, gateway-signed identity, mTLS, initially proposed WebSocket tickets, loopback
ports, users/subscriptions and data access, plus nginx/S3 video uploads with
post-upload validation and deferred hashing. These preferences are recorded as
communicated choices, not blanket approval of algorithms, lifetimes, migration,
API changes or every team member's agreement.

The [measurement specification](../../../docs/fase2-metricas-e-baseline.md) now
catalogs 60 security/upload/regression metrics, origins of proposed minimums/targets,
audited existing values and missing formal baseline measurements. It supersedes
the older percentage-reduction suggestion for discussion with the more recent
64/32 MiB proposals; neither set is an approved requirement. The Mac/ARM pilot
and the earlier Intel/Linux experiments must remain separate.

The final rationale section of the decision document records each choice's reason,
alternatives, costs, residual risks and tests. Changes to link expiration, upload
API compatibility, quota admission and hash/cache state need an explicit
functional-preservation decision before construction. No application code was
changed during this review. Required runtime measurements are not marked complete.

## Individual Validation of the First Decision Group

The user explicitly validated options A for D3/JWT, D7 and D6.1. This is the user's
individual validation, not confirmation of agreement by all four team members:

- **D3/JWT:** Retain HS256 user JWTs in this phase, with a renewed secret outside
  the repository. Use RS256 for gateway-issued internal identity. Define the session
  transition, including anonymous sessions, before secret renewal. Transition
  mechanics, token lifetimes and rotation details were open at this first group;
  the November 17 selection below subsequently fixes the working profile.
- **D7:** Permit absence of `owner`; when present, require one value matching the
  owner in the path and reject contradictions. `projects` always verifies ownership
  and sharing independently of that parameter check.
- **D6.1:** Reject Socket.IO connections without a valid JWT, including anonymous
  access, which already has a session JWT. Room entry still requires authorization;
  the concrete mechanism remains for D6.2.

These choices do not approve the metric thresholds, a session migration strategy,
D6.2 or any other previously open point. No application changes are authorized
by treating this validation as final construction readiness.

## Individual Selection of Room Authorization and Removal

The user subsequently selected **D6.2 B + D6.3 A**, conditional on technical
confirmation; the assistant confirmed the combination as proportionate to the
scope/deadline with medium confidence. This is still an individual position, not
whole-team agreement:

- **D6.2 B:** Consult `projects` over an authenticated service path for every room
  entry and use its current authorization decision. Do not add signed room tickets.
  If projects is unavailable, temporarily refuse new entries and allow a retry.
- **D6.3 A:** Actively withdraw access to the affected room when effective
  authorization ceases. Preserve other authorized rooms and alternative legitimate
  access paths, such as another still-valid link presented by the user.
- **Rationale:** Avoid an extra room-token issuer, keys, lifetime, renewal and
  invalidation machinery. Reduced complexity is an engineering inference; no
  measured need to eliminate per-entry calls has been demonstrated. Room tickets
  may be reconsidered if measured load/latency or availability requirements justify it.
- **Open at that point (see later validation below):** Authenticated consultation contract/timeout, continued-membership
  revalidation, propagation failures, join/revocation races, measurable cutoff time,
  behavior during revalidation failure, and session expiration during active
  connections. A one-off event cannot guarantee the cutoff bound.

The earlier first-group paragraph records the state at that time; this section
updates D6.2/D6.3 only. No token lifetime, 5 s/2 s cutoff proposal or implementation
has been approved by inference, and D3/JWT, D7 and D6.1 retain their validated rules.

## Individual Validation of Periodic Membership and Session Expiry

The user explicitly validated **A in all three permanence/failure/JWT proposals**
and reconfirmed **D6.2 B: consult projects on every entry**, with these conditions:

- **Periodic revalidation:** Initially every **1 s**, subject to load/latency
  measurement. Group requests by project, retaining an individual authorization
  decision for each member and their access context. Fewer HTTP requests do not
  remove processing growth with the number of members/contexts.
- **Cutoff:** Adopt **≤5 s as acceptance criterion and ≤2 s as target** after
  confirmed revocation, both awaiting experimental validation in agreed scenarios.
- **Local validity:** At most **5 s from the start of the query that returned a
  positive result**, ending earlier on JWT or effective-permission expiry. Failures
  never extend that deadline. Late/out-of-order responses must not restore improper
  access; do not restart validity from response arrival.
- **Denial and failure:** An explicit denial of effective authorization removes
  access to the affected room immediately while preserving other valid
  authorizations. Unavailability never permits new entries. Existing members may
  retain access only until the existing bounded authorization expires.
- **JWT expiry:** Terminate the connection at expiration. The frontend must handle
  reconnection explicitly, presenting a valid JWT and requesting fresh authorization
  for every room. Do not assume automatic reconnection after server disconnection.
  Transition and renewal must preserve anonymous identities and their projects;
  their concrete design remains open, before HS256 secret renewal.
- **Deferred alternative:** Revocation events remain an evolution to reconsider if
  consultations create relevant load or fail the criteria.
- **Evidence limits:** Do not claim equal security of A/B during failures or that
  active-connection expiry is rare; neither is demonstrated. No compliance, load
  result or whole-team agreement is inferred from this individual validation.

This updates the earlier historical open state of revalidation, cutoff, failure
policy and active JWT expiry. The authenticated contract/timeout, batch limits,
access-context representation, response ordering/join-race coordination, session
transition/renewal, remaining token lifetimes and agreed experiment scenarios still
need detail. The measurement plan §4.1 specifies the pending verification. This is
partial requirements elicitation, not approval of the complete requirement set or
construction readiness.

## D4 Change and WebSocket Contract Validation

The [WS authorization contract proposal](../../../docs/architecture/fase2-contrato-websocket.md)
specifies candidate join/batch payloads, per-member/access-context decisions,
membership generations/query sequences, expiry controls and race/error scenarios.
It preserves the agreed pair and individually validated WS conditions.

The user explicitly chose **D4 mTLS for internal service authentication**,
superseding their previously chosen **HTTPS + asymmetric service JWT**. The earlier
selection was reported by the user in this message; its original timestamp is not
supplied. It is recorded as superseded, not silently rewritten. **D3 is unchanged:**
HS256 user JWTs and gateway-issued RS256 internal identity retain their functions.
mTLS authenticates services; it does not replace user identity or authorization.

The user individually validated:

- **WS-C1 A:** Direct ws_gateway → projects over mTLS. Projects authenticates the
  specific WS service and authorizes its permitted operations; another certificate
  from the CA is insufficient. WS transmits identity/expiry verified in the
  connection JWT, bound to member-presented contexts. This is explicitly trusted
  delegation from WS; projects always decides effective permissions. Projects does
  not verify the original HS256 JWT in this option or receive that secret.
- **WS-C2 A:** Initial configurable **1 s total timeout** including waiting,
  connection, send and read, and **up to 50 member/context evaluations per request**.
  Larger projects use multiple batches, **bounded concurrency and fair scheduling**;
  there is no 50-participant limit or demonstrated capacity. Failure/retry never
  extends authorization; cutoff acceptance ≤5 s/target ≤2 s remain.

The [D4 certificate lifecycle and pair matrix](../../../docs/fase2-ideias-1-e-2.md#d4--mtls-entre-serviços-ciclo-de-certificados-e-pares)
specifies the proposed operational detail: separate service identities/keys, CA key
outside application containers, restricted read-only secret mounts outside repo/
images/logs, verified chain/identity/purpose, reproducible issuance and renewal,
controlled rotation and explicit withdrawal/revocation policy. No service gets the
gateway RS256 private key or CA signing key by virtue of mTLS. The WS pair is
explicitly validated; the other observed application pairs need route/action review.
The later delivery-scope decision below fixes the required transport categories.
Exact per-channel configuration/termination and support in the deployed versions
remain to specify and verify, without claiming existing complete TLS/mTLS coverage.

Later WS-C3/PKI-C1 decisions below fix initial concurrency/JSON body limits and
certificate lifetimes/renewal window. WS-C4/PKI-C2/PKI-C3 below subsequently fix queue size and the trust-withdrawal/
maintenance strategy; channel proof, PKI timing and demonstrated workload capacity
remain open at this stage. **The November 17 WS-C5 selection below later takes
the contract as the working specification; full requirements review remains open.** Validation is individual, attributes no agreement to other
members, declares no tests run and does not authorize application changes. The ten
proposed verification cases map to existing metrics; full requirements review is
still outstanding.

## Delivery Security Coverage — Option A Validated

The user explicitly selected **option A for delivery on 27 November 2026**:
concentrate mTLS on internal application APIs and protect the remaining channels
with verified server TLS, service-specific credentials and least privilege where
applicable. This clarifies D4; it does not replace mTLS with service JWTs or reopen
the agreed QC-06 + QC-05 pair.

- **Internal APIs:** Require mTLS and authenticate the specific calling service,
  destination and allowed operations. This includes ws_gateway → projects and
  the application API pairs listed in D4. A certificate from the same CA alone
  never grants all operations. Route/action details remain to review.
- **Other channels:** Require TLS with server certificate-chain, validity and
  hostname/identity verification. Universal client-certificate authentication is
  not a delivery requirement. An unsupported protocol/version requires an explicit
  implementation/termination decision; plaintext or disabled verification cannot
  silently count as compliance.
- **Data and messaging:** Use service-specific credentials and minimum necessary
  permissions for MongoDB, RabbitMQ and S3 wherever applicable. Preserve legitimate
  asynchronous workers, backup and public signed-media reads; shared administrator
  credentials are not a substitute for the service identities/permissions required.
- **Preservation:** Keep D3 HS256 user JWTs/gateway RS256 identity, domain ownership/
  sharing checks, D7 and all individually validated WS entry, membership, failure,
  expiry and batching conditions unchanged.
- **Verification:** Check both negative and legitimate controls per channel. Use
  S08/S09 for internal mTLS identity/operation checks, S16/S17 for data/broker TLS,
  credentials and permissions, and S19/S20 for secret lifecycle/rotation. Confirm
  the remaining transport coverage in the D4 matrix, including nginx and tools.

This is individual scope validation, not measured compliance, full requirements
approval or construction authorization. Remaining certificate lifecycle details, exact
pair/route policy, infrastructure configuration, session transition/renewal and
remaining workload/metric decisions are still open. Option B, mandatory mTLS for
every internal protocol, is not required for this delivery; it may be reconsidered
if the threat model or evidence changes.

## WS, Certificate and Access-Policy Review — Individual A/A/A Validation

The user explicitly agreed with **WS-C3 A, PKI-C1 A and ACL-C1 A**, subject to the
conditions below. This is individual validation, not approval of the full
requirements set, measured compliance or authorization to change the application.

- **WS-C3 A:** Initially 4 global simultaneous authorization HTTP queries, at most
  1 per project, alternating batches between projects, and 64 KiB (65,536 UTF-8
  bytes) per JSON request/response body. The 50-evaluation and byte limits apply
  jointly; split before exceeding either, reject/log indivisible oversized bodies
  and never silently truncate. These parameters are configurable engineering
  choices. The 1 s total timeout includes queue waiting and never restarts when
  HTTP begins. Bound the pending queue (subsequently fixed at 16 by WS-C4), coalesce
  repeated context revalidations without postponing their deadline, and apply
  failure/no-renewal/no-new-entry rules to overflow and excessive waiting.
- **Capacity qualification:** Four concurrent queries do not imply a maximum of
  four queries/s or a demonstrated limit of twenty projects. Throughput depends on
  occupied time, scheduling and batches per project; four/s assumes roughly 1 s
  occupancy, and all timeouts can mean zero successful renewals. Test more than
  twenty active projects as a stress case, not a known capacity boundary. Include
  one 500-member project plus several small projects and measure small-project
  waits, refusals, actual cadence and cutoff ≤5 s/target ≤2 s. Final corpus remains
  to freeze; limits do not guarantee either deadline.
- **PKI-C1 A:** One CA per installation, CA lifetime 365 days, separate service
  keys, service certificates 30 days, renew with 7 days remaining (about day 23).
  Resolve the delivery tradeoff by including an administrator-invoked local
  issuance/renewal script and its verification in scope, retaining 30 days rather
  than silently switching to 90. No background automatic renewal is required.
  Check validity before startup; after >30 days offline, renew before resuming
  service. Never issue beyond CA validity. CA expiry/insufficient remaining life
  requires explicit CA handling before issuing a full new service lifetime.
- **Key-protection gap:** The [read-only source audit](evidence/security-planning-audit-2026-11-16.json)
  found no ignore match for three synthetic private-key paths, six tracked legacy
  private-key paths and seven reviewed build contexts copying the whole context
  without demonstrated key exclusions. No key contents were collected or images
  built. Implement Git/build exclusions with external secret mounts and verify
  synthetic private-key markers are absent from Git, contexts and image layers.
  Ignore rules alone do not remove tracked keys. CA keys must stay outside Git,
  build contexts and application containers. PKI-C2 B/PKI-C3 A below subsequently choose CA replacement and maintenance;
  later PKI-C4 fixes isolation timing, while replacement calibration/channel proof
  remain pending; membership cutoff is not a
  certificate-revocation SLA.
- **ACL-C1 A:** Only the owner may delete an entire project. Editors retain
  legitimate editing and media removal; readers may delete neither. The current
  DELETE guard accepts edit permission, so this is an explicit access-policy
  change justified as a security correction, not a rule unequivocally inherited
  from RF53–RF55. Preserve authorized owner-scoped cleanup on account deletion.
  Static inspection found the delete control in the current user's project list;
  no rendered UI behavior was tested. Verify any shared-editor path and hide or
  disable whole-project deletion for non-owners while enforcing it in the backend.
  Plan disposable-project owner/editor/reader tests, including the editor's
  successful media removal; do not use either preserved dataset as destructive
  fixtures.

Confidence is medium for WS sizing/certificate durations, and high for the
recommendation to separate editing from administration; these are engineering
judgments, not benchmarks or evidence of academic acceptance. The subsequent
A/B/A validation below resolves queue size and withdrawal/maintenance strategy;
final load corpus, channel verification, emergency reconciliation and remaining
contract/pair-operation details still require review. No application, ignore/build files,
certificates or preserved data were changed, and no new runtime tests were run.

## Operational Security Validation — WS-C4 A, PKI-C2 B and PKI-C3 A

The user explicitly selected **A/B/A** with conditions, recorded at
2026-11-16T20:14:36Z. This is individual validation, not whole-team/full-requirements
approval or construction authorization. The [operational contract and testable
runbook](../../../docs/architecture/fase2-fila-ws-e-revogacao.md) records:

- **WS-C4 A:** Initially 16 pending batches per WS process, besides 4 active,
  at most 1 pending per project. A second pending plan for the same project replaces
  the old one in its slot, retaining original admission time/deadline and removing
  expired work; never restart the total 1 s timeout. Complete replaced join
  callbacks explicitly; discard obsolete evaluations without mixing different
  members/contexts or creating hidden queues. Overflow/timeout never grant joins
  or renew authorization. Later WS-C5 B fixes membership-state caps; physical
  workload/manifest still need completion.
- **PKI-C2 B:** Withdraw trust by replacing the installation CA, reissuing all its
  certificates/keys and removing old CA trust from every participant. This replaces
  the assistant's earlier CRL recommendation; CRL and its proposed durations are
  not part of the selected mechanism. A single compromised service requires the
  full procedure, with installation-wide coordination/downtime. Ordinary expiry
  renewal can retain the CA and does not itself invalidate an old still-valid
  certificate; if immediate withdrawal is required, use the full CA procedure.
  CA 365 days is a maximum lifetime, not a minimum period of retaining trust.
- **PKI-C3 A:** Isolate, update coherently and restart affected processes/clients/
  verifiers, removing old sockets, pools, session caches/tickets. Partial updates
  keep the installation isolated. Planned maintenance requires no active work;
  compromise triggers isolation immediately, without waiting for jobs. Before
  reopening, require complete WS → projects and projects → storage calls, all
  other affected participants, old-CA rejection on a new connection and closure/
  invalidation of previous connections and TLS resumption. Preserve volumes,
  identity, quota and reconcile interrupted work rather than retry mutations blindly.

The runbook, positive/negative controls, version manifest and failure outcomes are
specified for implementation/evaluation, not executed. Confidence in proportionality
is medium; there is no comparative benchmark or demonstrated short outage. No PKI
operational deadline is selected; WS ≤5 s/target ≤2 s are separate. Channel/version
checks, concrete emergency reconciliation, WS state/abuse limits, workload and
remaining session/upload choices stay open. No application changes, certificates,
PKI script implementation, new runtime tests or collective approval are inferred.

## Operational Criteria Validation — PKI-C4 B, PKI-C5 A and OPS-C1 A

The user explicitly selected **B/A/A**, recorded at 2026-11-16T20:33:46Z, with
conditions in the [operational criteria contract](../../../docs/architecture/fase2-criterios-operacionais-seguranca.md).
This remains individual validation, not measured compliance/full requirements
approval or construction authorization:

- **PKI-C4 B:** Isolation ≤30 s, target ≤10 s from administrative command entry,
  including internal checks/wait, until new/persistent/internal connections,
  RabbitMQ consumers and active workers' effects are cut. Test ongoing connections/
  consumers and do not equate broker loss/zero queues with stopped processing.
  Failure is incomplete isolation: continue and keep the original clock. Failed
  replacement/checks keep the installation isolated. No 15/5-minute replacement
  bound is imposed; measure actual duration, installation/load and all attempts.
- **Pilot milestone:** Set **2026-11-23T18:00:00Z (18:00 Europe/Lisbon)** as the
  planning deadline, leaving time before 27 November. This does not select either
  preserved installation or assert team availability. Record installation, load,
  participants/images/hardware, per-phase times, attempt count/raw evidence/failures
  and conclusion. A valid pilot before delivery supplies an empirical, documented-
  scenario comparison criterion based on observed time, not a universal SLA. If
  missing/delayed, record status/limitation and explicit revised plan, no silent
  extension or invented result. The former 15/5-minute recommendation is superseded.
- **PKI-C5 A:** Full matrix with current/target state per channel, automated probes
  and reproducible manual browser checks using a known-trust test profile; never
  bypass certificate warnings to count a pass. **expand_ai_tool → generative-mock
  is explicitly included as an internal mTLS API.** Its HTTP client/Flask server
  need real implementation/tests, preliminary effort and a rollback plan; the new
  matrix row alone is not protection. Other APIs/data/broker retain the validated
  coverage distinction. Runtime versions/termination remain to prove per channel.
- **OPS-C1 A:** Implement and test an administrative tool/executable procedure by
  delivery, without automatic replay. Preserve evidence before correction; keep
  indeterminate results out of committed results, and prevent duplicate quota
  correction even across a crash/lost response. A journal written after an unsafe
  refund is not proof of idempotence. Without evidence, keep the case pending/
  isolated. Without implemented/tested procedure by 27 November, record a limitation,
  never existing recovery capability. Automatic recovery is future evolution;
  early acknowledgement remains a known defect. Restarted consumers do not prove
  correct completion. Manual effort/downtime and integrity limits remain explicit.

Preliminary effort estimates in the contract are engineering ranges, not measured
work or approved team budgets. Chosen targets remain unverified; WS 5 s/2 s and F08
have separate clocks/scenarios. Installation/load, concrete isolation, TLS/mTLS
termination, executable reconciliation and tests, WS state/abuse limits, sessions/
uploads and full baseline/review remain to complete. Only documents were changed;
no application, Compose, credentials or preserved data were modified, and no new
runtime tests or PKI/admin tool implementation were performed.

## November 17 Security Selection — SESS-C1 A/JWT-C1 A/LINK-C1 A/WS-C5 B

The user recommended **A/A/A/B** for confirmation; the assistant technically
confirmed proportionality with the stated conditions at 2026-11-17T11:53:34Z.
Record this as an **individual selection communicated by the user and technical
confirmation**, not a separately worded whole-team approval or completed test.
The [contract and logical scenarios v1](../../../docs/architecture/fase2-sessoes-identidade-partilhas-ws.md)
specifies the selected working design:

- **SESS-C1 A:** Assisted transition/reissue for the same identity, registered login,
  anonymous independent administrative proof, 7-day absolute HS256 user JWT without
  automatic refresh. Future anonymous expiry also needs assistance. Without proof,
  preserve data/case pending; knowing ID/old exposed-secret JWT is insufficient.
  Issuance/import procedure must be implemented/tested. Network error/expiry must
  not silently create a new anonymous account. No generic individual-session
  revocation is claimed; copied bearer/logout risk remains explicit.
- **JWT-C1 A:** Per-request RS256 identity up to 30 s/no later than session expiry,
  bound to issuer/audience/type/method/internal path and specific mTLS peer.
  Scoped projects delegation on downstream quota/storage pairs is explicit trust,
  not accepting the wrong audience or sharing gateway signing keys. No generic
  anti-replay store: same authorized peer/context may reuse during validity. jti
  alone is not single-use; even persisted jti does not give exactly-once effects.
  Thirty seconds bounds admission, not legitimate upload/job duration. S07 separates
  invalid-profile rejection from this accepted residual reuse.
- **LINK-C1 A / D8:** Preserve old/new links until explicit revocation, retaining
  RNF52 (verified physical PDF page 27); expiresAt/schema/UI/migration postponed
  for this delivery, superseding the earlier communicated expiry preference.
  Revocation/revalidation and other valid access paths remain; signed S3/upload
  credential lifetimes are separate outstanding upload decisions.
- **WS-C5 B:** Initial 512 connections/4096 contexts per process including pending
  reservations, 32 rooms/connection, 4 contexts/room and the contract's bounded
  rates/buckets/input sizes. Free state on every error/timeout/leave path, including
  failed authentication before connect. Apply 4/8/64 KiB to the corresponding
  inputs without truncating legitimate outbound events. Control protected project
  events in personal rooms as well as project rooms; source producer context and
  emission guards require actual implementation/tests.

Logical scenarios v1 are fixed for evaluation: normal 50 connections/10 projects,
fairness 500+5+5=510 connections, many projects 40×5=200, and independent state/
rate/byte/error boundaries. Attempts above 512/4096 test controlled refusal and
existing-authorization preservation, not fully supported load. If the corpus needs
more admitted concurrency, explicitly revise A/values before physical freeze.
Within-cap load also needs measurement; a backend timeout is not cap overflow.
Host/untrusted-container D10 paths, positive controls and raw results are specified.

Confidence is high for link preservation, medium for other proportionality choices;
limits/TTL are not capacity evidence. Concrete anonymous proof/browser mapping,
physical installation/load/manifest, issuance/import and emission-control tooling,
channel support, administrative reconciliation, uploads and full requirements/
baseline review remain incomplete. Only documentation changed; no application,
secrets, browsers, volumes or deployment changed, and no new runtime test ran.

## Session Transition — Source Findings, Proof Pending

### Anonymous Recovery Concretization — Evidence Unknown

The user selected detailing anonymous recovery and issuance/import. When asked
whether an independent reliable association record exists, the user answered that
they do not yet know. Record **unknown**, not evidence present/absent or account
eligibility. The historical two anonymous accounts are not newly inspected cases.

The [working procedure](../../../docs/architecture/fase2-recuperacao-anonima.md)
and [empty case template](../../../docs/templates/anonymous-session-recovery-case.template.json)
now specify proof conditions, private administrative states, restricted issuer,
bearer delivery file and server-validated import before replacing local session.
The template is not approval and contains no credential/real subject ID. Filled
records stay outside Git; pending evidence prevents issuance.

Implementation must suspend normal SessionProvider/register/validate/logout/socket
effects before recovery starts; a page inside today's provider is insufficient.
Validate issuer/sub/type/expiry against server and independent approved case, handle
wrong installation/profile, storage/network failure, concurrent tabs/callbacks and
ambiguous issuance without blind retries. The delivery JWT remains the normal
7-day user bearer from issuance, not single-use/refresh; deleting a file does not
revoke copies. Future anonymous expiry still requires assisted proof/reissue.

AR-01–AR-12 detail existing SEC-01/SEC-02 and S06/S19/S20/F06 guards. Concrete
recovery evidence remains unknown; tooling/import UI/server profile and tests are
not implemented by this specification. No account, browser, secret or retained
data was read/changed, no token issued and no case approved. Full requirements,
baseline and construction review remain pending; SESS-C1 A is unchanged.

Source inspection during continued elicitation found:

- [JWT issuance](../../../users/auth/auth.js) currently uses HS256 with a seven-day
  lifetime. This is observed behavior, not a newly approved lifetime policy.
- [Anonymous registration](../../../frontend/lib/session.ts) stores the returned
  JWT; the inspected [user schema](../../../users/models/user.js) has no independent
  anonymous recovery/session credential. No such recovery mechanism was found in
  the inspected authentication/session paths; do not generalize that inspection
  into a claim about every external deployment.
- [Session-update error handling](../../../frontend/lib/mutations/session.ts)
  currently logs out and creates an anonymous identity on error. That cannot be
  treated as preservation of the previous anonymous identity/projects.
- A JWT signed under an exposed signing secret is not, by itself, independent
  proof of legitimate ownership for upgrading an old identity to new credentials.
  Storing an old user ID in the browser is not additional proof. Do not claim
  transparent safe migration solely by verifying/re-signing such a JWT.

**Deployment scope clarified by the user:** PictuRAS is used only locally on the
team members' computers through Docker Compose; each member administers their own
installation. The user states there is no shared installation and no external
users, and no formal environment list yet. Record this as supplied operational
context, not a runtime census or an inference from source inspection. It supersedes
the earlier unknown deployment-scope state; specific installations, volumes,
browser profiles and identity/project associations still need enumeration.

Before executing the selected assisted migration, complete the inventory:

- Deployments and retained datasets whose anonymous sessions/projects must survive.
- Anonymous identities and associated projects in the local installations;
  distinguish fixtures, data to preserve and unclassified cases without inventing
  counts or treating all local data as disposable.
- Which browsers are controlled/accessibly recoverable by the team, based on
  deployment/operator information rather than inferred from database records alone.
- Available independent identity/ownership evidence or assisted recovery procedure,
  expiry constraints and clients that cannot participate in a planned transition.

Record source, time and responsible operator for the inventory; do not collect raw
JWTs or private credentials in documentation/logs. This is a planning prerequisite,
not an executed migration or completed ownership proof. Until eligible mappings are verified,
preserve the existing identity/project requirement; do not rotate the secret or
substitute new anonymous identities as if preservation were achieved.

The [session inventory worksheet](../../../docs/architecture/fase2-inventario-sessoes.md)
now provides the four administrators' roster, collection fields/sources, known
historical candidate environments, a read-only collection procedure and completion
criteria. It does not assume one installation per person or mark counts complete.
The source review also confirms `localStorage.session` and session-validation
effects that can replace an anonymous identity; collection must not trigger that
replacement by treating page reload/login as a neutral observation.

SESS-C1 A now selects registered reauthentication and assisted anonymous reissue,
including future expiry, with 7-day absolute user tokens. Concrete independent
proof, browser mapping and executable issuance/import remain to complete before
using that mechanism. No accounts, tokens or projects were modified.

After the user requested continuation, read-only Docker metadata was collected on
one local daemon: 13 stopped containers/6 labeled volumes for the historical
experiment and 8 retained volumes/no matching containers for `picturas`. The
[normalized observation](evidence/session-inventory-local-2026-11-16.json) records
scope, sources and limits. The old temporary Compose file is absent. At that first
observation no database/browser contents were read or services started.

The user subsequently confirmed **Luís as administrator of this machine (ADM-01)**
and instructed preservation of **both complete volume sets**, with the development/
evaluation installation to be selected later. They requested account/project
counts without modifying original data. The [aggregate collection](evidence/session-counts-local-2026-11-16.json)
used private temporary copies of four source volumes mounted read-only; MongoDB
ran only on the copies without external networking/published ports. Original file
manifest hashes matched before/after and temporary databases/copies were removed.

| Preserved data set | Accounts | Anonymous / free / premium | Projects | Projects owned by anonymous accounts |
|--------------------|----------|----------------------------|----------|--------------------------------------|
| picturas | 4 | 2 / 2 / 0 | 2 | 0 |
| picturas-quality-20261114 | 13 | 0 / 13 / 0 | 10 | 0 |

The project owners were found in the respective accounts collection and all are
free accounts. Media references were counted (3/28), not verified against storage.
No private IDs or credentials are archived; browser associations/presets remain
unexamined and other administrators' computers uninventoried. These are account
counts per data set, not distinct people or active sessions. Zero anonymously owned
projects does not authorize discarding anonymous identities. A failed first copy
attempt is retained separately; it also verified unchanged originals and cleanup.
No original application/database was started or changed. No migration, secret
rotation, disposal or development/evaluation-source selection has been made.

## Business Goals

| Goal | Evidence of success | Priority |
|------|---------------------|----------|
| Address two concrete quality weaknesses relevant to PictuRAS stakeholders. | Independently specified and evaluated requirements, classified under ISO/IEC 25010:2011. Quality priorities are awaiting team input. | Must |
| Demonstrate improvement rather than assume it from an architectural change. | Comparable initial/final measurements with identified scenarios, data, environment and instruments. WS cutoff criteria have individual validation; remaining numerical targets and whole-team approval are pending. Compliance is not yet measured. | Must |
| Preserve the existing editing product. | Regression evidence for images, video and mixed projects, including subtitles and frame extraction where affected. | Must |

## Stakeholders

Registered and premium users benefit from dependable editing and understandable
feedback. Developers and operators need maintainable services and predictable
resource consumption. Anonymous image users must retain the supported behavior
even though video is unavailable to that profile. The academic team needs a
defensible link between requirements, evidence, decisions and results.

## Scope

### In Scope

- Retain the six-direction exploration and pair comparison as the rationale for
  the agreed QC-06 + QC-05 pair; complete the two requirements without reopening
  selection by default. Pair agreement is recorded as communicated by the user.
- Specify each requirement's metric, unit, measurement method, baseline, target
  and minimum acceptable value, with the origin of each numerical value recorded.
- Measure the unchanged application before refactoring the affected behavior.
- Compare architectural options, account for dependencies and assess trade-offs.
- Refactor the selected paths and repeat the same measurements afterward.
- Preserve existing public behavior and provide regression evidence for affected
  image and video flows.
- Document AI assistance, limitations and validation.

### Out of Scope

- New product features such as a video library or premium segment-editing variants.
- Replacing the project-wide pipeline with independent pipelines for every item.
- Treating all weaknesses in the diagnosis as mandatory implementation work.
- Choosing an architectural alternative before the quality requirements are defined.
- Treating historical test results or qualitative matrix ratings as a new baseline.

## Functional Requirements

No new functional requirements have been generated. Detailed preservation criteria
will be recorded after clarification of the chosen quality requirements. The known
product boundary includes project-wide ordered pipelines, batch processing,
per-video trim/speed, profile quotas, audio behavior, previews, subtitles and
terminal frame extraction. Existing source requirements and implemented behavior
must be distinguished wherever they differ.

## Non-Functional Requirements

The selected pair is **QC-06 security/end-to-end authorization** and **QC-05
performance efficiency/upload resource utilization**, with agreement provenance
above. Detailed quantitative NFRs remain in elicitation: the individually validated
WS conditions are recorded, remaining targets are proposals, and formal baseline
values must still be completed. No unmeasured value is asserted as a result.

The six directions under exploration are reliability/recovery, video capacity,
maintainability/modularity, pipeline usability and background-work feedback,
upload resource use and internal-service security (QC-01 through QC-06 in the
[comparison](quality-exploration.md)). This comparison is retained as selection
rationale, not a commitment to implement every direction or adopt ALT-1 or ALT-2.

## Constraints

- Follow the 2026/2027 Phase 2 guidelines: refactoring with functional preservation.
- Classify the two selected requirements under ISO/IEC 25010:2011 and evaluate
  each one independently, including relevant adverse effects on other attributes.
- Preserve an identifiable application baseline before changing code or deployment.
- Keep measurements reproducible and comparable; record CPU/RAM allocations,
  model warm/cold state and concurrent workloads when they influence the result.
- Delivery is on **27 November 2026**, explicitly corrected by the user during
  this conversation. This supersedes the earlier 20 November planning date. The
  supplied guidelines still state 20 November; retain that source unchanged and
  attribute the current planning deadline to the user's later correction. The
  submission time, available team hours and participant access remain unknown.

Project-wide implementation conventions remain in the repository guidance and
will be maintained separately from these intent-specific requirements.

## Assumptions

| Assumption | Risk if invalid | Mitigation |
|------------|-----------------|------------|
| This intent continues the Phase 2 work discussed after Exercise 6. | Scope could diverge from the team's intended next improvement. | Keep this draft open for correction during elicitation. |
| The existing diagnosis is useful starting evidence. | Runtime conditions or code may have changed since its measurements. | Re-identify the current commit/environment and measure the selected requirements before refactoring. |

## Open Questions

| Question | Owner | Resolution |
|----------|-------|------------|
| Which two quality weaknesses should this intent prioritize? | PL2-G4 | Resolved: QC-06 security/end-to-end authorization + QC-05 performance efficiency/upload resource utilization. Pair agreement recorded on the user's explicit instruction at 2026-11-16T15:12:33Z; details and measurements remain open. |
| What hardware/resource budget, time, representative workloads and participants are available? | PL2-G4 | Pilot resources are recorded. Team hours, final workload scope and participant access remain open for the team review. |
| What delivery deadline applies? | PL2-G4 | User explicitly corrected delivery to 27 November 2026; the previous 20 November planning date is superseded. Submission time remains unknown. |
| What deployment/browser context must session migration preserve? | PL2-G4 / each local administrator | Local-only/no external users confirmed. Luís administers LOCAL-HOST-01 and requires both volume sets preserved. On isolated copies: picturas 4 accounts/2 projects (2 anonymous accounts, 0 anonymous projects); experiment 13 accounts/10 projects (0 anonymous accounts). Browser associations, presets/media integrity and other computers pending; no development/evaluation installation selected. |
| What target and minimum acceptable values are justified by the baseline and stakeholder needs? | PL2-G4 | WS cutoff ≤5 s/target ≤2 s and initial 1 s revalidation are individually validated, awaiting experimental proof. Other metric proposals remain unapproved; complete applicable gate review, whole-team agreement and reproducible formal baseline before refactoring. |
| Which architecture details remain undecided? | PL2-G4 | SESS-C1 A/JWT-C1 A/LINK-C1 A/WS-C5 B are individually selected with assistant technical confirmation, not pending A/B choices. Concrete anonymous proof/browser mapping, physical corpus/installation/manifest, executable migration/emission/reconciliation controls and per-channel support still need completion; upload/API/token/hash decisions remain separate. Logical scenarios v1 fixed; excess 513/4097 is refusal testing, not capacity. Full requirements and formal baseline remain incomplete. |

## Sources

- [Exercise 6 architectural diagnosis](../../../docs/exercises/06-architectural-patterns/resolution.md),
  including its EV/H/ALT identifiers and evidence limitations.
- [Phase 2 guidelines, version 1](../../../docs/guidelines/fase-2-guidelines-1.pdf).
- [Video extension requirements](../../../docs/requirements/doc-ext-requisitos-2627.pdf).
- [Documentation index](../../../docs/README.md) for the earlier requirements,
  architecture report and course material.
- [Repository guidance](../../../AGENTS.md).
