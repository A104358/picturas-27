const express = require("express");
const fs = require("fs");
const https = require("https");
const uploadRoutes = require("./route/upload");
const imageRoutes = require("./route/images");
const deleteRoutes = require("./route/delete");
const copyRoutes = require("./route/copy"); 

const app = express();

app.use((req, res, next) => {
  const peer = req.client.authorized && req.socket.getPeerCertificate()?.subject?.CN;
  if (peer !== "projects") return res.status(403).json({ error: "Client not authorized" });
  next();
});

app.use("/upload", uploadRoutes);
app.use("/image", imageRoutes);
app.use("/delete", deleteRoutes);
app.use("/copy", copyRoutes); 

const PORT = process.env.PORT || 11000;

https.createServer({
  key: fs.readFileSync("/run/secrets/pki/service.key"),
  cert: fs.readFileSync("/run/secrets/pki/service.crt"),
  ca: fs.readFileSync("/run/secrets/pki/ca.crt"),
  requestCert: true,
  rejectUnauthorized: true,
}, app).listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});
