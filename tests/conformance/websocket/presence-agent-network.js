// Run by docker exec -i in projects. Synthetic fixtures only; output has no IDs.
const assert = require("node:assert/strict");
const mongoose = require("mongoose");
const axios = require("axios");
const dns = require("node:dns").promises;
const { httpsAgent } = require("./utils/presenceAgent");
const Project = require("./models/project");
let connections = 0;
const sessions = [];
const create = httpsAgent.createConnection.bind(httpsAgent);
httpsAgent.createConnection = (...args) => {
  connections++;
  const socket = create(...args);
  socket.once("secureConnect", () => sessions.push(socket.isSessionReused()));
  return socket;
};

(async () => {
  await mongoose.connect(process.env.MONGO_URI);
  const project = await Project.findOne({ name: /^(B4|B8)/ }).sort({ _id: -1 }).lean();
  assert.ok(project, "synthetic fixture absent");
  const path = `/${project.user_id}/type`;
  const options = { httpsAgent, timeout: 5000 };
  const first = await axios.get("https://users:10001" + path, options);
  const second = await axios.get("https://users:10001" + path, options);
  assert.equal(first.status, 200); assert.equal(second.status, 200);
  assert.equal(second.request.reusedSocket, true); assert.equal(connections, 1);
  console.log("PASS presence mTLS: verified fresh GETs share one connection");
  const denied = await axios.get("https://users:10001/", { ...options, validateStatus: () => true });
  assert.equal(denied.status, 403); assert.equal(denied.request.reusedSocket, true);
  console.log("PASS presence D4: existing connection cannot expand service operations");
  const { address } = await dns.lookup("users");
  let mismatch;
  try { await axios.get(`https://${address}:10001${path}`, options); }
  catch (error) { mismatch = error.code; }
  assert.equal(mismatch, "ERR_TLS_CERT_ALTNAME_INVALID");
  console.log("PASS presence client: wrong server name refused despite pooled connection");
  const previous = connections;
  await new Promise((resolve) => setTimeout(resolve, 4300));
  const after = await axios.get("https://users:10001" + path, options);
  assert.equal(after.status, 200); assert.ok(connections > previous);
  assert.equal(after.request.reusedSocket, false);
  assert.ok(sessions.every((resumed) => !resumed));
  console.log("PASS presence idle: connection closed before 5s; next request uses a full mTLS handshake without session resumption");
  httpsAgent.destroy(); await mongoose.disconnect();
})().catch((error) => { console.error("Presence network control failed:", error.name); process.exit(1); });
