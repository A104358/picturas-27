const { randomUUID } = require("node:crypto");
const { performance } = require("node:perf_hooks");

const DEFAULTS = Object.freeze({
  timeoutMs: 1000, batchSize: 50, bodyBytes: 65536, active: 4, pending: 16,
  revalidateMs: 1000, retryMs: 250, leaseMs: 5000, connections: 512, contexts: 4096,
  rooms: 32, paths: 4, subjectRate: 5, subjectBurst: 10,
  globalRate: 100, globalBurst: 200, buckets: 2048, retentionMs: 2000,
});
const bytes = (value) => Buffer.byteLength(JSON.stringify(value));
const objectId = (value) => typeof value === "string" && /^[a-f\d]{24}$/i.test(value);

function configuration(env = process.env) {
  const config = { ...DEFAULTS };
  for (const key of Object.keys(config)) {
    const name = `WS_${key.replace(/[A-Z]/g, (letter) => `_${letter}`).toUpperCase()}`;
    if (env[name] !== undefined) {
      const value = Number(env[name]);
      if (!Number.isSafeInteger(value) || value < 1) throw new Error(`Invalid ${name}`);
      config[key] = value;
    }
  }
  // The receiving endpoint's protocol ceilings and the security deadlines cannot
  // be weakened through deployment configuration.
  if (config.bodyBytes > 65536 || config.batchSize > 50 || config.leaseMs > 5000 ||
      config.timeoutMs > 1000 || config.revalidateMs > 1000 ||
      config.retryMs > config.revalidateMs) throw new Error("Unsafe WS configuration");
  return config;
}

class AuthorizationQueue {
  constructor(evaluate, config = DEFAULTS, now = () => performance.now()) {
    this.evaluate = evaluate;
    this.config = config;
    this.now = now;
    this.pending = new Map();
    this.active = new Map();
    this.counts = {};
    this.closed = false;
    this.peakActive = 0;
    this.peakPending = 0;
    this.timing = { requests: 0, evaluations: 0, waitMaxMs: 0, httpMaxMs: 0 };
  }

  count(reason) { this.counts[reason] = (this.counts[reason] || 0) + 1; }
  envelope(projectId, requestId, items) {
    return { projectId, requestId, evaluations: items.map((item) => item.wire) };
  }

  submit(projectId, items) {
    if (this.closed) return items.forEach((item) => item.done(null, "closed"));
    this.expire();
    const previous = this.pending.get(projectId);
    if (!previous && this.pending.size >= this.config.pending) {
      this.count("queue_full");
      return items.forEach((item) => item.done(null, "queue_full"));
    }
    const requestId = randomUUID();
    const selected = [];
    const refs = new Set(items.map((item) => item.wire.ref));
    const candidates = items.concat(previous ? previous.items.filter((item) => !refs.has(item.wire.ref)) : []);
    const deadline = Math.min(previous?.deadline ?? Infinity,
      ...items.map((item) => item.at + this.config.timeoutMs));
    if (previous) {
      clearTimeout(previous.timer);
      for (const item of previous.items) {
        if (refs.has(item.wire.ref)) item.done(null, "superseded");
      }
    }
    for (const item of candidates) {
      if (selected.length < this.config.batchSize &&
          bytes(this.envelope(projectId, requestId, selected.concat(item))) <= this.config.bodyBytes) {
        selected.push(item);
      } else {
        this.count("batch_full");
        item.done(null, "batch_full");
      }
    }
    if (!selected.length) { this.pending.delete(projectId); return; }
    const batch = { projectId, requestId, items: selected, deadline };
    batch.timer = setTimeout(() => this.expire(), Math.max(0, deadline - this.now()));
    this.pending.set(projectId, batch);
    this.peakPending = Math.max(this.peakPending, this.pending.size);
    this.drain();
  }

