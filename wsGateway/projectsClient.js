const https = require("node:https");
const pki = require("./tls/pkiTls");

const agent = pki.clientAgent();
module.exports = function authorize(body, { signal }) {
  return new Promise((resolve, reject) => {
    const data = Buffer.from(JSON.stringify(body));
    const request = https.request({ hostname: "projects", port: 9001, method: "POST", agent, signal,
      path: `/internal/ws/projects/${encodeURIComponent(body.projectId)}/authorize`,
      headers: { "Content-Type": "application/json", "Content-Length": data.length } }, (response) => {
      const chunks = [];
      let size = 0;
      response.on("data", (chunk) => {
        size += chunk.length;
        if (size > 65536) { response.destroy(); request.destroy(new Error("response_too_large")); return; }
        chunks.push(chunk);
      });
      response.on("error", reject);
      response.on("aborted", () => reject(new Error("response_truncated")));
      response.on("end", () => {
        try {
          if (response.statusCode !== 200 || !response.complete) throw new Error("authorization_unavailable");
          resolve(JSON.parse(Buffer.concat(chunks).toString("utf8")));
        } catch (error) { reject(error); }
      });
    });
    request.on("error", reject);
    request.end(data);
  });
};
