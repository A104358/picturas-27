const axios = require("axios");

const fs = require("fs");

const key = fs.readFileSync(process.env.TLS_KEY_FILE || "/run/secrets/pki/service.key");
const cert = fs.readFileSync(process.env.TLS_CERT_FILE || "/run/secrets/pki/service.crt");

const https = require("https");
const httpsAgent = new https.Agent({
  ca: fs.readFileSync("/run/secrets/pki/ca.crt"),
  cert: cert,
  key: key,
});

const img_storage_ms = "https://img_storage:11000";

async function get_image_internal_url(user, project, type, img) {
  return await axios.get(
    `${img_storage_ms}/image/internal/${user}/${project}/${type}/${img}`,
    { httpsAgent },
  );
}

async function get_image_public_url(user, project, type, img) {
  return await axios.get(
    `${img_storage_ms}/image/public/${user}/${project}/${type}/${img}`,
    { httpsAgent },
  );
}

async function post_image(user, project, type, file) {
  return await axios.post(
    `${img_storage_ms}/upload/${user}/${project}/${type}`,
    file,
    // Videos can be hundreds of MB
    { httpsAgent, maxBodyLength: Infinity, maxContentLength: Infinity, headers: file.getHeaders ? file.getHeaders() : undefined },
  );
}

async function delete_image(user, project, type, img) {
  return await axios.delete(
    `${img_storage_ms}/delete/${user}/${project}/${type}/${img}`,
    { httpsAgent },
  );
}

async function copy_image(userId, projectId, fromStage, toStage, fileName) {
  // usa o mesmo serviço interno (docker network) tal como as outras
  return axios.post(
    `${img_storage_ms}/copy/${userId}/${projectId}/${fromStage}/${toStage}/${fileName}`,
    {},
    { httpsAgent }
  );
}

module.exports = { get_image_internal_url, get_image_public_url, post_image, delete_image, copy_image };
