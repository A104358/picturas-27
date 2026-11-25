const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const ts = require(process.env.B8_TS_COMPILER || "typescript");

const source = fs.readFileSync(process.argv[2], "utf8");
const compiled = ts.transpileModule(source, { compilerOptions: {
  module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, esModuleInterop: true,
} }).outputText;
const token = `fixture.${Buffer.from(JSON.stringify({ sub: "000000000000000000000001" })).toString("base64url")}.signature`;
const flush = async () => { for (let n = 0; n < 10; n++) await Promise.resolve(); };

function fixture() {
  const timers = new Set();
  const events = [];
  const checks = [];
  let validate = async () => ({});
  const socket = { connected: false, auth: {}, connections: 0, handlers: {},
    on(name, callback) { this.handlers[name] = callback; return this; },
    connect() { this.connected = true; this.connections++; },
    disconnect() { this.connected = false; this.handlers.disconnect?.("io client disconnect"); } };
  const module = { exports: {} };
  const context = { module, exports: module.exports, console, atob,
    CustomEvent: class { constructor(type) { this.type = type; } },
    window: { location: { origin: "https://fixture.invalid" }, dispatchEvent: (event) => events.push(event.type) },
    setTimeout: (callback) => { timers.add(callback); return callback; }, clearTimeout: (callback) => timers.delete(callback),
    require: (name) => name === "socket.io-client" ? () => socket : {
      validateSession: (input) => { checks.push(input); return validate(input); },
    },
  };
  vm.runInNewContext(compiled, context);
  return { ...module.exports, socket, checks, events, timers,
    validator: (value) => { validate = value; },
    advance: async () => { const pending = [...timers]; timers.clear(); pending.forEach((f) => f()); await flush(); },
  };
}

(async () => {
  const f = fixture();
  const socket = f.createProjectSocket(token);
  const release = f.retainProjectSocket(socket);
  const releaseOther = f.retainProjectSocket(socket);
  await flush();
  assert.equal(socket.connections, 1);
  assert.equal(f.checks[0].token, token);
  assert.equal(f.checks[0].userId, "000000000000000000000001");
  releaseOther(); assert.equal(socket.connected, true);
  socket.connected = false; socket.handlers.disconnect("transport close");
  await f.advance();
  assert.equal(socket.connections, 2);
  assert.equal(socket.auth.token, token);
  console.log("PASS reconnect: revalidates the same token and user; multiple consumers share one connection");
  f.validator(async () => { throw new Error("network unavailable"); });
  socket.connected = false; socket.handlers.disconnect("transport close");
  await f.advance();
  assert.equal(f.events.length, 0);
  assert.equal(socket.connections, 2);
  f.validator(async () => ({})); await f.advance();
  assert.equal(socket.connections, 3);
  console.log("PASS network outage: no logout/identity replacement; retry resumes the same session");
  f.validator(async () => { throw { response: { status: 401 } }; });
  socket.connected = false; socket.handlers.disconnect("transport close");
  await f.advance();
  assert.deepEqual(f.events, ["picturas-session-invalid"]);
  assert.equal(socket.connections, 3);
  release(); assert.equal(f.timers.size, 0);
  console.log("PASS rejected session: explicit invalid-session signal, no anonymous account or automatic reconnect");

  const strict = fixture();
  let resolve;
  strict.validator(() => new Promise((done) => { resolve = done; }));
  const strictSocket = strict.createProjectSocket(token);
  strict.retainProjectSocket(strictSocket)();
  const finalRelease = strict.retainProjectSocket(strictSocket);
  strict.validator(async () => ({})); resolve({}); await flush();
  assert.equal(strictSocket.connections, 1);
  finalRelease();
  console.log("PASS React remount during validation: stale completion cannot connect and the live consumer still reconnects");
})().catch((error) => { console.error(error); process.exitCode = 1; });
