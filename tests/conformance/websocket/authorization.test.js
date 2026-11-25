const { test } = require("node:test");
const assert = require("node:assert/strict");
const { Authorization, AuthorizationQueue, DEFAULTS, bytes } = require("../../../wsGateway/authorization");

const id = (n) => n.toString(16).padStart(24, "0");
const flush = async () => { for (let n = 0; n < 10; n++) await Promise.resolve(); };
const response = (body, decide = () => "allow") => ({ requestId: body.requestId, projectId: body.projectId,
  decisions: body.evaluations.map((item) => ({ ref: item.ref, generation: item.generation,
    sequence: item.sequence, decision: decide(item), permission: "read" })) });

function fixture(evaluate = async (body) => response(body)) {
  let time = 0;
  const epoch = Date.now();
  const auth = new Authorization(evaluate, DEFAULTS, { now: () => time, wall: () => epoch + time });
  const sockets = [];
  function connect(n, sub = id(n + 1), exp = Math.floor(epoch / 1000) + 3600) {
    const socket = { id: `socket-${n}`, events: [], rooms: new Set(), closed: false,
      emit(event, data) { this.events.push({ event, data, at: time }); },
      join(room) { this.rooms.add(room); }, leave(room) { this.rooms.delete(room); },
      disconnect() { this.closed = true; } };
    const refusal = auth.connect(socket, { sub, exp });
    sockets.push(socket);
    return { socket, refusal };
  }
  async function join(socket, project = id(100), access = { kind: "owner" }) {
    const replies = [];
    auth.join(socket.id, { projectId: project, access }, (reply) => replies.push(reply));
    await flush();
    return replies;
  }
  return { auth, connect, join, sockets, advance: (ms) => { time += ms; }, now: () => time };
}

test("WS-T01: verified connection identity, fresh joins, canonical contexts and callbacks", async () => {
  const calls = [];
  const f = fixture(async (body) => { calls.push(body); return response(body); });
  try {
    const { socket } = f.connect(1);
    assert.equal((await f.join(socket))[0].status, "joined");
    assert.equal((await f.join(socket))[0].status, "joined");
    assert.equal(calls.length, 2);
    assert.equal(calls[0].evaluations[0].sub, id(2));
    assert.equal(f.auth.contexts, 1);
    const invalid = [];
    f.auth.join(socket.id, { projectId: id(100), access: { kind: "owner" }, sub: id(99) }, (r) => invalid.push(r));
    assert.equal(invalid[0].status, "invalid_request");
    await f.join(socket, id(100), { kind: "share", shareId: "presented" });
    await f.join(socket, id(100), { shareId: "presented", kind: "share" });
    assert.equal(f.auth.contexts, 2);
  } finally { f.auth.close(); }
});

test("WS-T02/T03/T04/E1: outage denies fresh join; failures never renew; emission checks deadline without timers", async () => {
  let available = true;
  const f = fixture(async (body) => available ? response(body) : null);
  try {
    const { socket } = f.connect(1);
    await f.join(socket);
    available = false;
    assert.equal((await f.join(socket))[0].status, "unavailable");
    f.advance(1000); f.auth.tick(); await flush();
    f.auth.emit(id(100), "preview-ready", "protected", id(2));
    assert.equal(socket.events.filter((e) => e.event === "preview-ready").length, 1);
    f.advance(4000);
    f.auth.emit(id(100), "preview-ready", "late", id(2));
    f.auth.emit(undefined, "process-update", "missing context", id(2));
    assert.equal(socket.events.filter((e) => e.event === "preview-ready").length, 1);
    f.auth.tick(); await flush();
    // Decision 53 (D-30 A): the lapsed context is suspended, not removed, and receives nothing.
    assert.equal(f.auth.contexts, 1);
    assert.deepEqual(socket.events.filter((e) => e.event === "project-access").map((e) => e.data.status), ["suspended"]);
    f.auth.emit(id(100), "preview-ready", "suspended", id(2));
    assert.equal(socket.events.filter((e) => e.event === "preview-ready").length, 1);
    available = true;
    f.advance(250); f.auth.tick(); await flush();
    f.auth.emit(id(100), "preview-ready", "resumed without a new join", id(2));
    assert.equal(socket.events.filter((e) => e.event === "preview-ready").length, 2);
    assert.equal((await f.join(socket))[0].status, "joined");
  } finally { f.auth.close(); }
});

