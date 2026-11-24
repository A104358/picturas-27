const crypto = require("node:crypto");
const http = require("node:http");
const https = require("node:https");
const { execFile } = require("node:child_process");
const axios = require("axios");
const fs = require("node:fs");
const path = require("node:path");
const { PassThrough } = require("node:stream");
const Upload = require("../models/upload");
const UploadSlot = require("../models/uploadSlot");
const Project = require("../models/project");
const mongoose = require("mongoose");
const { validateVideo, videoOutputName } = require("./video");

const storage = "https://img_storage:11000/video-objects";
const agent = require("../tls/pkiTls").clientAgent({ keepAlive: true });
const seaweedAgent = new https.Agent({
  ca: fs.readFileSync("/run/secrets/pki/ca.crt"), servername: "seaweedfs", maxCachedSessions: 0,
  keepAlive: true,
});
const active = new Set();
let hashPumpBusy = false;
let admissions = Promise.resolve();
let slotsReady;

function ensureSlots() {
  if (!slotsReady) {
    slotsReady = (async () => {
      for (let n = 1; n <= 3; n++) {
        try { await UploadSlot.updateOne({ _id: n }, { $setOnInsert: { uploadId: null } }, { upsert: true }); }
        catch (error) { if (error.code !== 11000) throw error; }
      }
    })().catch((error) => { slotsReady = null; throw error; });
  }
  return slotsReady;
}

mongoose.connection.asPromise().then(() => ensureSlots()).catch((error) => {
  console.error("Upload slots initialization failed", error.code || error.name);
});

// Storage and infrastructure failures are not the client's fault: callers answer them as
// the legacy route did (501), never as a validation error (400).
function serverError(message) {
  const error = new Error(message);
  error.serverSide = true;
  return error;
}

function isServerError(error) {
  return Boolean(error?.serverSide || error?.isAxiosError || /^Mongo|^Mongoose/.test(error?.name || ""));
}

function objectPath(upload) {
  return `${storage}/${upload.ownerId}/${upload.projectId}/${upload.stage}/${upload.objectName}`;
}

async function reserve(ownerId, projectId, callerId, maxBytes, userType, expectedVersion, transport, shareId = "", barrier = 0) {
  let unlock;
  const previous = admissions;
  admissions = new Promise((resolve) => { unlock = resolve; });
  await previous;
  try {
    await ensureSlots();
    if (await Upload.countDocuments() >= 4096) return null;
    const id = new mongoose.Types.ObjectId();
    const deadline = new Date(Date.now() + 900000);
    const slot = await UploadSlot.findOneAndUpdate({ uploadId: null },
      { $set: { uploadId: id, leaseUntil: deadline } }, { new: true });
    if (!slot) return null;
    try {
      return await Upload.create({
        _id: id, ownerId, projectId, callerId, transport, maxBytes, userType,
        expectedVersion, shareId, barrier, slot: slot._id,
        state: "created", deadline, tokenExpiresAt: new Date(Date.now() + 300000),
      });
    } catch (error) {
      await UploadSlot.updateOne({ _id: slot._id, uploadId: id },
        { $set: { uploadId: null, leaseUntil: null } });
      throw error;
    }
  } finally { unlock(); }
}

async function release(attempt) {
  await UploadSlot.updateOne({ uploadId: attempt._id }, { $set: { uploadId: null, leaseUntil: null } });
}

async function claim(id, ownerId, projectId, callerId) {
  return Upload.findOneAndUpdate({
    _id: id, ownerId, projectId, callerId, state: "created", deadline: { $gt: new Date() },
    tokenExpiresAt: { $gt: new Date() },
  }, { $set: { state: "receiving" } }, { new: true });
}

