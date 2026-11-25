const AWS = require("aws-sdk");
const fs = require("fs");
const https = require("https");

// Shared S3 client for SeaweedFS over the internal Docker network. URLs signed
// for the browser are rewritten to the public proxy path in getPresignedUrl.js.
const s3 = new AWS.S3({
  endpoint: `https://${process.env.S3_ENDPOINT || "seaweedfs:9000"}`,
  // Credentials come from the installation secrets (ops/secrets.sh); there is no default.
  accessKeyId: process.env.S3_ACCESS_KEY,
  secretAccessKey: process.env.S3_SECRET_KEY,
  s3ForcePathStyle: true,
  region: "us-east-1",
  httpOptions: {
    agent: new https.Agent({ ca: fs.readFileSync("/run/secrets/pki/ca.crt"), rejectUnauthorized: true, maxCachedSessions: 0, keepAlive: true }),
  },
});

module.exports = s3;
