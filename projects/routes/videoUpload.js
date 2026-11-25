const express = require("express");
const crypto = require("node:crypto");
const Busboy = require("busboy");
const axios = require("axios");
const { checkSharePermission, requireEditPermission } = require("../middleware/shareAuth");
const { requireProjectVersion } = require("../middleware/projectVersion");
const enforcePresenceLimit = require("../middleware/enforcePresenceLimit");
const { VIDEO_LIMITS, isVideoFile } = require("../utils/video");
const engine = require("../utils/videoUploadEngine");
const Upload = require("../models/upload");
const Project = require("../models/project");

const router = express.Router();
const agent = require("../tls/pkiTls").clientAgent({ keepAlive: true });

async function profile(req, res, next) {
  try {
    const response = await axios.get(`https://users:10001/${req.internalIdentity.sub}/type`, { httpsAgent: agent });
    req.videoUserType = response.data.type;
    const limits = VIDEO_LIMITS[req.videoUserType];
    if (!limits) return res.status(403).jsonp("Anonymous users cannot upload videos. Create an account to edit video.");
    req.videoMaxBytes = limits.maxSizeMB * 1024 * 1024;
    next();
  } catch (_) { res.status(503).jsonp("Profile unavailable"); }
}

async function currentVideoType(callerId) {
  const response = await axios.get(`https://users:10001/${callerId}/type`,
    { httpsAgent: agent, timeout: 5000 });
  return response.data.type;
}

function declaredWithinLimits(attempt, type) {
  const limits = VIDEO_LIMITS[type];
  return limits && attempt.size <= limits.maxSizeMB * 1024 * 1024 &&
    attempt.declaredDuration <= limits.maxDurationS &&
    attempt.declaredWidth <= limits.maxWidth && attempt.declaredHeight <= limits.maxHeight;
}

const beforeBody = [checkSharePermission, requireEditPermission, enforcePresenceLimit, requireProjectVersion, profile];

function tokenHash(token) {
  if (!/^[a-f0-9]{64}$/.test(token || "")) return null;
  return crypto.createHash("sha256").update(token).digest("hex");
}

async function directAttempt(req) {
  const hash = tokenHash(req.params.token);
  if (!hash) return null;
  return Upload.findOne({ tokenHash: hash, callerId: req.internalIdentity.sub,
    ...(req.params.user ? { ownerId: req.params.user, projectId: req.params.project } : {}),
    transport: "direct" });
}

router.post("/:user/:project/video/uploads", ...beforeBody, async (req, res) => {
  const { name, size, type, duration, width, height } = req.body || {};
  const limits = VIDEO_LIMITS[req.videoUserType];
  if (typeof name !== "string" || name.length > 255 || !isVideoFile(name, type) ||
      !["video/mp4", "video/quicktime", "video/webm"].includes(type) ||
      !Number.isSafeInteger(size) || size < 1 || size > req.videoMaxBytes ||
      !Number.isFinite(duration) || duration <= 0 || duration > limits.maxDurationS ||
      !Number.isSafeInteger(width) || width < 1 || width > limits.maxWidth ||
      !Number.isSafeInteger(height) || height < 1 || height > limits.maxHeight) {
    return res.status(size > req.videoMaxBytes ? 413 : 400).jsonp("Invalid video metadata");
  }
  const token = crypto.randomBytes(32).toString("hex");
  try {
    const attempt = await engine.reserve(req.params.user, req.params.project,
      req.internalIdentity.sub, req.videoMaxBytes, req.videoUserType, req.expectedVersion,
      "direct", req.query.share || "", req.projectDoc.uploadBarrier || 0);
    if (!attempt) return res.status(429).jsonp("Upload capacity reached");
    const extension = require("node:path").extname(name).toLowerCase();
    await Upload.updateOne({ _id: attempt._id, state: "created" }, { $set: {
      tokenHash: crypto.createHash("sha256").update(token).digest("hex"), name, mime: type,
      size, objectName: `${crypto.randomUUID()}${extension}`, stage: "staging",
      declaredDuration: duration, declaredWidth: width, declaredHeight: height,
    } });
    res.status(201).json({ token, expiresIn: 300, uploadUrl: `/api-gateway/uploads/${token}` });
  } catch (_) { res.status(503).jsonp("Upload unavailable"); }
});

