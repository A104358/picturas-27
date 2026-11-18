# Documentary verification — Exercise 6 Block 2 and Exercise 7

Recorded: 2026-11-18T14:59:46Z. Source checkout: 1d7103b.

The check read the current documents, their supplied-source manifest and the
previous Block 1 from Git. No application, Docker, database, browser or retained
volume was accessed through a runtime interface. No load/fault/regression test
was executed, and no new decision approval is inferred.

| Check | Result |
|-------|--------|
| Four newly supplied files | SHA-256 unchanged after moving to exercise sources; absent from the repository root |
| Application baseline comparison | No changed application paths between 484be13 and 1d7103b in the recorded comparison scope |
| Previous registry rows | Original EV-01–37 and H-01–13 retained verbatim |
| Previous pattern matrix | Block 1 §3.3 retained verbatim |
| Continued registry | EV-01–48 and H-01–18 unique and sequential; ALT-1/ALT-2 retained |
| Canonical quality scenarios | Six definitions in Block 2; exactly two CAND entries |
| Exercise 7 scenario use | ISO, stimulus and response/measure copied exactly for QS-01/QS-02; six-element definitions remain in Block 2 |
| Tactics and decisions | 13 unique TAT; at least three per primary scenario; two DA; two class-C capabilities rejected |
| Required document sections | Block 2 §§4–7 and Exercise 7 §§1–6 with required subsections present; no unfilled template placeholders/guidance in the resolutions |
| Diagram sources | Two Mermaid blocks equal their editable before.mmd/after.mmd files; basic delimiter consistency checked |
| Rendering | No Mermaid renderer or browser screenshot used; no claim of rendered SVG/visual validation |
| References and formatting | Local file links resolve; table-block structure and diff whitespace checked |
| Existing file formatting | Original CRLF/LF choice preserved in edited tracked files; supplied originals unchanged byte for byte |
| Project scope | Existing 60 metric IDs retained, U25 G, evaluation template unfrozen and UP-C4–C9 unselected |
| Human academic review | Pending; automatic document checks do not provide nominal team approval |

Method: Python standard library parsing of Markdown/JSON and SHA-256; Git
read-only diff/show and git diff --check. Generated media and new application
measurements are not part of this verification. The original assignment/template
files intentionally retain placeholders as source material; only the resolutions
are checked as completed documents.