test("WS-T02/T04 (decision 53): suspension keeps limits, resumes only on a fresh allow, deny removes", async () => {
  let mode = "allow";
  const calls = [];
  const f = fixture(async (body) => {
    calls.push(f.now());
    return mode === "down" ? null : response(body, () => mode);
  });
  try {
    const { socket } = f.connect(1);
    await f.join(socket);
    mode = "down";
    f.advance(1000); f.auth.tick(); await flush();          // first failure at 1000
    f.advance(250); f.auth.tick(); await flush();           // one quick retry at 1250
    f.advance(250); f.auth.tick(); await flush();           // nothing due at 1500
    assert.deepEqual(calls, [0, 1000, 1250]);
    f.advance(750); f.auth.tick(); await flush();           // back to the 1 s cadence at 2250
    assert.deepEqual(calls, [0, 1000, 1250, 2250]);
    f.advance(2750); f.auth.tick(); await flush();          // lease from admission at 0 lapses at 5000
    assert.equal(f.auth.stats().reasons.suspended, 1);
    f.advance(250); f.auth.tick(); await flush();           // suspended: retries every 250 ms
    assert.deepEqual(calls.slice(-2), [5000, 5250]);
    assert.equal(f.auth.contexts, 1, "a suspended context still counts in the 4096 limit");
    f.auth.emit(id(100), "project-op", "while suspended");
    assert.equal(socket.events.filter((e) => e.event === "project-op").length, 0);
    mode = "allow";
    f.advance(250); f.auth.tick(); await flush();
    const context = [...f.auth.sockets.get(socket.id).rooms.get(id(100)).paths.values()][0];
    assert.equal(context.until, 5500 + DEFAULTS.leaseMs, "lease counted from the new admission");
    f.auth.emit(id(100), "project-op", "resumed");
    assert.equal(socket.events.filter((e) => e.event === "project-op").length, 1);
    mode = "down";
    f.advance(5000); f.auth.tick(); await flush();
    mode = "deny";
    f.advance(250); f.auth.tick(); await flush();
    assert.equal(f.auth.contexts, 0, "a deny removes a suspended context");
    assert.equal(socket.events.at(-1).data.status, "denied");
  } finally { f.auth.close(); }
});

test("WS-T05/E1: leave, disconnect and rejoin invalidate delayed evaluations; replacements acknowledge", async () => {
  const held = [];
  const f = fixture((body) => new Promise((resolve) => held.push({ body, resolve })));
  try {
    const { socket } = f.connect(1);
    const replies = await f.join(socket);
    f.auth.leave(socket.id, id(100));
    assert.equal(replies[0].status, "unavailable");
    const newer = await f.join(socket);
    held[0].resolve(response(held[0].body)); await flush();
    assert.equal(newer.length, 0);
    held[1].resolve(response(held[1].body)); await flush();
    assert.equal(newer[0].status, "joined");
    const pending = await f.join(socket);
    f.auth.disconnect(socket.id);
    assert.equal(pending[0].status, "unavailable");
    assert.equal(f.auth.contexts, 0);
    held[2].resolve(response(held[2].body)); await flush();
    assert.equal(f.auth.sockets.size, 0);
  } finally { f.auth.close(); }
});

