# Applied PKI operations

Export `PICTURAS_SECRETS_DIR` to the private directory outside the checkout for
every command. Select the actual Compose project explicitly. Keep one application
stack running at a time. The official measurement project `picturas-nfr` is refused
by these administrative scripts; use a separate, reviewed evaluation procedure.

## Planned renewal

```bash
export PICTURAS_SECRETS_DIR=$HOME/picturas-secrets
ops/secrets.sh render
ops/pki.sh check
ops/pki.sh renew --project picturas-dev
```

Renewal is due at seven days remaining. `--service nginx` selects one leaf;
`--force` deliberately renews it even when it is not due. All participants are
recreated to close HTTP keep-alive, WebSocket, database, AMQP and S3 pools, TLS
session caches and ticket keys. Verification checks the actual new processes,
served certificates, application trust records and registered consumers.

New ingress requests receive 503 while draining. An upload body buffered in nginx,
an active response, a Process, queued/unacknowledged work or an active local worker
defers the cut. The command returns an error and leaves admissions suspended; it
does not wait indefinitely or kill a job. Inspect the private operation state and
drain observations. Repeat the same operation only after confirming the work has
finished; its original clock is retained. `ops/maintenance.sh cancel --project
picturas-dev` can reopen an unchanged, uncut planned deferral. It refuses after any
cut, certificate change or participant change.

Normal renewal keeps the CA. The earlier certificate remains trusted until it
expires. Use retirement when that earlier identity must be rejected.

## Incident isolation and retirement

```bash
export PICTURAS_SECRETS_DIR=$HOME/picturas-secrets
ops/maintenance.sh isolate --project picturas-dev --mode compromise \
  --detected-at 2026-11-24T12:00:00Z
ops/maintenance.sh status --project picturas-dev
ops/pki.sh retire --project picturas-dev --mode compromise
```

Use the real incident declaration time. Compromise isolation does not wait for
jobs or upload completion. It disables restart policies and terminates every
participant, including workers executing local effects. It verifies processes
stopped and refusal of new connections from inside the network and outside nginx.
An optional `--cut-proof` supplies an independently observed, operation-bound
receipt for all prior persistent connections. The pilot uses this additional
receipt and a real running video job.

`t_comando` starts before internal validations. `t_isolado` is recorded only after
the observed cuts. Over 30 seconds is a failed isolation criterion, even if the
installation subsequently becomes isolated. A missing cut observation remains
`isolation_incomplete`; retrying the same operation never restarts the clock.

Retirement generates a new CA and every leaf with new keys in private staging,
validates them, records activation intent, archives withdrawn material privately
and activates the new tree while participants remain stopped. The archived CA is
evidence, never application trust or a rollback. Do not manually start consumers.
Interrupted business work requires the B11 reconciliation procedure; B10 refuses
to reopen a normal compromised installation before that reconciliation exists.
Use [`ops/reconcile`](reconciliation-operations.md) to inventory, classify and
quarantine affected runs and apply only proven quota compensation. B10 checks the
operation-bound business seal before starting consumers; PKI maintenance itself
provides no replay, compensation or quota refund.

The D-33 exception is restricted to the marked technical pilot installation and
an operation-bound private receipt. Its harness quarantines only the identified
technical message and output directory and proves no domain Process or debit.
It cannot authorize a normal installation to resume interrupted business work.

## Reopening and browser trust

Before reopening, remove the withdrawn CA from each controlled browser profile
and install the verified new CA. Do not change a personal/global trust store as a
test fixture. In a dedicated profile, record browser version, origin, old/new CA
fingerprints and the following interactive checks:

1. The current certificate loads the page with normal TLS validation.
2. A controlled old-CA server certificate is refused as untrusted.
3. Current-CA certificates with an expired validity or a wrong host name are refused.
4. Expand the warning details to inspect the cause; never accept the risk, add an
   exception or use a validation bypass.
5. After reopening, verify the real application and a fresh authorized WSS join.

`tests/conformance/pki-operations/manual_browser.py` prepares a labelled local TLS
fixture on port 8080 only while the application is stopped. Its isolated Firefox
profile retains no application credentials. It saves native pages for inspection;
automated preparation is not an inspection receipt. The B10 agent records its own
visual inspection explicitly as Codex, never as human-user approval. A human
operator can repeat the same four checks and record their own observation.

For a retired CA, `reopen` requires `--browser-proof` and `--persistent-proof`.
Receipts are bound to the operation and new CA. Persistent evidence must show all
prior connections cut and old sessions refused, including at least one still
unexpired old TLS ticket. An expired ticket or an unavailable service cannot count
as rejection. The pilot keeps SSL sessions only in observer memory.

Verification starts fresh processes with admissions still closed. It checks the
complete participant/mount manifest, current CA only, exact leaf fingerprints,
actual peer certificates, allowed and denied roles, native data clients and all
required consumers. Any partial start or failed control terminates the participants
again. Only a complete successful observation removes the admission flag.

## State, failures and operator recovery

State is stored privately in `maintenance/<project>/state.json` and an operation
archive under `PICTURAS_SECRETS_DIR`; records are mode 0600 and written with fsync
and atomic replacement. They contain public certificate metadata and selected
container state, never Docker environment dumps or credentials. Process trust
records inside containers contain only public fingerprints. Do not publish the
private installation or its directory contents.

The journal records detection, command, observed isolation, staging, activation,
restart, controls and reopening. Keep human/operator delays in elapsed substitution
and total unavailability. Do not convert a contextual pilot maximum into a general
availability guarantee.

A process crash may leave `operation.lock` or activation intent. Inspect the journal,
processes and actual mounted material before recovery. Never delete the lock and
repeat an emission, activation, message mutation or compensation blindly. Repair
the identified cause while isolated; a `reopen` retry only repeats verification
with fresh processes. It does not regenerate the CA. Keep the withdrawn CA archived
and excluded from trust. A mount mismatch, invalid certificate, wrong peer, missing
participant or restart failure leaves admissions closed.

Stop an entire stack with `docker compose -p <project> down` **without `-v`**.
Preserve all volumes and quarantined evidence. Never use a global prune or a
measurement helper that deletes volumes to clean up a PKI operation.