  expire() {
    for (const [projectId, batch] of this.pending) {
      if (batch.deadline <= this.now()) {
        this.pending.delete(projectId);
        clearTimeout(batch.timer);
        this.count("queue_timeout");
        batch.items.forEach((item) => item.done(null, "queue_timeout"));
      }
    }
  }

  drain() {
    this.expire();
    for (const [projectId, batch] of this.pending) {
      if (this.active.size >= this.config.active) break;
      if (this.active.has(projectId)) continue;
      this.pending.delete(projectId);
      clearTimeout(batch.timer);
      this.active.set(projectId, batch);
      this.peakActive = Math.max(this.peakActive, this.active.size);
      const controller = new AbortController();
      const started = this.now();
      this.timing.requests++;
      this.timing.evaluations += batch.items.length;
      this.timing.waitMaxMs = Math.max(this.timing.waitMaxMs, ...batch.items.map((item) => started - item.at));
      let finished = false;
      const finish = (response, reason) => {
        if (finished) return;
        finished = true;
        this.timing.httpMaxMs = Math.max(this.timing.httpMaxMs, this.now() - started);
        clearTimeout(batch.timer);
        controller.abort();
        this.active.delete(projectId);
        if (this.now() >= batch.deadline) { response = null; reason = "timeout"; }
        let decisions = null;
        try {
          if (response && bytes(response) <= this.config.bodyBytes &&
              response.requestId === batch.requestId && response.projectId === projectId &&
              Array.isArray(response.decisions) && response.decisions.length === batch.items.length) {
            const byRef = new Map(response.decisions.map((decision) => [decision.ref, decision]));
            if (byRef.size === batch.items.length && batch.items.every(({ wire }) => {
              const decision = byRef.get(wire.ref);
              return decision && decision.generation === wire.generation && decision.sequence === wire.sequence &&
                ["allow", "deny", "unavailable"].includes(decision.decision) &&
                (decision.decision !== "allow" || ["owner", "read", "edit"].includes(decision.permission));
            })) decisions = byRef;
          }
        } catch (_) { /* Invalid JSON shape never authorizes a prefix. */ }
        if (!decisions) this.count(reason || "invalid_response");
        batch.items.forEach((item) => item.done(decisions?.get(item.wire.ref), decisions ? undefined : reason || "invalid_response"));
        this.drain();
      };
      batch.cancel = () => finish(null, "closed");
      batch.timer = setTimeout(() => finish(null, "timeout"), Math.max(0, batch.deadline - this.now()));
      Promise.resolve().then(() => this.evaluate(this.envelope(projectId, batch.requestId, batch.items),
        { signal: controller.signal, deadline: batch.deadline }))
        .then((response) => finish(response), () => finish(null, "transport"));
    }
  }

  cancel(ref) {
    for (const [projectId, batch] of this.pending) {
      const removed = batch.items.filter((item) => item.wire.ref === ref);
      batch.items = batch.items.filter((item) => item.wire.ref !== ref);
      removed.forEach((item) => item.done(null, "cancelled"));
      if (!batch.items.length) { clearTimeout(batch.timer); this.pending.delete(projectId); }
    }
    // Active results retain their captured generation/sequence and are discarded
    // by the member if it left. Other members of the same batch remain useful.
  }

  close() {
    this.closed = true;
    for (const batch of this.pending.values()) {
      clearTimeout(batch.timer);
      batch.items.forEach((item) => item.done(null, "closed"));
    }
    this.pending.clear();
    for (const batch of [...this.active.values()]) batch.cancel();
  }
}

class Authorization {
  constructor(evaluate, config = DEFAULTS, clock = {}) {
    this.config = config;
    this.now = clock.now || (() => performance.now());
    this.wall = clock.wall || Date.now;
    this.queue = new AuthorizationQueue(evaluate, config, this.now);
    this.sockets = new Map();
    this.projects = new Map();
    this.buckets = new Map();
    this.global = { tokens: config.globalBurst, at: this.now() };
    this.contexts = 0;
    this.generation = 0;
    this.cursor = 0;
    this.counts = {};
    this.cadence = { ticks: 0, tickGapMaxMs: 0, renewalGapMaxMs: 0 };
    this.lastTick = this.now();
  }
  count(reason) { this.counts[reason] = (this.counts[reason] || 0) + 1; }
  sessionValid(record) { return this.now() < record.deadline && this.wall() < record.exp * 1000; }

