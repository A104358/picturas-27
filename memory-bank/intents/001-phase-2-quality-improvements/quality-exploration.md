---
intent: 001-phase-2-quality-improvements
phase: inception
status: draft
created: 2026-11-14T17:16:06Z
updated: 2026-11-18T14:11:52Z
---

# Quality Options and Team Decision

## Purpose and Current State

Explore all six candidate directions before selecting exactly two distinct quality
requirements for Phase 2. The user requested exploration followed by validation
and agreement from the whole PL2-G4 team. Exploration does not commit the team to
implementing all candidates or to a particular architectural alternative.

This document contains a qualitative analysis of the six directions and their
15 possible pairs. It is not an exhaustive catalog of every possible refactoring.
Candidate benefits, effort and risks are engineering hypotheses. The subsequent
[investigation plan](investigation-plan.md) adds a local acknowledgement-order
demonstration, host regression results and processor-only experiments. The
[live findings](live-findings.md) now add measurements through a 13-service
application slice, an internal access matrix and one worker kill/restart. Broader
load/fault coverage, real Whisper, scaling, maintenance-task experiments and
participant usability remain pending. The user has since requested recording
agreement on **QC-06 security/end-to-end authorization + QC-05 performance
efficiency/upload resource utilization**; see the canonical record below.
Full quantitative requirements and remaining decisions still need review.

The [Exercise 6 resolution](../../../docs/exercises/06-architectural-patterns/resolution.md)
provides the EV/H evidence identifiers used below. Targeted source checks during
this preparation confirmed manual video acknowledgements and prefetch 1 in
`Tools/video/video.py`, acknowledgement before awaiting the asynchronous callback
in `projects/utils/rabbit_mq.js`, duplicated PIL operations in
`Tools/video/effects.py`, memory-backed uploads in the gateway/orchestrator/storage
and video-dependent toolbar visibility. These checks support structural findings;
they do not establish operational failure rates or user difficulty.

## Candidate Directions

The classifications below use ISO/IEC 25010:2011, as required by the
[Phase 2 guidelines](../../../docs/guidelines/fase-2-guidelines-1.pdf).
A direction must become a concrete, bounded requirement before selection is final.
Two distinct requirements may belong to the same top-level characteristic if
their scope and independent evaluation are clear.

