// Fault-injection probes on the isolated stack: handled tool error, broker restart,
// message durability. Synthetic accounts; only the picturas-nfr project is touched.
import { GW, register, bearer, createProject, getProject, uploadFile, request, sleep, inspect, cname } from './lib.mjs';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
const DIR = new URL('.', import.meta.url).pathname;
const MG = 'http://localhost:35672/api/';
const auth = { Authorization: 'Basic ' + Buffer.from('user:password').toString('base64') };
const q = async (name) => { const r = await request('GET', MG + 'queues/%2F/' + name, { headers: auth }); return r.status === 200 ? { consumers: r.data.consumers, messages: r.data.messages ?? 0 } : { status: r.status }; };
const mongoCount = (coll) => Number(execFileSync('docker', ['exec', cname('projects_mongoDB'), 'mongo', '--quiet', '--port', '27018', '--eval', `db.getSiblingDB("project").${coll}.count()`], { encoding: 'utf8' }).trim());
const docker = (...a) => execFileSync('docker', a, { encoding: 'utf8' }).trim();
const out = { recorded_at: new Date().toISOString(), experiments: [] };
const log = (e) => { out.experiments.push(e); console.log(JSON.stringify(e)); };
const ops = async (a) => (await request('GET', GW + `users/${a.id}`)).data?.remaining_operations;

// WebSocket listener for one account (polling transport)
async function listen(account) {
  const base = 'https://localhost:28080/socket.io/?EIO=4&transport=polling';
  const hs = await request('GET', base + '&t=' + Date.now());
  const sid = JSON.parse(String(hs.raw).slice(1)).sid;
  const url = () => `${base}&sid=${sid}&t=${Date.now()}`;
  const post = (p) => request('POST', url(), { headers: { 'Content-Type': 'text/plain;charset=UTF-8' }, body: Buffer.from(p) });
  await post('40' + JSON.stringify({ token: account.jwt }));
  const events = []; let stop = false;
  (async () => { while (!stop) { try { const p = await request('GET', url()); if (p.status !== 200) break; for (const pk of String(p.raw).split('\x1e')) { if (pk === '2') await post('3'); if (pk.startsWith('42')) { const [ev] = JSON.parse(pk.slice(2)); events.push({ ev, t: Date.now() }); } } } catch { break; } } })();
  return { events, close: () => { stop = true; post('41').catch(() => {}); } };
}
async function addTool(a, p, procedure, params) { await getProject(a, p); return request('POST', GW + `projects/${a.id}/${p.id}/tool`, { headers: { ...bearer(a), 'X-Project-Version': String(p.version) }, json: { procedure, params } }); }
async function apply(a, p) { await getProject(a, p); return request('POST', GW + `projects/${a.id}/${p.id}/process`, { headers: { ...bearer(a), 'X-Project-Version': String(p.version) }, json: {} }); }
async function upImg(a, p, name = 'probe.png') { await getProject(a, p); return uploadFile(GW + `projects/${a.id}/${p.id}/img`, 'image', DIR + 'probe.png', name, 'image/png', { ...bearer(a), 'X-Project-Version': String(p.version) }); }
async function upVid(a, p, name = 'v.mp4') { await getProject(a, p); return uploadFile(GW + `projects/${a.id}/${p.id}/video`, 'video', DIR + 'pad_10MiB.mp4', name, 'video/mp4', { ...bearer(a), 'X-Project-Version': String(p.version) }); }

const which = process.argv[2] || 'all';

