// Run via stdin in the isolated projects container. Never print credentials,
// Axios error objects, signed URLs, registration bodies or full application logs.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createHash, randomUUID } = require('node:crypto');
const { execFileSync } = require('node:child_process');
const axios = require('axios');
const FormData = require('form-data');
const sharp = require('sharp');
const amqp = require('amqplib');
const agent = new (require('node:https').Agent)({ rejectUnauthorized: false });
const http = axios.create({ httpsAgent: agent, timeout: 30000, validateStatus: () => true, maxBodyLength: Infinity, maxContentLength: Infinity });
const base = 'https://nginx/api-gateway/';
const work = fs.mkdtempSync(path.join(os.tmpdir(), 'picturas-live-quality-'));
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const sha = data => createHash('sha256').update(data).digest('hex');
const report = { recorded_at: new Date().toISOString(), source_commit: process.env.SOURCE_COMMIT,
  load_generator: process.env.LOAD_GENERATOR || 'inside-projects-container; resource samples include client overhead',
  scope: 'Isolated 13-service image/video slice through nginx; three processing batches and a finite access matrix.',
  accounts: [], uploads: [], access: [], batches: [], outputs: [], amqp: [], phases: [], failures: [],
  limits: ['Pilot sample sizes; no p95 or approved acceptance targets.', 'No real Whisper, worker scaling, fault injection or participant study.',
    'Socket.IO polling client exercises the gateway protocol, not a rendered browser.', 'Upload sizes are controlled with an MP4 free box; not representative content entropy.'] };
let connection, channel;
const sockets = [];

function expect(response, statuses, label) {
  if (!statuses.includes(response.status)) throw new Error(`${label}: HTTP ${response.status}`);
  return response;
}
async function call(account, method, route, data, headers = {}) {
  return http.request({ method, url: base+route, data, headers: { ...(account ? {Authorization: `Bearer ${account.jwt}`} : {}), ...headers } });
}
async function register(label) {
  const response = expect(await call(null, 'post', 'users/', { name: `Quality exploration ${label}`, email: `quality-${randomUUID()}@example.invalid`, password: randomUUID(), type: 'free' }), [201], 'register');
  const account = { id: response.data.user._id, jwt: response.data.jwt };
  report.accounts.push({ label, id: account.id, profile: 'free' });
  return account;
}
async function project(account, label) {
  const response = expect(await call(account, 'post', `projects/${account.id}`, { name: `Quality exploration ${label}` }), [201], 'create project');
  return { id: response.data._id, version: 0, account, route: `projects/${account.id}/${response.data._id}` };
}
async function pcall(p, method, suffix = '', data, extra = {}) {
  const response = await call(p.account, method, p.route+suffix, data, {'X-Project-Version':String(p.version), ...extra});
  if (response.headers['x-project-version'] !== undefined) p.version = Number(response.headers['x-project-version']);
  return response;
}
async function upload(p, kind, filename, diskPath, contentType) {
  const data = new FormData();
  data.append(kind === 'video' ? 'video' : 'image', fs.createReadStream(diskPath), { filename, contentType });
  return pcall(p, 'post', kind === 'video' ? '/video' : '/img', data, data.getHeaders());
}
async function phase(label, callback) {
  const record = { label, started_at_ms: Date.now() };
  report.phases.push(record);
  console.error(`[probe] ${label}`);
  try { await callback(); record.status = 'completed'; }
  catch (error) { record.status = 'failed'; record.error = error.message; report.failures.push({phase:label, message:error.message}); }
  record.ended_at_ms = Date.now();
}

class ProgressClient {
  constructor(account, label) { this.account=account; this.label=label; this.events=[]; this.closed=false; }
  url() { return `https://nginx/socket.io/?EIO=4&transport=polling&sid=${encodeURIComponent(this.sid)}&t=${Date.now()}`; }
  async post(packet) { expect(await http.post(this.url(), packet, { headers:{'Content-Type':'text/plain;charset=UTF-8'} }), [200], 'Socket.IO POST'); }
  async start() {
    const handshake = expect(await http.get(`https://nginx/socket.io/?EIO=4&transport=polling&t=${Date.now()}`), [200], 'Engine.IO handshake');
    this.sid=JSON.parse(String(handshake.data).slice(1)).sid;
    await this.post('40'+JSON.stringify({token:this.account.jwt}));
    this.startedAt=Date.now();
    this.loop=this.poll();
    await pause(150);
    return this;
  }
  async poll() {
    while (!this.closed) {
      try {
        const response=await http.get(this.url(), {timeout:30000});
        if (response.status!==200) { this.error=`HTTP ${response.status}`; break; }
        for (const packet of String(response.data).split('\x1e')) {
          if (packet==='2') await this.post('3');
          if (packet.startsWith('42')) {
            const [event,data]=JSON.parse(packet.slice(2));
            if (['video-progress','process-update','process-error','preview-error'].includes(event)) {
              this.events.push({unix_ms:Date.now(), event, ...(event==='video-progress' ? {project_id:data.projectId,media_id:data.imgId,percent:data.percent,preview:data.preview} : {})});
            }
          }
        }
      } catch (error) { if (!this.closed) this.error=error.code || error.message; break; }
    }
  }
  async close() { this.closed=true; if(this.sid) { try { await this.post('41'); await this.post('1'); } catch {} } }
}

