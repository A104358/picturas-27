---
intent: 001-phase-2-quality-improvements
phase: inception
status: draft
created: 2026-11-14T17:31:51Z
updated: 2026-11-14T17:31:51Z
---

# Investigation Plan for the Six Quality Directions

## Scope and Confirmed Constraints

The user selected continuation of the exploration and confirmed delivery on
20 November 2026. Team hours and access to usability participants are still
unknown. This plan defines bounded investigations before the team chooses two
requirements. It does not approve requirement targets or architectural changes.

The current source revision is `5678c7cecca1e78ad54ce80e68a3f8f8988bd125`.
`git diff 484be13 HEAD --name-only` restricted to application code, Compose and
RabbitMQ configuration returned no changes. The previous architectural diagnosis
therefore remains structurally relevant; its historical runtime results still
need to be distinguished from the new experiments.

At inspection, `docker compose ps` listed no running services for this project.
Local application images are available. The new video experiment ran in a separate
temporary container without application volumes or network access. It used current
source mounted read-only, a fixed image ID, 2 CPU and 1 GiB of memory. No stack was
started, scaled or interrupted, and no existing application data were changed.

See the [evidence index](evidence/README.md) for commands, hashes, raw results,
the local acknowledgement-order demonstration and the host regression run.

## Coverage of the Teaching Guidelines

The six broad QC directions are an exploration aid rather than a restriction on
which two concrete RNFs the team may define. In particular, pipeline creation and
background work are separate usability scenarios within QC-04. They must not be
merged into one vague success metric.

| Indicative idea in the guidelines | Investigation coverage |
|----------------------------------|------------------------|
| Usability of pipeline creation | QC-04a: applicability, ordering and validation of existing tools. |
| Modularity of video processing | QC-03: internal modularization versus distributed effects. |
| Elasticity | QC-02: first measure capacity and resource headroom; distinguish a fixed worker pool from dynamic elasticity. |
| Working in the background | QC-04b: existing processing feedback, navigation, refresh and cancellation behavior. |
| Large-file uploads | QC-05: memory cost and acceptance of valid files through the existing route. |
| Internal security | QC-06: reachable boundaries, caller identity, authorization and exposure. |
| Additional diagnosis-based direction | QC-01: processing failure/recovery windows and coherent results. |

