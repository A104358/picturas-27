---
intent: 001-phase-2-quality-improvements
phase: inception
status: draft
created: 2026-11-14T18:06:50Z
updated: 2026-11-16T15:51:14Z
---

# Live Exploration Findings and Decision Brief

**Historical findings:** The user later corrected delivery to **27 November
2026**. The 20 November date below belongs to the original experiment context;
use the corrected date for current planning. Measurements are unchanged.

## Scope and Reproducibility

This is initial empirical evidence for candidate requirements, not a selected pair
or an approved final specification. Delivery remains 20 November 2026. Team hours
and usability participants have not been supplied.

Source revision: `24484b7` (planning commit). The application sources are unchanged
from the preceding diagnosis. SHA-256 comparison of 182 source files across seven
running application services found no differences from the checkout. Image IDs,
resource limits and deployment changes are recorded in the
[sanitized stack manifest](evidence/live-stack-2026-11-14.json) and
[source comparison](evidence/live-source-hashes-2026-11-14.json).

The experiment used 13 services on a separate internal Docker network, with new
project-scoped volumes. The slice included nginx, frontend, both gateways, users,
projects, image storage, SeaweedFS, RabbitMQ, the two relevant MongoDB instances,
the video worker and brightness image worker. Billing, backup and unused effects
were omitted. No existing application volumes or other projects were changed.
The 13 services were stopped after measurement; experiment volumes were retained.

The video worker had 2 CPU and 1 GiB; the final load generator had a separate
1 CPU / 512 MiB container. Other per-service limits are in the manifest. Services
were warm after preliminary trials, with no forced GC or cold-cache reset. Results
therefore describe this bounded setup, not the unrestricted default deployment.

The authoritative run is [live-api-isolated-2026-11-14.json](evidence/live-api-isolated-2026-11-14.json).
Its [raw resource series](evidence/live-resources-isolated-2026-11-14.jsonl.gz)
contains 5,369 samples, with median interval 50.223 ms and maximum 80.405 ms.
[Derived measurements](evidence/live-analysis-2026-11-14.json) can be regenerated
with the [analysis script](evidence/analyze-live-results.py).

## Upload Memory: QC-05

The client uploaded valid 10 s / 1280×720 / 30 fps MP4/H.264/AAC files padded with
an MP4 `free` box to exactly 10 and 50 MiB. This controls transferred bytes while
holding content/probe characteristics constant; it does not represent a natural
video bitrate distribution. Both uploads returned HTTP 204 through nginx and the
API gateway. Total request times were 589 ms and 2,462 ms, respectively. These are
not post-send acceptance times.

Node RSS observations below use the median of the 500 ms before the request and
the maximum from request start through 500 ms after its response. Units are MiB
(1,048,576 bytes). Each size has one final observation; no percentile is claimed.

| File size | Service | Pre-request RSS (MiB) | Observed peak RSS (MiB) | Increase (MiB) |
|-----------|---------|-----------------------|-------------------------|----------------|
| 10 MiB | API gateway | 175.65 | 199.17 | 23.52 |
| 10 MiB | Projects | 172.55 | 172.85 | 0.30 |
| 10 MiB | Storage facade | 100.03 | 110.34 | 10.32 |
| 50 MiB | API gateway | 179.29 | 334.16 | 154.88 |
| 50 MiB | Projects | 172.85 | 224.86 | 52.01 |
| 50 MiB | Storage facade | 110.34 | 180.16 | 69.81 |

The observation supports investigation of repeated full-buffer handling across
services. It does not establish a linear memory formula or a safe concurrency
limit. Warm allocator reuse explains why a small increment can coexist with a
large retained RSS; the exact allocation mechanism was not heap-profiled. Independent
per-service maxima must not be summed and presented as a measured simultaneous
peak. Cgroup memory, which also includes cache/children, is retained separately.

**Next bounded requirement option:** Limit the peak memory cost of valid uploads
through this route at specified sizes/concurrency, retaining validation and
ownership. Streaming and bounded disk spooling remain alternatives. Targets and
minimum acceptable values need justification and team agreement.

## Internal Access Boundaries: QC-06

The finite matrix used two synthetic free accounts and separate ownership. It
measures access from inside the experiment's Docker network. Host connections to
published loopback ports were refused by this internal-network deployment, so this
experiment does not demonstrate host/internet reachability of the original stack.