// Called by the gateway's nginx auth subrequest. It claims the one-use token before any
// body reaches SeaweedFS. The signed S3 URL never reaches the browser.
router.post("/video/uploads/:token/authorize", async (req, res) => {
  const attempt = await directAttempt(req);
  if (!attempt) return res.sendStatus(404);
  if (attempt.tokenExpiresAt <= new Date() || attempt.deadline <= new Date()) return res.sendStatus(410);
  if (["cancelled", "expired", "failed", "rejected"].includes(attempt.state)) return res.sendStatus(410);
  if (attempt.state !== "created") return res.sendStatus(409);
  const length = Number(req.body?.length);
  if (!Number.isSafeInteger(length) || length < 1) return res.sendStatus(411);
  if (length !== attempt.size || length > attempt.maxBytes) return res.sendStatus(413);
  if (req.body?.type !== attempt.mime) return res.sendStatus(400);
  const project = await Project.findOne({ _id: attempt.projectId, user_id: attempt.ownerId }).lean();
  if (!project) return res.sendStatus(404);
  if (project.version !== attempt.expectedVersion || project.uploadBarrier !== attempt.barrier) return res.sendStatus(409);
  if (attempt.shareId && !project.sharedLinks?.some((link) =>
    link.id === attempt.shareId && link.permission === "edit" && !link.revoked)) return res.sendStatus(403);
  let type;
  try { type = await currentVideoType(attempt.callerId); }
  catch (_) { return res.sendStatus(503); }
  if (!declaredWithinLimits(attempt, type)) return res.sendStatus(403);
  const claimed = await engine.claim(attempt._id, attempt.ownerId, attempt.projectId, attempt.callerId);
  if (!claimed) return res.sendStatus(409);
  try {
    const response = await axios.get(`${engine.objectPath(claimed)}/put-url`, {
      httpsAgent: agent, timeout: 5000, params: { size: claimed.size, type: claimed.mime },
    });
    return res.set("X-Upload-Target", response.data.url).sendStatus(204);
  } catch (error) {
    console.error("Direct upload signing failed", error.response?.status || error.code || error.name);
    await engine.fail(claimed, "Upload URL unavailable");
    return res.sendStatus(503);
  }
});

router.post("/:user/:project/video/uploads/:token/confirm", async (req, res) => {
  const attempt = await directAttempt(req);
  if (!attempt) return res.sendStatus(404);
  if (attempt.state === "ready" || attempt.state === "ready_hash_pending") {
    return res.set("X-Project-Version", String(attempt.resultVersion)).sendStatus(204);
  }
  if (attempt.cancelRequested) return res.sendStatus(410);
  if (["failed", "cancelled", "expired", "rejected"].includes(attempt.state) ||
      attempt.deadline <= new Date()) return res.sendStatus(410);
  if (attempt.state !== "receiving") return res.sendStatus(409);
  const id = String(attempt._id);
  engine.active.add(id);
  try {
    let type;
    try { type = await currentVideoType(attempt.callerId); }
    catch (_) { return res.sendStatus(503); }
    if (!declaredWithinLimits(attempt, type)) {
      await engine.fail(attempt, "Video profile no longer permits upload", "rejected");
      return res.sendStatus(403);
    }
    const staging = engine.objectPath(attempt);
    let head;
    try { head = await axios.head(staging, { httpsAgent: agent, timeout: 10000 }); }
    catch (error) {
      if (error.response?.status === 404) return res.status(409).jsonp("Upload body incomplete");
      throw error;
    }
    if (Number(head.headers["content-length"]) !== attempt.size) throw new Error("Video size mismatch");
    const candidate = await Upload.findOneAndUpdate({ _id: attempt._id, state: "receiving",
      cancelRequested: { $ne: true } },
      { $set: { stage: "src", state: "promoting" } }, { new: true });
    if (!candidate) return res.sendStatus(409);
    await axios.post(`${engine.storage}/${attempt.ownerId}/${attempt.projectId}/${attempt.objectName}/promote`,
      null, { httpsAgent: agent, timeout: 30000 });
    await Upload.updateOne({ _id: attempt._id, state: "promoting" }, { $set: { state: "received" } });
    const candidateHead = await axios.head(engine.objectPath(candidate), { httpsAgent: agent, timeout: 10000 });
    const version = await engine.finalize({ ...candidate.toObject(),
      probeUrl: candidateHead.headers["x-video-read-url"] }, type);
    try {
      await axios.delete(staging, { httpsAgent: agent, timeout: 10000 });
      await Upload.updateOne({ _id: attempt._id }, { $set: { cleanup: "cleaned" } });
    } catch (_) {
      await Upload.updateOne({ _id: attempt._id }, { $set: { cleanup: "cleanup_pending" } });
    }
    res.set("X-Project-Version", String(version)).sendStatus(204);
  } catch (error) {
    await engine.fail(attempt, error.message, "rejected");
    if (!res.headersSent) res.status(engine.isServerError(error) ? 503 :
      error.message === "Project version conflict" ? 409 : 400).jsonp(error.message);
  } finally { engine.active.delete(id); }
});

