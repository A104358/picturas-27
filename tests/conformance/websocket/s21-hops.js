// Diagnose S21 using only the latest synthetic s21 fixture. No credentials or
// identifiers are printed, and only its ordinary presence heartbeat is updated.
const mongoose = require("mongoose");
const axios = require("axios");
const hopClock = require("node:perf_hooks").performance;
let httpsAgent;
try { ({ httpsAgent } = require("./utils/presenceAgent")); }
catch (error) {
  if (error.code !== "MODULE_NOT_FOUND") throw error;
  ({ httpsAgent } = require("./utils/httpsAgent"));
}
const Presence = require("./models/presence");
const Project = require("./models/project");
const { ensureEditorSlot } = require("./utils/presence");
const times = { userHttp: [], presenceWrite: [], projectRead: [], total: [], dns: [], tcp: [], tls: [] };
const get = axios.get.bind(axios);
axios.get = async (...args) => {
  const at = hopClock.now();
  try { return await get(...args); } finally { times.userHttp.push(hopClock.now() - at); }
};
const update = Presence.updateOne.bind(Presence);
Presence.updateOne = async (...args) => {
  const at = hopClock.now();
  try { return await update(...args); } finally { times.presenceWrite.push(hopClock.now() - at); }
};
const create = httpsAgent.createConnection.bind(httpsAgent);
httpsAgent.createConnection = (...args) => {
  const at = hopClock.now();
  const socket = create(...args);
  socket.once("lookup", () => times.dns.push(hopClock.now() - at));
  socket.once("connect", () => times.tcp.push(hopClock.now() - at));
  socket.once("secureConnect", () => times.tls.push(hopClock.now() - at));
  return socket;
};

(async () => {
  await mongoose.connect(process.env.MONGO_URI);
  const project = await Project.findOne({ name: "s21" }).sort({ _id: -1 }).lean();
  if (!project) throw new Error("S21 fixture absent");
  for (let n = 0; n < 40; n++) {
    if (n === 10) for (const values of Object.values(times)) values.length = 0;
    const start = hopClock.now();
    await ensureEditorSlot({ ownerId: String(project.user_id), projectId: String(project._id), callerId: String(project.user_id) });
    const at = hopClock.now();
    await Project.findOne({ user_id: project.user_id, _id: project._id }).lean();
    times.projectRead.push(hopClock.now() - at);
    times.total.push(hopClock.now() - start);
  }
  const summary = {};
  for (const [key, values] of Object.entries(times)) {
    values.sort((a,b) => a-b);
    summary[key] = { n: values.length, median_ms: +(values[Math.floor(values.length/2)] || 0).toFixed(3),
      max_ms: +(values[values.length-1] || 0).toFixed(3) };
  }
  console.log(JSON.stringify(summary));
  httpsAgent.destroy();
  await mongoose.disconnect();
})().catch((error) => { console.error("S21 hop diagnostic failed:", error.name); process.exit(1); });
