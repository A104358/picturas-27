// Administrative CLI only. Never mounted by Express; no credentials in diagnostics.
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const STATES = new Set(["pending_evidence", "evidence_verified", "approved", "issued",
  "import_verified", "imported", "completed", "conflict", "failed", "issued_unconfirmed"]);
const required = (value) => typeof value === "string" && value.trim().length > 0;
const fingerprint = (account) => crypto.createHash("sha256").update(JSON.stringify(account)).digest("hex");
function refuse(code) { const error = new Error(code); error.code = code; throw error; }

function privatePath(file, directory = false) {
  const resolved = path.resolve(file);
  if (fs.realpathSync(resolved) !== resolved) refuse("unsafe_path");
  const st = fs.lstatSync(resolved);
  if (st.uid !== process.getuid() || (st.mode & 0o077) !== 0 ||
      (directory ? !st.isDirectory() : !st.isFile() || st.nlink !== 1)) refuse("unsafe_permissions");
  return resolved;
}
function loadCase(file) {
  const checkout = path.resolve(__dirname, "../..");
  const application = fs.existsSync(path.join(checkout, ".git")) ? checkout : path.resolve(__dirname, "..");
  if (file === application || file.startsWith(application + path.sep)) refuse("case_must_be_outside_application");
  privatePath(path.dirname(file), true);
  privatePath(file);
  if (fs.statSync(file).size > 65536) refuse("case_too_large");
  const record = JSON.parse(fs.readFileSync(file, "utf8"));
  if (record.schema_version !== 1 || !STATES.has(record.state)) refuse("invalid_case");
  return record;
}
function storeCase(file, record) {
  const tmp = `${file}.${crypto.randomUUID()}.tmp`;
  const fd = fs.openSync(tmp, "wx", 0o600);
  try { fs.writeFileSync(fd, JSON.stringify(record, null, 2) + "\n"); fs.fsyncSync(fd); }
  finally { fs.closeSync(fd); }
  fs.renameSync(tmp, file);
  const dir = fs.openSync(path.dirname(file), "r");
  try { fs.fsyncSync(dir); } finally { fs.closeSync(dir); }
}
function eligible(record, account, expected) {
  if (record.template_only !== false || record.state !== "approved") refuse("case_not_approved");
  if (!account || account.type !== "anonymous") refuse("account_not_eligible");
  if (![record.case_ref, record.administrator_ref, record.browser_profile_ref].every(required)) refuse("incomplete_case");
  if (record.installation_ref !== expected.installation || record.dataset_ref !== expected.dataset ||
      record.target?.issuer !== expected.issuer || record.target?.origin !== "https://localhost:8080" ||
      record.subject_id !== String(account._id) || record.target?.expected_subject_id !== String(account._id) ||
      record.target?.required_account_type !== "anonymous" ||
      !required(record.target?.controlled_destination_verified_at)) refuse("target_conflict");
  const evidence = record.evidence;
  if (evidence?.existence_status !== "verified" ||
      ![evidence.source_ref, evidence.trusted_provenance_basis, evidence.independent_association_basis,
        evidence.verified_by, evidence.verified_at].every(required)) refuse("evidence_required");
  if (record.approval?.status !== "approved" ||
      ![record.approval?.approved_by, record.approval?.approved_at].every(required)) refuse("approval_required");
  if (evidence.account_fingerprint !== fingerprint(account)) refuse("account_changed");
  if (record.issuance?.status !== "not_issued") refuse("issuance_already_started");
}

async function execute(command, file, output, expected, deps) {
  file = path.resolve(file);
  let record = loadCase(file);
  if (!["inspect", "status", "issue"].includes(command)) refuse("invalid_command");
  if (command === "status") return { state: record.state, locked: fs.existsSync(`${file}.lock`),
    issuance: record.issuance?.status || "not_issued", reconciliation_required:
      record.state === "issued_unconfirmed" || fs.existsSync(`${file}.lock`) };
  if (!required(expected.installation) || !required(expected.dataset) || !required(expected.issuer)) refuse("installation_required");
  if (command === "inspect") {
    const account = await deps.findAccount(record.subject_id);
    return { state: record.state, account_exists: Boolean(account), anonymous: account?.type === "anonymous",
      account_fingerprint: account ? fingerprint(account) : null };
  }
  const lockFile = `${file}.lock`;
  let lock;
  try { lock = fs.openSync(lockFile, "wx", 0o600); } catch (_) { refuse("case_locked"); }
  try {
    record = loadCase(file);
    const account = await deps.findAccount(record.subject_id);
    eligible(record, account, expected);
    if (!required(output) || path.basename(output) !== output || output === path.basename(file) ||
        output.endsWith(".lock") || output.endsWith(".tmp")) refuse("unsafe_output");
    const target = path.join(path.dirname(file), output);
    if (fs.existsSync(target) || fs.lstatSync(path.dirname(target)).isSymbolicLink()) refuse("output_exists");
    const now = new Date();
    record.state = "issued_unconfirmed";
    record.issuance = { status: "issued_unconfirmed", issuance_ref: crypto.randomUUID(),
      issued_at: now.toISOString(), expires_at: null, private_output_ref: output,
      ambiguity: "Reconcile the private output before any further issuance." };
    // Durable intent precedes signing/output. A crash never enables blind retry.
    storeCase(file, record);
    const token = deps.issue(account);
    const claims = deps.verify(token);
    if (claims.sub !== String(account._id) || claims.exp - claims.iat !== 604800) refuse("issuer_profile_mismatch");
    const bundle = { schema_version: 1, case_ref: record.case_ref, installation_ref: record.installation_ref,
      intended_origin: record.target.origin, issued_at: new Date(claims.iat * 1000).toISOString(),
      expires_at: new Date(claims.exp * 1000).toISOString(), token };
    const fd = fs.openSync(target, "wx", 0o600);
    try { fs.writeFileSync(fd, JSON.stringify(bundle) + "\n"); fs.fsyncSync(fd); }
    finally { fs.closeSync(fd); }
    record.state = "issued";
    Object.assign(record.issuance, { status: "issued", issued_at: bundle.issued_at,
      expires_at: bundle.expires_at, ambiguity: null });
    storeCase(file, record);
    return { state: "issued", output_created: true };
  } finally { fs.closeSync(lock); fs.unlinkSync(lockFile); }
}

if (require.main === module) {
  (async () => {
    const [command, file, installation, dataset, output] = process.argv.slice(2);
    if (!command || !file) refuse("usage_inspect_issue_status_case_installation_dataset_output");
    const mongoose = require("mongoose");
    try {
      if (command !== "status") await mongoose.connect(process.env.MONGO_URI, { serverSelectionTimeoutMS: 5000 });
      const auth = require("../auth/auth");
      const User = require("../models/user");
      const result = await execute(command, file, output, { installation, dataset, issuer: process.env.JWT_ISSUER }, {
        findAccount: async (id) => /^[a-f0-9]{24}$/.test(id || "") ? User.findById(id).lean().exec() : null,
        issue: auth.get_jwt, verify: auth.verify_session,
      });
      process.stdout.write(JSON.stringify(result) + "\n");
    } finally { await mongoose.disconnect(); }
  })().catch((error) => {
    // Driver errors can contain credentials/URLs: emit only our closed error codes.
    process.stderr.write(JSON.stringify({ error: /^[a-z_]+$/.test(error.code || "") ? error.code : "recovery_failed" }) + "\n");
    process.exitCode = 1;
  });
}
module.exports = { execute, eligible, fingerprint, loadCase };
