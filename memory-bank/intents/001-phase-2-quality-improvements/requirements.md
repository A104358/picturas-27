---
intent: 001-phase-2-quality-improvements
phase: inception
status: draft
created: 2026-11-14T17:10:27Z
updated: 2026-11-14T18:19:23Z
---

# Requirements: Phase 2 Quality Improvements

## Intent Overview

Improve two distinct non-functional requirements of PictuRAS through refactoring,
preserving existing image and video behavior. Use the architectural diagnosis from
Exercise 6 as the starting evidence and evaluate each improvement separately with
reproducible measurements before and after implementation.

**Type:** Refactoring of an existing full-stack application.
**Team:** PL2-G4.
**Planning state:** Intent initialized; detailed requirements have not been elicited
or approved. The two quality requirements and the implementation approach remain
open. The user requested exploration of all six candidate directions before
selection, followed by explicit agreement from all four team members. The
[quality exploration](quality-exploration.md) records the comparison, investigation
protocols and pending decision record. This draft is not a completed requirements
specification.

The [investigation plan](investigation-plan.md) and [evidence index](evidence/README.md)
now include renewed source checks, an acknowledgement-order demonstration,
74 passing host video tests and processor-only pilots. Final requirement baselines
and numerical acceptance values remain pending.

The subsequent [live findings](live-findings.md) add candidate measurements from
an isolated 13-service deployment: upload RSS, three video batches, Socket.IO
progress, internal access tests and one worker-recovery scenario. These results
support a provisional discussion shortlist; no pair or quantitative targets have
been approved by the team.

The [team review packet](team-review.md) now consolidates all six directions,
the recommended discussion pair QC-05 + QC-06, proposed boundaries and numerical
options. Its proposed percentages and zero-bypass criterion are unapproved
engineering proposals. They do not change the count of selected requirements
or replace the later full requirements review.

## Business Goals

| Goal | Evidence of success | Priority |
|------|---------------------|----------|
| Address two concrete quality weaknesses relevant to PictuRAS stakeholders. | Independently specified and evaluated requirements, classified under ISO/IEC 25010:2011. Quality priorities are awaiting team input. | Must |
| Demonstrate improvement rather than assume it from an architectural change. | Comparable initial and final measurements with identified scenarios, data, environment and instruments. Numerical targets and minimum acceptable values remain to be defined. | Must |
| Preserve the existing editing product. | Regression evidence for images, video and mixed projects, including subtitles and frame extraction where affected. | Must |

## Stakeholders

Registered and premium users benefit from dependable editing and understandable
feedback. Developers and operators need maintainable services and predictable
resource consumption. Anonymous image users must retain the supported behavior
even though video is unavailable to that profile. The academic team needs a
defensible link between requirements, evidence, decisions and results.

## Scope

### In Scope

- Explore all six candidate directions and their possible pairs using the existing
  diagnosis, then select and justify exactly two quality requirements with explicit
  agreement from all four PL2-G4 members.
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

Neither of the two quality requirements has been selected. No numerical acceptance
targets or unmeasured baseline values are asserted in this draft.

The six directions under exploration are reliability/recovery, video capacity,
maintainability/modularity, pipeline usability and background-work feedback,
upload resource use and internal-service security (QC-01 through QC-06 in the
[comparison](quality-exploration.md)). These are options for elicitation, not
commitments to implement every direction or to adopt ALT-1 or ALT-2.

## Constraints

- Follow the 2026/2027 Phase 2 guidelines: refactoring with functional preservation.
- Classify the two selected requirements under ISO/IEC 25010:2011 and evaluate
  each one independently, including relevant adverse effects on other attributes.
- Preserve an identifiable application baseline before changing code or deployment.
- Keep measurements reproducible and comparable; record CPU/RAM allocations,
  model warm/cold state and concurrent workloads when they influence the result.
- Delivery is on 20 November 2026, confirmed by the user and consistent with the
  supplied guidelines. The submission time, available team hours and participant
  access have not been supplied.

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
| Which two quality weaknesses should this intent prioritize? | All four PL2-G4 members | Evidence committed as 793df2e and a team review packet prepared. QC-05 + QC-06 is recommended for discussion; no pair selected and no individual agreement recorded. |
| What hardware/resource budget, time, representative workloads and participants are available? | PL2-G4 | Pilot resources are recorded. Team hours, final workload scope and participant access remain open for the team review. |
| What delivery deadline applies? | PL2-G4 | User confirmed 20 November 2026. |
| What target and minimum acceptable values are justified by the baseline and stakeholder needs? | PL2-G4 | To quantify after the measurement method and initial results are available. |

## Sources

- [Exercise 6 architectural diagnosis](../../../docs/exercises/06-architectural-patterns/resolution.md),
  including its EV/H/ALT identifiers and evidence limitations.
- [Phase 2 guidelines, version 1](../../../docs/guidelines/fase-2-guidelines-1.pdf).
- [Video extension requirements](../../../docs/requirements/doc-ext-requisitos-2627.pdf).
- [Documentation index](../../../docs/README.md) for the earlier requirements,
  architecture report and course material.
- [Repository guidance](../../../AGENTS.md).
