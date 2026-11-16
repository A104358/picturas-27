// Shared helpers for the NFR probes. Runs on the host with Node 22, no deps.
// Never prints tokens, passwords or signed URLs.
import https from 'node:https';
import http from 'node:http';
import fs from 'node:fs';
import { randomUUID } from 'node:crypto';
import { execFileSync } from 'node:child_process';

export const GW = process.env.GW || 'https://localhost:28080/api-gateway/';
export const PROJECT = process.env.COMPOSE_PROJECT || 'picturas-nfr';
const agent = new https.Agent({ rejectUnauthorized: false, keepAlive: false });

export function request(method, url, { headers = {}, body, json } = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const mod = u.protocol === 'https:' ? https : http;
    let payload = body;
    if (json !== undefined) { payload = Buffer.from(JSON.stringify(json)); headers = { 'Content-Type': 'application/json', ...headers }; }
    if (payload) headers = { 'Content-Length': payload.length, ...headers };
    const started = performance.now();
    const req = mod.request(u, { method, headers, agent: u.protocol === 'https:' ? agent : undefined }, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        const raw = Buffer.concat(chunks);
        let data = raw.toString();
        try { data = JSON.parse(data); } catch {}
        resolve({ status: res.statusCode, headers: res.headers, data, raw, ms: performance.now() - started });
      });
    });
    req.on('error', reject);
    req.end(payload);
  });
}

export async function register(type = 'free') {
  const r = await request('POST', GW + 'users/', { json: { name: `nfr-${type}`, email: `nfr-${randomUUID()}@example.invalid`, password: randomUUID(), type } });
  if (r.status !== 201) throw new Error('register HTTP ' + r.status);
  return { id: r.data.user._id, jwt: r.data.jwt, type: r.data.user.type };
}
export const bearer = (a) => ({ Authorization: `Bearer ${a.jwt}` });

export async function createProject(a, name = 'nfr') {
  const r = await request('POST', GW + `projects/${a.id}`, { headers: bearer(a), json: { name } });
  if (r.status !== 201) throw new Error('project HTTP ' + r.status);
  return { id: r.data._id, version: r.data.version ?? 0, owner: a };
}
export async function getProject(a, p) {
  const r = await request('GET', GW + `projects/${p.owner.id}/${p.id}`, { headers: bearer(a) });
  if (r.status === 200 && r.data.version !== undefined) p.version = r.data.version;
  return r;
}

// Streams a multipart upload and separates "last byte handed to the socket"
// from "response received" (post-send acceptance time, REQ-VID-SUBMIT-008).
export function uploadFile(url, field, filePath, filename, contentType, headers = {}) {
  return new Promise((resolve, reject) => {
    const boundary = '----nfr' + randomUUID();
    const head = Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="${field}"; filename="${filename}"\r\nContent-Type: ${contentType}\r\n\r\n`);
    const tail = Buffer.from(`\r\n--${boundary}--\r\n`);
    const size = fs.statSync(filePath).size;
    const u = new URL(url);
    const t0 = performance.now();
    let tSent = null;
    const req = https.request(u, { method: 'POST', agent, headers: { 'Content-Type': `multipart/form-data; boundary=${boundary}`, 'Content-Length': head.length + size + tail.length, ...headers } }, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        const t1 = performance.now();
        resolve({ status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks).toString().slice(0, 200), bytes: size,
          total_ms: +(t1 - t0).toFixed(1), send_ms: tSent === null ? null : +(tSent - t0).toFixed(1), post_send_ms: tSent === null ? null : +(t1 - tSent).toFixed(1) });
      });
    });
    req.on('error', (e) => resolve({ status: 0, error: e.code || e.message, bytes: size, total_ms: +(performance.now() - t0).toFixed(1), send_ms: tSent === null ? null : +(tSent - t0).toFixed(1) }));
    req.write(head);
    const stream = fs.createReadStream(filePath, { highWaterMark: 1 << 20 });
    stream.on('error', reject);
    stream.on('end', () => req.end(tail, () => { tSent = performance.now(); }));
    stream.pipe(req, { end: false });
  });
}

// Container helpers -------------------------------------------------------
export const cname = (svc) => `${PROJECT}-${svc}-1`;
export function dexec(svc, script) {
  return execFileSync('docker', ['exec', cname(svc), 'sh', '-c', script], { encoding: 'utf8' });
}
// Largest-RSS node process in the container: the service itself.
const PIDSH = `best=0;bp=0;for d in /proc/[0-9]*;do n=$(cat $d/comm 2>/dev/null);case "$n" in node*|MainThread) r=$(awk '/VmRSS/{print $2}' $d/status 2>/dev/null);[ "\${r:-0}" -gt "$best" ]&&best=$r&&bp=\${d#/proc/};;esac;done;echo $bp`;
export function nodePid(svc) { return dexec(svc, PIDSH).trim(); }
export function resetPeak(svc) {
  const pid = nodePid(svc);
  const out = dexec(svc, `echo 5 > /proc/${pid}/clear_refs; awk '/VmRSS/{print $2}' /proc/${pid}/status`);
  return { pid, rss_kb: Number(out.trim()) };
}
export function readPeak(svc, pid) {
  try {
    const out = dexec(svc, `awk '/VmHWM/{h=$2}/VmRSS/{r=$2}END{print h, r}' /proc/${pid}/status`).trim().split(' ');
    return { hwm_kb: Number(out[0]), rss_kb: Number(out[1]), alive: true };
  } catch { return { alive: false }; }
}
export function inspect(svc, fmt) {
  return execFileSync('docker', ['inspect', cname(svc), '--format', fmt], { encoding: 'utf8' }).trim();
}
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
export const mib = (kb) => +(kb / 1024).toFixed(1);
