const fs = require("node:fs");
const jwt = require("jsonwebtoken");

const service = process.env.INTERNAL_SERVICE_NAME;
const publicKey = fs.readFileSync("/run/secrets/jwt/rs256-public.pem");

function publicRoute(method, path) {
  if (service === "projects") return method === "GET" && /^\/share\/[^/]+$/.test(path);
  if (service === "users") {
    return (method === "POST" && (path === "/" || /^\/[^/]+\/login$/.test(path))) ||
      (method === "GET" && (/^\/validate\/[^/]+$/.test(path) ||
        /^\/presets\/share\/[^/]+$/.test(path)));
  }
  return false;
}

// Account named by an internal path; preset routes are mounted under /users/:user.
function pathSubject(path) {
  const parts = path.split("/").filter(Boolean);
  return parts[0] === "users" ? parts[1] : parts[0];
}

// Profile type and quota operations of the users service (projects only, D4 matrix).
function quotaOperation(method, path) {
  return (method === "GET" && /^\/[^/]+\/type\/?$/.test(path)) ||
    (["GET", "PUT"].includes(method) && /^\/[^/]+\/process\/[^/]+$/.test(path)) ||
    (method === "POST" && /^\/[^/]+\/process\/refund\/[^/]+$/.test(path));
}

function serviceOperation(peer, method, path) {
  if (service === "users" && peer === "projects") return quotaOperation(method, path);
  return service === "projects" && peer === "users" && method === "DELETE" &&
    /^\/[^/]+$/.test(path);
}

function requireInternalIdentity(req, res, next) {
  const certificate = req.socket.getPeerCertificate?.();
  const peer = req.client.authorized && certificate?.subject?.CN;
  if (!peer) return res.status(403).jsonp("Client identity required");

  const path = new URL(req.originalUrl, "https://internal.invalid").pathname;
  if (peer !== "api_gateway") {
    if (!serviceOperation(peer, req.method, path)) {
      return res.status(403).jsonp("Service operation denied");
    }
    req.internalIdentity = { source: peer, sub: pathSubject(path) };
    return next();
  }

  try {
    const token = req.headers["x-internal-identity"];
    if (typeof token !== "string") throw new Error("Missing internal identity");
    const verified = jwt.verify(token, publicKey, {
      complete: true,
      algorithms: ["RS256"],
      audience: service,
      issuer: `${process.env.JWT_ISSUER}/gateway`,
      clockTolerance: 0,
    });
    const { header, payload } = verified;
    const query = new URL(req.originalUrl, "https://internal.invalid").searchParams;
    const share = query.getAll("share");
    if (header.typ !== "picturas-internal+jwt" || header.kid !== "gateway-1" ||
        payload.source !== "api_gateway" || payload.method !== req.method ||
        payload.path !== path || payload.share !== (share.length === 1 ? share[0] : "") ||
        share.length > 1 || !Number.isInteger(payload.iat) ||
        !Number.isInteger(payload.exp) || payload.exp - payload.iat > 30 ||
        typeof payload.requestId !== "string" ||
        (payload.public ? !publicRoute(req.method, path) : typeof payload.sub !== "string")) {
      throw new Error("Invalid internal context");
    }
    if (service === "projects" && req.method === "DELETE" && /^\/[^/]+$/.test(path)) {
      return res.status(403).jsonp("Service operation denied");
    }
    if (service === "users") {
      if (req.method === "GET" && path === "/") return res.status(403).jsonp("User list denied");
      if (quotaOperation(req.method, path)) return res.status(403).jsonp("Service operation denied");
      if (!payload.public && pathSubject(path) !== payload.sub) {
        return res.status(403).jsonp("Account mismatch");
      }
    }
    if (service === "subscriptions") {
      if (req.method === "GET" && (path === "/" || path === "/cards")) {
        return res.status(403).jsonp("Subscription list denied");
      }
      const rollback = req.method === "DELETE" && payload.originMethod === "POST" &&
        ["/subscriptions", "/subscriptions/"].includes(payload.originPath);
      if (path !== "/" && !rollback && pathSubject(path) !== payload.sub) {
        return res.status(403).jsonp("Subscription owner mismatch");
      }
    }
    req.internalIdentity = payload;
    next();
  } catch (_) {
    res.status(401).jsonp("Invalid internal identity");
  }
}

module.exports = { requireInternalIdentity };