router.post("/:user/:project/video/uploads/:token/cancel", async (req, res) => {
  const attempt = await directAttempt(req);
  if (!attempt) return res.sendStatus(404);
  if (attempt.state === "created") {
    const cancelled = await Upload.findOneAndUpdate({ _id: attempt._id, state: "created" },
      { $set: { state: "cancelled" } }, { new: true });
    if (!cancelled) return res.sendStatus(409);
    await engine.fail(cancelled, "Upload cancelled", "cancelled");
    return res.sendStatus(204);
  }
  if (attempt.state === "receiving") {
    try {
      const head = await axios.head(engine.objectPath(attempt), { httpsAgent: agent, timeout: 5000 });
      if (Number(head.headers["content-length"]) === attempt.size) {
        const cancelled = await Upload.findOneAndUpdate({ _id: attempt._id, state: "receiving" },
          { $set: { state: "cancelled" } }, { new: true });
        if (!cancelled) return res.sendStatus(409);
        await engine.fail(cancelled, "Upload cancelled", "cancelled");
        return res.sendStatus(204);
      }
    } catch (_) { /* An incomplete PUT is not visible yet; leave its writer fenced. */ }
    // The nginx→SeaweedFS writer may still finish after the browser disconnects.
    // Fence confirmation now; the 900-second deadline fences cleanup of that writer.
    await Upload.updateOne({ _id: attempt._id, state: "receiving" },
      { $set: { cancelRequested: true } });
    return res.sendStatus(204);
  }
  if (["cancelled", "expired", "failed", "rejected"].includes(attempt.state)) return res.sendStatus(204);
  return res.sendStatus(409);
});

router.post("/:user/:project/video/preflight", ...beforeBody, async (req, res) => {
  try {
    const attempt = await engine.reserve(req.params.user, req.params.project,
      req.internalIdentity.sub, req.videoMaxBytes, req.videoUserType, req.expectedVersion, "legacy",
      req.query.share || "", req.projectDoc.uploadBarrier || 0);
    if (!attempt) return res.status(429).jsonp("Upload capacity reached");
    res.json({ uploadId: String(attempt._id), maxBytes: req.videoMaxBytes });
  } catch (_) { res.status(503).jsonp("Upload unavailable"); }
});

router.post("/:user/:project/video/cancel", checkSharePermission, requireEditPermission, async (req, res) => {
  const Upload = require("../models/upload");
  const attempt = await Upload.findOne({ _id: req.headers["x-upload-id"], ownerId: req.params.user,
    projectId: req.params.project, callerId: req.internalIdentity.sub, state: "created" });
  if (attempt) await engine.fail(attempt, "Upload cancelled", "cancelled");
  res.sendStatus(204);
});

