---
intent: 001-phase-2-quality-improvements
phase: inception
status: draft
created: 2026-11-14T17:16:06Z
updated: 2026-11-14T18:19:23Z
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
participant usability remain pending. No final requirements or team approvals
are recorded.

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
   the [live findings](live-findings.md) now provide provisional discussion pairs;
   no pair is selected or approved.
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

## Decision Record — Pending

The [team review packet](team-review.md) provides the proposal to discuss against
evidence commit `793df2e`. This record remains the single source for actual team
agreement; the packet's recommendation and numerical options are not approvals.

| Field | Current value |
|-------|---------------|
| Reviewed document revision / commit | Pending |
| Experiment records and limitations | [Live findings available](live-findings.md): candidate upload/queue/progress/access measurements and one recovery scenario, plus prior processor/helper probes. Broader evaluation limits are explicit. |
| Selected requirement 1 / metric | Pending |
| Selected requirement 2 / metric | Pending |
| Rationale and rejected alternatives | Pending |
| Estimated effort and available resources | Delivery on 20 November confirmed by the user; team hours and participants unknown. Local Docker images available; investigation protocols prepared. |
| Functional-preservation checks | To specify for the selected paths |
| Whole-team agreement | Not recorded |

| Team member | Student number | Decision / concerns | Reviewed revision | Timestamp |
|-------------|----------------|---------------------|-------------------|-----------|
| Luís Miguel Coelho | PG64000 | Pending | Pending | Pending |
| Alexandre de Oliveira Monsanto | PG65397 | Pending | Pending | Pending |
| Diogo Alexandre Gomes Silva | PG63941 | Pending | Pending | Pending |
| José Miguel da Silva Santos | PG63522 | Pending | Pending | Pending |

The agreement record can be completed from an explicit team review or meeting
record provided in this workspace. No approval is inferred from the user's request
to explore options, and no messages have been sent to other team members. Changes
to the selected pair or material scope require renewed agreement from all four.

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
final selection and quantitative requirement approval remain pending.
