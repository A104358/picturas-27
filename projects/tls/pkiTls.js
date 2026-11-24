// Installation TLS for the Node services (Phase 2, B5: D4, option A, PKI-C3 A).
// Identical copy in every Node service (users, subscriptions, projects, apiGateway,
// imageStorageService, wsGateway, frontend): change all of them together.
//
// - serverOptions(): HTTPS with a mandatory client certificate from the installation CA and
//   no TLS session resumption, so every connection presents and checks its certificate
//   (SP-09: a resumed session would carry an identity across connections).
// - clientAgent(): the service's own certificate, the installation CA, server name checked
//   against the URL host (the Docker service name), no cached sessions.
// - peerName()/peerAllowed(): the authenticated peer's certificate CN and the allowlist.
// - guardValidity(): refuses to start with a certificate outside its validity period and
//   stops the process when it expires while running (the channel closes; with the restart
//   policy the start-up check keeps it suspended until the certificate is renewed).
const crypto = require("node:crypto");
const fs = require("node:fs");
const https = require("node:https");

const DIR = process.env.PKI_DIR || "/run/secrets/pki";
const key = fs.readFileSync(`${DIR}/service.key`);
const cert = fs.readFileSync(`${DIR}/service.crt`);
const ca = fs.readFileSync(`${DIR}/ca.crt`);
// Public fingerprints of the material actually loaded by this live process (B10).
// Per-process files keep command-line probes and healthchecks out of application output.
const trustedCAs = ca.toString().match(/-----BEGIN CERTIFICATE-----[\s\S]+?-----END CERTIFICATE-----/g) || [];
fs.writeFileSync(`/tmp/pki-loaded-${process.pid}.json`, JSON.stringify({ pid: process.pid,
  ca: new crypto.X509Certificate(ca).fingerprint256.replace(/:/g, "").toLowerCase(),
  trusted_cas: trustedCAs.map((value) => new crypto.X509Certificate(value).fingerprint256.replace(/:/g, "").toLowerCase()).sort(),
  certificate: new crypto.X509Certificate(cert).fingerprint256.replace(/:/g, "").toLowerCase(),
}) + "\n", { mode: 0o600 });

function serverOptions() {
  return {
    key, cert, ca,
    requestCert: true,
    rejectUnauthorized: true,
    minVersion: "TLSv1.2",
    secureOptions: crypto.constants.SSL_OP_NO_TICKET,
  };
}

function clientAgent(options = {}) {
  return new https.Agent({
    key, cert, ca,
    rejectUnauthorized: true,
    minVersion: "TLSv1.2",
    maxCachedSessions: 0,
    ...options,
  });
}

function peerName(req) {
  const socket = req.socket;
  if (!socket || !socket.authorized) return null;
  const subject = socket.getPeerCertificate()?.subject;
  return typeof subject?.CN === "string" ? subject.CN : null;
}

function peerAllowed(req, allowed) {
  const peer = peerName(req);
  return peer !== null && allowed.includes(peer);
}

const MAX_TIMER_MS = 2 ** 31 - 1;

function guardValidity(onExpire) {
  const own = new crypto.X509Certificate(cert);
  const notBefore = Date.parse(own.validFrom);
  const notAfter = Date.parse(own.validTo);
  const stop = (reason) => {
    console.error(`pki: own certificate ${reason}; stopping (renew with ops/pki.sh)`);
    try {
      if (onExpire) onExpire();
    } finally {
      process.exit(1);
    }
  };
  const check = () => {
    const now = Date.now();
    if (now < notBefore) return stop("not yet valid");
    if (now >= notAfter) return stop("expired");
    setTimeout(check, Math.min(notAfter - now, MAX_TIMER_MS)).unref();
  };
  check();
}

module.exports = { serverOptions, clientAgent, peerName, peerAllowed, guardValidity };
