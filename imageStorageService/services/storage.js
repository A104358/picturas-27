const s3 = require("./s3Client");

// All files live in one shared bucket, separated by key prefix:
//   users/<userId>/projects/<projectId>/<stage>/<fileName>
// A bucket per user does not scale on SeaweedFS: every bucket needs volumes of
// its own, so uploads started failing for new users after the first few.
const BUCKET = process.env.S3_BUCKET || "picturas";

function objectKey(userId, projectId, stage, fileName) {
  return `users/${userId}/projects/${projectId}/${stage}/${fileName}`;
}

// The one-shot bootstrap job creates the bucket before this service starts.
// Cache the check so concurrent uploads share it.
let bucketReady = null;

function ensureBucket() {
  if (!bucketReady) {
    bucketReady = (async () => {
      await s3.headBucket({ Bucket: BUCKET }).promise();
    })().catch((error) => {
      bucketReady = null;
      throw error;
    });
  }
  return bucketReady;
}

module.exports = { BUCKET, objectKey, ensureBucket };