test("WS-T06: only presented paths survive individual denial; all denied removes room", async () => {
  const revoked = new Set();
  const f = fixture(async (body) => response(body, (item) => revoked.has(item.access.shareId) ? "deny" : "allow"));
  try {
    const { socket } = f.connect(1);
    await f.join(socket, id(100), { kind: "share", shareId: "first" });
    await f.join(socket, id(100), { kind: "share", shareId: "second" });
    revoked.add("first"); f.advance(1000); f.auth.tick(); await flush();
    assert.equal(f.auth.contexts, 1);
    f.auth.emit(id(100), "project-op", {});
    assert.equal(socket.events.filter((e) => e.event === "project-op").length, 1);
    revoked.add("second"); f.advance(1000); f.auth.tick(); await flush();
    f.auth.emit(id(100), "project-op", {});
    assert.equal(socket.events.filter((e) => e.event === "project-op").length, 1);
    assert.equal(f.auth.contexts, 0);
  } finally { f.auth.close(); }
});

test("WS-T07: absolute JWT expiry gates every event and terminates connection", async () => {
  const f = fixture();
  try {
    const { socket } = f.connect(1, id(2), Math.floor(Date.now() / 1000) + 2);
    await f.join(socket);
    f.advance(2000);
    f.auth.emit(id(100), "project-op", {});
    assert.equal(socket.events.length, 0);
    f.auth.tick();
    assert.equal(socket.closed, true);
    assert.equal(f.auth.contexts, 0);
  } finally { f.auth.close(); }
});

test("WS-T08: partial, duplicate, swapped, oversized and truncated responses grant nothing", async () => {
  for (const corrupt of [
    (r) => ({ ...r, decisions: [] }),
    (r) => ({ ...r, decisions: r.decisions.concat(r.decisions) }),
    (r) => ({ ...r, requestId: "different" }),
    (r) => ({ ...r, projectId: id(999) }),
    (r) => ({ ...r, decisions: r.decisions.map((d) => ({ ...d, generation: d.generation + 1 })) }),
    (r) => ({ ...r, padding: "x".repeat(65536) }),
    () => "{truncated",
  ]) {
    const f = fixture(async (body) => corrupt(response(body)));
    try {
      const { socket } = f.connect(1);
      assert.equal((await f.join(socket))[0].status, "unavailable");
      assert.equal(f.auth.contexts, 0);
    } finally { f.auth.close(); }
  }
});

test("WS-T10: 4 active + 16 pending; 17th refused; replacement keeps deadline and acknowledges", async () => {
  let time = 0;
  const q = new AuthorizationQueue(() => new Promise(() => {}), DEFAULTS, () => time);
  const results = [];
  const item = (n) => ({ at: time, wire: { ref: `ref-${n}`, generation: 1, sequence: 1 },
    done: (decision, reason) => results.push({ n, decision, reason }) });
  try {
    for (let n = 0; n < 20; n++) q.submit(id(n), [item(n)]);
    assert.equal(q.active.size, 4); assert.equal(q.pending.size, 16);
    q.submit(id(21), [item(21)]);
    assert.equal(results.find((r) => r.n === 21).reason, "queue_full");
    time = 100;
    q.submit(id(4), [item(4)]);
    assert.equal(q.pending.get(id(4)).deadline, 1000);
    assert.equal(results.find((r) => r.n === 4).reason, "superseded");
    time = 1000; q.expire();
    assert.equal(q.pending.size, 0);
    assert.equal(q.peakActive, 4); assert.equal(q.peakPending, 16);
    assert.equal(results.filter((r) => r.reason === "queue_timeout").length, 16);
  } finally { q.close(); }
});

