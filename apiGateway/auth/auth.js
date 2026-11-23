const jwt = require("jsonwebtoken");

const SESSION_TYPE = "picturas-session+jwt";
const SESSION_SECONDS = 7 * 24 * 60 * 60;

function verifySession(header) {
  const match = /^Bearer ([^ ]+)$/.exec(header || "");
  if (!match) throw new Error("Missing session");
  const verified = jwt.verify(match[1], process.env.JWT_SECRET_KEY, {
    complete: true,
    algorithms: ["HS256"],
    issuer: process.env.JWT_ISSUER,
    audience: process.env.JWT_AUDIENCE,
    clockTolerance: 0,
    maxAge: SESSION_SECONDS,
  });
  const { header: tokenHeader, payload } = verified;
  if (tokenHeader.typ !== SESSION_TYPE || typeof payload.sub !== "string" ||
      payload.id !== payload.sub || !Number.isInteger(payload.iat) ||
      !Number.isInteger(payload.exp) || payload.exp - payload.iat > SESSION_SECONDS) {
    throw new Error("Invalid session");
  }
  return payload;
}

function checkToken(req, res, next) {
  if (req.authUserId) return next();
  try {
    const payload = verifySession(req.headers.authorization);
    req.authUserId = payload.sub;
    req.sessionExpiresAt = payload.exp;
    next();
  } catch (_) {
    res.status(401).jsonp("Invalid or expired session");
  }
}

function authorize(req, res, next) {
  const path = req.path.split("/").filter(Boolean);
  const service = path[0];
  const method = req.method;
  const publicRoute =
    (service === "projects" && method === "GET" && path[1] === "share" && path.length === 3) ||
    (service === "users" && method === "POST" && (path.length === 1 ||
      (path.length === 3 && path[2] === "login"))) ||
    (service === "users" && method === "GET" && path[1] === "validate" && path.length === 3) ||
    (service === "users" && method === "GET" && path[1] === "presets" && path[2] === "share" && path.length === 4);
  if (publicRoute) return next();

  checkToken(req, res, () => {
    const query = new URL(req.originalUrl, "https://gateway.invalid").searchParams;
    const owners = query.getAll("owner");
    const shares = query.getAll("share");
    if (owners.length > 1 || shares.length > 1 || (owners.length === 1 && !owners[0])) {
      return res.status(403).jsonp("Invalid owner or share context");
    }

    if (service === "projects") {
      if (path[1] === "share" && path[3] === "project") return next();
      const owner = path[1];
      if (owners.length && owners[0] !== owner) return res.status(403).jsonp("Owner mismatch");
      if (shares.length && shares[0] && path.length >= 3) return next();
      if (owner !== req.authUserId) return res.status(403).jsonp("Owner mismatch");
    } else if (service === "users") {
      if (path[1] !== req.authUserId) return res.status(403).jsonp("Account mismatch");
    } else if (service === "subscriptions") {
      if (path.length > 1 && path[1] !== req.authUserId) {
        return res.status(403).jsonp("Subscription owner mismatch");
      }
    }
    next();
  });
}

module.exports = { checkToken, authorize, verifySession };
