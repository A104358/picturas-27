const express = require("express");
const axios = require("axios");
const router = express.Router();
const httpsAgent = require("../tls/pkiTls").clientAgent({ keepAlive: true });
const base = "https://projects:9001/";

function answer(res, error) {
  const status = error.response?.status || 503;
  res.status(status).jsonp(error.response?.data || "Upload unavailable");
}

router.get("/uploads/auth", async (req, res) => {
  if (req.headers["x-original-method"] !== "PUT") return res.sendStatus(403);
  const match = /^\/api-gateway\/uploads\/([a-f0-9]{64})$/.exec(req.headers["x-original-uri"] || "");
  if (!match) return res.sendStatus(404);
  try {
    const response = await axios.post(`${base}video/uploads/${match[1]}/authorize`, {
      length: req.headers["x-original-length"] || null,
      type: req.headers["x-original-type"] || null,
    }, { httpsAgent, picturasRequest: req, timeout: 8000 });
    res.set("X-Upload-Target", response.headers["x-upload-target"]).sendStatus(204);
  } catch (error) {
    const status = error.response?.status || 503;
    if (status === 401) return res.sendStatus(401);
    res.set("X-Deny-Status", String(status)).sendStatus(403);
  }
});

router.post("/projects/:user/:project/video/uploads", async (req, res) => {
  try {
    const response = await axios.post(`${base}${req.params.user}/${req.params.project}/video/uploads`, req.body,
      { httpsAgent, picturasRequest: req, params: req.query.share ? { share: req.query.share } : undefined,
        headers: { "X-Project-Version": req.headers["x-project-version"] } });
    res.status(response.status).json(response.data);
  } catch (error) { answer(res, error); }
});

router.post("/projects/:user/:project/video/uploads/:token/confirm", async (req, res) => {
  try {
    const response = await axios.post(`${base}${req.params.user}/${req.params.project}/video/uploads/${req.params.token}/confirm`,
      null, { httpsAgent, picturasRequest: req, timeout: 190000 });
    if (response.headers["x-project-version"]) res.set("X-Project-Version", response.headers["x-project-version"]);
    res.sendStatus(response.status);
  } catch (error) { answer(res, error); }
});

router.post("/projects/:user/:project/video/uploads/:token/cancel", async (req, res) => {
  try {
    await axios.post(`${base}${req.params.user}/${req.params.project}/video/uploads/${req.params.token}/cancel`,
      null, { httpsAgent, picturasRequest: req, timeout: 10000 });
    res.sendStatus(204);
  } catch (error) { answer(res, error); }
});

module.exports = router;
