# Exercise 7 — Architectural tactics

[Documentation index](../../README.md) · **Team: PL2-G4**

Read the [completed resolution](resolution.md). It follows the supplied
assignment/template **3.0, November 17, 2026**, and reuses the two candidates and
canonical scenarios from [Exercise 6, Block 2](../06-architectural-patterns/resolution-block-2.md).
The [shared evidence/hypothesis registry](../06-architectural-patterns/resolution.md)
continues EV/H identifiers from Block 1. DA-1/DA-2 here summarize existing choices;
they do not select UP-C4–C9 or authorize application changes.

## Files

| Artifact | Purpose |
|----------|---------|
| [Assignment HTML](sources/RAS-exercicio_7_taticas_SWdesign_PT.html) | Original version 3.0, including the minimum tactics catalog in Annex A. |
| [Original Markdown template](sources/RAS-exercicio_7_taticas_SWdesign_template_PT.md) | Version 3.0, preserved unfilled as supplied; completed work is resolution.md. |
| [Resolution](resolution.md) | Scenario references, 13 candidate tactics, two decisions, trade-offs, measurement/regression plans and AI record. |
| [Before diagram source](diagrams/before.mmd) | Mermaid source of the observed application view, embedded in the resolution. |
| [After diagram source](diagrams/after.mmd) | Mermaid source of selected design versus still-open mechanisms; not deployed behavior. |
| [Input hashes and source comparison](../06-architectural-patterns/evidence/continuation-sources-2026-11-18.json) | Proves preservation of the four supplied files and records the static application diff scope. |
| [Documentary verification](evidence/verification-2026-11-18.md) | ID/scenario/template/source/reference checks; no runtime tests or rendered-diagram claim. |

## Material actually available

The four new originals were moved from the repository root to the corresponding
exercise sources directories, without changing bytes. The earlier requirements,
architecture report, guidelines and Styles lecture remain under their existing
topic folders. The provided templates mention Markdown assignments, whereas the
supplied assignment files are HTML; versions/filenames actually read are explicit.

Slides 9 (`RAS-slidesEN-9-ARCH-Tactics.pdf`) and the four referenced
`Apoio/Taticas` sheets (`availability_tactics.md`, `performance_tatics_PT.md`,
`security_tatics.md`, `RAS_support_doc_tectics_EN.md`) were not supplied in this
workspace. The resolution uses **Annex A of the supplied HTML**, plus the available
documents and official SEI abstracts cited in EV-47. It does not claim to have
read the missing materials or the complete SAIP book. Version 2.0 history mentions
Block 2 v1.2; the Block 2 material actually supplied is **1.1**, recorded accurately.
Version 3.0 removes peer review; this resolution does not reintroduce that task.

## Status

Documentary resolution prepared, with human academic review still pending. No
application, load/fault/PKI test, baseline or final campaign was run for these
exercises. Existing individual decisions and engineering criteria retain their
provenance; the exercises do not turn them into measured results. Actual baseline,
final quantification and implementation remain separate project work.
