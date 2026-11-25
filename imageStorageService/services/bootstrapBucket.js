const AWS = require("aws-sdk");
const fs = require("fs");
const https = require("https");

const bucket = process.env.S3_BUCKET;
if (bucket !== "picturas") throw new Error("Unexpected S3 bucket configuration");

const credentials = JSON.parse(fs.readFileSync("/run/secrets/s3-bootstrap/credentials.json", "utf8"));
const s3 = new AWS.S3({
  endpoint: `https://${process.env.S3_ENDPOINT}`,
  accessKeyId: credentials.accessKeyId,
  secretAccessKey: credentials.secretAccessKey,
  s3ForcePathStyle: true,
  region: "us-east-1",
  httpOptions: {
    agent: new https.Agent({ ca: fs.readFileSync("/run/secrets/pki/ca.crt"), rejectUnauthorized: true, maxCachedSessions: 0 }),
  },
});

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function bootstrap() {
  for (let attempt = 0; attempt < 90; attempt++) {
    try {
      await s3.headBucket({ Bucket: bucket }).promise();
      console.log("S3 application bucket ready");
      return;
    } catch (error) {
      if (error.statusCode === 404) {
        try {
          await s3.createBucket({ Bucket: bucket }).promise();
          console.log("S3 application bucket created");
          return;
        } catch (createError) {
          if (createError.code === "BucketAlreadyExists" || createError.code === "BucketAlreadyOwnedByYou") {
            // A concurrent bootstrap may have created the bucket. Recheck ownership.
            continue;
          }
          if (createError.statusCode && createError.statusCode < 500) break;
        }
      } else if (error.statusCode && error.statusCode < 500) {
        break;
      }
    }
    await delay(2000);
  }
  throw new Error("S3 bucket bootstrap failed");
}

bootstrap().catch(() => {
  console.error("S3 bucket bootstrap failed");
  process.exitCode = 1;
});
