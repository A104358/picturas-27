const express = require("express");
const Busboy = require("busboy");
const axios = require("axios");
const { checkSharePermission, requireEditPermission } = require("../middleware/shareAuth");
const { requireProjectVersion } = require("../middleware/projectVersion");
const enforcePresenceLimit = require("../middleware/enforcePresenceLimit");
const { VIDEO_LIMITS, isVideoFile } = require("../utils/video");
const engine = require("../utils/videoUploadEngine");

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

const beforeBody = [checkSharePermission, requireEditPermission, enforcePresenceLimit, requireProjectVersion, profile];

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
