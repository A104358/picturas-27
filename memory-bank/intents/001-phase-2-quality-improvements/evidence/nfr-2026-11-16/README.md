# November 16 supplied experiments — evidence audit

The original results and scripts were supplied in commit `7d994d8` and are
attributed by the catalog to Claude, requested by Miguel. The reported measurement
machine is an Apple M4 Pro / Docker Desktop ARM64 environment. This directory is
not a new runtime execution by the current review, and its numbers must not be
pooled with the November 14 Intel/Linux measurements.

The current academic documents are the
[ideas 1/2 rationale](../../../../../docs/fase2-ideias-1-e-2.md) and
[metric specification](../../../../../docs/fase2-metricas-e-baseline.md).
Paths above are relative to this nested evidence directory; the repository-root
commands below are the reproduction entry points.

## Immutable original results

| File | Scope | Limitation |
|------|-------|------------|
| [uploads-result.json](uploads-result.json) | 14 successful uploads at 10/100/500 MiB, two unauthenticated rejections and one gateway OOM failure. | Warm/reused state, one first observed request, small samples and client-side send marker. No complete image/source/runtime manifest. |
| [security-result.json](security-result.json) | 23 records: 22 negative/concurrency cases plus one positive control. | Several assertions are incomplete; the reported 17 admissions are not a validated final denominator. |
| [reliability-R0-result.json](reliability-R0-result.json) | One valid image control. | Single trial. |
| [reliability-R1-result.json](reliability-R1-result.json) | Invalid border parameter; no client event, one orphan and worker restart. | Single handled-error scenario. |
| [reliability-R2-result.json](reliability-R2-result.json) | Broker restart and consumer/restart observations. | First consumer sample at +5 s is relative to API recovery, not the beginning of the restart. |
| [reliability-R3-result.json](reliability-R3-result.json) | Queued video request disappears after broker restart; one pending process, quota charged and empty ZIP. | One scenario, 45 s observation; repeat per-project state assertions for the formal campaign. |

These originals were not rewritten by the audit. In particular, G02 inspects an
absent `user_id`, D06 uses an absent `og_img_key`, D05 initially uses an empty
account, and G08/G09 involve an absent subscriptions service. `verify.mjs` exists,
but its stdout is not archived here; do not invent its output or treat a source
comment as a recorded measurement. The correctly hashed source read in the older
November 14 supplemental record remains evidence for that older environment.

## Audit and current static baseline

The review added scripts outside the original raw directory. They read existing
JSON or tracked source/certificate metadata; they do not send network requests,
change application code, print secret values or start/stop services.

```bash
python3 memory-bank/intents/001-phase-2-quality-improvements/evidence/audit-new-baselines.py --output /tmp/picturas-new-audit.json
python3 memory-bank/intents/001-phase-2-quality-improvements/evidence/collect-static-baseline.py --output /tmp/picturas-new-static-inventory.json
```

Their archived outputs are the
[baseline audit](../baseline-audit-2026-11-16.json) and
[static inventory](../static-inventory-2026-11-16.json). Input hashes are recorded
in the audit. Static certificate expiry depends on execution time. The collectors
require Python; the static collector also needs PyYAML, Git and OpenSSL.

Do not run the original load/fault scripts blindly: they create accounts/media,
can exhaust memory or restart services, use fixed experiment names/ports and some
write results back into this directory. Confirm isolation and correct assertions
first. The previous 13-service Mac setup omits frontend/subscriptions/AI; the expanded
security scope needs additional fixtures and services. Premium registration as
currently used by the performance script exploits an existing profile weakness;
the comparable final setup must provision premium legitimately or via a controlled
fixture. Keep generated MP4/PNG data outside Git.

## What remains before refactoring

The audit is not completion of the formal baseline. Close the open architecture,
compatibility, expiry and state decisions, approve the applicable P/G metric rows,
freeze corpus/instruments/environment and collect missing runtime values while
application behavior is unchanged. New-mechanism metrics may be justified as NA,
but user-visible effects still need an equivalent before/after comparison.
