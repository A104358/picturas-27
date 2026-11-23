const { AsyncLocalStorage } = require("node:async_hooks");
const crypto = require("node:crypto");
const fs = require("node:fs");
const axios = require("axios");
const jwt = require("jsonwebtoken");

const requests = new AsyncLocalStorage();
const privateKey = fs.readFileSync("/run/secrets/jwt/rs256-private.pem");
const destinations = new Set(["projects", "users", "subscriptions"]);

function requestContext(req, _res, next) {
  req.picturasRequestId = crypto.randomUUID();
  requests.run({ req, requestId: req.picturasRequestId }, next);
}

axios.interceptors.request.use((config) => {
  // Multipart handlers can lose the async context, so they pass the request explicitly.
  const context = (config.picturasRequest && {
    req: config.picturasRequest,
    requestId: config.picturasRequest.picturasRequestId,
  }) || requests.getStore();
  if (!context) return config;
  const url = new URL(config.url, config.baseURL);
  if (!destinations.has(url.hostname)) return config;
  const { req, requestId } = context;
  const now = Math.floor(Date.now() / 1000);
  const exp = Math.min(now + 30, req.sessionExpiresAt || now + 30);
  if (exp <= now) throw new Error("Session expired before forwarding");
  const incoming = new URL(req.originalUrl, "https://gateway.invalid");
  // The signed share context is the one the destination receives, not the browser's query.
  const share = url.searchParams.getAll("share");
  const param = config.params?.share;
  if (param !== undefined && param !== null) share.push(...[].concat(param).map(String));
  const claims = {
    source: "api_gateway",
    method: (config.method || "get").toUpperCase(),
    path: url.pathname,
    share: share.length === 1 ? share[0] : "",
    originMethod: req.method,
    originPath: incoming.pathname,
    requestId,
    iat: now,
    exp,
  };
  if (req.authUserId) claims.sub = req.authUserId;
  else claims.public = true;
  const token = jwt.sign(claims, privateKey, {
    algorithm: "RS256",
    audience: url.hostname,
    issuer: `${process.env.JWT_ISSUER}/gateway`,
    keyid: "gateway-1",
    header: { typ: "picturas-internal+jwt" },
  });
  config.headers = axios.AxiosHeaders.from(config.headers);
  config.headers.delete("X-Caller-Id");
  config.headers.delete("X-Internal-Identity");
  config.headers.set("X-Internal-Identity", token);
  config.headers.set("X-Request-Id", requestId);
  if (url.hostname !== "users" || incoming.pathname !== "/users/validate/" +
      incoming.pathname.split("/").at(-1)) {
    config.headers.delete("Authorization");
  }
  return config;
}, undefined, { synchronous: true });

module.exports = { requestContext };