  connect(socket, session) {
    this.cleanBuckets();
    if (this.sockets.size >= this.config.connections) return "connection_limit";
    let bucket = this.buckets.get(session.sub);
    if (!bucket) {
      if (this.buckets.size >= this.config.buckets) return "bucket_limit";
      bucket = { tokens: this.config.subjectBurst, at: this.now(), refs: 0, until: Infinity };
      this.buckets.set(session.sub, bucket);
    }
    bucket.refs++;
    bucket.until = Infinity;
    const record = { socket, sub: session.sub, exp: session.exp, rooms: new Map(),
      deadline: this.now() + Math.max(0, session.exp * 1000 - this.wall()) };
    this.sockets.set(socket.id, record);
    record.timer = setTimeout(() => this.expireSession(record), Math.max(0, record.deadline - this.now()));
    return null;
  }
  cleanBuckets() {
    for (const [sub, bucket] of this.buckets) if (!bucket.refs && bucket.until <= this.now()) this.buckets.delete(sub);
  }
  expireSession(record) {
    if (!this.sockets.has(record.socket.id)) return;
    record.socket.emit("session-expired", { status: "session_expired" });
    this.disconnect(record.socket.id);
    record.socket.disconnect(true);
  }
  disconnect(socketId) {
    const record = this.sockets.get(socketId);
    if (!record) return;
    clearTimeout(record.timer);
    for (const room of [...record.rooms.values()]) this.leaveRecord(record, room);
    this.sockets.delete(socketId);
    const bucket = this.buckets.get(record.sub);
    bucket.refs--;
    if (!bucket.refs) bucket.until = this.now() + this.config.retentionMs;
  }
  take(bucket, rate, burst) {
    bucket.tokens = Math.min(burst, bucket.tokens + Math.max(0, this.now() - bucket.at) * rate / 1000);
    bucket.at = this.now();
    return bucket.tokens >= 1;
  }
  rate(record) {
    const subject = this.buckets.get(record.sub);
    const first = this.take(subject, this.config.subjectRate, this.config.subjectBurst);
    const second = this.take(this.global, this.config.globalRate, this.config.globalBurst);
    if (!first || !second) return false;
    subject.tokens--; this.global.tokens--;
    return true;
  }
  live(context) { return context.room.paths.get(context.key) === context && this.sockets.has(context.record.socket.id); }
  allowed(record, room) {
    return this.sessionValid(record) && [...room.paths.values()].some((context) => context.until > this.now());
  }
  remove(context, status = "unavailable") {
    if (!this.live(context)) return;
    const { record, room } = context;
    room.paths.delete(context.key);
    this.contexts--;
    this.projects.get(room.id)?.members.delete(context);
    context.ack?.({ status, reason: "authorization_removed" });
    context.ack = null;
    this.queue.cancel(context.ref);
    if (!room.paths.size) record.rooms.delete(room.id);
    if (!this.projects.get(room.id)?.members.size) this.projects.delete(room.id);
    if (!this.allowed(record, room)) {
      record.socket.leave(`project:${room.id}`);
      if (context.ever) record.socket.emit("project-access", { projectId: room.id, status });
    }
  }
  // Decision 53 (D-30 A): a lease that lapses suspends the context instead of removing it.
  // It receives nothing (emit() checks the lease), keeps its slot in the 512/4096 limits and
  // keeps being revalidated (every retryMs while it fails); only a fresh allow, valid for at
  // most leaseMs after its admission, resumes it without a new join. A deny still removes it
  // and an expired JWT still closes the socket.
  suspend(context) {
    if (!this.live(context) || context.suspended) return;
    context.suspended = true;
    this.count("suspended");
    const { record, room } = context;
    if (!this.allowed(record, room)) {
      record.socket.leave(`project:${room.id}`);
      record.socket.emit("project-access", { projectId: room.id, status: "suspended" });
    }
  }
  leaveRecord(record, room) {
    for (const context of [...room.paths.values()]) this.remove(context);
    record.socket.leave(`project:${room.id}`);
  }
  leave(socketId, projectId) {
    const record = this.sockets.get(socketId);
    const room = record?.rooms.get(projectId);
    if (room) this.leaveRecord(record, room);
  }

