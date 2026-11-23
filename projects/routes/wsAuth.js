const express = require("express");
const Project = require("../models/project");
const pki = require("../tls/pkiTls");
const { performance } = require("node:perf_hooks");

const router = express.Router();
const MAX_BYTES = 65536;
const id = (value) => typeof value === "string" && /^[a-f\d]{24}$/i.test(value);
const reference = (value) => typeof value === "string" && /^[\w-]{1,80}$/.test(value);
const telemetry = { batches: 0, evaluations: 0, reads: 0, failures: 0, dbTotalMs: 0, dbMaxMs: 0 };
setInterval(() => console.log(JSON.stringify({ type: "ws-authorization-db", ...telemetry })), 10000).unref();

// D4 / WS-C1: this peer can only delegate verified sessions to this read-only
// endpoint. It never receives the HS256 secret or the gateway signing key.
router.use((req, res, next) => {
  if (!pki.peerAllowed(req, ["ws_gateway"])) return res.sendStatus(403);
  next();
});
router.use(express.json({ limit: MAX_BYTES, strict: true, inflate: false }));

router.post("/projects/:projectId/authorize", async (req, res) => {
  const { requestId, evaluations } = req.body || {};
  if (!id(req.params.projectId) || !reference(requestId) || !Array.isArray(evaluations) ||
      !evaluations.length || evaluations.length > 50 ||
      new Set(evaluations.map((item) => item?.ref)).size !== evaluations.length ||
      evaluations.some((item) => !item || !reference(item.ref) ||
        !Number.isSafeInteger(item.generation) || item.generation < 0 ||
        !Number.isSafeInteger(item.sequence) || item.sequence < 0)) {
    return res.status(400).json({ error: "invalid_request" });
  }
  let project;
  let unavailable = false;
  const started = performance.now();
  telemetry.batches++;
  telemetry.evaluations += evaluations.length;
  telemetry.reads++;
  try {
    // Always the primary's current state; no presence/editor-slot mutation.
    project = await Project.findById(req.params.projectId)
      .select("user_id version sharedLinks").read("primary").maxTimeMS(800).lean().exec();
  } catch (_) {
    unavailable = true;
    telemetry.failures++;
  } finally {
    const duration = performance.now() - started;
    telemetry.dbTotalMs += duration;
    telemetry.dbMaxMs = Math.max(telemetry.dbMaxMs, duration);
  }
  const decisions = evaluations.map((item) => {
    const result = { ref: item.ref, generation: item.generation, sequence: item.sequence };
    if (unavailable) return { ...result, decision: "unavailable" };
    let permission;
    if (project && id(item.sub) && Number.isInteger(item.exp) && item.exp * 1000 > Date.now()) {
      if (item.access?.kind === "owner" && String(project.user_id) === item.sub) permission = "owner";
      if (item.access?.kind === "share" && typeof item.access.shareId === "string") {
        const link = project.sharedLinks?.find((entry) => entry.id === item.access.shareId && !entry.revoked);
        if (link && ["read", "edit"].includes(link.permission)) permission = link.permission;
      }
    }
    return { ...result, decision: permission ? "allow" : "deny", ...(permission ? { permission } : {}) };
  });
  const body = JSON.stringify({ requestId, projectId: req.params.projectId,
    projectVersion: project?.version ?? null, decisions });
  if (Buffer.byteLength(body) > MAX_BYTES) return res.status(413).json({ error: "response_too_large" });
  res.type("json").send(body);
});

router.use((err, req, res, next) => {
  res.status(err.status === 413 ? 413 : 400).json({ error: "invalid_request" });
});
router.use((req, res) => res.sendStatus(403));
module.exports = router;