test("WS-B1: exact 4 KiB multibyte join and 64 KiB batch; +1 rejected explicitly", async () => {
  const f = fixture();
  try {
    const { socket } = f.connect(1);
    const payload = { projectId: id(100), access: { kind: "share", shareId: "é" } };
    payload.access.shareId += "x".repeat(4096 - bytes(payload));
    assert.equal(bytes(payload), 4096);
    const accepted = [];
    f.auth.join(socket.id, payload, (r) => accepted.push(r)); await flush();
    assert.equal(accepted[0].status, "joined");
    payload.access.shareId += "x";
    const rejected = [];
    f.auth.join(socket.id, payload, (r) => rejected.push(r));
    assert.equal(rejected[0].status, "invalid_request");
  } finally { f.auth.close(); }
  const seen = [];
  const q = new AuthorizationQueue(async (body) => { seen.push(bytes(body)); return response(body); });
  try {
    const wire = { ref: "bytes", generation: 1, sequence: 1, padding: "é" };
    const body = q.envelope(id(1), "x".repeat(36), [{ wire }]);
    wire.padding += "x".repeat(65536 - bytes(body));
    q.submit(id(1), [{ at: q.now(), wire, done: () => {} }]); await flush();
    assert.equal(seen[0], 65536);
    wire.padding += "x";
    const rejected = [];
    q.submit(id(1), [{ at: q.now(), wire, done: (d, r) => rejected.push(r) }]); await flush();
    assert.deepEqual(rejected, ["batch_full"]);
    assert.equal(seen.length, 1);
  } finally { q.close(); }
});

test("WS-N1/J1/P1: bounded scheduler renews normal, 500+5+5 and 40x5 workloads fairly", async () => {
  for (const sizes of [Array(10).fill(5), [500, 5, 5], Array(40).fill(5)]) {
    const f = fixture();
    try {
      let n = 0;
      for (let p = 0; p < sizes.length; p++) for (let m = 0; m < sizes[p]; m++) {
        const { socket } = f.connect(n++);
        assert.equal((await f.join(socket, id(1000 + p)))[0].status, "joined");
        f.advance(11); f.auth.tick(); await flush();
      }
      const total = sizes.reduce((a, b) => a + b, 0);
      for (let round = 0; round < 250; round++) {
        f.advance(25); f.auth.tick(); await flush();
      }
      assert.equal(f.auth.contexts, total);
      for (let p = 0; p < sizes.length; p++) f.auth.emit(id(1000 + p), "project-op", {});
      assert.ok(f.sockets.every((s) => s.events.some((e) => e.event === "project-op")));
      assert.ok(f.auth.queue.peakActive <= 4 && f.auth.queue.peakPending <= 16);
      console.log(JSON.stringify({ workload: sizes, ...f.auth.stats() }));
    } finally { f.auth.close(); }
  }
});

test("WS-L1/L2: live 512 connections/4096 contexts; controlled refusal at 513/4097 and cleanup", async () => {
  const f = fixture();
  try {
    for (let n = 0; n < 512; n++) {
      const { socket, refusal } = f.connect(n);
      assert.equal(refusal, null);
      for (let p = 0; p < 8; p++) {
        assert.equal((await f.join(socket, id(1000 + p)))[0].status, "joined");
        f.advance(11); f.auth.tick(); await flush();
      }
    }
    assert.equal(f.auth.sockets.size, 512); assert.equal(f.auth.contexts, 4096);
    assert.equal(f.connect(513).refusal, "connection_limit");
    assert.equal((await f.join(f.sockets[0], id(9999)))[0].reason, "context_limit");
    assert.equal(f.auth.contexts, 4096);
    f.auth.disconnect(f.sockets[0].id);
    assert.equal(f.auth.contexts, 4088);
    console.log(JSON.stringify({ workload: "512/4096", ...f.auth.stats() }));
  } finally { f.auth.close(); assert.equal(f.auth.contexts, 0); }
});

