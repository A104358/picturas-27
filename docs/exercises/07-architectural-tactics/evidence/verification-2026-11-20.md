# Documentary review — Exercise 6 and Exercise 7

Recorded: 2026-11-20T10:32:42Z. Source checkout:
`405b6c06047f4a9e969b7c935cbecd7bce6769a5` (`405b6c0`).

The user selected review of the exercise resolutions. This review compares the
supplied assignments/templates, current documentation, prior registry and relevant
application source. It does not resume the stopped UP-C4–C9 choices or authorize
construction. The [November 18 verification](verification-2026-11-18.md) remains
an unchanged historical record of the earlier versions.

## Corrections

| Finding | Correction and location |
|---------|-------------------------|
| QS-01 combined unauthorized admission and revocation of a previously valid authorization | [Block 2 §4.2](../../06-architectural-patterns/resolution-block-2.md#42-cenários-de-qualidade-para-a-extensão-de-vídeo) now defines admission as QS-01 and revocation as new QS-07, complementary to the same CAND-1. No old ID is reassigned and no third requirement is selected. Exercise 7 §1.2 records the change; its primary QS-01 fields are copied from the corrected canonical definition. QS-02 is unchanged. |
| The effect matrix could read as predicting increased Node RSS while calling it an improvement | [Exercise 7 §5.1](../resolution.md#51-matriz-de-efeitos) distinguishes improvement of an attribute from the numerical sign of a metric. Lower memory is a hypothesis; extra I/O can still worsen latency. No improvement is reported as measured. |
| The diagrams combined worker results and browser events into one return to projects | Both inline diagrams and editable sources distinguish project_queue → projects from ws_queue → wsGateway. The after view labels TLS/mTLS by channel and leaves event payload/context adaptation explicit rather than implying it is implemented. |
| Tactic names could be confused with structural patterns or implementation tools | The perimeter and transport tactics name the intended response mechanism; gateways, mTLS and nginx/S3 remain realizations, without claiming that a tool or pattern proves quality. |
| Owner-only project deletion is a visible policy change | Block 2 §6 and Exercise 7 DA-1 retain the individual choice, the editor's media-removal permission and class-B justification. Current DELETE uses requireEditPermission. The exercise must justify this change under functional preservation; individual selection does not establish inherited behavior or academic approval. |
| Prior engineering criteria and final exercise quantification have different provenance | Block 2 §5.1 preserves selected criteria, requires explicit/versioned revisions and forbids adjusting targets to make MF pass. Formal BF and final quantification remain pending; no new numerical choice is inferred. |

## Static checks

Completed: 2026-11-20T10:36:44Z.

| Check | Result |
|-------|--------|
| Four supplied originals | SHA-256 and byte counts match the [November 18 manifest](../../06-architectural-patterns/evidence/continuation-sources-2026-11-18.json); original root paths remain absent |
| Application source comparison | No changed application paths from 484be13 to 405b6c0, or in this working tree, within the manifest's comparison scope |
| Earlier evidence/hypotheses and matrix | EV-01–48 and H-01–18 rows retained verbatim from 405b6c0; Block 1 §3.3 unchanged |
| Current registry | EV-01–49 and H-01–18 unique and sequential; prior ALT identifiers preserved |
| Canonical scenarios and candidates | Seven QS definitions, exactly two CAND; QS-07 complements CAND-1, QS-02 unchanged |
| Scenario transcription | Exercise 7's ISO, stimulus and response/measure equal the canonical QS-01/QS-02 fields; six-element definitions remain in Block 2 |
| Tactics and decisions | 13 unique TAT, at least three per primary scenario, two DA and two class-C capabilities rejected |
| Diagrams | Two inline Mermaid blocks equal the editable before.mmd/after.mmd sources; result/event routes and basic delimiters checked |
| Rendering | No Mermaid renderer or browser used; rendered visual validation remains pending |
| References and formatting | Local links, table structure, completed-document placeholders, EV/H references, original line-ending styles and git diff whitespace checked |
| Planning scope | Existing 60 metric IDs and U25 G unchanged; evaluation manifest template remains unfrozen; UP-C4–C9 remain unselected |

Method: Python standard-library checks of Markdown/JSON, SHA-256 and source
comparison through read-only Git diff/show. Assignment 1.1 and 3.0 requirements
were checked against the completed sections; templates in sources intentionally
retain their original placeholders. Block 1 resolution is now 1.3; Block 2 and
Exercise 7 resolutions are 1.1. Source assignment/template versions are unchanged.

## Remaining validation

The team still needs to review the academic argument, including the visible ACL
restriction. No nominal approval is attributed to any member. Formal BF/MF,
calibration, physical corpus, open implementation choices, rendered diagrams and
runtime/regression/security/load tests remain separate work. No Docker, database,
browser, retained-volume, credential or application runtime was accessed; no
application code was changed and no new workload result was produced.
