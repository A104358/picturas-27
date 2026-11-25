// amqplib (promise API) with server verification, as projects/ws_gateway would use it.
const amqp = require("amqplib");
const fs = require("fs");
const ca = (f) => [fs.readFileSync(f)];
const url = (u, p, host = "rabbitmq", port = 5671, proto = "amqps") => `${proto}://${u}:${p}@${host}:${port}`;
async function t(label, fn) {
  try { const r = await fn(); console.log(`ALLOW  ${label}${r === undefined ? "" : ": " + String(r).slice(0, 60)}`); }
  catch (e) { console.log(`DENY   ${label}: ${String(e.message || e).slice(0, 120)}`); }
}
const P = ["projects_svc", "projects-pw-0123456789"];
const opts = (f = "/pki/ca.crt", extra = {}) => ({ ca: ca(f), servername: "rabbitmq", ...extra });
(async () => {
  await t("amqp:// plaintext 5672", async () => (await amqp.connect(url(...P, "rabbitmq", 5672, "amqp"), { timeout: 3000 })).close());
  await t("amqps wrong CA", async () => (await amqp.connect(url(...P), opts("/pki/otherca.crt"))).close());
  const ip = require("dns").promises; const addr = (await ip.lookup("rabbitmq")).address;
  await t("amqps by IP (name not in SAN)", async () => (await amqp.connect(url(...P, addr), { ca: ca("/pki/ca.crt") })).close());
  await t("amqps rejectUnauthorized default + CA (no servername override)", async () => (await amqp.connect(url(...P), { ca: ca("/pki/ca.crt") })).close());
  await t("amqps user/password", async () => (await amqp.connect(url("user", "password"), opts())).close());
  let c = await amqp.connect(url(...P), opts());
  c.on("error", (e) => console.log(`       connection 'error' event handled: ${String(e.message).slice(0, 80)}`));
  const sock = c.connection.stream;
  console.log(`       TLS: authorized=${sock.authorized} protocol=${sock.getProtocol()} peerCN=${sock.getPeerCertificate().subject.CN}`);
  await t("projects checkExchange picturas (passive)", async () => { const ch = await c.createChannel(); await ch.checkExchange("picturas"); await ch.close(); });
  await t("projects assertExchange picturas (active, as today)", async () => { const ch = await c.createChannel(); ch.on("error", () => {}); await ch.assertExchange("picturas", "direct", { durable: true }); await ch.close(); });
  await t("projects publish picturas -> brightness_queue (confirm)", async () => { const ch = await c.createConfirmChannel(); ch.publish("picturas", "brightness_queue", Buffer.from("{}")); await ch.waitForConfirms(); await ch.close(); });
  await t("projects consume project_queue", async () => { const ch = await c.createChannel(); const r = await ch.consume("project_queue", () => {}, { noAck: false }); await ch.close(); return r.consumerTag; });
  await t("projects get ws_queue", async () => { const ch = await c.createChannel(); ch.on("error", () => {}); await ch.get("ws_queue"); await ch.close(); });
  console.log(`       connection still usable after channel 403s: ${await c.createChannel().then((ch) => ch.close()).then(() => true, () => false)}`);
  await c.close();
})();
