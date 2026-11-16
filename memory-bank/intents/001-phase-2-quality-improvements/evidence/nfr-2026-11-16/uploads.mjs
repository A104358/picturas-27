// Upload acceptance time (REQ-VID-SUBMIT-008) and per-service peak RSS (QC-05),
// plus the unauthenticated-upload buffering case.
import { GW, register, bearer, createProject, getProject, uploadFile, resetPeak, readPeak, inspect, sleep, mib, request } from './lib.mjs';
import fs from 'node:fs';

const DIR = new URL('.', import.meta.url).pathname;
const SERVICES = ['api_gateway', 'projects', 'img_storage'];
const out = { recorded_at: new Date().toISOString(), runs: [], notes: [] };

async function measured(label, fn) {
  const before = {};
  for (const s of SERVICES) before[s] = { ...resetPeak(s), restarts: Number(inspect(s, '{{.RestartCount}}')) };
  await sleep(300);
  const res = await fn();
  await sleep(700);
  const mem = {};
  for (const s of SERVICES) {
    const p = readPeak(s, before[s].pid);
    const restarts = Number(inspect(s, '{{.RestartCount}}'));
    const oom = inspect(s, '{{.State.OOMKilled}}');
    mem[s] = p.alive
      ? { pre_rss_mib: mib(before[s].rss_kb), peak_rss_mib: mib(p.hwm_kb), delta_mib: +(mib(p.hwm_kb) - mib(before[s].rss_kb)).toFixed(1), post_rss_mib: mib(p.rss_kb) }
      : { pre_rss_mib: mib(before[s].rss_kb), process_died: true };
    mem[s].restarted = restarts > before[s].restarts; mem[s].oom_killed = oom;
  }
  const rec = { label, ...res, mem };
  out.runs.push(rec);
  console.error(JSON.stringify(rec));
  return rec;
}

const free = await register('free');
const premium = await register('premium'); // public registration accepts the profile field
out.notes.push(`registered profile via public API: requested premium, got ${premium.type}`);

const plan = [
  ['free', free, 10, 3], ['free', free, 100, 3], ['premium', premium, 10, 3], ['premium', premium, 100, 2], ['premium', premium, 500, 3],
];
// warm-up: one small upload per account
for (const [prof, acct, size, reps] of plan) {
  const proj = await createProject(acct, `upload-${size}`);
  for (let i = 0; i < reps; i++) {
    await getProject(acct, proj);
    const r = await measured(`${prof}-${size}MiB-#${i + 1}`, () => uploadFile(GW + `projects/${acct.id}/${proj.id}/video`, 'video', `${DIR}pad_${size}MiB.mp4`, `pad_${size}_${i}.mp4`, 'video/mp4', { ...bearer(acct), 'X-Project-Version': String(proj.version) }));
    if (r.status !== 204) await sleep(8000); // let services recover after a failure
    await sleep(1500);
  }
}
// Unauthenticated bodies: the gateway parses the multipart before checking the JWT.
for (const size of [100, 500]) {
  await measured(`no-token-${size}MiB`, () => uploadFile(GW + `projects/000000000000000000000000/000000000000000000000000/video`, 'video', `${DIR}pad_${size}MiB.mp4`, 'x.mp4', 'video/mp4', {}));
  await sleep(5000);
}
// Oversized for the free profile: rejected only after full buffering in two services.
{
  const proj = await createProject(free, 'too-big');
  await getProject(free, proj);
  await measured('free-500MiB-over-limit', () => uploadFile(GW + `projects/${free.id}/${proj.id}/video`, 'video', `${DIR}pad_500MiB.mp4`, 'big.mp4', 'video/mp4', { ...bearer(free), 'X-Project-Version': String(proj.version) }));
}
fs.writeFileSync(`${DIR}uploads-result.json`, JSON.stringify(out, null, 1));