test("WS-L3/R1: 32 rooms, 4 paths, per-subject bursts across reconnects, global burst and bucket retention", async () => {
  const f = fixture();
  try {
    const { socket } = f.connect(1);
    for (let n = 0; n < 32; n++) {
      await f.join(socket, id(100 + n)); f.advance(201); f.auth.tick(); await flush();
    }
    assert.equal(f.auth.sockets.get(socket.id).rooms.size, 32);
    assert.equal((await f.join(socket, id(999)))[0].reason, "room_limit");
    for (let n = 0; n < 3; n++) { f.advance(201); await f.join(socket, id(100), { kind: "share", shareId: `path-${n}` }); }
    f.advance(201);
    assert.equal((await f.join(socket, id(100), { kind: "share", shareId: "fifth" }))[0].reason, "path_limit");
    const other = f.connect(2, id(20)).socket;
    for (let n = 0; n < 10; n++) assert.equal((await f.join(other))[0].status, "joined");
    assert.equal((await f.join(other))[0].status, "rate_limited");
    f.auth.disconnect(other.id);
    const again = f.connect(3, id(20)).socket;
    assert.equal((await f.join(again))[0].status, "rate_limited");
    f.auth.leave(again.id, id(100));
    f.auth.disconnect(again.id);
    assert.ok(f.auth.buckets.has(id(20)));
    f.advance(2000); f.auth.cleanBuckets(); assert.equal(f.auth.buckets.has(id(20)), false);
  } finally { f.auth.close(); }
});

test("WS-R1: global burst 200, subject-map cap 2048 and two-second retention", async () => {
  const f = fixture();
  try {
    for (let n = 0; n < 200; n++) {
      const { socket } = f.connect(n);
      assert.equal((await f.join(socket))[0].status, "joined");
    }
    const extra = f.connect(200).socket;
    assert.equal((await f.join(extra))[0].status, "rate_limited");
    assert.equal(f.auth.contexts, 200);
  } finally { f.auth.close(); }
  const buckets = fixture();
  try {
    for (let n = 0; n < 2048; n++) {
      const { socket, refusal } = buckets.connect(n);
      assert.equal(refusal, null);
      buckets.auth.disconnect(socket.id);
    }
    assert.equal(buckets.auth.buckets.size, 2048);
    assert.equal(buckets.connect(2048).refusal, "bucket_limit");
    buckets.advance(2000); buckets.auth.cleanBuckets();
    assert.equal(buckets.auth.buckets.size, 0);
    assert.equal(buckets.connect(2049).refusal, null);
  } finally { buckets.auth.close(); }
});

test("WS-T04: positive result at/after total deadline never grants or renews", async () => {
  const held = [];
  const f = fixture((body) => new Promise((resolve) => held.push({ body, resolve })));
  try {
    const { socket } = f.connect(1);
    const replies = await f.join(socket);
    f.advance(1000);
    held[0].resolve(response(held[0].body)); await flush();
    assert.equal(replies[0].status, "unavailable");
    assert.equal(f.auth.contexts, 0);
    assert.equal(socket.rooms.size, 0);
  } finally { f.auth.close(); }
});

test("WS-B1/T10: wide UTF-8 contexts split before 64 KiB even below 50 evaluations", async () => {
  const batches = [];
  const f = fixture(async (body) => { batches.push(body); return response(body); });
  try {
    for (let n = 0; n < 30; n++) {
      const { socket } = f.connect(n);
      assert.equal((await f.join(socket, id(100), { kind: "share", shareId: "é".repeat(1800) }))[0].status, "joined");
    }
    const before = batches.length;
    f.advance(1000);
    for (let n = 0; n < 4; n++) { f.auth.tick(); await flush(); }
    const revalidations = batches.slice(before);
    assert.ok(revalidations.length > 1);
    assert.equal(revalidations.reduce((count, batch) => count + batch.evaluations.length, 0), 30);
    assert.ok(revalidations.every((batch) => batch.evaluations.length <= 50 && bytes(batch) <= 65536));
    assert.equal(f.auth.contexts, 30);
    for (const record of f.auth.sockets.values()) {
      assert.ok([...record.rooms.get(id(100)).paths.values()].every((context) => context.until === 6000));
    }
  } finally { f.auth.close(); }
});