| Case | Expected boundary | Observed response / outcome |
|------|-------------------|-----------------------------|
| Owner JWT through gateway | Permit | 200; project returned. |
| Missing JWT through gateway | Reject | 401; project not returned. |
| Invalid JWT through gateway | Reject | 401; project not returned. |
| Other owner's JWT through gateway | Reject | 401; project not returned. |
| No identity at direct project route | Reject | 401. |
| Other owner's JWT at direct project route | Reject | 200; target project returned. |
| No token at direct storage signer | Reject | 200; returned URL downloaded the actual source bytes, verified by SHA-256. |
| No token at direct storage upload | Reject | 201; an unlinked synthetic marker object was added under the owner's prefix. |

The [supplemental probe](evidence/live-access-supplement-2026-11-14.json) also
observed HTTP 200 and target-project data with an `X-Caller-Id` header claiming the
owner and no bearer token. Thus the issue is a demonstrated internal trust boundary,
not just the existence of published ports or a hypothetical unsigned identity.
The write probe added an object; it did not demonstrate overwrite/delete of an
existing object. Signed URLs, tokens, passwords and file contents are excluded
from the persisted evidence.

**Next bounded requirement option:** Enforce a stated identity/ownership boundary
for direct project/storage access and preserve authorized gateway, sharing,
worker and signed-download paths. Hiding host ports alone would not address this
Docker-network threat model. TLS and secret management remain separate scope choices.
Success over this finite matrix cannot prove complete system security.

## Queueing and Capacity: QC-02

Three independent free accounts each submitted a project containing three 10 s
videos and one project-wide brightness operation. All batches yielded three
committed video results. Quota went from 5 to 2 in each account. The client polled
results every 100 ms, adding observation/request overhead to the commit time.

| Batch | Dispatch-to-observed-commit (s) | Observed videos/min | Mean video-worker CPU cores |
|-------|---------------------------------|---------------------|-----------------------------|
| 1 | 43.362 | 4.151 | 1.967 |
| 2 | 45.001 | 4.000 | 1.967 |
| 3 | 42.665 | 4.219 | 1.951 |

There were nine committed results; one result per batch was downloaded and probed.
All three samples were 10 s MP4/H.264/AAC and had the same output SHA-256 for the
same generated input. Codec correctness was not individually probed for all nine.
Peak video-container memory was approximately 566–574 MiB, including charged cache.

The AMQP tap recorded one request and response per video. Worker execution was
approximately 13.2–16.0 s per job. The last job in a batch had a non-processing
request-to-response residual of approximately 28.3–30.5 s. This residual includes
queueing and delivery/publication overhead; it is not a pure queue-wait trace.
One first-job residual was -0.184 ms, consistent with timestamp/measurement
granularity, and remains in the raw data rather than being clamped to zero.

The single worker was close to its 2-CPU ceiling. These results support a queueing
and capacity investigation, but do not show that replicas improve throughput under
the same total budget. No scaling or real Whisper processing was performed. A fixed
pool and dynamic elasticity remain distinct options.

## Progress and Operability: QC-04

An authenticated Engine.IO/Socket.IO polling client received 51 progress events
per video in the authoritative normal run. Progress was monotonic and ended at
100 for all nine jobs. The maximum observed interval between successive progress
events of an active video was below 0.6 s in this workload. The first progress for
the last queued video arrived approximately 29.5–31.4 s after batch dispatch.
Project-wide event gaps including dispatch/completion boundaries were 0.908–1.305 s.

These are different metrics: frequent events from an active job do not show that
every queued media item receives timely progress. Requirements must explicitly
define whether queue wait, speech recognition and completion persistence count.
The supplied 5 s/2 s values must not be applied to a different interval silently.

A fresh connection after each completed batch observed no historical event replay
in approximately 0.8 s. This narrow observation does not establish what a browser
can recover after refresh during active processing. No rendered-browser task,
navigation/cancellation trial or participant study was conducted. Pipeline creation
and background operation remain separate usability candidates in the plan.

## One Worker-Recovery Scenario: QC-01

The [recovery controller/result](evidence/live-recovery-2026-11-14.json) records an
abrupt kill after early progress of a synthetic 30 s video. It verified the target
worker's experiment label before interruption. Before restart, the queue showed
one ready request and zero consumers. The controller then restarted the same worker.
This is an explicit restart action; the experiment disabled automatic restart and
did not evaluate restart-policy availability.

