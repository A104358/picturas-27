# B10 PKI operations conformance

Read [the operational runbook](../../../docs/pki-operations.md) before running
destructive-to-connections tests. These commands never commit, push or delete volumes.
They operate only on the separate marked installation `picturas-pki-pilot-b10` with
private durable material in `$HOME/picturas-secrets/b10-fixture`. The original
installation CA and data are preserved. Never point the pilot at a normal dataset.

`ops/maintenance-probe.Dockerfile` builds `picturas-maintenance-probe`.
`observer.Dockerfile` builds `picturas-pki-observer`. Application images must contain
the B10 trust/work observations. `pilot_paths.py` records the private fixture paths;
the private Compose override reuses those application image tags.

```bash
export PICTURAS_SECRETS_DIR=$HOME/picturas-secrets
python3 -m unittest discover -s tests/conformance/pki-operations -p test_maintenance.py
node --test tests/conformance/pki-operations/work-callback.test.js
tests/conformance/pki-operations/run-b10.sh status
tests/conformance/pki-operations/run-b10.sh renew
tests/conformance/pki-operations/run-b10.sh begin 1
tests/conformance/pki-operations/run-b10.sh replace 1
tests/conformance/pki-operations/run-b10.sh browser 1
```

`begin` refuses an existing trial directory. It establishes real HTTP keep-alive,
public HTTPS, Socket.IO owner WSS, authenticated Mongo pool, authenticated AMQP,
signed S3 and an HTTP/2 gRPC connection. It confirms a video worker is executing a
90-second 720p technical fixture with four brightness stages before declaring the incident. The independent
observer has no Docker socket; it records each persistent cut and holds old SSL
sessions only in memory. Host-side maintenance separately observes network refusal
and stopped processes. No domain Process is created or quota debited (D-33).
The final three cycles record native broker connections/consumers per principal
immediately before isolation, process-grounded zero counts while stopped and fresh
native counts after reopening. Four independent read-only shared-volume samples
also prove that the partial output stops changing after the cut. The first three
cycles, which lacked these direct per-principal snapshots, remain as
`initial-trial-1..3`; their timings and raw results are not overwritten or hidden.

`replace` retires the CA and every leaf key, quarantines only the owned fixture's
durable message and output, and stops the native backends again. `browser` updates
only the isolated NSS profile and opens the real native Firefox TLS controls. The
current certificate must load normally; old CA, wrong name and expiry must be
refused. Inspect all four saved native pages without any warning override.
`record-visual-review` is deliberately a separate action, used only after the
agent actually views those four screenshots; it records Codex as the actor and
explicitly does not claim human-user confirmation. The test preparation alone
never creates the receipt. A human can repeat and record their own inspection.

```bash
tests/conformance/pki-operations/run-b10.sh record-visual-review 1
tests/conformance/pki-operations/run-b10.sh resume 1
```

Repeat the full sequence for 2 and 3. `resume` keeps admissions closed until the
complete actual participant/trust manifest, roles, native clients, old server/client
CA negatives and old-session attempts pass. At least one old ticket must still be
within its recorded lifetime. A failed verification kills partially started
participants and preserves the operation clock; it does not reissue material.

`inventory` collects effective runtime/library versions, image IDs/registry digests
and public certificate profiles. `export` emits an explicit public field allowlist,
including boolean assertions that every leaf and the CA have different keys.
It never exports key bytes, secret values, JWTs or signed URLs. `negative`, run
after the comparable trials, archives only the already-quarantined owned messages
privately, then checks an old participant mount, expiry, wrong service identity
and an actual restart failure. Every fault must leave all processes stopped and
admissions closed. Recovery uses the current CA and exact valid current leaves.

Preparation failures are preserved separately. The earlier temporary-directory
installation lost its private CA/state across an interruption and is not a valid
pilot; its volumes remain preserved. The first persistent-installation diagnostic
needed a TLS probe correction and a verification retry. It is retained as
`diagnostic-control-retry`, outside the three comparable trials, with its full
elapsed time and the failure declared. TLS 1.2 client-CA controls against Node also
require a positive current-client control in TLS 1.2; a close/reset or unsupported
protocol is not silently counted as a CA rejection.

Public results: `../results/2026-11-24/B10-*`. S20 is established by this conformance
group; it is not added to the frozen measurement engine. EXP runs keep the existing
instrument unchanged and use `MED_WS_JOIN_FORMAT=v2`.