The [15-pair comparison](quality-exploration.md#comparison-of-all-candidate-pairs)
covers pairs between the six broad directions. Two distinct requirements within
one direction, such as QC-04a and QC-04b, can also be considered if each is specified
and evaluated separately. The guidelines do not require different ISO top-level
characteristics. Neither the pair table nor ALT-1/ALT-2 exhausts the possibilities.

## Evidence Acquired in This Exploration

| Direction | New evidence or renewed inspection | What remains unproven |
|-----------|------------------------------------|-----------------------|
| QC-01 | The real Node AMQP helper, evaluated with a fake transport, called `ack` while an asynchronous callback was still pending. Video manual ack, non-persistent publication and shared execution paths were rechecked. | Broker/database crash outcomes, loss frequency, duplicate commits and recovery time. |
| QC-02 | One configured video service and prefetch 1 were confirmed. Twelve processor runs completed in a fixed-resource isolated container, across ordinary/preview/extraction cases. | Queueing, concurrent capacity, real Whisper contention, benefits of replicas or dynamic scaling. |
| QC-03 | Eight ordinary effects in `FRAME_EFFECTS` and their image-tool counterparts were confirmed; video processing has internal modules but shares deployment. | Maintenance-task effort, change propagation and the benefit of internal extraction versus ALT-1. |
| QC-04 | Tool visibility, browser-local progress, overlay and percentage-triggered updates were rechecked. Local callback timings were captured by the processor probe. | User task success/comprehension, browser refresh/navigation behavior in a live session and WebSocket event cadence. |
| QC-05 | Memory-backed upload handling was confirmed in gateway, projects and storage. Source limits distinguish free and premium uploads. | Peak memory, disconnect cleanup, successful concurrency envelope and upload latency under controlled load. |
| QC-06 | Gateway JWT verification contrasts with internal caller-header trust and JWT decoding; storage routes lack equivalent authentication middleware and internal ports are published. | Reachable cross-owner read/write bypasses under the actual deployment and correctness of any proposed enforcement. |

The host video suite passed 74 tests. Its fake recognizer does not evaluate real
speech recognition. Local processing kept the original input hash unchanged and
rejected the corrupted sample without leaving its target output. These observations
support a functional checkpoint, not operational reliability or whole-system RNF
compliance. No final quality requirement has yet received a measured baseline.

## Common Measurement Contract

Before each investigation, record the source commit, working-tree differences,
image IDs, service topology, CPU/memory budgets, dependency versions, input hashes,
profile and quotas, tool sequence, repetitions and collector version. Separate cold
model loading from warm processing. Record failures and timeouts in the denominator;
do not retain only successful samples.

Use synthetic accounts and projects. Preserve baseline data and use separate
deployment names, storage and work paths for fault/concurrency experiments. Check
for explicit `container_name` or fixed host-port conflicts before assuming that a
different Compose project name alone creates isolation. Do not wipe shared volumes.

Instrument only what the selected metric needs. If measurement requires tracing,
keep that instrumentation equivalent before/after and record its overhead. Define
clock origins: timestamps from different processes need a common clock or a
documented synchronization error. An HTTP 201 means dispatch was accepted by the
application; it is not a committed result or a broker publisher confirmation.

Three repetitions are used for the current processor pilot. This is a proposed
exploration setting, not a final sample size or target. For final measurements,
choose repetitions after observing variability and available time. Report raw
values and distributions; a p95 from three samples is not useful evidence.

Every final requirement needs its own metric/unit, scenario, measured baseline,
target, minimum acceptable value, numerical origin and adverse-effect checks.
Those fields remain open until evidence and stakeholder decisions justify them.

## QC-01 Protocol: Processing Recovery

**Candidate scope:** One ordinary video batch initially; add extracted-frame output
if the chosen recovery boundary includes result cardinality. Keep image behavior
in the regression scope. Grounding: `REQ-VID-FAIL-004`, H-03 and H-12.

**Stimulus:** A defined interruption after application acceptance and before the
result is committed. Treat malformed input and handled processing exceptions as
separate scenarios from abrupt process/broker termination.

**Measurements:** For each interruption point, record accepted jobs, correct
committed successes within a stated recovery window, terminal failures, unfinished
jobs, extra result sets, quota discrepancies and time to recovery. Report recovery
fraction as `correct recovered successes / accepted valid interrupted jobs`.
Expected frame counts belong to correctness, not to the duplicate-result count.

**Execution:** Use a disposable deployment; map dispatch, worker response and
orchestrator persistence boundaries. Reproduce the same cut points before/after.
Observe `Process`, `Result`, active/committed tokens, file generations and quota.
Include a no-interruption control. A caller-visible failure is not counted as
successful recovery of valid work, even if it is a coherent terminal state.

**Options to compare:** Await asynchronous persistence before acknowledgement;
publisher confirmation/persistence with bounded retry; idempotent completion and
work paths scoped to an execution. Distributed effects add more boundaries and
need separate justification. The current acknowledgement demonstration only
establishes that a failure window exists in the helper's execution order.

**Target / minimum / baseline:** Pending; do not inherit the overall EDIT-012 success
percentage as a fault-recovery threshold without defining the fault model.
**Guardrails:** Normal latency, duplicate work, cleanup, quota and cancellation.

## QC-02 Protocol: Capacity and Elasticity

**Candidate scope:** Independent video projects under a fixed resource envelope.
Grounding: `REQ-VID-EDIT-011`, H-02, H-08 and H-12. Full dynamic elasticity is a
separate, broader option than a fixed competing-consumer pool.

**Workloads:** Ordinary editing; extraction; a short real-speech segment; and a mixed
batch with a heavy job before ordinary jobs. The supplied 176.621 s speech sample
exceeds the free duration limit: use a properly identified short derivative or
a dedicated premium account. Record any derivative's source, license, command,
duration and hash. Do not silently raise limits or bypass quota for a benchmark.

**Measurements:** Count committed correct outputs and wall time from first batch
dispatch to final commit. Throughput is `successful videos / elapsed minutes`.
Collect dispatch-to-worker-start, worker execution and dispatch-to-commit separately;
the first is a queueing proxy if publication/delivery overhead is not isolated.
Also sample CPU and memory, errors and cross-project fairness. A terminal extraction
job counts as one video job regardless of the number of output frames.

**Execution:** First measure unchanged topology. Assess headroom before testing a
bounded two-consumer variant. Resolve the known shared-path risk before simultaneous
Apply on the same project; a stress variant must not corrupt baseline files. Use
the same total CPU/RAM budget when comparing designs, or explicitly report that
the experiment measures added resources rather than architectural efficiency.

**Elasticity variant:** If selected, define the workload ramp, scale-up/down policy,
settling time, resource ceiling and scale actions. Compare with a static baseline
at a stated budget. Merely starting two replicas is not dynamic elasticity.

**Target / minimum / baseline:** Pending. The source's conditional two-video MVP and
simple-edit duration factors are source criteria, not approved team targets for
this workload. The processor pilot does not measure queue throughput or elasticity.
**Guardrails:** Audio/frame equivalence, file isolation, memory and failed jobs.

## QC-03 Protocol: Modularity and Change Impact

**Candidate scope:** Maintenance of existing ordinary effect logic, or isolation of
the existing subtitle stage. Choose one primary maintenance scenario. Grounding:
`REQ-VID-EDIT-013`, EV-18, EV-19 and H-04.

**Measurements:** Number of implementation modules and deployable services touched,
dependency/rebuild scope, regressions and elapsed task effort. Count production
changes separately from tests and packaging. Lines changed alone are insufficient
evidence; splitting files can improve the count without improving isolation.

**Execution:** Define an equivalent correction to an existing effect and a checklist
before doing it. Use separate branches/patches on the baseline and refactored
architecture; retain both diffs and results. Counterbalance developer/task order
where feasible and record learning/tooling bias. The temporary maintenance task
must not add a feature to the delivery.

**Options to compare:** Internal pure-effect boundary/shared code; an adapter between
transport and processing; independently deployed stage services (ALT-1). Evaluate
packaging and contract overhead as well as module independence. Shared effects
must preserve parameter validation and image/video rendering behavior.

**Target / minimum / baseline:** Pending. Do not report eight registered effects as
a maintenance-effort baseline or promise an automatic benefit from more services.
**Guardrails:** Ordinary decode/encode passes, pixel behavior, audio and stage order.

## QC-04 Protocol: Two Separate Usability Scenarios

**QC-04a — configure pipelines:** Ask participants to build an image-only and a mixed
pipeline with the existing catalog, include per-video trim/speed, and explain why
an image-only effect is unavailable. Include extraction ordering. Count independent
task completion, invalid attempts, time and correct explanations. Grounding:
H-06 and the pipeline-creation idea in the guidelines.

**QC-04b — background operation:** Start a deliberately long supported job, navigate
within the application, reload, identify its state and exercise existing cancel
behavior. Define observable success criteria before the session. Separately capture
Socket.IO event arrival times, including dispatch-to-first-event and final-event-
to-completion gaps. Grounding: `REQ-VID-STATUS-003`, `REQ-VID-EDIT-002`,
`REQ-VID-CANCEL-001/002`, EV-23, EV-25 and H-10.

**Execution:** Record participant experience, task order, assistance and failures.
Counterbalance before/after ordering where possible. Team-only trials must be
reported as a pilot. Participant availability remains unknown. Source inspection
and local callback timestamps cannot replace a browser session or user study.

**Options to compare:** Explain existing tool applicability and validate earlier;
present processing state without the blocking overlay; recover existing job state
after reload. Confirm scope against the guidelines, which allow visible usability
improvements. Do not add new editing capabilities or claim that logical cancellation
already terminates FFmpeg/Whisper. If a requirement changes actual cancellation,
describe and validate that semantics explicitly.

**Target / minimum / baseline:** Pending for each subscenario. Source intervals
of 5 s (MVP) and 2 s (target) are for progress, not user task-completion thresholds.
**Guardrails:** Accessibility, quota visibility, collaboration and truthful errors.

## QC-05 Protocol: Upload Memory

**Candidate scope:** Existing video upload through nginx, gateway, projects and
storage. Keep ZIP export outside the selected requirement unless explicitly
included with its own workload. Grounding: H-05 and `REQ-VID-SUBMIT-008`.

**Workload:** Generate valid duration/resolution/codec-compliant files at increasing
sizes and controlled concurrency. Initial proposed pilot sizes are 10 and 50 MiB
for a free profile; larger files require a premium test account and enough memory.
These are experiment parameters, not acceptance targets. Record exact byte sizes;
the implementation uses its own MB conversion. Preflight profile limits before
any large request and retain a separate intentionally invalid case.

**Measurements:** Sample each affected process's idle and peak RSS, and each
container's memory over the whole transfer. Report `peak RSS - idle RSS` per process,
plus synchronized aggregate samples if needed. The sum of independent per-service
maxima is not a measured simultaneous peak. Container memory may include children
and caches and is not interchangeable with Node RSS.

Record total upload response time, completion/failure, ownership and stored object
integrity. If measuring post-send acceptance, define the client/server byte-completion
timestamp carefully; client writes can still be buffered by nginx or the network.
Measure the same path and input rate before/after. Record the sampling period so
short peaks are not silently missed.

**Options to compare:** Streaming with backpressure versus bounded disk spooling.
Inspect nginx buffering and validation-before-forwarding constraints. A full
multipart buffer can remain upstream even if the last hop streams.

**Target / minimum / baseline:** Pending; the source's <3 s/<1 s post-send values
do not establish a RAM budget. **Guardrails:** Validation, partial-upload cleanup,
disconnects, ownership, storage I/O and supported API responses.

## QC-06 Protocol: Authorization Boundary

**Candidate scope:** Pick a concrete read/write boundary, such as direct storage
access versus the authenticated project route, and state the attacker's reachability.
Grounding: inherited RNF44, `REQ-VID-ACCESS-002`, EV-24 and H-07. TLS validation,
secret handling and published ports are related options, not one unlimited RNF.

**Matrix:** Two synthetic owners with separate projects; authorized owner, unrelated
user, missing/invalid token and forged caller header; gateway route versus reachable
direct route; read versus write. Add valid/revoked sharing as explicit positive/
negative controls. Classify deliberately public share resolution and unexpired
signed URLs according to their intended contract before calling them a bypass.

**Measurements:** Record permitted unauthorized reads/writes, prevented unauthorized
actions over defined attempts, and authorized success. Report test-case identities
and response semantics, not only a percentage. Network blocking is an acceptable
boundary control only under the stated threat model; connection failure does not
demonstrate application-level authorization. Host exposure and Docker-network
access are different threat surfaces.

**Options to compare:** Reduce unnecessary host exposure; verify internal callers;
enforce ownership at the selected service boundary; validate certificates. Identify
all legitimate gateway, worker, WS, sharing and storage paths before changing them.
Do not expose real credentials in evidence or use third-party user data.

**Target / minimum / baseline:** Pending; any proposed zero-unauthorized-action
criterion applies to the defined matrix, not a claim of complete security.
**Guardrails:** Authorized functionality, signed download expiry and latency.

## Feasibility and Decision Preparation

The following scope assessments are qualitative inferences from affected paths,
not measured effort or stakeholder scores. None is a selected or excluded direction.

| Direction | Narrow investigation available | Main prerequisite | Scope risk to discuss |
|-----------|--------------------------------|-------------------|-----------------------|
| QC-01 | Acknowledgement-order demonstration completed | Disposable services and deterministic interruption points | Recovery can cross publication, persistence, files and quota. |
| QC-02 | Processor pilot completed | Live queue, headroom, safe work paths and real-speech setup | A worker pool is narrower than full dynamic elasticity. |
| QC-03 | Register/dependency inspection completed | Comparable maintenance task and reviewer | ALT-1 adds contracts, deployment and recoding risks. |
| QC-04 | UI/state inspection completed | Running browser and participants | Pipeline clarity and background operation need separate measures. |
| QC-05 | Buffering path inspection completed | Live transfer, memory collector and valid corpus | Streaming can shift buffering upstream or add disk cost. |
| QC-06 | Trust-boundary inspection completed | Isolated deployment, synthetic owners and expected access matrix | Broad security reform is larger than one enforced boundary. |

Before shortlisting, have each team member review stakeholder impact, evidence
strength, measurable outcome, implementation complexity, effort, functional risk
and adverse effects. Record a reason for keeping/deprioritizing each option.
Avoid invented numeric weights while stakeholder priorities and available hours
remain unknown. Shared prerequisites do not remove the need for two independent
quality evaluations.

Proposed sequencing relative to delivery: use the next exploration session to
close environment and workload gaps; choose the pair with the four members early
enough to preserve time for initial measurements, refactoring and evaluation;
reserve the last working day before submission for repeated measurements and
report/evidence review. These are planning suggestions, not agreed team dates.

## Remaining Decisions

- Available person-hours, participants and resource budget.
- Live baseline deployment and measurement corpus for the retained candidates.
- Evidence-based shortlist and agreement from all four members.
- Final two quantitative RNFs, numerical origins and regression scope.

The [team decision record](quality-exploration.md#decision-record--pending) remains
pending. Investigation and instrumentation can continue without selecting a pair.
Construction planning follows approved requirements; this exploration does not
create units, stories or implementation bolts prematurely.