Observed outcome: one successful response to one published request, one committed
MP4/H.264/AAC result of 30 s, no pending `Process` records, matching active/committed
token 1, and quota 4 after starting at 5. The stored original's SHA-256 was unchanged.
Completion was observed approximately 26.3 s after the controller's restart returned.
Progress fell from 3% to 1% after restart, which should inform progress-state design.

This case supports the existing worker's manual-ack recovery behavior. It does not
cover failure after response publication, orchestrator persistence, a broker crash,
handled errors, duplicate publication or concurrent Apply. In particular, it does
not remove the separate acknowledgement-order finding in the Node helper or prove
exactly-once execution. A recovery rate cannot be inferred from one interruption.

## Modularity and Functional Checks: QC-03

The source/deployment evidence for eight ordinary effects, shared video deployment
and duplicated PIL operations is unchanged. There is no new measured maintenance
task or independent-deployment comparison. The protocol remains ready for the
team to define equivalent before/after tasks and account for learning bias.

The eight existing Node orchestrator tests passed in the source-verified projects
container (0 failures). They cover pipeline filtering, extraction ordering/manifest
handling, batch registration and commit-token behavior. The 74-test host video run
and its dependency limitations remain documented in the earlier verification record;
that suite was not rerun unnecessarily. Live recovery and sampled outputs add
functional evidence for the measured paths, not for every omitted effect/service.

## Acquisition Corrections

Earlier raw runs remain available for audit but are not mixed into the authoritative
metrics above:

- The initial load client ran inside `projects`, contaminating its resource usage.
  The final client ran in a separate container.
- The initial RSS predicate matched `node`, while the image used `node-MainThread`.
  Zero values from that predicate are missing measurements, not real zero RSS.
  Its cgroup data remain observations, but the final series uses the corrected
  predicate and is the source of the table above.
- The initial storage-read case used a key absent from the public project response.
  It cannot establish authorization. The corrected harness and supplemental probe
  derive the actual object key from its URL and verify downloaded bytes.

Both corrections and the changed acquisition conditions are documented so the
trial runs cannot be mistaken for before/after refactoring measurements. The raw
series never contains credentials or application logs.

## Discussion Shortlist — No Pair Selected

All six directions and the original 15 broad pairs remain open. Based on the new
evidence, the following are concrete starting points for the team's discussion,
not approved priorities, effort estimates or an automatic ranking:

| Pair | Evidence supporting discussion | Main unresolved work |
|------|--------------------------------|----------------------|
| QC-05 + QC-06 | Measured upload memory growth and demonstrated internal ownership bypasses give separate, concrete outcomes. | Define upload budgets and the exact security boundary; preserve validation and all legitimate callers. |
| QC-02 + QC-05 | Queueing and transfer memory are measurable stages of the same media workflow. | Demonstrate safe capacity improvement under a fixed budget; keep the two workloads/metrics distinct. |
| QC-01 + QC-02 | Concurrent processing and recovery share state/file-isolation concerns. | Broaden fault points before claiming a reliability improvement; the current single-worker restart case already succeeds. |

QC-03 remains useful when maintenance impact is the team's priority. QC-04 requires
human task evidence, especially if the final objective is intuitive operation.
Their absence from this provisional discussion list does not exclude them or any
other well-founded pair. A narrow port-only change or a topology-only change must
not be presented as a demonstrated improvement of an unmeasured quality attribute.

The next step identified on November 14 was for all four members to review this evidence, available effort and stakeholder
priorities. Record actual agreement in the
[existing decision record](quality-exploration.md#decision-record--pair-agreement), then
specify two distinct quantitative RNFs with target/minimum origins. Reuse these
initial measurements only if the selected protocols and conditions match; otherwise
measure the unchanged application again before refactoring. No team approval or
construction authorization has been inferred.

**Later selection update, 2026-11-16T15:12:33Z:** The user explicitly requested
recording the pair agreement: QC-06 security/end-to-end authorization + QC-05
performance efficiency/upload resource utilization. The linked canonical record
states the source and limits. This updates the selection state only; it does not
change these November 14 observations, approve remaining targets or authorize code.

Codex and the invoked Inception skill prepared and executed the scripts and this
analysis. Automated source/data checks are recorded; human review and participant
validation remain the team's responsibility.
