// Run from the repository root with the existing projects container:
// docker exec -i picturas-projects-1 node < docs/exercises/06-architectural-patterns/evidence/preparacao.cjs
// Creates a dedicated free account and mixed project; keeps them for inspection.
// Generated media stay in the container's temporary directory and object storage.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { randomUUID } = require('node:crypto');
const { execFileSync } = require('node:child_process');
const axios = require('axios');
const FormData = require('form-data');
const sharp = require('sharp');
const httpsAgent = new (require('node:https').Agent)({ rejectUnauthorized: false });
const http = axios.create({ baseURL: 'https://nginx/api-gateway/', httpsAgent, timeout: 30000 });
const work = fs.mkdtempSync(path.join(os.tmpdir(), 'picturas-ex6-'));
let token, root, version = 0;
async function call(method, url, data, headers = {}) {
  const response = await http.request({ method, url, data, headers: {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    'X-Project-Version': String(version), ...headers,
  } });
  if (response.headers['x-project-version'] !== undefined) version = Number(response.headers['x-project-version']);
  return response.data;
}
async function upload(kind, filename, contentType) {
  const form = new FormData();
  form.append(kind, fs.createReadStream(path.join(work, filename)), { filename, contentType });
  await call('post', `${root}/${kind === 'image' ? 'img' : 'video'}`, form, form.getHeaders());
}
async function results(count) {
  const deadline = Date.now() + 60000;
  while (Date.now() < deadline) {
    const data = await call('get', `${root}/process/url`);
    if (data.imgs.length === count) return data.imgs;
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  throw new Error(`Expected ${count} committed outputs within 60 s`);
}
async function main() {
  console.log('Date:', new Date().toISOString());
  console.log('Scope: API smoke check through nginx; no browser or performance baseline.');
  execFileSync('ffmpeg', ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=160x120:rate=10',
    '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=44100', '-t', '4',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', path.join(work, 'exercise6.mp4')]);
  await sharp({ create: { width: 160, height: 120, channels: 3, background: '#8090a0' } })
    .png().toFile(path.join(work, 'exercise6.png'));
  const account = await call('post', 'users/', { name: 'Exercise 6 PL2-G4',
    email: `exercise6-${randomUUID()}@example.invalid`, password: randomUUID(), type: 'free' });
  token = account.jwt;
  const userId = account.user._id;
  const project = await call('post', `projects/${userId}`, { name: 'Exercise 6 PL2-G4 mixed media' });
  root = `projects/${userId}/${project._id}`;
  console.log('Dedicated account:', userId, 'project:', project._id);
  await upload('image', 'exercise6.png', 'image/png');
  await upload('video', 'exercise6.mp4', 'video/mp4');
  const mixed = await call('get', root);
  assert.deepEqual(mixed.imgs.map(item => item.media_type).sort(), ['image', 'video']);
  console.log('Upload: 1 PNG + 1 MP4, 4 s, 160x120, 10 fps, AAC audio.');
  await call('post', `${root}/tool`, { procedure: 'brightness', params: { brightness: 0.6 } });
  await call('post', `${root}/process`, {});
  const edited = await results(2);
  assert.deepEqual(edited.map(item => item.type).sort(), ['image', 'video']);
  const movie = edited.find(item => item.type === 'video');
  const response = await http.get(movie.url.replace('https://localhost:8080', 'https://nginx'), { responseType: 'arraybuffer' });
  const output = path.join(work, 'result.mp4'); fs.writeFileSync(output, response.data);
  const info = JSON.parse(execFileSync('ffprobe', ['-v', 'error', '-show_streams', '-show_format', '-of', 'json', output]));
  assert(info.streams.some(stream => stream.codec_name === 'h264'));
  assert(info.streams.some(stream => stream.codec_name === 'aac'));
  console.log('Apply brightness: committed image + MP4/H.264/AAC; public download succeeded.');
  await call('post', `${root}/tool`, { procedure: 'extract_frames', params: { mode: 'count', count: 3, format: 'png' } });
  await call('post', `${root}/process`, {});
  const frames = await results(4);
  assert(frames.every(item => item.type === 'image'));
  assert.equal(new Set(frames.map(item => item.result_id)).size, 4);
  const videoId = mixed.imgs.find(item => item.media_type === 'video')._id;
  assert.equal(frames.filter(item => item.og_img_id === videoId).length, 3);
  console.log('Apply brightness + extract_frames: 1 edited image + 3 frames; unique result IDs and source video ID.');
  const zip = await http.get(`${root}/process`, { headers: { Authorization: `Bearer ${token}` }, responseType: 'arraybuffer' });
  const archive = await require('jszip').loadAsync(zip.data);
  assert.equal(Object.values(archive.files).filter(file => !file.dir).length, 4);
  console.log('ZIP: 4 files. Remaining daily operations:', (await call('get', `users/${userId}`)).remaining_operations);
  console.log('PASS. Test account/project retained; no credentials written to the evidence.');
}
main().catch(error => {
  // Never dump Axios errors: request headers contain the ephemeral JWT.
  console.error('FAIL:', error.message, 'HTTP status:', error.response?.status ?? 'none');
  process.exitCode = 1;
}).finally(() => fs.rmSync(work, { recursive: true, force: true }));
