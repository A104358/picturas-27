// Production Next.js server over HTTPS for the nginx -> frontend hop (Phase 2, B5; SP-09).
// mTLS with the installation CA: only nginx may call it. Uses the normal build (.next).
const https = require("https");
const next = require("next");
const pki = require("./tls/pkiTls");

const port = parseInt(process.env.PORT || "3000", 10);
const app = next({ dev: false, dir: __dirname });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const server = https.createServer(pki.serverOptions(), (req, res) => {
    if (!pki.peerAllowed(req, ["nginx"])) {
      res.statusCode = 403;
      return res.end("Client not authorized\n");
    }
    handle(req, res);
  });
  server.listen(port, "0.0.0.0", () => console.log(`> https ready on :${port}`));
  pki.guardValidity(() => server.close());
});