  join(socketId, payload, callback = () => {}) {
    const ack = typeof callback === "function" ? callback : () => {};
    const record = this.sockets.get(socketId);
    if (!record || !this.sessionValid(record)) { ack({ status: "session_expired" }); return; }
    const access = payload?.access;
    if (!payload || bytes(payload) > 4096 || !objectId(payload.projectId) ||
        Object.keys(payload).some((key) => !["projectId", "access"].includes(key)) ||
        !access || !["owner", "share"].includes(access.kind) ||
        Object.keys(access).some((key) => !["kind", "shareId"].includes(key)) ||
        (access.kind === "owner" && access.shareId !== undefined) ||
        (access.kind === "share" && (typeof access.shareId !== "string" || !access.shareId.length))) {
      ack({ status: "invalid_request" }); return;
    }
    if (!this.rate(record)) { this.count("rate_limited"); ack({ status: "rate_limited" }); return; }
    let room = record.rooms.get(payload.projectId);
    const key = access.kind === "owner" ? "owner" : `share:${access.shareId}`;
    let context = room?.paths.get(key);
    const limit = !room && record.rooms.size >= this.config.rooms ? "room_limit" :
      !context && room?.paths.size >= this.config.paths ? "path_limit" :
      !context && this.contexts >= this.config.contexts ? "context_limit" : null;
    if (limit) { this.count(limit); ack({ status: "rate_limited", reason: limit }); return; }
    if (!room) { room = { id: payload.projectId, paths: new Map() }; record.rooms.set(room.id, room); }
    if (!context) {
      context = { record, room, key, access: { ...access }, ref: randomUUID(),
        generation: ++this.generation, sequence: 0, until: 0, ever: false, suspended: false, retried: false, pending: false, due: Infinity };
      room.paths.set(key, context);
      this.contexts++;
      if (!this.projects.has(room.id)) this.projects.set(room.id, { members: new Set(), cursor: 0 });
      this.projects.get(room.id).members.add(context);
    }
    context.ack?.({ status: "unavailable", reason: "superseded" });
    context.ack = ack;
    const item = this.evaluation(context);
    this.queue.submit(room.id, [item]);
  }

  evaluation(context) {
    const sequence = ++context.sequence;
    const at = this.now();
    context.pending = true;
    return { at, wire: { ref: context.ref, generation: context.generation, sequence,
      sub: context.record.sub, exp: context.record.exp, access: context.access },
    done: (decision, reason) => {
      if (!this.live(context) || context.sequence !== sequence) return;
      context.pending = false;
      const ack = context.ack;
      context.ack = null;
      if (!this.sessionValid(context.record)) {
        ack?.({ status: "session_expired" }); this.expireSession(context.record); return;
      }
      if (decision?.decision === "deny") {
        ack?.({ status: "denied" }); this.remove(context, "denied"); return;
      }
      if (decision?.decision === "allow" && this.now() < at + this.config.timeoutMs) {
        if (context.ever && !context.suspended) this.cadence.renewalGapMaxMs = Math.max(this.cadence.renewalGapMaxMs, at - context.lastPositive);
        context.lastPositive = at;
        context.until = Math.min(at + this.config.leaseMs, context.record.deadline,
          this.now() + Math.max(0, context.record.exp * 1000 - this.wall()));
        context.ever = true;
        context.suspended = false;
        context.retried = false;
        context.due = at + this.config.revalidateMs;
        context.record.socket.join(`project:${context.room.id}`);
        ack?.({ status: "joined" });
      } else {
        this.count(reason || "unavailable");
        ack?.({ status: "unavailable", reason: reason || "unavailable" });
        if (!context.ever) this.remove(context);
        else if (!["superseded", "batch_full", "queue_full"].includes(reason)) {
          // One quick retry after a failure, and quick retries while suspended, so a context
          // resumes soon after projects answers again. A failure never extends the lease.
          context.due = this.now() + (context.retried && !context.suspended ? this.config.revalidateMs : this.config.retryMs);
          context.retried = true;
        }
      }
    } };
  }