async function main() {
  const movie=path.join(work,'sample.mp4');
  execFileSync('ffmpeg',['-y','-v','error','-f','lavfi','-i','testsrc2=size=1280x720:rate=30','-f','lavfi','-i','sine=frequency=440:sample_rate=44100','-t','10','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',movie]);
  const picture=path.join(work,'sample.png');
  await sharp({create:{width:160,height:120,channels:3,background:'#8090a0'}}).png().toFile(picture);
  report.input={bytes:fs.statSync(movie).size,sha256:sha(fs.readFileSync(movie)),seconds:10,width:1280,height:720,fps:30,audio:'AAC'};
  connection=await amqp.connect({hostname:process.env.RABBITMQ_HOST,port:Number(process.env.RABBITMQ_PORT),username:process.env.RABBITMQ_USER,password:process.env.RABBITMQ_PASS});
  channel=await connection.createChannel();
  const tap=await channel.assertQueue('',{exclusive:true,autoDelete:true});
  for(const key of ['video_queue','project_queue']) await channel.bindQueue(tap.queue,'picturas',key);
  await channel.consume(tap.queue,msg=>{
    if(!msg) return;
    const data=JSON.parse(msg.content.toString());
    if(msg.fields.routingKey==='video_queue' || String(data.messageId).startsWith('video-')) report.amqp.push({
      unix_ms:Date.now(),routing_key:msg.fields.routingKey,message_id:data.messageId,correlation_id:data.correlationId,
      project_id:data.parameters?.progress?.projectId,media_id:data.parameters?.progress?.imgId,status:data.status,
      worker_processing_ms:data.metadata?.processingTime,worker_timestamp:data.timestamp,
    });
  },{noAck:true});
  const owner=await register('owner');
  const outsider=await register('outsider');
  const uploadProject=await project(owner,'upload-memory');
  report.upload_project={owner_id:owner.id,project_id:uploadProject.id};
  await phase('upload-warmup',async()=>expect(await upload(uploadProject,'video','warmup.mp4',movie,'video/mp4'),[204],'warmup upload'));
  for(const sizeMiB of [10,50]) {
    const padded=path.join(work,`padded-${sizeMiB}.mp4`);
    fs.copyFileSync(movie,padded);
    const extra=sizeMiB*1024*1024-fs.statSync(padded).size;
    const header=Buffer.alloc(8);header.writeUInt32BE(extra);header.write('free',4,'ascii');fs.appendFileSync(padded,header);
    const zeros=Buffer.alloc(1024*1024);let remaining=extra-8;
    while(remaining>0) {const count=Math.min(remaining,zeros.length);fs.appendFileSync(padded,zeros.subarray(0,count));remaining-=count;}
    await pause(1000);
    await phase(`upload-${sizeMiB}MiB`,async()=>{
      const started=Date.now();const response=await upload(uploadProject,'video',`padded-${sizeMiB}.mp4`,padded,'video/mp4');const ended=Date.now();
      report.uploads.push({size_mib:sizeMiB,bytes:fs.statSync(padded).size,sha256:sha(fs.readFileSync(padded)),started_at_ms:started,ended_at_ms:ended,elapsed_ms:ended-started,status:response.status});
      expect(response,[204],'padded upload');
    });
  }
  await phase('access-matrix',async()=>{
    const route=uploadProject.route;
    const cases=[['gateway-owner',base+route,{Authorization:`Bearer ${owner.jwt}`},true],
      ['gateway-no-token',base+route,{},false],['gateway-invalid-token',base+route,{Authorization:'Bearer invalid-exploration-token'},false],
      ['gateway-outsider-token',base+route,{Authorization:`Bearer ${outsider.jwt}`},false],
      ['direct-project-no-token',`https://projects:9001/${owner.id}/${uploadProject.id}`,{},false],
      ['direct-project-outsider-token',`https://projects:9001/${owner.id}/${uploadProject.id}`,{Authorization:`Bearer ${outsider.jwt}`},false]];
    for(const [label,url,headers,shouldAllow] of cases) {
      const response=await http.get(url,{headers});
      report.access.push({case:label,operation:'read-project',expected_allowed:shouldAllow,status:response.status,protected_data_returned:response.data?._id===uploadProject.id});
    }
    const full=expect(await pcall(uploadProject,'get'),[200],'owner project').data;
    const key=decodeURIComponent(path.posix.basename(new URL(full.imgs[0].url).pathname));
    const signed=await http.get(`http://img_storage:11000/image/internal/${owner.id}/${uploadProject.id}/src/${encodeURIComponent(key)}`);
    let contentRead=false;
    if(signed.status===200 && signed.data.url) {
      const content=await http.get(signed.data.url,{responseType:'arraybuffer'});
      contentRead=content.status===200 && sha(content.data)===report.input.sha256;
    }
    report.access.push({case:'direct-storage-no-token',operation:'read-object',expected_allowed:false,status:signed.status,protected_data_returned:contentRead});
    const marker=Buffer.from('PictuRAS synthetic authorization probe');const form=new FormData();
    form.append('file',marker,{filename:'authorization-probe.txt',contentType:'text/plain'});
    const write=await http.post(`http://img_storage:11000/upload/${owner.id}/${uploadProject.id}/src`,form,{headers:form.getHeaders()});
    report.access.push({case:'direct-storage-no-token-write',operation:'write-owner-prefix',expected_allowed:false,status:write.status,write_accepted:write.status===201});
  });
  for(let repetition=1;repetition<=Number(process.env.BATCH_REPETITIONS ?? 3);repetition++) await phase(`batch-${repetition}`,async()=>{
    const account=await register(`batch-${repetition}`);const p=await project(account,`batch-${repetition}`);
    for(let i=1;i<=3;i++) expect(await upload(p,'video',`video-${i}.mp4`,movie,'video/mp4'),[204],'batch upload');
    expect(await pcall(p,'post','/tool',{procedure:'brightness',params:{brightness:0.6}}),[201],'add brightness');
    const socket=await new ProgressClient(account,`batch-${repetition}`).start();sockets.push(socket);
    const batch={repetition,project_id:p.id,account_id:account.id,started_at_ms:Date.now(),count:3};report.batches.push(batch);
    const submitted=await pcall(p,'post','/process',{});batch.accepted_at_ms=Date.now();batch.dispatch_status=submitted.status;
    expect(submitted,[201],'dispatch');
    const deadline=Date.now()+120000;let outputs=[];
    while(Date.now()<deadline) {
      const response=expect(await pcall(p,'get','/process/url'),[200],'poll committed outputs');
      outputs=response.data.imgs||[];
      if(outputs.length===3) break;
      await pause(100);
    }
    batch.observed_commit_at_ms=Date.now();batch.output_count=outputs.length;batch.completed=outputs.length===3;
    batch.elapsed_ms=batch.observed_commit_at_ms-batch.started_at_ms;
    batch.poll_interval_ms=100;
    await pause(150);await socket.close();batch.socket_events=socket.events;batch.socket_error=socket.error||null;
    batch.remaining_operations=expect(await call(account,'get',`users/${account.id}`),[200],'remaining quota').data.remaining_operations;
    if(!batch.completed) throw new Error('No complete three-video result set within 120 s');
    const first=outputs[0];const fetched=await http.get(first.url.replace('https://localhost:8080','https://nginx'),{responseType:'arraybuffer'});
    expect(fetched,[200],'download result');const resultPath=path.join(work,`batch-${repetition}-result.mp4`);fs.writeFileSync(resultPath,fetched.data);
    const metadata=JSON.parse(execFileSync('ffprobe',['-v','error','-show_streams','-show_format','-of','json',resultPath]));
    report.outputs.push({batch:repetition,bytes:fetched.data.length,sha256:sha(fetched.data),video_codec:metadata.streams.find(s=>s.codec_type==='video')?.codec_name,audio_codec:metadata.streams.find(s=>s.codec_type==='audio')?.codec_name,duration_s:Number(metadata.format.duration)});
    // A new Socket.IO connection receives no historical events without new work.
    const fresh=await new ProgressClient(account,`after-batch-${repetition}`).start();sockets.push(fresh);await pause(600);await fresh.close();
    batch.reconnect_observation_ms=Date.now()-fresh.startedAt;batch.replayed_events_after_completion=fresh.events.length;
  });
}

main().catch(error=>{report.failures.push({phase:'fatal',message:error.message});process.exitCode=1;}).finally(async()=>{
  for(const socket of sockets) await socket.close();
  if(channel) await channel.close().catch(()=>{});
  if(connection) await connection.close().catch(()=>{});
  report.finished_at=new Date().toISOString();
  fs.rmSync(work,{recursive:true,force:true});
  console.log(JSON.stringify(report,null,2));
});
