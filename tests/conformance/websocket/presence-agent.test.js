const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const https = require("node:https");
const moduleValue = { exports: {} };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../../../projects/utils/presenceAgent.js"), "utf8"), {
  module: moduleValue, require: () => ({ clientAgent: (options) => new https.Agent({ ...options, maxCachedSessions: 0 }) }),
});
const agent = moduleValue.exports.httpsAgent;
assert.equal(agent.keepAlive, true);
assert.equal(agent.maxCachedSessions, 0);
assert.equal(agent.options.timeout, undefined);
const socket = { timeout: 0, _httpMessage: { res: { headers: { "keep-alive": "timeout=5" } } },
  setKeepAlive() {}, unref() {}, ref() {}, removeListener() {}, setTimeout(ms) { this.timeout = ms; } };
assert.equal(agent.keepSocketAlive(socket), true);
assert.equal(socket.timeout, 4000);
const request = {};
agent.reuseSocket(socket, request);
assert.equal(socket.timeout, 0);
assert.equal(request.reusedSocket, true);
agent.destroy();
console.log("PASS presence agent: idle 4s < server 5s; active timeout policy restored; TLS-session cache disabled");