  tick() {
    this.cadence.ticks++;
    this.cadence.tickGapMaxMs = Math.max(this.cadence.tickGapMaxMs, this.now() - this.lastTick);
    this.lastTick = this.now();
    this.cleanBuckets();
    for (const record of [...this.sockets.values()]) {
      if (!this.sessionValid(record)) { this.expireSession(record); continue; }
      for (const room of [...record.rooms.values()]) {
        for (const context of [...room.paths.values()]) {
          if (context.ever && context.until <= this.now()) this.suspend(context);
        }
      }
    }
    const projects = [...this.projects.entries()];
    if (!projects.length) return;
    this.cursor %= projects.length;
    for (let i = 0; i < projects.length; i++) {
      const [projectId, state] = projects[(this.cursor + i) % projects.length];
      // Existing pending batches get their turn. Unadmitted projects are visited
      // by the same rotating cursor; there is no second queue of promises.
      if (this.queue.pending.has(projectId) || this.queue.active.has(projectId) ||
          this.queue.pending.size >= this.config.pending) continue;
      const members = [...state.members];
      const items = [];
      for (let n = 0; n < members.length; n++) {
        const index = state.cursor % members.length;
        const context = members[index];
        state.cursor = (index + 1) % members.length;
        if (context.pending || context.due > this.now()) continue;
        const candidate = { wire: { ref: context.ref, generation: context.generation,
          sequence: context.sequence + 1, sub: context.record.sub, exp: context.record.exp, access: context.access } };
        if (bytes(this.queue.envelope(projectId, "x".repeat(36), items.concat(candidate))) > this.config.bodyBytes) {
          if (!items.length) this.remove(context);
          break;
        }
        items.push(this.evaluation(context));
        if (items.length >= this.config.batchSize) break;
      }
      if (items.length) this.queue.submit(projectId, items);
    }
    this.cursor = (this.cursor + 1) % projects.length;
  }

  emit(projectId, event, payload, user) {
    if (!objectId(projectId)) { this.count("event_missing_project"); return; }
    // Never broadcast protected data with io.to(): each recipient's lease and
    // absolute JWT expiry are checked immediately before every emission.
    for (const record of this.sockets.values()) {
      if (user !== undefined && String(user) !== record.sub) continue;
      const room = record.rooms.get(projectId);
      if (room && this.allowed(record, room)) record.socket.emit(event, payload);
    }
  }
  close() {
    for (const record of [...this.sockets.values()]) {
      this.disconnect(record.socket.id); record.socket.disconnect(true);
    }
    this.queue.close();
  }
  stats() {
    return { connections: this.sockets.size, contexts: this.contexts, buckets: this.buckets.size,
      active: this.queue.active.size, pending: this.queue.pending.size,
      peakActive: this.queue.peakActive, peakPending: this.queue.peakPending,
      reasons: { ...this.counts }, queueReasons: { ...this.queue.counts },
      timing: { ...this.queue.timing }, cadence: { ...this.cadence } };
  }
}

module.exports = { Authorization, AuthorizationQueue, DEFAULTS, configuration, bytes, objectId };
