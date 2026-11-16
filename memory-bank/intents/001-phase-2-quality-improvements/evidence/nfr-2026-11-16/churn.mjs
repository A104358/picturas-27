import { GW, register, bearer, createProject, getProject, uploadFile, request, sleep } from './lib.mjs';
const DIR = new URL('.', import.meta.url).pathname;
const auth = { Authorization: 'Basic ' + Buffer.from('user:password').toString('base64') };
const created = async () => { await sleep(6000); return (await request('GET', 'http://localhost:35672/api/overview', { headers: auth })).data.churn_rates.connection_created; };
const a = await register('premium'); const p = await createProject(a, 'churn');
for (let i = 0; i < 5; i++) { await getProject(a, p); await uploadFile(GW + `projects/${a.id}/${p.id}/img`, 'image', DIR + 'probe.png', `i${i}.png`, 'image/png', { ...bearer(a), 'X-Project-Version': String(p.version) }); }
for (const b of [1.1, 1.2, 1.3]) { await getProject(a, p); await request('POST', GW + `projects/${a.id}/${p.id}/tool`, { headers: { ...bearer(a), 'X-Project-Version': String(p.version) }, json: { procedure: 'brightness', params: { brightness: b } } }); }
const c0 = await created(); await getProject(a, p); const t0 = Date.now();
const r = await request('POST', GW + `projects/${a.id}/${p.id}/process`, { headers: { ...bearer(a), 'X-Project-Version': String(p.version) }, json: {} });
await sleep(8000); const c1 = await created();
console.log(JSON.stringify({ apply: r.status, images: 5, tools: 3, tool_steps: 15, amqp_connections_opened_by_one_apply: c1 - c0 }));
