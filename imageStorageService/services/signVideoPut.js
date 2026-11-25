const crypto = require("node:crypto");

const sha256 = (value) => crypto.createHash("sha256").update(value).digest("hex");
const hmac = (key, value) => crypto.createHmac("sha256", key).update(value).digest();
const encode = (value) => encodeURIComponent(value).replace(/[!'()*]/g,
  (character) => `%${character.charCodeAt(0).toString(16).toUpperCase()}`);

// AWS SDK v2 rejects ContentLength on presigned URLs. Sign the exact PUT headers
// used by nginx so neither a different size nor a different object is authorized.
module.exports = function signVideoPut({ Bucket, Key, size, type }) {
  const host = process.env.S3_ENDPOINT || "seaweedfs:9000";
  const access = process.env.S3_ACCESS_KEY;
  const secret = process.env.S3_SECRET_KEY;
  if (!access || !secret) throw new Error("S3 signing credentials unavailable");
  const now = new Date().toISOString().replace(/[-:]|\.\d{3}/g, "");
  const day = now.slice(0, 8);
  const scope = `${day}/us-east-1/s3/aws4_request`;
  const signedHeaders = "content-length;content-type;host";
  const uri = `/${encode(Bucket)}/${Key.split("/").map(encode).join("/")}`;
  const params = [
    ["X-Amz-Algorithm", "AWS4-HMAC-SHA256"],
    ["X-Amz-Credential", `${access}/${scope}`],
    ["X-Amz-Date", now],
    ["X-Amz-Expires", "300"],
    ["X-Amz-SignedHeaders", signedHeaders],
  ];
  const query = params.map(([key, value]) => `${encode(key)}=${encode(value)}`).join("&");
  const headers = `content-length:${size}\ncontent-type:${type}\nhost:${host}\n`;
  const request = `PUT\n${uri}\n${query}\n${headers}\n${signedHeaders}\nUNSIGNED-PAYLOAD`;
  const toSign = `AWS4-HMAC-SHA256\n${now}\n${scope}\n${sha256(request)}`;
  const key = hmac(hmac(hmac(hmac(`AWS4${secret}`, day), "us-east-1"), "s3"), "aws4_request");
  return `https://${host}${uri}?${query}&X-Amz-Signature=${crypto.createHmac("sha256", key).update(toSign).digest("hex")}`;
};