async function store(attempt, stream, name, mime, declaredBodyBytes) {
  const extension = path.extname(name).toLowerCase();
  const objectName = `${crypto.randomUUID()}${extension}`;
  const stage = attempt.transport === "legacy" ? "src" : "staging";
  attempt = await Upload.findOneAndUpdate({ _id: attempt._id, state: "receiving" },
    { $set: { name, mime, objectName, stage } }, { new: true });
  const url = objectPath(attempt);
  const small = Number.isSafeInteger(declaredBodyBytes) && declaredBodyBytes > 0 &&
    declaredBodyBytes <= 11 * 1024 * 1024;
  const response = await axios.put(url, stream, {
    httpsAgent: agent, headers: {
      "Content-Type": mime,
      ...(small ? { "X-Declared-Small-Upload": "1" } : {}),
    }, maxBodyLength: Infinity,
    maxRedirects: 0,
    timeout: 600000, validateStatus: () => true,
  });
  if (response.status !== 201) {
    console.error("Video storage failed", response.status);
    throw serverError("Video storage failed");
  }
  const head = await axios.head(url, { httpsAgent: agent, timeout: 10000 });
  const size = Number(head.headers["content-length"]);
  if (!Number.isSafeInteger(size) || size <= 0 || size > attempt.maxBytes) {
    throw new Error("Video too large");
  }
  await Upload.updateOne({ _id: attempt._id, state: "receiving" },
    { $set: { state: "received", size } });
  return { ...attempt.toObject(), size, probeUrl: head.headers["x-video-read-url"] };
}

function metadata(raw, size) {
  const streams = raw.streams || [];
  const video = streams.find((item) => item.codec_type === "video");
  const audio = streams.find((item) => item.codec_type === "audio");
  if (!video) throw new Error("The file has no video stream");
  const duration = Number(raw.format?.duration || video.duration || 0);
  const [n, d] = String(video.avg_frame_rate || video.r_frame_rate || "0/1").split("/");
  return {
    duration, width: video.width, height: video.height,
    fps: Number(d) ? Math.round(Number(n) / Number(d) * 100) / 100 : 0,
    video_codec: video.codec_name, audio_codec: audio?.codec_name || null,
    format_name: raw.format?.format_name, size_bytes: size,
  };
}

// SeaweedFS answers an open-ended range (`bytes=N-`) by reading the rest of the object into
// memory, even when the client closes after a few MiB: +~800 MiB for a 500 MiB object (D-24).
// Objects are therefore read in bounded windows, one at a time, on the same connection.
const READ_WINDOW = 4 * 1024 * 1024;

function rangedStream(url, start, end, { deadline, onBytes } = {}) {
  const out = new PassThrough({ highWaterMark: 1024 * 1024 });
  let current = null;
  let closed = false;
  out.on("close", () => { closed = true; current?.destroy(); });
  (async () => {
    for (let pos = start; pos <= end && !closed; pos += READ_WINDOW) {
      const last = Math.min(end, pos + READ_WINDOW - 1);
      const response = await axios.get(url, {
        httpsAgent: seaweedAgent, responseType: "stream", maxRedirects: 0,
        headers: { Range: `bytes=${pos}-${last}` },
        timeout: deadline ? Math.max(1, deadline - Date.now()) : 30000,
      });
      current = response.data;
      for await (const chunk of response.data) {
        if (closed) break;
        if (onBytes && onBytes(chunk.length) === false) { out.destroy(); break; }
        if (!out.write(chunk)) {
          await new Promise((resolve) => { out.once("drain", resolve); out.once("close", resolve); });
        }
      }
      current = null;
    }
    if (!closed) out.end();
  })().catch((error) => out.destroy(error));
  return out;
}

