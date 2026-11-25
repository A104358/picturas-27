const https = require("node:https");
const socketIo = require("socket.io");
const jwt = require("jsonwebtoken");
const pki = require("./tls/pkiTls");
const { Authorization, configuration, bytes } = require("./authorization");
const authorize = require("./projectsClient");
const { read_rabbit_msg } = require("./utils/rabbit_mq");
const { parser, JOIN_BYTES } = require("./protocol");

const config = configuration();
const authorization = new Authorization(authorize, config);
const httpServer = https.createServer({ ...pki.serverOptions(), maxHeaderSize: 8192 });
const io = socketIo(httpServer, {
  cors: { origin: "*", methods: ["GET", "POST"] },
  maxHttpBufferSize: 65536,
  parser,
  allowRequest: (req, callback) => callback(null,
    pki.peerAllowed(req, ["nginx"]) && io.engine.clientsCount < config.connections &&
    Buffer.byteLength(req.url || "") <= 8192),
});

io.use((socket, next) => {
  let status = "denied";
  try {
    const token = socket.handshake.auth?.token;
    if (bytes(socket.handshake.auth || {}) > 8192 || typeof token !== "string" ||
        Buffer.byteLength(token) > 8192) throw new Error("Invalid session");
    const { header, payload } = jwt.verify(token, process.env.JWT_SECRET_KEY, {
      complete: true, algorithms: ["HS256"], issuer: process.env.JWT_ISSUER,
      audience: process.env.JWT_AUDIENCE, clockTolerance: 0, maxAge: 7 * 24 * 60 * 60,
    });
    if (header.typ !== "picturas-session+jwt" || typeof payload.sub !== "string" ||
        payload.id !== payload.sub || !Number.isInteger(payload.iat) || !Number.isInteger(payload.exp) ||
        payload.iat > Math.floor(Date.now() / 1000) || payload.exp <= payload.iat || payload.exp - payload.iat > 7 * 24 * 60 * 60) throw new Error("Invalid session");
    const limit = authorization.connect(socket, payload);
    if (limit) { status = "rate_limited"; authorization.count(limit); throw new Error("Connection limit"); }
    next();
  } catch (error) {
    authorization.disconnect(socket.id);
    if (error.name === "TokenExpiredError") status = "session_expired";
    const refusal = new Error(status);
    refusal.data = { status };
    next(refusal);
    socket.conn.close();
  }
});

io.on("connection", (socket) => {
  socket.on("join-project", (...args) => {
    const ack = typeof args[args.length - 1] === "function" ? args.pop() : () => {};
    const payload = args[0];
    if (args.length !== 1 || !payload || typeof payload !== "object" ||
        payload[JOIN_BYTES] === undefined || payload[JOIN_BYTES] > 4096) {
      ack({ status: "invalid_request" });
      return;
    }
    authorization.join(socket.id, payload, ack);
  });
  socket.on("leave-project", (payload) => {
    const projectId = typeof payload === "string" ? payload : payload?.projectId;
    if (typeof projectId === "string") authorization.leave(socket.id, projectId);
  });
  socket.on("disconnect", () => authorization.disconnect(socket.id));
});

const timer = setInterval(() => authorization.tick(), 25);
timer.unref();
// Aggregate telemetry has no subject IDs, tokens, project IDs or share links.
setInterval(() => console.log(JSON.stringify({ type: "ws-authorization", ...authorization.stats(),
  rss: process.memoryUsage().rss, cpu: process.cpuUsage() })), 10000).unref();
pki.guardValidity(() => { authorization.close(); io.disconnectSockets(true); httpServer.close(); });
httpServer.listen(4000);

read_rabbit_msg("ws_queue", (message) => {
  let content;
  try { content = JSON.parse(message.content.toString()); }
  catch (_) { authorization.count("invalid_broker_message"); return; }
  const { messageId = "", projectId, user, status } = content;
  const emit = (event, payload) => {
    if (!user) return authorization.count("event_missing_user");
    authorization.emit(projectId, event, payload, user);
  };
  if (/update-client-video-progress/.test(messageId)) {
    emit("video-progress", { projectId, imgId: content.imgId, preview: content.preview, percent: content.percent });
  } else if (/update-client-preview/.test(messageId)) {
    if (status === "error") emit("preview-error", { error_code: content.errorCode, error_msg: content.errorMsg });
    else emit("preview-ready", content.img_url);
  } else if (/update-client-process/.test(messageId)) {
    if (status === "error") emit("process-error", { error_code: content.errorCode, error_msg: content.errorMsg });
    else emit("process-update", messageId);
  } else if (content.type === "project-op" && content.op) {
    authorization.emit(projectId, "project-op", { projectId, op: content.op });
  } else if (/project-updated/.test(messageId) || content.type === "project-updated") {
    authorization.emit(projectId, "project-updated", { projectId, version: content.version });
  }
});
