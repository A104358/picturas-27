const AWS = require("aws-sdk");

// Shared S3 client for SeaweedFS over the internal Docker network. URLs signed
// for the browser are rewritten to the public proxy path in getPresignedUrl.js.
const s3 = new AWS.S3({
  endpoint: `http://${process.env.S3_ENDPOINT || "seaweedfs:9000"}`,
  // Credentials come from the installation secrets (ops/secrets.sh); there is no default.
  accessKeyId: process.env.S3_ACCESS_KEY,
  secretAccessKey: process.env.S3_SECRET_KEY,
  s3ForcePathStyle: true,
  region: "us-east-1",
});

module.exports = s3;
