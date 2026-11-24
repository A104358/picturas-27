# B9 sessions and assisted reissuance

Only synthetic fixtures. No real migration, reset, retained browser or host-clock change.

- `node tests/conformance/sessions/issuer.test.js`: AR-01–04/12, fail-closed eligibility,
  account fingerprint, ownership/mode, exclusive output, locks and durable ambiguous intent.
- `client.test.js`: execute the production TypeScript recovery/storage modules with the
  frontend image compiler (`B9_TS_COMPILER=/usr/src/app/node_modules/typescript`), repository
  mounted read-only, working directory `/repo`. AR-05/07/08/10, exact bytes, server refusal,
  network/storage failures, identity conflict, stale compare-and-set and held lock.
- `mutations.test.js`: execute with the same compiler/image as `client.test.js`; actual
  session hooks under delayed validation, an uncooperative old writer, active recovery
  lock and explicit logout (AR-09/10, SEC-01/02).
- `session-profile.test.js`: run in the users image, test path mounted read-only. Normal
  issuer/validator, absolute seven days at exp−1/exp/exp+1, isolated verifier clock (S06/SEC-02).
- `b9-browser.py`: real Chromium and production frontend/API/users administrative CLI.
  Needs Docker, `PICTURAS_SECRETS_DIR`, and Playwright from `requirements-browser.txt`
  in an external venv (`python -m playwright install chromium`); run from repository root
  with dev up. Browser installation and private files do not belong in the checkout.
  Cases/delivery files live in a private temporary directory outside the repository, removed
  after the run. Chromium trusts the installation nginx public key; all fixture API requests
  verify the installation CA. No headers, bearers or identifying fixture values in output.
  AR-02/05–12, bootstrap isolation with absent/rejected session, file boundaries, server
  validation before confirmation, real locks/storage conflicts and preserved identity/data.

The independent evidence in every fixture is explicitly synthetic and does not make any
real recovery case eligible. Administrators perform and record evidence/approval/import
verification in the private journal; the UI has no access to it. Limits/cases are documented
in `docs/architecture/fase2-recuperacao-anonima.md`. Browser quiescence includes closing older
clients that do not implement the session lock; a storage conflict halts the importer.

Earlier diagnostic results are retained: the initial functional test exposed future `iat`
acceptance (fixed in all three session verifiers); the first smoke invocation used
localhost inside the test container and was replaced by the host invocation. Browser
selector diagnostics preceded the final scoped-alert assertions. Only the final
`B9-*-dev.txt` results and acceptance index describe the reviewed version.
