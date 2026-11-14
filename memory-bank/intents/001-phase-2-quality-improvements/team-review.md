---
intent: 001-phase-2-quality-improvements
phase: inception
status: draft
created: 2026-11-14T18:19:23Z
updated: 2026-11-14T18:19:23Z
---

# Team Review: Evidence, Proposed Scope and Selection

## Review State

**Evidence revision:** `793df2e14ff67f3d247874d3b35fce000d5c69fc`.
**Application measured:** `24484b7`, with 182 runtime source files matching the
checkout. The intervening commit contains evidence/documentation, not application
refactoring. **Team:** PL2-G4. **Delivery:** 20 November 2026.

The user requested commitment of the live evidence followed by preparation of this
review. That authorizes the review work; it does not record agreement from any of
the four members on a pair, numerical targets or an implementation. This packet
supports selection before completing the detailed requirements specification.
It is not the final Inception artifact/readiness review.

The recommendation is to discuss **QC-05, upload resource efficiency, together with
QC-06, internal identity/ownership protection**. Both have observed weaknesses,
separate measures and clear stakeholder outcomes. All six directions and their
[15 broad pairs](quality-exploration.md#comparison-of-all-candidate-pairs) remain
available. No pair is selected here.

## What the Evidence Supports

| Direction | Evidence now available | Main uncertainty for selection |
|-----------|------------------------|--------------------------------|
| QC-01 — recovery | A helper acknowledges before its async callback completes; one early live worker interruption recovered one coherent result and one charge. | Recovery at later publication/persistence windows remains untested. The already successful early restart case alone would not establish a new improvement. |
| QC-02 — capacity | Three three-video batches took 42.665–45.001 s; queueing residuals for last jobs were approximately 28.3–30.5 s. Worker CPU was close to its 2-core ceiling. | Replicas need an explicit resource budget and safe work paths. Added resources and better efficiency are different claims. |
| QC-03 — modularity | Eight ordinary effects, duplicate PIL operations and common video deployment are identified. | No equivalent maintenance task or measured change-impact baseline yet; distributed effects also introduce I/O/contracts. |
| QC-04 — usability | Tool/state mechanisms are inspected; Socket.IO timings separate active-job progress from queued-job delay. | No participant task evidence or rendered-browser refresh/navigation trial. Configuration and background operation require separate measures. |
| QC-05 — upload resources | A 50 MiB upload increased Node RSS by about 154.88 MiB in the gateway, 52.01 MiB in projects and 69.81 MiB in storage. | One final sample per size; allocator/cache state and workload representativeness need controlled baseline repetitions. |
| QC-06 — internal security | Cross-owner project read, forged caller header, tokenless source download and write under an owner's storage prefix were demonstrated. | Finite Docker-network threat model; no claim of internet reachability, complete access coverage or TLS/secret remediation. |

The [live findings](live-findings.md) explain conditions, raw evidence and acquisition
corrections. Earlier co-located-client trials and invalid object-key reads are not
used to establish the recommendation. No qualitative score has been presented as
a measured benefit, and no priorities or available person-hours are assumed.

## Recommended Pair: Proposed Decision Boundary

The two candidates share gateway/projects/storage components. Their evaluation must
remain independent: a request rejected by authentication cannot be reported as a
memory-efficient successful upload. Use authorized uploads for QC-05, and record
unauthorized plus legitimate control requests separately for QC-06.

### Candidate QC-05: Memory Cost of Valid Video Uploads

**Stakeholder outcome:** Free users uploading supported media should not cause
repeated file-sized buffers to consume service memory unnecessarily. Operators
benefit from a predictable resource envelope.

**Classification:** ISO/IEC 25010:2011, performance efficiency / resource utilization.

**Proposed scope for discussion:** Uploads through the existing video endpoint,
nginx, API gateway, projects and storage facade. Start with the existing valid
10/50 MiB free-profile workload at concurrency 1. Keep image upload and all profile
limits functionally compatible. ZIP export, multipart UI redesign, direct-to-S3
upload as a new public flow, and a promise for 1 GiB uploads are outside this
initial candidate scope. Expand sizes/concurrency only if the team chooses and
measures that explicit scope before refactoring.

**Measurement proposal:** For each affected Node service, measure pre-request RSS,
peak RSS and `delta = peak - pre-request RSS`. Keep the existing 50 ms sampler,
500 ms pre-request median and request-through-500-ms-after-response observation
window. Report absolute peaks, pre-request RSS, synchronized cgroup memory and
temporary-file/I/O behavior as guardrails. Do not sum unrelated service peaks.

**Initial evidence:** At 50 MiB, observed deltas were 154.88 / 52.01 / 69.81 MiB
for gateway / projects / storage, respectively. These are individual pilot values,
not a stable median baseline or acceptance thresholds.

**Proposed next baseline:** Three independent repetitions using an identical
service-start/warm-up sequence, fixed image/resource budgets and the same input
hashes, with a separate load generator. Agree that sequence before running and
repeat it unchanged after refactoring. Three repetitions are a feasibility
proposal for this bounded comparison, not a basis for a population percentile.
If this differs from the archived warm setup, establish a new initial baseline;
do not compare a fresh final process against the old warm pilot.

**Numerical options for discussion, not approved requirements:** Use the median
per-run 50 MiB delta for each service, `B` before and `F` after. Proposed target:
`F <= 0.25 * B` (75% reduction); proposed minimum: `F <= 0.50 * B` (50% reduction).
These percentages are engineering proposals for a material reduction in the
observed buffering cost. They do not come from the guidelines or an existing
stakeholder agreement. Reassess them against the repeated baseline before freezing
the specification. A baseline indistinguishable from sampler noise requires a
different primary comparison; percentages against near-zero values are invalid.

Absolute peak and idle RSS must also be reported to prevent an apparent improvement
created merely by retaining memory before the request. No claim is accepted if the
same request fails, skips validation, changes bytes/ownership or shifts an unbounded
cost into another service. Latency, cgroup memory and temporary disk usage must be
compared; their acceptable limits still require team input.

**Alternatives to assess after selection:** Streaming/backpressure across existing
boundaries versus bounded disk spooling that supports ffprobe and hashing. Inspect
nginx buffering and upstream behavior. No implementation choice is approved here.

### Candidate QC-06: Verified Internal Identity and Ownership

**Stakeholder outcome:** One user's project/media cannot be read or written by an
unrelated caller that reaches the selected internal HTTP interfaces.

**Classification:** ISO/IEC 25010:2011, security / confidentiality, integrity and
authenticity. This is distinct from the upload memory requirement.

**Proposed scope for discussion:** Direct project-read and storage signer/upload
boundaries exercised in the current matrix. The attacker can reach those HTTP
interfaces, use a legitimate JWT for a different synthetic owner, omit/forge a token
and forge caller headers. A header alone is not evidence of a verified identity.
Include ownership and permitted sharing, rather than checking only that some token
exists. Existing asynchronous processing must retain an authorized service path.

Privileged host/database/broker compromise is outside this bounded claim. If its
design assumes protected service credentials, that assumption must hold: committed
default credentials are a known current limitation. Include non-versioned boundary
credentials/rotation or appropriate network isolation as necessary prerequisites;
do not present a new shared secret committed to the repository as a solution.
General security certification, all subsystem authorization, monthly availability
and full privacy compliance are not claimed by this candidate.

**Measurement proposal:** Keep a versioned finite negative/positive request matrix.
Record prevented and admitted unauthorized operations by case, plus successful
legitimate controls and their result integrity. Preserve payload checks: an error
page, issued-but-unusable URL or failed valid request is not an authorized success.

**Initial evidence:** The authoritative matrix has seven negative cases, with
three admitted unauthorized operations: direct cross-owner project read, direct
tokenless source read and direct tokenless write under the owner prefix. Four
negative cases were rejected. A supplemental forged-header case adds another
admitted project read. These are eight distinct negative cases with four observed
bypasses, not a population-wide security failure rate. The owner gateway read is
the existing positive control. Any expanded matrix needs its own initial results.

**Numerical option for discussion:** Target and minimum both **zero admitted
unauthorized operations in the agreed negative matrix**, with every agreed
legitimate control passing. Allowing one known ownership bypass would defeat this
bounded security objective; that explains the identical target/minimum. This is an
engineering proposal, not team approval or proof of complete security.

**Positive controls to define before implementation:** Owner project/media access;
read-only sharing versus edit sharing; authorized background processing and source/
result storage; existing image/video preview and export; public share resolution
where intentionally public. Existing unexpired signed URLs are delegated access
by design; direct issuance of a new URL is a different boundary. Do not introduce
immediate signed-URL revocation or other new sharing semantics silently.

**Alternatives to assess after selection:** Verified user identity and ownership in
projects, scoped service identity/delegation for storage, and reduced unnecessary
reachability. Distinguish a network-only boundary from application authorization.
The current internal-network bypasses are not fixed merely by hiding host ports.

## Alternatives and Reasons to Choose Them Instead

| Pair / direction | When it may better match team priorities | Evidence/work still needed |
|------------------|-----------------------------------------|----------------------------|
| QC-02 + QC-05 | Capacity and upload resources are the team's main operational pain points. | Specify a fixed-budget capacity scenario, test safe concurrent execution and avoid calling a static pool dynamic elasticity. |
| QC-01 + QC-02 | The team prioritizes correctness while increasing concurrent processing. | Exercise later failure windows and duplicate handling before selecting a recovery metric that the base already satisfies. |
| QC-03 with another direction | Developer change impact is more important to the team than one measured operational issue. | Define an equivalent maintenance task, rebuild/dependency measures and learning controls. |
| QC-04a and/or QC-04b | User operation is the team's priority and participants are available. | Run configuration/background tasks and distinguish UI success from transport cadence. Two separate usability RNFs may be valid. |

The original comparison remains the catalog for the other pairs. A different pair
is acceptable when the team records its evidence, scope, resources and stakeholder
rationale. The recommendation does not exclude an alternative by default.

## Review Outcome to Record

Each member reviews this document together with the evidence revision. Discuss:

1. Which pair best addresses the team's stakeholder priorities, and why?
2. Is the proposed workload/threat scope appropriate, or must it change?
3. What person-hours/resources and regression coverage can the team actually supply?
4. Are the proposed numerical options defensible, or should they be revised after
   repeated baselines? Pair agreement does not automatically approve thresholds.
5. What concerns remain for any member, and what evidence will resolve them?

Use the [single canonical team decision record](quality-exploration.md#decision-record--pending)
for the chosen pair, rationale, reviewed revision and each member's actual agreement
or concerns. All four named entries remain pending. The user may provide an
explicit outcome on behalf of a team meeting; no direct contact with teammates is
required or performed. Silence, a majority preference or a request to continue
does not record the unanimous agreement the user requested.

Once a pair is explicitly agreed, complete the detailed FR preservation criteria
and two quantitative NFRs for requirements review. Freeze or renew their initial
measurements before code changes. Context, units, stories and bolts follow the
approved requirements. This packet makes the decision reviewable; it does not
authorize construction or attribute human validation to AI-generated work.