async function probe(url, size) {
  // ffprobe can issue several Range requests. Count bytes across all of them.
  const budget = size * 2 + 16 * 1024 * 1024;
  const deadline = Date.now() + 15000;
  let used = 0;
  const server = http.createServer((req, res) => {
    if (req.url !== "/probe" || !["GET", "HEAD"].includes(req.method) || Date.now() >= deadline) {
      res.writeHead(404).end(); return;
    }
    let start = 0;
    let end = size - 1;
    const range = req.headers.range;
    if (range) {
      const match = /^bytes=(\d+)-(\d*)$/.exec(range);
      if (!match || Number(match[1]) >= size) {
        res.writeHead(416, { "content-range": `bytes */${size}` }).end(); return;
      }
      start = Number(match[1]);
      if (match[2]) end = Math.min(Number(match[2]), size - 1);
    }
    const headers = {
      "content-type": "video/mp4", "accept-ranges": "bytes", "content-length": String(end - start + 1),
    };
    if (range) headers["content-range"] = `bytes ${start}-${end}/${size}`;
    res.writeHead(range ? 206 : 200, headers);
    if (req.method === "HEAD") { res.end(); return; }
    const body = rangedStream(url, start, end, { deadline, onBytes: (n) => {
      used += n;
      return used <= budget && Date.now() < deadline;
    } });
    body.on("error", () => res.destroy());
    body.on("close", () => { if (!res.writableEnded) res.destroy(); });
    res.on("close", () => body.destroy());
    body.pipe(res);
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    const output = await new Promise((resolve, reject) => execFile("ffprobe", [
      "-v", "error", "-rw_timeout", "3000000", "-print_format", "json", "-show_format", "-show_streams",
      `http://127.0.0.1:${server.address().port}/probe`,
    ], { timeout: Math.max(1, deadline - Date.now()), maxBuffer: 10 * 1024 * 1024 },
    (error, stdout) => error ? reject(new Error("Unreadable or corrupted video file")) : resolve(stdout)));
    return metadata(JSON.parse(output), size);
  } finally { server.closeAllConnections(); server.close(); }
}

async function finalize(attempt, userType) {
  const validationDeadline = Date.now() + 180000;
  const probeUrl = attempt.probeUrl;
  attempt = await Upload.findOneAndUpdate({ _id: attempt._id, state: "received", deadline: { $gt: new Date() } },
    { $set: { state: "validating" } }, { new: true });
  if (!attempt) throw new Error("Upload expired or already used");
  if (typeof probeUrl !== "string" || !probeUrl.startsWith("https://seaweedfs:9000/")) {
    throw serverError("Video read URL unavailable");
  }
  const meta = await probe(probeUrl, attempt.size);
  const reason = validateVideo(meta, attempt.name, attempt.mime, userType);
  if (reason) throw new Error(reason);
  if (Date.now() >= validationDeadline) throw new Error("Video validation timed out");
  const ready = await Upload.findOneAndUpdate({ _id: attempt._id, state: "validating", deadline: { $gt: new Date() } },
    { $set: { state: "committing" } }, { new: true });
  if (!ready) throw new Error("Upload expired");
  const ogUri = `./images/users/${attempt.ownerId}/projects/${attempt.projectId}/src/${attempt.name}`;
  const filter = {
    _id: attempt.projectId, user_id: attempt.ownerId, version: attempt.expectedVersion,
    uploadBarrier: attempt.barrier,
    "imgs.og_uri": { $ne: ogUri },
  };
  if (attempt.shareId) filter.sharedLinks = { $elemMatch: {
    id: attempt.shareId, permission: "edit", revoked: false,
  } };
  const result = await Project.findOneAndUpdate(filter, { $push: { imgs: {
    og_uri: ogUri,
    new_uri: `./images/users/${attempt.ownerId}/projects/${attempt.projectId}/out/${videoOutputName(attempt.name)}`,
    og_img_key: attempt.objectName, media_type: "video", video: meta,
    hash_state: "ready_hash_pending",
  } }, $inc: { version: 1 } }, { new: true, maxTimeMS: Math.max(1, validationDeadline - Date.now()) });
  if (!result) {
    const current = await Project.findOne({ _id: attempt.projectId, user_id: attempt.ownerId },
      { version: 1, "imgs.og_uri": 1 }).lean();
    if (current?.version === attempt.expectedVersion &&
        current.imgs?.some((item) => item.og_uri === ogUri)) {
      throw new Error("This project already has a video with that name.");
    }
    throw new Error("Project version conflict");
  }
  const media = result.imgs.find((item) => item.og_uri === ogUri);
  await Upload.updateOne({ _id: attempt._id, state: "committing" },
    { $set: { state: "ready_hash_pending", mediaId: media._id, resultVersion: result.version } });
  return result.version;
}

async function fail(attempt, message, terminal = "failed") {
  const changed = await Upload.findOneAndUpdate({ _id: attempt._id,
    state: { $nin: ["ready", "ready_hash_pending"] } },
  { $set: { state: terminal, cleanup: "cleanup_pending", error: message } }, { new: true });
  if (changed) await cleanupOne(changed);
}

async function cleanupOne(attempt) {
  if (attempt.objectName) {
    // Fence any validation worker that has not won the conditional project commit.
    await Project.updateOne({ _id: attempt.projectId, user_id: attempt.ownerId },
      { $inc: { uploadBarrier: 1 } });
    const published = await Project.findOne({ _id: attempt.projectId, user_id: attempt.ownerId,
      "imgs.og_img_key": attempt.objectName }, { "imgs.$": 1, version: 1 });
    if (published?.imgs?.[0]) {
      await Upload.updateOne({ _id: attempt._id }, { $set: { state: "ready_hash_pending",
        mediaId: published.imgs[0]._id, resultVersion: published.version, cleanup: "cleaned" } });
      return;
    }
    try { await axios.delete(objectPath(attempt), { httpsAgent: agent, timeout: 10000 }); }
    catch (_) { await Upload.updateOne({ _id: attempt._id }, { $set: { cleanup: "cleanup_failed" } }); return; }
  }
  await Upload.updateOne({ _id: attempt._id }, { $set: { cleanup: "cleaned" } });
  await release(attempt);
}

async function hashOne(attempt) {
  const urlResponse = await axios.get(`${objectPath(attempt)}/url`, { httpsAgent: agent, timeout: 5000 });
  const hash = crypto.createHash("sha256");
  for await (const chunk of rangedStream(urlResponse.data.url, 0, attempt.size - 1)) hash.update(chunk);
  const sha = hash.digest("hex");
  await Project.updateOne({ _id: attempt.projectId, user_id: attempt.ownerId,
    "imgs._id": attempt.mediaId, "imgs.hash_state": "ready_hash_pending" },
  { $set: { "imgs.$.og_sha256": sha, "imgs.$.hash_state": "ready" }, $inc: { __v: 1 } });
  await Upload.updateOne({ _id: attempt._id, state: "ready_hash_pending" }, { $set: { state: "ready" } });
  await release(attempt);
}

async function maintain() {
  const committing = await Upload.find({ state: "committing" }).limit(50);
  for (const attempt of committing) {
    if (active.has(String(attempt._id)) || !attempt.objectName) continue;
    const project = await Project.findOne({ _id: attempt.projectId, user_id: attempt.ownerId,
      "imgs.og_img_key": attempt.objectName }, { "imgs.$": 1, version: 1 });
    if (project?.imgs?.[0]) {
      await Upload.updateOne({ _id: attempt._id, state: "committing" },
        { $set: { state: "ready_hash_pending", mediaId: project.imgs[0]._id,
          resultVersion: project.version } });
    }
  }
  const expired = await Upload.find({ state: { $in: ["created", "receiving", "received", "validating", "committing"] }, deadline: { $lte: new Date() } }).limit(50);
  for (const attempt of expired) {
    if (active.has(String(attempt._id))) continue;
    await fail(attempt, "Upload expired", "expired");
  }
  const unused = await Upload.find({ state: "created", tokenExpiresAt: { $lte: new Date() } }).limit(50);
  for (const attempt of unused) {
    if (!active.has(String(attempt._id))) await fail(attempt, "Upload token expired", "expired");
  }
  const dirty = await Upload.find({ cleanup: { $in: ["cleanup_pending", "cleanup_failed"] } }).limit(50);
  for (const attempt of dirty) {
    if (!active.has(String(attempt._id))) await cleanupOne(attempt);
  }
  // Keep the asynchronous hash outside the ready response's resource window.
  await Upload.deleteMany({ state: { $in: ["ready", "failed", "rejected", "expired", "cancelled"] },
    cleanup: { $in: ["cleaned", "none"] }, updatedAt: { $lt: new Date(Date.now() - 24 * 3600000) } });
}

async function pumpHash() {
  if (hashPumpBusy) return;
  hashPumpBusy = true;
  try {
    const pending = await Upload.findOne({ state: "ready_hash_pending",
      updatedAt: { $lte: new Date(Date.now() - 1000) } }).sort({ createdAt: 1 });
    if (!pending) return;
    active.add("hash");
    try { await hashOne(pending); }
    catch (error) {
      console.error("Background video hash failed", error.code || error.name || "error");
    } finally { active.delete("hash"); }
  } finally { hashPumpBusy = false; }
}

setInterval(() => pumpHash().catch((error) => {
  console.error("Background video hash pump failed", error.code || error.name || "error");
}), 1000).unref();

setInterval(() => maintain().catch((error) => {
  console.error("Upload maintenance failed", error.code || error.name || "error");
}), 5000).unref();

mongoose.connection.asPromise().then(async () => {
  const interrupted = await Upload.find({ state: { $in: ["receiving", "validating", "committing"] } }).limit(100);
  for (const attempt of interrupted) {
    if (!active.has(String(attempt._id))) await fail(attempt, "Upload interrupted");
  }
  await maintain();
}).catch(() => {});

module.exports = { reserve, claim, store, finalize, fail, release, active, isServerError };
