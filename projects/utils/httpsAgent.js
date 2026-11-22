const fs = require("fs");
const https = require("https");

const key = fs.readFileSync(process.env.TLS_KEY_FILE || "/run/secrets/pki/service.key");
const cert = fs.readFileSync(process.env.TLS_CERT_FILE || "/run/secrets/pki/service.crt");

const httpsAgent = new https.Agent({
  rejectUnauthorized: false,
  cert,
  key,
});

module.exports = { httpsAgent };
