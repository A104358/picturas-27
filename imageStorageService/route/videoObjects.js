const express = require("express");
const s3 = require("../services/s3Client");
const { BUCKET, objectKey, ensureBucket } = require("../services/storage");
const signVideoPut = require("../services/signVideoPut");

const router = express.Router();
const stages = new Set(["staging", "src"]);

router.get("/:userId/:projectId/staging/:fileName/put-url", async (req, res) => {
  const location = target({ params: { ...req.params, stage: "staging" } }, res);
  if (!location) return;
  const size = Number(req.query.size);
  const type = req.query.type;
  if (!Number.isSafeInteger(size) || size < 1 || size > 1024 * 1024 * 1024 ||
      !["video/mp4", "video/quicktime", "video/webm"].includes(type)) {
    return res.status(400).json({ error: "Invalid upload metadata" });
  }
  try {
    const url = signVideoPut({ ...location, size, type });
    res.json({ url });
  } catch (error) {
    console.error("Video upload URL failed", error.code || error.name);
    res.status(502).json({ error: "Video upload URL failed" });
  }
});

router.post("/:userId/:projectId/:fileName/promote", async (req, res) => {
  const source = target({ params: { ...req.params, stage: "staging" } }, res);
  if (!source) return;
  const candidate = target({ params: { ...req.params, stage: "src" } }, res);
  if (!candidate) return;
  try {
    await s3.copyObject({ ...candidate, CopySource: `/${BUCKET}/${source.Key}` }).promise();
    res.sendStatus(201);
  } catch (_) {
    res.status(502).json({ error: "Video promotion failed" });
  }
});

function target(req, res) {
  const { userId, projectId, stage, fileName } = req.params;
  if (!stages.has(stage) || !/^[a-f0-9-]{36}\.(mp4|mov|webm)$/.test(fileName) ||
      !/^[a-f0-9]{24}$/.test(userId) || !/^[a-f0-9]{24}$/.test(projectId)) {
    res.status(400).json({ error: "Invalid video object" });
    return null;
  }
  return { Bucket: BUCKET, Key: objectKey(userId, projectId, stage, fileName) };
}

// Multipart parts of large uploads: size (MiB, S3 minimum 5) and how many are sent at once.
const PART_MIB = Math.max(5, Number(process.env.VIDEO_S3_PART_MIB) || 5);
const PART_QUEUE = Math.max(1, Number(process.env.VIDEO_S3_PART_QUEUE) || 1);

// Each multipart part is a 5 MiB buffer outside the V8 heap; V8 frees them only at its next
// collection, so a fresh process grows by several parts per upload (U01). With --expose-gc
// (docker-compose.yaml), collect after every 16 MiB sent so at most a few parts are alive.
function releasePartBuffers(task) {
  if (typeof global.gc !== "function") return;
  let next = 16 * 1024 * 1024;
  task.on("httpUploadProgress", (progress) => {
    if (progress.loaded < next) return;
    next = progress.loaded + 16 * 1024 * 1024;
    setImmediate(() => global.gc());
  });
}

router.put("/:userId/:projectId/:stage/:fileName", async (req, res) => {
  const location = target(req, res);
  if (!location) return;
  try {
    await ensureBucket();
    const partSize = req.headers["x-declared-small-upload"] === "1" ? 11 : PART_MIB;
    const task = s3.upload({ ...location, Body: req, ContentType: req.headers["content-type"] || "application/octet-stream" },
      { partSize: partSize * 1024 * 1024, queueSize: PART_QUEUE });
    req.on("aborted", () => task.abort());
    releasePartBuffers(task);
    await task.promise();
    res.sendStatus(201);
  } catch (_) {
    if (!res.headersSent) res.status(502).json({ error: "Video storage failed" });
  }
});

router.head("/:userId/:projectId/:stage/:fileName", async (req, res) => {
  const location = target(req, res);
  if (!location) return;
  try {
    const object = await s3.headObject(location).promise();
    const readUrl = await s3.getSignedUrlPromise("getObject", { ...location, Expires: 60 });
    res.set("Content-Length", String(object.ContentLength))
      .set("X-Video-Read-Url", readUrl).status(200).end();
  } catch (error) {
    res.sendStatus(error.statusCode === 404 ? 404 : 502);
  }
});

router.delete("/:userId/:projectId/:stage/:fileName", async (req, res) => {
  const location = target(req, res);
  if (!location) return;
  try {
    let keyMarker;
    let uploadIdMarker;
    for (let page = 0; page < 100; page++) {
      const listed = await s3.listMultipartUploads({
        Bucket: BUCKET, Prefix: location.Key, MaxUploads: 100,
        ...(keyMarker ? { KeyMarker: keyMarker, UploadIdMarker: uploadIdMarker } : {}),
      }).promise();
      for (const upload of listed.Uploads || []) {
        if (upload.Key !== location.Key) continue;
        try { await s3.abortMultipartUpload({ ...location, UploadId: upload.UploadId }).promise(); }
        catch (error) { if (error.statusCode !== 404) throw error; }
      }
      if (!listed.IsTruncated) break;
      if (page === 99) throw new Error("Multipart cleanup pagination limit");
      keyMarker = listed.NextKeyMarker;
      uploadIdMarker = listed.NextUploadIdMarker;
    }
    await s3.deleteObject(location).promise();
    res.sendStatus(204);
  } catch (_) {
    res.sendStatus(502);
  }
});

router.get("/:userId/:projectId/:stage/:fileName/url", async (req, res) => {
  const location = target(req, res);
  if (!location) return;
  try {
    const url = await s3.getSignedUrlPromise("getObject", { ...location, Expires: 60 });
    res.json({ url });
  } catch (_) {
    res.status(502).json({ error: "Video URL failed" });
  }
});

module.exports = router;
