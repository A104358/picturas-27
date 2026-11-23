// Execute the real route with an isolated database failure, without stopping or
// changing a real database. Transport/parser/peer checks also run over the real
// network in b8-functional.py.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const router = { middleware: [], use(handler) { this.middleware.push(handler); },
  post(route, handler) { this.handler = handler; } };
let failure = false;
let reads = 0;
let project = { user_id: "000000000000000000000001", version: 7,
  sharedLinks: [{ id: "fixture-read", permission: "read", revoked: false }] };
const query = { select() { return this; }, read(mode) { assert.equal(mode, "primary"); return this; },
  maxTimeMS(ms) { assert.equal(ms, 800); return this; }, lean() { return this; },
  async exec() { if (failure) throw new Error("fixture database unavailable"); return project; } };
const moduleValue = { exports: {} };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../../../projects/routes/wsAuth.js"), "utf8"), {
  module: moduleValue, exports: moduleValue.exports, Buffer, Date, console,
  setInterval: () => ({ unref() {} }),
  require: (name) => {
    if (name === "express") return { Router: () => router, json: () => () => {} };
    if (name === "../models/project") return { findById: () => { reads++; return query; } };
    if (name === "../tls/pkiTls") return { peerAllowed: (req, allowed) => allowed.includes(req.peer) };
    return require(name);
  },
});
const body = { requestId: "fixture", evaluations: [
  { ref: "owner", generation: 1, sequence: 1, sub: "000000000000000000000001", exp: Math.floor(Date.now()/1000)+60, access: { kind: "owner" } },
  { ref: "reader", generation: 1, sequence: 1, sub: "000000000000000000000002", exp: Math.floor(Date.now()/1000)+60, access: { kind: "share", shareId: "fixture-read" } },
  { ref: "invalid", generation: 1, sequence: 1, sub: "000000000000000000000002", exp: Math.floor(Date.now()/1000)+60, access: { kind: "share", shareId: "not-presented" } },
] };

function response() {
  return { code: 200, status(code) { this.code = code; return this; }, type() { return this; },
    json(data) { this.data = data; return this; }, send(body) { this.data = JSON.parse(body); return this; },
    sendStatus(code) { this.code = code; return this; } };
}
async function call(body) {
  const res = response();
  await router.handler({ params: { projectId: "000000000000000000000010" }, body }, res);
  return res;
}

(async () => {
  const denied = response();
  router.middleware[0]({ peer: "api_gateway" }, denied, () => { throw new Error("wrong peer admitted"); });
  assert.equal(denied.code, 403);
  console.log("PASS WS-C1: other peer cannot delegate to the route");
  const mixed = await call(body);
  assert.equal(mixed.code, 200);
  assert.deepEqual(Array.from(mixed.data.decisions, (d) => d.decision), ["allow", "allow", "deny"]);
  assert.equal(reads, 1);
  console.log("PASS WS-T08: one primary read, independent owner/read/invalid decisions");
  failure = true;
  const unavailable = await call(body);
  assert.deepEqual(Array.from(unavailable.data.decisions, (d) => d.decision), ["unavailable", "unavailable", "unavailable"]);
  console.log("PASS WS-T02: database failure is unavailable for every member, never ownership or revocation confirmation");
  failure = false;
  project = null;
  const absent = await call(body);
  assert.ok(absent.data.decisions.every((d) => d.decision === "deny"));
  console.log("PASS deleted project: denial requires a successful current read");
})().catch((error) => { console.error(error); process.exitCode = 1; });
