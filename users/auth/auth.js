const bcrypt = require("bcrypt");
const jwt = require("jsonwebtoken");

const SESSION_TYPE = "picturas-session+jwt";
const SESSION_SECONDS = 7 * 24 * 60 * 60;

async function authenticate(password, user) {
  return bcrypt.compare(password, user.password_hash);
}

function get_jwt(user) {
  return jwt.sign(
    { id: String(user._id) },
    process.env.JWT_SECRET_KEY,
    {
      algorithm: "HS256",
      expiresIn: SESSION_SECONDS,
      issuer: process.env.JWT_ISSUER,
      audience: process.env.JWT_AUDIENCE,
      subject: String(user._id),
      header: { typ: SESSION_TYPE },
    },
  );
}

function verify_session(token) {
  const verified = jwt.verify(token, process.env.JWT_SECRET_KEY, {
    complete: true,
    algorithms: ["HS256"],
    issuer: process.env.JWT_ISSUER,
    audience: process.env.JWT_AUDIENCE,
    clockTolerance: 0,
    maxAge: SESSION_SECONDS,
  });
  const { header, payload } = verified;
  if (header.typ !== SESSION_TYPE || typeof payload.sub !== "string" ||
      payload.id !== payload.sub || !Number.isInteger(payload.iat) ||
      !Number.isInteger(payload.exp) || payload.iat > Math.floor(Date.now() / 1000) ||
      payload.exp <= payload.iat || payload.exp - payload.iat > SESSION_SECONDS) {
    throw new Error("Invalid session token");
  }
  return payload;
}

function validate_jwt(user, token) {
  try {
    return Boolean(user) && verify_session(token).sub === String(user._id);
  } catch (_) {
    return false;
  }
}

module.exports = { authenticate, get_jwt, verify_session, validate_jwt };
