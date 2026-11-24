const express = require("express");
const https = require("https");
const uploadRoutes = require("./route/upload");
const imageRoutes = require("./route/images");
const deleteRoutes = require("./route/delete");
const copyRoutes = require("./route/copy"); 
const videoObjects = require("./route/videoObjects");

const app = express();

const pki = require("./tls/pkiTls");

// Only the projects service may call img_storage (D4 matrix, S03).
app.use((req, res, next) => {
  if (!pki.peerAllowed(req, ["projects"])) return res.status(403).json({ error: "Client not authorized" });
  next();
});

app.use("/upload", uploadRoutes);
app.use("/image", imageRoutes);
app.use("/delete", deleteRoutes);
app.use("/copy", copyRoutes); 
app.use("/video-objects", videoObjects);

const PORT = process.env.PORT || 11000;

const server = https.createServer(pki.serverOptions(), app).listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});
pki.guardValidity(() => server.close());
