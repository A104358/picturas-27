// Production Next.js behind nginx over TLS (mTLS: only peers with a client certificate from the installation CA).
const fs = require("fs");
const https = require("https");
const tls = require("tls");
const next = require("next");

const app = next({ dev: false, dir: __dirname });
const handle = app.getRequestHandler();
const allowedPeers = (process.env.TLS_ALLOWED_PEERS || "nginx").split(",");

app.prepare().then(() => {
  const server = https.createServer(
    {
      key: fs.readFileSync(process.env.TLS_KEY),
      cert: fs.readFileSync(process.env.TLS_CERT),
      ca: fs.readFileSync(process.env.TLS_CA),
      requestCert: true,
      rejectUnauthorized: true,
      minVersion: "TLSv1.2",
    },
    (req, res) => {
      const peer = req.socket.getPeerCertificate();
      if (!peer || !allowedPeers.includes(peer.subject && peer.subject.CN)) {
        res.statusCode = 403;
        return res.end("peer not allowed\n");
      }
      handle(req, res);
    }
  );
  server.listen(3000, "0.0.0.0", () => console.log("> https ready on :3000"));
});