if (which === 'all' || which === 'R0') { // positive control: valid image job
  const a = await register('free'); const p = await createProject(a, 'r0'); await upImg(a, p);
  await addTool(a, p, 'brightness', { brightness: 1.3 });
  const ws = await listen(a); const t0 = Date.now(); const r = await apply(a, p);
  for (let i = 0; i < 40 && !ws.events.some((e) => /process-(update|error)/.test(e.ev)); i++) await sleep(250);
  log({ id: 'R0', what: 'valid image + brightness (control)', apply_status: r.status, events: ws.events.map((e) => `${e.ev}@${e.t - t0}ms`), pending_process_docs: mongoCount('processes') }); ws.close();
}
if (which === 'all' || which === 'R1') { // handled error inside an image tool
  const a = await register('free'); const p = await createProject(a, 'r1'); await upImg(a, p);
  const t = await addTool(a, p, 'border', { borderWidth: 'not-a-number', r: 0, g: 0, b: 0 });
  const before = { restarts: Number(inspect('border_tool', '{{.RestartCount}}')), started: inspect('border_tool', '{{.State.StartedAt}}'), pending: mongoCount('processes') };
  const ws = await listen(a); const t0 = Date.now(); const r = await apply(a, p);
  await sleep(30000);
  log({ id: 'R1', what: 'image + border with invalid borderWidth; observed 30 s', add_tool_status: t.status, apply_status: r.status, client_events_in_30s: ws.events.map((e) => `${e.ev}@${e.t - t0}ms`),
    border_tool_restarts: Number(inspect('border_tool', '{{.RestartCount}}')) - before.restarts, border_tool_restarted: inspect('border_tool', '{{.State.StartedAt}}') !== before.started,
    pending_process_docs_delta: mongoCount('processes') - before.pending, border_queue: await q('border_queue'), tool_log_tail: docker('logs', '--tail', '3', cname('border_tool')).split('\n').slice(-2).join(' | ').slice(0, 300) }); ws.close();
}
if (which === 'all' || which === 'R2') { // broker restart: who reconnects?
  const names = ['project_queue', 'ws_queue', 'video_queue', 'brightness_queue', 'border_queue'];
  const before = {}; for (const n of names) before[n] = (await q(n)).consumers;
  const starts = {}; for (const s of ['projects', 'ws_gateway', 'video_tool', 'brightness_tool', 'border_tool']) starts[s] = inspect(s, '{{.RestartCount}} {{.State.StartedAt}}');
  const t0 = Date.now(); docker('restart', cname('rabbitmq'));
  let up = null; for (let i = 0; i < 120; i++) { try { const r = await request('GET', MG + 'overview', { headers: auth }); if (r.status === 200) { up = Date.now() - t0; break; } } catch {} await sleep(500); }
  const timeline = [];
  for (const wait of [5, 15, 30, 60]) { await sleep((wait - (timeline.at(-1)?.s ?? 0)) * 1000); const c = {}; for (const n of names) c[n] = (await q(n)).consumers; timeline.push({ s: wait, consumers: c }); }
  const svc = {}; for (const s of Object.keys(starts)) { const now = inspect(s, '{{.RestartCount}} {{.State.StartedAt}}'); svc[s] = { state: inspect(s, '{{.State.Status}}'), container_restarted: now !== starts[s] }; }
  // can a user still process after the broker came back?
  const a = await register('free'); const p = await createProject(a, 'r2'); await upImg(a, p); await addTool(a, p, 'brightness', { brightness: 1.3 });
  const ws = await listen(a); const t1 = Date.now(); const r = await apply(a, p);
  for (let i = 0; i < 80 && !ws.events.some((e) => /process-(update|error)/.test(e.ev)); i++) await sleep(250);
  log({ id: 'R2', what: 'docker restart rabbitmq while idle', broker_api_back_ms: up, consumers_before: before, consumers_after: timeline, services: svc,
    job_after_restart: { apply_status: r.status, events_in_20s: ws.events.map((e) => `${e.ev}@${e.t - t1}ms`) }, projects_log_tail: docker('logs', '--tail', '4', cname('projects')).split('\n').join(' | ').slice(-400) }); ws.close();
}
if (which === 'all' || which === 'R3') { // durability of an accepted job across a broker restart
  const a = await register('free'); const p = await createProject(a, 'r3'); const u = await upVid(a, p); await addTool(a, p, 'brightness', { brightness: 1.3 });
  docker('stop', cname('video_tool'));
  const opsBefore = await ops(a); const pend0 = mongoCount('processes');
  const r = await apply(a, p); await sleep(2000);
  const ctl = () => docker('exec', cname('rabbitmq'), 'rabbitmqctl', '-q', 'list_queues', 'name', 'messages', 'consumers').split('\n').find((l) => l.startsWith('video_queue'))?.split(/\s+/).slice(1).join(' msgs / consumers '); const queued = ctl();
  docker('restart', cname('rabbitmq'));
  for (let i = 0; i < 120; i++) { try { const x = await request('GET', MG + 'overview', { headers: auth }); if (x.status === 200) break; } catch {} await sleep(500); }
  await sleep(3000);
  const afterRestart = ctl();
  docker('start', cname('video_tool')); await sleep(45000);
  const res = await request('GET', GW + `projects/${a.id}/${p.id}/process`, { headers: bearer(a) });
  log({ id: 'R3', what: 'video job accepted (worker stopped) -> broker restart -> worker started; observed 45 s', upload_status: u.status, apply_status: r.status,
    video_queue_before_restart: queued, video_queue_after_restart: afterRestart, ops_before: opsBefore, ops_after: await ops(a),
    pending_process_docs_delta: mongoCount('processes') - pend0, results_endpoint_status: res.status, results: Array.isArray(res.data?.imgs) ? res.data.imgs.length : (typeof res.data === 'string' ? res.data.slice(0, 80) : Object.keys(res.data || {})) });
}
fs.writeFileSync(DIR + `reliability-${which}-result.json`, JSON.stringify(out, null, 1));
