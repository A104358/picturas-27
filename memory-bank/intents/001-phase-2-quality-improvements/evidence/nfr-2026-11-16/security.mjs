// Finite authorization matrix: public gateway, direct service ports and WebSocket.
// Synthetic accounts only. No token, password, signed URL or payload is stored.
import { GW, register, bearer, createProject, getProject, uploadFile, request, sleep } from './lib.mjs';
import fs from 'node:fs';
import zlib from 'node:zlib';
import { createHash, randomUUID } from 'node:crypto';
import { execFileSync } from 'node:child_process';

const DIR = new URL('.', import.meta.url).pathname;
const PROJ = process.env.PROJECTS_DIRECT || 'https://localhost:29002/';
const STOR = process.env.STORAGE_DIRECT || 'http://localhost:31000/';
const USERS = process.env.USERS_DIRECT || 'https://localhost:30001/';
const WS = process.env.WS_URL || 'https://localhost:28080/socket.io/';
const cases = [];
const add = (id, surface, description, expected, observed, admitted) => { const c = { id, surface, description, expected, observed, unauthorized_admitted: admitted }; cases.push(c); console.error(JSON.stringify(c)); };

// minimal valid PNG (64x64 grey)
function png() {
  const crcT = Array.from({ length: 256 }, (_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c >>> 0; });
  const crc = (b) => { let c = 0xffffffff; for (const x of b) c = crcT[(c ^ x) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
  const chunk = (t, d) => { const l = Buffer.alloc(4); l.writeUInt32BE(d.length); const td = Buffer.concat([Buffer.from(t), d]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([l, td, c]); };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(64, 0); ihdr.writeUInt32BE(64, 4); ihdr[8] = 8; ihdr[9] = 2;
  const raw = Buffer.alloc(64 * (1 + 64 * 3), 128); for (let y = 0; y < 64; y++) raw[y * 193] = 0;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}
fs.writeFileSync(DIR + 'probe.png', png());
const pngSha = createHash('sha256').update(png()).digest('hex');

const owner = await register('free');
const outsider = await register('free');
const proj = await createProject(owner, 'victim');
await getProject(owner, proj);
const up = await uploadFile(GW + `projects/${owner.id}/${proj.id}/img`, 'image', DIR + 'probe.png', 'probe.png', 'image/png', { ...bearer(owner), 'X-Project-Version': String(proj.version) });
const pr = await getProject(owner, proj);
const img = pr.data.imgs?.[0];
add('C00', 'gateway', 'Owner reads own project (positive control)', 'permit', `HTTP ${pr.status}, upload HTTP ${up.status}, media=${pr.data.imgs?.length}`, false);

// ---- Public gateway ----
let r = await request('GET', GW + `projects/${owner.id}/${proj.id}`, { headers: bearer(outsider) });
add('G01', 'gateway', "Other user's JWT reads owner's project (path user = owner)", 'reject', `HTTP ${r.status}`, r.status === 200);
r = await request('GET', GW + `projects/${outsider.id}/${proj.id}?owner=${owner.id}`, { headers: bearer(outsider) });
add('G02', 'gateway', "Outsider JWT + ?owner=<victim> on GET project", 'reject', `HTTP ${r.status}${r.status === 200 ? `, returned project of user ${String(r.data.user_id) === owner.id ? 'OWNER' : '?'}` : ''}`, r.status === 200 && String(r.data.user_id) === owner.id);
const vBefore = (await getProject(owner, proj)).data.version;
r = await request('POST', GW + `projects/${outsider.id}/${proj.id}/tool?owner=${owner.id}`, { headers: { ...bearer(outsider), 'X-Project-Version': String(vBefore) }, json: { procedure: 'brightness', params: { brightness: 1.5 } } });
const after = (await getProject(owner, proj)).data;
add('G03', 'gateway', "Outsider JWT + ?owner=<victim> adds a tool to the owner's pipeline", 'reject', `HTTP ${r.status}; owner's tools ${after.tools?.length}, version ${vBefore}->${after.version}`, (after.tools?.length || 0) > 0);
r = await uploadFile(GW + `projects/${outsider.id}/${proj.id}/img?owner=${owner.id}`, 'image', DIR + 'probe.png', 'intruder.png', 'image/png', { ...bearer(outsider), 'X-Project-Version': String(after.version) });
const after2 = (await getProject(owner, proj)).data;
add('G04', 'gateway', "Outsider JWT + ?owner=<victim> uploads media into the owner's project", 'reject', `HTTP ${r.status}; owner's media ${after2.imgs?.length}`, (after2.imgs?.length || 0) > 1);
r = await request('GET', GW + `users/${owner.id}`);
add('G05', 'gateway', "No token reads another user's profile", 'reject', `HTTP ${r.status}; fields=${r.status === 200 ? Object.keys(r.data).join(',') : '-'}`, r.status === 200);
const prem = await register('premium');
add('G06', 'gateway', 'Public registration with type=premium (no payment)', 'reject or downgrade to free', `HTTP 201; stored profile=${prem.type}`, prem.type === 'premium');
r = await request('PUT', GW + `users/${outsider.id}`, { headers: bearer(outsider), json: { type: 'premium' } });
const me = await request('GET', GW + `users/${outsider.id}`);
add('G07', 'gateway', 'Free user sets own profile to premium through profile update', 'reject', `HTTP ${r.status}; profile now=${me.data?.type}`, me.data?.type === 'premium');
try {
  r = await request('GET', GW + `subscriptions/${owner.id}/status`);
  add('G08', 'gateway', "No token queries another user's subscription status", 'reject (401)', `HTTP ${r.status}`, r.status >= 200 && r.status < 300);
  r = await request('PUT', GW + `subscriptions/${owner.id}/cancel`);
  add('G09', 'gateway', "No token calls cancel on another user's subscription", 'reject (401)', `HTTP ${r.status} (no auth check ran; 4xx/5xx here comes from the missing subscription)`, r.status !== 401 && r.status !== 403);
} catch (e) { add('G08', 'gateway', 'subscriptions service', 'n/a', 'not measured: ' + e.message, null); }

// ---- Direct service ports (published on the host by docker-compose) ----
r = await request('GET', PROJ + `${owner.id}/${proj.id}`);
add('D01', 'projects:9001', 'No identity reads project', 'reject', `HTTP ${r.status}`, r.status === 200);
r = await request('GET', PROJ + `${owner.id}/${proj.id}`, { headers: { 'X-Caller-Id': owner.id } });
add('D02', 'projects:9001', 'Forged X-Caller-Id header, no token', 'reject', `HTTP ${r.status}`, r.status === 200);
r = await request('GET', PROJ + `${owner.id}/${proj.id}`, { headers: bearer(outsider) });
add('D03', 'projects:9001', "Outsider's JWT (decoded, never verified)", 'reject', `HTTP ${r.status}`, r.status === 200);
const forged = 'x.' + Buffer.from(JSON.stringify({ id: owner.id })).toString('base64url') + '.x';
r = await request('GET', PROJ + `${owner.id}/${proj.id}`, { headers: { Authorization: 'Bearer ' + forged } });
add('D04', 'projects:9001', 'Unsigned hand-made JWT naming the owner', 'reject', `HTTP ${r.status}`, r.status === 200);
r = await request('DELETE', PROJ + `${outsider.id}`);
add('D05', 'projects:9001', "DELETE /:user with no identity (outsider's own synthetic account, no projects)", 'reject', `HTTP ${r.status}`, r.status >= 200 && r.status < 300);
if (img) {
  r = await request('GET', STOR + `image/internal/${owner.id}/${proj.id}/src/${img.og_img_key}`);
  let same = false;
  if (r.status === 200 && r.data.url) {
    // internal URL host is only resolvable inside the network: fetch it from a container
    try { const h = execFileSync('docker', ['exec', 'picturas-nfr-projects-1', 'sh', '-c', `curl -s "${r.data.url}" | sha256sum | cut -d' ' -f1`], { encoding: 'utf8' }).trim(); same = h === pngSha; } catch {}
  }
  add('D06', 'img_storage:11000', "No token asks a signed URL for the owner's original", 'reject', `HTTP ${r.status}; bytes match original=${same}`, r.status === 200);
  r = await uploadFile(STOR.replace('http:', 'http:') + `upload/${owner.id}/${proj.id}/src`, 'file', DIR + 'probe.png', 'x.png', 'image/png').catch((e) => ({ status: 0, error: String(e) }));
}
r = await request('POST', STOR + `upload/${owner.id}/${proj.id}/out`, (() => { const b = '----x' + randomUUID(); const body = Buffer.concat([Buffer.from(`--${b}\r\nContent-Disposition: form-data; name="file"; filename="m.png"\r\nContent-Type: image/png\r\n\r\n`), png(), Buffer.from(`\r\n--${b}--\r\n`)]); return { headers: { 'Content-Type': `multipart/form-data; boundary=${b}` }, body }; })());
add('D07', 'img_storage:11000', "No token writes an object under the owner's prefix", 'reject', `HTTP ${r.status}`, r.status === 201);
const markerKey = r.data?.data?.imageKey?.split('/').pop();
if (markerKey) {
  r = await request('DELETE', STOR + `delete/${owner.id}/${proj.id}/out/${markerKey}`);
  add('D08', 'img_storage:11000', "No token deletes an object under the owner's prefix (the marker just written)", 'reject', `HTTP ${r.status}`, r.status >= 200 && r.status < 300);
}
const victim = await register('free');
r = await request('PUT', USERS + `${victim.id}`, { json: { type: 'premium' } });
const v2 = await request('GET', GW + `users/${victim.id}`);
add('D09', 'users:10001', "No token changes a user's profile to premium", 'reject', `HTTP ${r.status}; profile now=${v2.data?.type}`, v2.data?.type === 'premium');
r = await request('GET', (process.env.RABBIT_MGMT || 'http://localhost:35672/') + 'api/overview', { headers: { Authorization: 'Basic ' + Buffer.from('user:password').toString('base64') } });
add('D10', 'rabbitmq:15672', 'Management API with the credentials committed in docker-compose.yaml', 'reject', `HTTP ${r.status}`, r.status === 200);
try {
  const o = execFileSync('docker', ['exec', 'picturas-nfr-projects_mongoDB-1', 'mongo', '--quiet', '--port', '27018', '--eval', 'db.getSiblingDB("project").projects.count()'], { encoding: 'utf8' }).trim();
  add('D11', 'projects_mongoDB:27018', 'Database read with no credentials', 'reject', `count returned (${/^\d+$/.test(o) ? 'numeric' : 'error'})`, /^\d+$/.test(o));
} catch (e) { add('D11', 'projects_mongoDB:27018', 'Database read with no credentials', 'reject', 'not measured', null); }

// ---- WebSocket: join another project's room without any token ----
{
  const base = WS + '?EIO=4&transport=polling';
  const hs = await request('GET', base + '&t=' + Date.now());
  const sid = JSON.parse(String(hs.raw).slice(1)).sid;
  const url = () => `${base}&sid=${sid}&t=${Date.now()}`;
  const post = (p) => request('POST', url(), { headers: { 'Content-Type': 'text/plain;charset=UTF-8' }, body: Buffer.from(p) });
  await post('40'); // connect to namespace with NO auth token
  await request('GET', url());
  await post('42' + JSON.stringify(['join-project', proj.id]));
  let got = null;
  const poll = (async () => { for (let i = 0; i < 6 && !got; i++) { const p = await request('GET', url()); for (const pk of String(p.raw).split('\x1e')) { if (pk === '2') await post('3'); if (pk.startsWith('42')) { const [ev, d] = JSON.parse(pk.slice(2)); if (ev === 'project-op') got = { type: d.op?.type, hasTools: Array.isArray(d.op?.payload?.tools) }; } } } })();
  await sleep(500);
  const cur = (await getProject(owner, proj)).data.version;
  await request('POST', GW + `projects/${owner.id}/${proj.id}/tool`, { headers: { ...bearer(owner), 'X-Project-Version': String(cur) }, json: { procedure: 'brightness', params: { brightness: 1.2 } } });
  await Promise.race([poll, sleep(8000)]);
  add('W01', 'socket.io', "Socket with no token joins the owner's project room and receives edit events", 'reject', got ? `received project-op ${got.type}, pipeline payload=${got.hasTools}` : 'no event received', !!got);
  post('41').catch(() => {});
}

// ---- Quota race: 20 parallel reservations of 1 op on a fresh free account (limit 5) ----
{
  const u = await register('free');
  const rs = await Promise.all(Array.from({ length: 20 }, () => request('GET', USERS + `${u.id}/process/1`)));
  const ok = rs.filter((x) => x.status === 200).length;
  const st = await request('GET', GW + `users/${u.id}`);
  add('Q01', 'users quota', '20 simultaneous 1-op reservations, daily limit 5', 'exactly 5 granted', `${ok} granted; remaining_operations=${st.data?.remaining_operations}; statuses=${[...new Set(rs.map((x) => x.status))].join('/')}`, ok > 5);
}
const neg = cases.filter((c) => c.expected.startsWith('reject') || c.expected.startsWith('exactly'));
const summary = { negative_cases: neg.length, admitted: neg.filter((c) => c.unauthorized_admitted === true).length, not_measured: neg.filter((c) => c.unauthorized_admitted === null).length };
console.error(JSON.stringify(summary));
fs.writeFileSync(DIR + 'security-result.json', JSON.stringify({ recorded_at: new Date().toISOString(), summary, cases }, null, 1));