function parseOne(req, maxBytes, onFile, remainingMs) {
  return new Promise((resolve, rejectParse) => {
    let parser;
    let fileStream;
    let timeout;
    let idle;
    let settled = false;
    // Any failure closes the file stream, so the storage PUT fed by it aborts at once instead
    // of waiting for its own timeout while the attempt keeps its upload slot.
    const reject = (error) => {
      if (fileStream && !fileStream.destroyed) fileStream.destroy(error);
      if (settled) return;
      settled = true;
      clearTimeout(timeout); clearTimeout(idle);
      rejectParse(error);
    };
    try {
      parser = Busboy({ headers: req.headers, limits: {
        fileSize: maxBytes + 1, files: 1, fields: 0, parts: 3,
      } });
    } catch (error) {
      console.error("Video multipart parser rejected content type", req.headers["content-type"], error.message);
      reject(new Error("Invalid video upload")); return;
    }
    let seen = false;
    let job;
    timeout = setTimeout(() => { req.destroy(); reject(new Error("Video upload timed out")); }, remainingMs);
    idle = setTimeout(() => { req.destroy(); reject(new Error("Video upload stalled")); }, 30000);
    req.on("data", () => {
      clearTimeout(idle);
      idle = setTimeout(() => { req.destroy(); reject(new Error("Video upload stalled")); }, 30000);
    });
    parser.on("file", (field, stream, info) => {
      if (seen || field !== "video" || !isVideoFile(info.filename, info.mimeType)) {
        stream.resume(); reject(new Error("Only video files (.mp4, .mov, .webm) can be uploaded here.")); return;
      }
      seen = true;
      fileStream = stream;
      stream.on("limit", () => {
        stream.destroy(new Error("Video too large"));
        reject(new Error("Video too large"));
      });
      job = onFile(stream, info.filename, info.mimeType);
      req.uploadStorageTask = job;
      job.catch(reject);
    });
    parser.on("error", reject);
    parser.on("filesLimit", () => reject(new Error("Invalid video upload")));
    parser.on("fieldsLimit", () => reject(new Error("Invalid video upload")));
    parser.on("partsLimit", () => reject(new Error("Invalid video upload")));
    parser.on("finish", async () => {
      clearTimeout(timeout); clearTimeout(idle);
      if (!seen) { reject(new Error("No file found")); return; }
      try { const value = await job; settled = true; resolve(value); } catch (error) { reject(error); }
    });
    req.on("aborted", () => reject(new Error("Upload interrupted")));
    req.on("close", () => { if (!req.complete) reject(new Error("Upload interrupted")); });
    req.pipe(parser);
  });
}

router.post("/:user/:project/video", async (req, res) => {
  const attempt = await engine.claim(req.headers["x-upload-id"], req.params.user,
    req.params.project, req.internalIdentity.sub);
  if (!attempt) {
    const status = req.internalIdentity.sub === req.params.user ? 409 : 403;
    return res.status(status).jsonp(status === 403 ? "Upload not permitted" : "Upload expired or already used");
  }
  const id = String(attempt._id);
  engine.active.add(id);
  try {
    const stored = await parseOne(req, attempt.maxBytes, async (stream, name, mime) => {
      return engine.store(attempt, stream, name, mime, Number(req.headers["content-length"]));
    }, Math.max(1, 600000 - (Date.now() - attempt.updatedAt.getTime())));
    const version = await engine.finalize(stored, attempt.userType);
    res.set("X-Project-Version", String(version)).sendStatus(204);
  } catch (error) {
    // Do not remove the candidate while its writer may still complete.
    if (req.uploadStorageTask) await req.uploadStorageTask.catch(() => {});
    await engine.fail(attempt, error.message);
    if (!res.headersSent) {
      if (engine.isServerError(error)) {
        // Same answer as the legacy route when storing the media failed.
        res.status(501).jsonp("Error storing image");
      } else {
        const status = error.message === "Project version conflict" ? 409 :
          error.message === "Video too large" ? 413 : 400;
        res.status(status).jsonp(error.message);
      }
    }
  } finally { engine.active.delete(id); }
});

module.exports = router;