QC-04 includes separate pipeline-creation and background-work scenarios. The
[guideline coverage map](investigation-plan.md#coverage-of-the-teaching-guidelines)
keeps both indicative usability ideas explicit. The 15 broad-direction pairs
below do not exclude two separately measured requirements within one direction.

| ID | Direction | Primary classification | Stakeholder outcome | Evidence / hypotheses |
|----|-----------|------------------------|---------------------|-----------------------|
| QC-01 | Reliable processing and recovery | Reliability: fault tolerance / recoverability | Accepted work reaches a coherent outcome despite a defined interruption. | EV-15, EV-16, EV-21, EV-25; H-03, H-12 |
| QC-02 | Video processing capacity | Performance efficiency: capacity; time behaviour as a guardrail | Concurrent batches finish with tolerable queueing under a fixed resource budget. | EV-09, EV-16, EV-19; H-02, H-08, H-12 |
| QC-03 | Video processing modularity | Maintainability: modularity / modifiability | An existing effect can be maintained with limited propagation and deployment impact. | EV-10, EV-18, EV-19; H-04 |
| QC-04 | Pipeline usability and background-work feedback | Usability: operability | Users can configure supported pipelines and understand execution and errors. | EV-15, EV-22, EV-23, EV-25; H-06, H-10 |
| QC-05 | Large-upload resource efficiency | Performance efficiency: resource utilization | Valid large media can be uploaded with bounded service memory consumption. | EV-11, EV-12, EV-21; H-05 |
| QC-06 | Internal access protection | Security: confidentiality / integrity / authenticity | Requests cannot bypass the defined user/project authorization boundary. | EV-11, EV-24; H-07 |

### QC-01: Reliable Processing and Recovery

**Current finding:** Image auto-acknowledgement and acknowledgement timing in the
orchestrator leave failure windows. Video acknowledges at the end of its callback,
but that does not guarantee that the orchestrator has persisted a result. Repeated
execution can also share work paths. Actual loss/duplication rates are unmeasured.

**Options:** Correct acknowledgement/publication handling and persist execution
state; add idempotent completion and paths scoped to an execution. Compare these
focused changes with any broader pipeline decomposition before choosing one.

**Discriminating experiment:** In a disposable deployment with dedicated data,
interrupt the worker, broker or orchestrator at specified processing/publication/
commit boundaries. Separate handled errors from abrupt termination. Count accepted
jobs, correct committed outcomes, missing or duplicated results, recovery time and
quota inconsistencies. Define the recovery window and repetitions before running.

**Cost / trade-off:** Cross-service changes and failure instrumentation may be
substantial. Retries can duplicate work; persistence can add latency. Guard the
existing commit-token, cancellation, quota and frame-manifest semantics.

### QC-02: Video Processing Capacity

**Current finding:** The configured video service has one consumer with prefetch 1;
recognition and ordinary effects share it. Extra workers may help independent jobs
when resources are available. They may also saturate the host or collide on files.

**Options:** Compare a bounded competing-consumer pool (ALT-2) with separation of
heavy stages or resource allocation. Distributed effects (ALT-1) introduce more
I/O and contracts and must justify their cost. No autoscaling benefit is assumed.

**Discriminating experiment:** Record queue wait, processing time, end-to-end p95,
completed videos per minute, CPU and memory for the same finite batch. Include
ordinary effects, real speech and extraction, separating cold/warm models. Start
with the unchanged topology. Test additional consumers only in an isolated variant
after checking file isolation and the available CPU/RAM budget.

**Cost / trade-off:** A topology change can be small, while safe concurrent execution
needs extra work. Guard output/audio equivalence, quotas, same-project concurrency
and memory. Faster batches do not necessarily mean faster individual videos.

### QC-03: Video Processing Modularity

**Current finding:** Video already has internal modules, but effect operations are
duplicated from image tools and deployed together. The orchestrator also combines
several responsibilities. Duplication alone does not quantify maintenance cost.

**Options:** Extract reusable pure effect operations with explicit boundaries;
separate orchestration from transport; compare internal modularization against
ALT-1's independently deployed effects. More services are not a prerequisite.

**Discriminating experiment:** Define an equivalent maintenance task on an existing
effect, such as correcting parameter validation. In isolated before/after branches,
record modules/services changed, dependencies affected, rebuild scope, regression
results and task duration. Control task familiarity and record its bias. A temporary
exercise must not become a new delivered feature.

**Cost / trade-off:** Internal extraction is narrower than distributed deployment;
actual effort remains unknown. Shared packages can couple releases. Guard effect
parameter contracts, image/video pixel behavior, stage ordering and packaging.

### QC-04: Pipeline Usability and Background-Work Feedback

**Current finding:** Tool visibility depends on media, progress is held in browser
state and execution uses an overlay. Some image error paths have correlation
problems. These mechanisms warrant investigation; user confusion is not measured.

**Options:** Clarify existing availability/validation rules and error feedback;
improve presentation of existing execution state. Assess any server-side state
change against the functional-preservation constraint before including it. Do not
silently turn this direction into new editing or cancellation functionality.

**Discriminating experiment:** Use identical image-only and mixed-project tasks;
measure successful task completion, errors, time and comprehension of existing
processing states. Record participant count/experience and counterbalance task
order. Measure progress-event gaps separately: event cadence cannot stand in for
user comprehension. Team-only trials are a pilot with limited generalizability.

**Cost / trade-off:** Requires participant availability and a controlled task script.
UI refactoring may be narrow; persistent progress may involve backend changes.
Guard accessibility, supported tool restrictions and actual cancellation behavior.

### QC-05: Large-Upload Resource Efficiency

**Current finding:** Gateway, projects and storage use memory-backed upload buffers.
ZIP export also uses memory, but is a separate scope decision. Neither peak usage
under representative uploads nor a safe concurrency envelope has been measured.

**Options:** Compare streaming/backpressure with disk-spooled uploads while retaining
the existing API, validation and ownership. Treat ZIP streaming as an additional
candidate within this direction, rather than silently expanding the upload scope.

**Discriminating experiment:** Upload identical valid files at controlled concurrency
and input rate. Record baseline/peak RSS per affected service, process/container
memory, accepted/rejected uploads, latency and stored-object integrity. Select
sizes within each profile's configured limits and repeat the same workload after
refactoring. Memory improvements must not be inferred from latency alone.

**Cost / trade-off:** Changes cross HTTP boundaries and temporary-file cleanup.
Disk spooling can exchange RAM for I/O and storage. Guard media validation,
disconnect handling, quotas, ownership and removal of incomplete uploads.

### QC-06: Internal Access Protection

**Current finding:** Published internal ports, trust in internal callers and disabled
TLS verification weaken the intended entry boundary. The exact reachable bypasses
and required legitimate service paths need a bounded test inventory.

**Options:** Reduce unnecessary exposure and enforce identity/authorization at the
selected boundary; validate internal TLS where applicable. Select a specific threat
scenario rather than promising that the entire system will become secure.

**Discriminating experiment:** With two dedicated test accounts/projects, enumerate
normal and direct entry paths. Test absent/invalid credentials and cross-owner
read/write requests, recording prevented unauthorized actions over a defined test
matrix alongside successful authorized requests. Network reachability alone is
not proof of authorization, and a finite suite is not proof of complete security.

**Cost / trade-off:** Port changes can be narrow; service identity and certificate
management can widen scope. Guard gateway/WS/S3 access, sharing, worker communication
and authorized processing. Use synthetic data and do not reproduce secret values.

## Comparison of All Candidate Pairs

These are prospective trade-offs, not scores or a ranked shortlist. Every pair
still needs an explicit scenario and independent measure for each requirement.

| Pair | Why consider it | Main issue to resolve |
|------|-----------------|-----------------------|
| QC-01 + QC-02 | Recovery and safe concurrent processing reinforce each other. | Cross-service scope; separate failure correctness from normal-load capacity. |
| QC-01 + QC-03 | Explicit module boundaries can simplify recovery responsibilities. | Internal modularity does not itself guarantee durable execution. |
| QC-01 + QC-04 | Coherent outcomes and understandable feedback address processing trust. | User feedback must reflect actual recovery state; participant access is needed. |
| QC-01 + QC-05 | Covers processing correctness and upload memory pressure. | Largely separate paths increase integration and validation effort. |
| QC-01 + QC-06 | Covers failure recovery and unauthorized state changes. | Broad cross-service scope and two different fault/threat models. |
| QC-02 + QC-03 | Can align processing boundaries with independent resource allocation. | Distributed effects may worsen I/O, latency and output equivalence. |
| QC-02 + QC-04 | Addresses queueing experience and user understanding. | Better perceived feedback must not be reported as increased capacity. |
| QC-02 + QC-05 | Covers processing and ingestion under resource pressure. | Same top-level ISO characteristic: define distinct workloads and measures. |
| QC-02 + QC-06 | Bounds workload capacity and its permitted entry paths. | Security overhead and deployment changes affect the capacity comparison. |
| QC-03 + QC-04 | Improves developer change impact and user operation. | Benefits are separate; maintenance and participant studies both need controls. |
| QC-03 + QC-05 | Clearer transfer boundaries may support efficient uploads. | Video-effect modularity and upload scope may have little overlap. |
| QC-03 + QC-06 | Explicit boundaries can make authorization responsibilities clearer. | Maintainability measures cannot substitute for access-control tests. |
| QC-04 + QC-05 | Addresses user operation and the cost of large uploads. | Upload progress is feedback, not evidence of bounded server memory. |
| QC-04 + QC-06 | Clarifies permitted operation and enforces its access boundary. | Preserve legitimate sharing and avoid exposing internal details in errors. |
| QC-05 + QC-06 | Efficient transfers and ownership checks share ingress boundaries. | Streaming must not bypass validation/authentication or retain partial data. |

## Exploration and Selection Procedure

1. **Catalog evidence:** Review all six directions using this document and the
   source diagnosis. Record disagreements and distinguish observed mechanisms
   from untested consequences. This initial qualitative catalog is prepared.
2. **Define comparable investigation protocols:** Establish the available time,
   hardware, datasets, participants and isolated test environment. For each
   direction, record its smallest useful experiment, estimated effort and any
   missing prerequisite. Do not run all alternatives as full implementations.
3. **Gather discriminating evidence:** Run affordable baseline checks; use short,
   isolated prototypes only where uncertainty affects the decision. Preserve the
   unchanged application revision and raw results. If a candidate cannot be tested,
   record that limitation rather than assign an invented result.
4. **Compare and shortlist:** Assess stakeholder impact, strength of evidence,
   measurement feasibility, delivery effort, regression risk and trade-offs. Every
   exclusion needs a reason. Shortlist pairs only after reviewing all six directions;
   the [live findings](live-findings.md) supplied provisional discussion pairs.
   Selection has since been recorded as QC-06 + QC-05 below; retain this comparison
   as the rationale for that choice.
5. **Obtain whole-team agreement:** All four members review the same revision,
   proposed pair, evidence and scope. Record each person's explicit agreement or
   concerns. Discussion resolves concerns before acceptance; a majority vote or
   silence does not satisfy the requested agreement of the whole team.
6. **Specify and review the final requirements:** For the agreed pair, complete each
   stimulus/context, response, metric/unit, protocol, unchanged-code baseline,
   justified target and minimum acceptable value. Revise with the team if the
   measurements undermine feasibility. Then continue the Inception requirements
   review and subsequent planning before construction.

Use the same conditions before/after implementation and record repetitions,
sample sizes, exceptions and variability. Numerical targets must identify whether
they come from source requirements, stakeholder agreement or a proposed engineering
goal. Historical EV-28 test passes and smoke checks do not supply these baselines.

## Decision Record — Pair Agreement

**Par acordado:** Segurança — autorização ponta a ponta (QC-06 / ideia 1) +
Eficiência de desempenho — utilização de recursos nos uploads (QC-05 / ideia 2).
**Equipa:** PL2-G4. **Registado em:** 2026-11-16T15:12:33Z.
**Fonte:** instrução explícita do utilizador, “Podes registar o acordo do par”,
na sequência da identificação deste par e da indicação de que faltava registar
o acordo coletivo. O acordo do par fica registado como comunicado pelo utilizador
para a equipa; não foram recolhidas declarações ou assinaturas nominais separadas.

O registo seleciona estas duas áreas e não aprova por associação os detalhes ainda
abertos, todas as métricas ou o início da implementação. As validações individuais
anteriores mantêm esse âmbito. Não se inventa uma reunião nem um commit revisto
por cada elemento.

November 16: the user supplied expanded ideas 1/2 with some choices marked made
and explicitly noted unresolved decisions. The
[updated decision document](../../../docs/fase2-ideias-1-e-2.md) preserves that
distinction; its final rationale and
[measurement plan](../../../docs/fase2-metricas-e-baseline.md) are ready for review.
No individual agreement is inferred from those documents.

### Individual Decision Records — Validations and Technically Confirmed Selections

| Timestamp | Decision | User-validated rule | Scope of validation |
|-----------|----------|---------------------|---------------------|
| 2026-11-16T14:34:42Z | D3/JWT | User JWTs remain HS256 with renewed non-versioned secret; gateway-issued internal identity uses RS256. Session transition, including anonymous sessions, must be defined before renewal. | Explicit validation by the user in this conversation; no agreement of the other members declared. |
| 2026-11-16T14:34:42Z | D7 | `owner` may be absent; if present, require one value matching the path owner and reject contradictions. `projects` always checks ownership/sharing. | Same individual validation; no metric/implementation approval inferred. |
| 2026-11-16T14:34:42Z | D6.1 | Valid JWT required for Socket.IO connection, including anonymous sessions; room authorization remains mandatory and its mechanism is open in D6.2. | Same individual validation; remaining open choices stay open. |
| 2026-11-16T14:43:28Z | D6.2 B | Consult projects for current authorization on every room entry. Temporarily refuse new entries if projects is unavailable and allow retry; no room tickets. | User selected B/A subject to technical confirmation; assistant confirmed proportionality with medium confidence. Individual decision, not whole-team approval. |
| 2026-11-16T14:43:28Z | D6.3 A | Actively remove room access when effective authorization ceases; preserve other rooms and legitimate alternate access. | Same individual selection/technical confirmation. Permanence mechanism, cutoff bound, failure policy and active-session expiry remain open. |
| 2026-11-16T15:05:43Z | D6.3 periodic A; D6.2 B reconfirmed | Initially revalidate every 1 s, subject to measured load/latency; batch by project with individual decisions for each member/access context. Consult projects on every entry. | Explicit individual validation; HTTP batching does not eliminate processing growth with members/contexts. Events deferred unless measured load or criteria justify reconsideration. |
| 2026-11-16T15:05:43Z | D6.3 failure/cutoff A | Acceptance ≤5 s, target ≤2 s, pending experimental validation. Local authorization ≤5 s from positive query start, bounded by JWT/effective permission; failures never renew; obsolete responses never restore improper access; effective denial removes affected access immediately, preserving valid alternatives. No new entries during unavailability. | Criteria individually validated, not experimentally demonstrated or whole-team approved. No claim of equal A/B security during failures. |
| 2026-11-16T15:05:43Z | D6.1 active JWT expiry A | Terminate at expiry. Frontend explicitly reconnects with valid JWT and fresh authorization per room; never assume automatic reconnection after server disconnection. Renewal/transition preserve anonymous identity/projects. | Explicit individual validation. Renewal/transition design remains open; no claim that active expiry is rare. |
| 2026-11-16T15:30:57Z | D4 previous choice — superseded | HTTPS + asymmetric service JWT is replaced by mTLS for internal service authentication. | User explicitly identifies this as their earlier choice in the current message; original selection timestamp not supplied. Does not supersede D3's gateway-issued RS256 identity. |
| 2026-11-16T15:30:57Z | D4 current choice | mTLS authenticates internal services; authorize specific service pairs/actions as well. Protect private keys and specify certificate issuance/renewal and peer permissions. | Explicit individual change. Operational lifecycle/pair elaboration remains for review where not specifically validated; no application changes or tests authorized/claimed. |
| 2026-11-16T15:30:57Z | WS-C1 A | Direct WS → projects mTLS; authenticate specifically WS and permitted operations. WS delegates identity/expiry verified from the connection JWT with member-presented contexts; projects always decides permissions. | Explicit individual validation; any certificate of the CA is insufficient. D3 HS256 user JWT and gateway RS256 identity remain; rest of contract remains proposed. |
| 2026-11-16T15:30:57Z | WS-C2 A | Initial configurable total timeout 1 s covering wait/connect/send/read; up to 50 member/context evaluations per request. Multiple batches with limited concurrency/fair scheduling; no extension on failures/retries. Cutoff ≤5 s/target ≤2 s retained. | Individual validation, subject to measurement, not demonstrated capacity. Global concurrency value/other limits remain to size; no agreement attributed to other members or tests claimed. |
| 2026-11-16T19:49:16Z | WS-C3 A | Initial 4 simultaneous global authorization HTTP queries, 1 per project, alternating batches and 64 KiB UTF-8 JSON request/response bodies, jointly with 50 evaluations. Total 1 s includes queue; bound/coalesce pending work, overflow/late wait never renew or grant joins; no silent truncation. | Individual validation with conditions. Queue maximum/final corpus open. Four concurrent queries do not prove 4/s or twenty-project capacity. Test >20 projects and 500-member project plus small ones, fairness, byte boundaries and cutoff ≤5 s/target ≤2 s; no runtime proof. |
| 2026-11-16T19:49:16Z | PKI-C1 A | CA per installation 365 days; service-specific keys/certificates 30 days, renew with 7 days remaining. Include administrator-invoked local issuance/renewal script and verification in delivery, no background daemon. Startup/offline recovery before service; never issue beyond CA validity. | Individual validation. Keep 30 days rather than switch to 90; implementation still unauthorized. Source Git/build audit finds gaps (3 nonignored probes/6 tracked keys/7 broad-copy contexts), not proven exclusions. Revocation/trust withdrawal/persistent connections remain open. |
| 2026-11-16T19:49:16Z | ACL-C1 A | Only owner deletes entire project; editor retains editing/media removal, reader neither. Preserve authorized account cleanup, verify/hide non-owner UI actions and test disposable fixtures. | Explicit individual policy change: current DELETE accepts edit; RF53–RF55 do not unequivocally reserve DELETE to owner. Security-correction rationale recorded without claiming existing rule, runtime tests or other members’ approval. |
| 2026-11-16T20:14:36Z | WS-C4 A | Initial 16 pending batches/process besides 4 active, at most 1 pending/project; keep latest pending plan in the same slot, preserve original 1 s deadline, remove expired work and invalidate obsolete evaluations. | Explicit individual agreement. Complete superseded callbacks; preserve different members/contexts and bound hidden waiting. Queue capacity/justice/state costs remain unmeasured. |
| 2026-11-16T20:14:36Z | PKI-C2 B | Withdraw certificate trust by replacing installation CA and reissuing all certificates, removing old trust everywhere. Replaces initial CRL recommendation. Normal expiry renewal can retain CA; 365 days is maximum, CA may be replaced earlier. | Individual validation, medium-confidence complexity assessment, no benchmark. One compromised service causes whole-installation interruption/coordination. Old-CA rejection in new connections, closed old connections/resumption and no partial reopening are mandatory controls. |
| 2026-11-16T20:14:36Z | PKI-C3 A | Isolated maintenance/restart; before reopening verify complete WS → projects and projects → storage calls, remaining participants and rejected old CA after withdrawal. Partial installation stays isolated. Planned maintenance waits for idle; compromise isolates immediately. | Individual agreement only. PKI operational deadline, per-channel proof and emergency reconciliation remain open. WS 5 s/2 s is not PKI timing. No app changes or runtime tests claimed. |
| 2026-11-16T20:33:46Z | PKI-C4 B | Isolation ≤30 s/target ≤10 s from administrative command until new/persistent/internal connections, consumers and worker effects are cut; incomplete isolation reported without resetting clock. Measure replacement without imposed 15/5 min; failed replacement remains isolated. | Individual choice. User requires installation/load/real duration and a pilot deadline; set planning milestone 23 November 18:00 UTC. Valid pilot before delivery yields contextual empirical comparison criterion, not universal SLA. No measured duration or installation selected. |
| 2026-11-16T20:33:46Z | PKI-C5 A | Complete current/target channel matrix, automated probes and reproducible known-trust browser profile; no certificate-warning bypass counts as pass. Explicitly classify expand_ai_tool → generative-mock as internal mTLS API with actual implementation/test effort and rollback. | Individual validation. Runtime/termination and full channel proof pending; source HTTP client/Flask server are not protected by adding a row. Preliminary effort ranges remain engineering estimates, not approved availability. |
| 2026-11-16T20:33:46Z | OPS-C1 A | Implement/test administrative reconciliation by delivery; preserve evidence first, exclude indeterminate results from committed state and prevent duplicate quota correction across reapply/crash. Without evidence, pending; without tool/tests by 27 November, explicit limitation rather than capability. | Individual validation. Automatic recovery future, early ack known defect; consumer restart not proof of completion. No application changes or runtime recovery tests claimed. |
| 2026-11-17T11:53:34Z | SESS-C1 A | Assisted same-ID transition/reissue, registered login and 7-day absolute user JWT without refresh; anonymous future expiry still needs administrator and independent proof. No proof means pending/preserved data; issuance/import must be implemented/tested. | User recommends A for assistant confirmation; assistant technically confirms with conditions. Individual selection, not a fabricated literal whole-team validation. Concrete proof/browser inventory still pending; no credentials issued. |
| 2026-11-17T11:53:34Z | JWT-C1 A | Per-request contextual RS256 up to 30 s/session exp, admission only; exact recipient/issuer/type/method/path/peer, scoped downstream delegation. Same authorized peer/context reuse during validity is accepted residual; no generic anti-replay store or exactly-once claim. | Same individual recommendation plus technical confirmation. jti alone is not single-use; S07 separates invalid-context rejection from residual reuse. No implementation/capacity proof. |
| 2026-11-17T11:53:34Z | LINK-C1 A / D8 | Old and new links persist until explicit revocation, preserving RNF52 verified on PDF page 27. expiresAt/schema/UI/temporal migration deferred, superseding earlier communicated D8 preference. Revocation and WS revalidation remain. | Individual selection plus technical confirmation; high confidence in preservation, not a new test result or other members’ approval. Signed-media/upload TTL remains separate. |
| 2026-11-17T11:53:34Z | WS-C5 B | Initial 512 connections/4096 contexts including pending reservations; selected contract, room/context/rate/bucket/input limits. Above caps test controlled refusal/preservation, not supported load. Logical scenarios v1 normal/fairness/saturation fixed. | User recommends lower caps and assistant confirms medium-confidence proportionality. No demonstrated capacity. If physical corpus needs higher admitted concurrency, explicitly revise before freeze; personal-room emission controls/proof still required. |

The timestamp records when this validation was entered in the workspace; it does
not fabricate a separate team meeting or each member's approval. The roster below
identifies the team covered by the collectively communicated pair agreement;
it does not attribute separate personal statements or individual timestamps.
The earlier D6.1 entry records its then-open D6.2 state; the later rows update that
state without rewriting the historical first-group validation. Preference for
consultation over tickets is a technical inference, not a benchmark result.
The latest three entries close the previously open permanence mechanism, cutoff,
failure policy and active JWT expiry at individual-validation level. Authenticated
contract/timeout, access-context representation, batch limits, ordering/join races,
session transition/renewal and experimental proof remain pending. They do not
approve the remaining metrics or replace the full requirements/team review.
The subsequent D4/WS-C1/WS-C2 entries supersede the open state of the service trust
choice and initial timeout/batch parameters. The rest of the WS contract is still
proposed; issuance/renewal/revocation parameters, pair coverage and concrete
ordering/scheduling remain to review. No certificate/key was generated or app changed.

The later WS-C3/PKI-C1/ACL-C1 rows fix the initial concurrency/body limits,
certificate durations/renewal threshold and whole-project deletion policy. Earlier
open-state statements above retain their historical scope. Remaining queue size,
load corpus, certificate revocation/persistent connections and WS contract details
are still open; engineering choices do not demonstrate capacity/compliance. The
manual PKI script/checks are delivery scope, not implemented in this planning task.

The [team review packet](team-review.md) provides the proposal to discuss against
evidence commit `793df2e`. This record remains the single source for actual team
agreement; the packet's recommendation and numerical options are not approvals.

| Field | Current value |
|-------|---------------|
| Reviewed document revision / commit | Pair text and source statement above; no jointly reviewed commit was supplied. Application evidence revisions remain identified separately. |
| Experiment records and limitations | [Live findings available](live-findings.md): candidate upload/queue/progress/access measurements and one recovery scenario, plus prior processor/helper probes. Broader evaluation limits are explicit. |
| Selected requirement 1 / metric | QC-06 Security: end-to-end authorization (confidentiality/integrity/authenticity); S01–S24 and affected guards in the measurement plan, remaining gates still under review. |
| Selected requirement 2 / metric | QC-05 Performance efficiency: upload resource utilization; U01–U26 and affected guards; memory thresholds still proposals, formal baseline incomplete. |
| Rationale and rejected alternatives | Authorization exposure/effects and high upload memory/OOM are observed. Distinct quality areas, independent evaluation and functional preservation. Six directions/15 pairs remain documented above; reliability/capacity/modularity/usability alternatives and limits are explained in the historical team packet and current decision rationale. No claim of measured lowest implementation effort. |
| Estimated effort and available resources | Delivery corrected by the user to 27 November 2026, superseding the previous 20 November planning date; team hours and participants remain unknown. Local Docker images available; investigation protocols prepared. |
| Functional-preservation checks | To specify for the selected paths |
| Whole-team agreement | Pair agreement recorded as communicated by the user, 2026-11-16T15:12:33Z; limited to the stated pair, without separately collected nominal declarations. |

| Team member | Student number | Pair agreement provenance | Separate nominal statement / reviewed revision |
|-------------|----------------|---------------------------|-----------------------------------------------|
| Luís Miguel Coelho | PG64000 | Collective agreement communicated by the user; source above | Not separately supplied |
| Alexandre de Oliveira Monsanto | PG65397 | Collective agreement communicated by the user; source above | Not separately supplied |
| Diogo Alexandre Gomes Silva | PG63941 | Collective agreement communicated by the user; source above | Not separately supplied |
| José Miguel da Silva Santos | PG63522 | Collective agreement communicated by the user; source above | Not separately supplied |

The source of agreement is the user's later explicit instruction to record it,
not earlier exploration requests or silence. No messages have been sent to other
team members. Changes to the selected pair or material scope require renewed
agreement; remaining details and full requirements review are still outstanding.

## Operational Choice Follow-up — A/B/A Individually Validated

The user answered the operational review with **WS-C4 A, PKI-C2 B, PKI-C3 A**.
The [operational contract/runbook](../../../docs/architecture/fase2-fila-ws-e-revogacao.md)
records conditions, acceptance controls, costs and remaining details. The earlier
assistant recommendation PKI-C2 A/local CRL is superseded by B, not adopted by
silence. Normal renewal and immediate trust withdrawal are distinguished; replacing
a CA affects all participants and still requires distribution/connection tests.
This later validation resolves the earlier pending-choice state. It does not
approve the full requirements, imply a measured short outage or attribute agreement
to the other members. Channel proof, PKI timing, emergency work reconciliation and
remaining WS/session/upload details stay open. No application changes or new
runtime tests were made.

## Operational Criteria Follow-up — B/A/A Individually Validated

The user selected **PKI-C4 B/PKI-C5 A/OPS-C1 A** with conditions. The
[criteria contract](../../../docs/architecture/fase2-criterios-operacionais-seguranca.md)
now specifies isolation endpoints/failure classification, a 23 November 18:00 UTC
pilot planning milestone and mandatory environment/load/duration/evidence records,
current/target state per channel, browser methodology, mock mTLS implementation/
rollback effort and implemented/tested administrative recovery (or delivery limitation).
The earlier 15/5-minute replacement recommendation is superseded, not validated.
A measured pilot before delivery provides a contextual comparison criterion; no
result has been invented. Installations/load, concrete isolation/termination,
reconciliation tooling and runtime verification remain incomplete. The choice does
not approve the full requirements or attribute agreement to the other members.

## November 17 Security Selection — A/A/A/B Technically Confirmed

The user recommended **SESS-C1 A/JWT-C1 A/LINK-C1 A/WS-C5 B** for confirmation;
the assistant technically confirmed the combination with the stated conditions.
The [contract/scenarios v1](../../../docs/architecture/fase2-sessoes-identidade-partilhas-ws.md)
records this provenance, future anonymous-expiry assistance, independent proof,
implemented/tested issuance/import, accepted contextual identity reuse, indefinite
links per RNF52 and controlled refusal above 512/4096. Logical scenarios distinguish
normal 50, fairness 510, many-project 200 and excess-cap attempts; physical manifest/
corpus and anonymous proof are still pending. D8 is now updated, not silently left
as expiry implementation work. Personal-room event emission also needs context/
authorization/cutoff implementation and tests. No runtime leak result is claimed.
This does not approve full requirements, confer whole-team detail agreement or
claim deployed security/capacity. No application/data changes or migration occurred.

## Anonymous Recovery Detail — Evidence Unknown, No New Selection Inferred

The user selected procedure concretization and explicitly said they do not yet
know whether a reliable independent identity/browser association record exists.
Record unknown, not evidence present/absent. The [working procedure](../../../docs/architecture/fase2-recuperacao-anonima.md)
and [empty case template](../../../docs/templates/anonymous-session-recovery-case.template.json)
detail eligibility, local administrative authority, issuance/import and bootstrap/
callback conflicts, 12 planned tests and implementation effort. No record was
approved, JWT issued or real browser/data inspected. This elaborates SESS-C1 A;
it does not add a new claimed individual validation, completed proof or construction
approval. Both retained datasets remain preserved and unselected for evaluation.

## Evaluation Preparation — Host Selected, Protocol Still Proposed

On November 18 the user chose evaluation preparation and this machine/Luís as
host. The [evaluation plan](../../../docs/fase2-plano-avaliacao.md) and empty
manifest/result templates consolidate all 60 metrics, scenarios/repetitions,
minimums/targets, baseline/final comparability and report rules. A host-only
resource readout is archived; no application metrics were collected. Isolated
synthetic deployment/budgets/corpus remain proposals, preserving both retained
volume sets and the existing security/upload decision states. Host selection
is individual; it neither freezes the campaign nor approves the whole requirement
baseline. The former six-direction protocols remain historical exploration.

## Evaluation Review — Individual A/A/A/A Selection with Conditions

User requested plan review. The [review](../../../docs/fase2-revisao-plano-avaliacao.md)
records the subsequent individual EVAL-B1/C1/R1/M1 A selection with conditions,
resource/retention arithmetic and disk floor at least 60 GiB. U25 is now G;
exact M1 scope is enumerated, other criteria keep prior status. Calibration,
physical freeze and BF/MF remain open; no whole-team approval or runtime capacity
inferred. UP-C1/C2/C3 were later individually selected on their own source;
UP-C4–C9 remain proposals in the [lifecycle](../../../docs/architecture/fase2-upload-ciclo-vida.md).

## Upload First Group — Individual A/A/A Selection

User recommends UP-C1/C2/C3 A with explicit conditions; assistant confirms
technically and records individual selection. Preserve bounded multipart
compatibility, charge only Apply and separate controlled attempts/staging, with
shared final authorization/validation/commit and real resource/failure tests.
The [lifecycle](../../../docs/architecture/fase2-upload-ciclo-vida.md) proposes
remaining states/deadlines/retry/candidate arbitration/hash/probe/cleanup and 12
UL cases; none of UP-C4–C9 or its numbers is inferred selected. No runtime proof,
whole-team agreement or app/data changes. Prior EVAL/60 metric/U25 G states retained.

## Traceability and AI Assistance

This exploration extends the [draft requirements](requirements.md) and is tracked
in the [Inception log](inception-log.md). It does not change the completed Exercise 6
diagnosis or imply that its two architectural alternatives are the only possible
solutions. Reference PDFs, assignment HTML, support HTML and architecture diagrams
remain accessible through the [documentation index](../../../docs/README.md).

Codex, using the local
[specsmd-inception-agent skill](../../../.codex/skills/specsmd-inception-agent/SKILL.md),
prepared this qualitative comparison and investigation procedure from existing
project evidence and targeted source reads. Subsequent AI-assisted exploratory
scripts, raw results and validation are documented in the
[evidence index](evidence/README.md). Team review, final requirement evaluation,
full quantitative requirement approval remain pending. Pair selection is recorded
above from the user's explicit instruction; neither that agreement nor the
individual validations approve all remaining details.
