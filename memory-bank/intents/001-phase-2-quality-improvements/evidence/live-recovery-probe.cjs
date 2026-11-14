// Single defined worker interruption, synthetic data only. The host controller
// restarts the isolated worker after RECOVERY_READY; this script never logs JWTs.
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {randomUUID,createHash}=require('node:crypto');
const {execFileSync}=require('node:child_process');
const axios=require('axios'),FormData=require('form-data'),amqp=require('amqplib'),mongoose=require('mongoose');
const agent=new (require('node:https').Agent)({rejectUnauthorized:false});
const http=axios.create({baseURL:'https://nginx/api-gateway/',httpsAgent:agent,timeout:30000,maxBodyLength:Infinity,maxContentLength:Infinity});
const work=fs.mkdtempSync(path.join(os.tmpdir(),'picturas-recovery-'));
const report={recorded_at:new Date().toISOString(),scenario:'Abrupt kill after first >=2% progress, then restart the same isolated video worker.',progress:[],responses:[],requests:[],failures:[]};
let account,pid,version=0,channel,connection,db,signaled=false;
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function call(method,url,data,headers={}) {
  const response=await http.request({method,url,data,headers:{...(account?{Authorization:`Bearer ${account.jwt}`} :{}),'X-Project-Version':String(version),...headers}});
  if(response.headers['x-project-version']!==undefined) version=Number(response.headers['x-project-version']);
  return response;
}
async function main() {
  const source=path.join(work,'recovery.mp4');
  execFileSync('ffmpeg',['-y','-v','error','-f','lavfi','-i','testsrc2=size=1280x720:rate=30','-f','lavfi','-i','sine=frequency=440','-t','30','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',source]);
  report.input={duration_s:30,width:1280,height:720,sha256:createHash('sha256').update(fs.readFileSync(source)).digest('hex'),bytes:fs.statSync(source).size};
  const registered=await call('post','users/',{name:'Quality recovery pilot',email:`quality-recovery-${randomUUID()}@example.invalid`,password:randomUUID(),type:'free'});
  account={id:registered.data.user._id,jwt:registered.data.jwt};report.owner_id=account.id;
  const created=await call('post',`projects/${account.id}`,{name:'Quality isolated recovery pilot'});pid=created.data._id;report.project_id=pid;
  const route=`projects/${account.id}/${pid}`;
  const form=new FormData();form.append('video',fs.createReadStream(source),{filename:'recovery.mp4',contentType:'video/mp4'});
  await call('post',`${route}/video`,form,form.getHeaders());
  await call('post',`${route}/tool`,{procedure:'brightness',params:{brightness:0.6}});
  connection=await amqp.connect({hostname:process.env.RABBITMQ_HOST,port:Number(process.env.RABBITMQ_PORT),username:process.env.RABBITMQ_USER,password:process.env.RABBITMQ_PASS});
  channel=await connection.createChannel();const tap=await channel.assertQueue('',{exclusive:true,autoDelete:true});
  for(const key of ['video_queue','project_queue','ws_queue']) await channel.bindQueue(tap.queue,'picturas',key);
  await channel.consume(tap.queue,msg=>{
    if(!msg)return;const data=JSON.parse(msg.content.toString());
    if(data.parameters?.progress?.projectId===pid) report.requests.push({unix_ms:Date.now(),message_id:data.messageId});
    if(report.requests.some(r=>r.message_id===data.correlationId)) report.responses.push({unix_ms:Date.now(),status:data.status,correlation_id:data.correlationId,processing_ms:data.metadata?.processingTime});
    if(data.projectId===pid && String(data.messageId).startsWith('update-client-video-progress-')) {
      report.progress.push({unix_ms:Date.now(),percent:data.percent});
      if(!signaled && data.percent>=2 && data.percent<40) {signaled=true;report.interruption_ready_at_ms=Date.now();console.error('RECOVERY_READY');}
    }
  },{noAck:true});
  report.started_at_ms=Date.now();const accepted=await call('post',`${route}/process`,{});report.accepted_at_ms=Date.now();report.dispatch_status=accepted.status;
  const deadline=Date.now()+180000;let outputs=[];
  while(Date.now()<deadline) {
    const response=await call('get',`${route}/process/url`);outputs=response.data.imgs||[];
    if(outputs.length)break;
    await pause(200);
  }
  report.observed_completion_at_ms=Date.now();report.output_count=outputs.length;report.completed=outputs.length===1;
  report.remaining_operations=(await call('get',`users/${account.id}`)).data.remaining_operations;
  if(outputs.length===1) {
    const output=await axios.get(outputs[0].url.replace('https://localhost:8080','https://nginx'),{httpsAgent:agent,responseType:'arraybuffer'});
    const file=path.join(work,'result.mp4');fs.writeFileSync(file,output.data);
    const metadata=JSON.parse(execFileSync('ffprobe',['-v','error','-show_streams','-show_format','-of','json',file]));
    report.output={bytes:output.data.length,video_codec:metadata.streams.find(s=>s.codec_type==='video')?.codec_name,audio_codec:metadata.streams.find(s=>s.codec_type==='audio')?.codec_name,duration_s:Number(metadata.format.duration)};
    const sourceProject=(await call('get',route)).data;
    const storedSource=await axios.get(sourceProject.imgs[0].url.replace('https://localhost:8080','https://nginx'),{httpsAgent:agent,responseType:'arraybuffer'});
    report.source_object_unchanged=createHash('sha256').update(storedSource.data).digest('hex')===report.input.sha256;
  }
  db=await mongoose.createConnection('mongodb://projects_mongoDB:27018/project').asPromise();
  const filter={project_id:new mongoose.Types.ObjectId(pid)};
  const project=await db.collection('projects').findOne({_id:new mongoose.Types.ObjectId(pid)});
  report.persisted={result_count:await db.collection('results').countDocuments(filter),process_count:await db.collection('processes').countDocuments(filter),active_token:project.activeToken,committed_token:project.committedToken};
  report.input_unchanged=createHash('sha256').update(fs.readFileSync(source)).digest('hex')===report.input.sha256;
  report.limits='One video, one interruption point, no orchestrator/broker failure. A successful recovery is not a general reliability rate or proof of exactly-once execution.';
  if(!signaled || !report.completed)throw new Error('Recovery probe did not reach its expected checkpoints');
}
main().catch(error=>{report.failures.push({message:error.message,status:error.response?.status||null});process.exitCode=1;}).finally(async()=>{
  if(channel)await channel.close().catch(()=>{});if(connection)await connection.close().catch(()=>{});if(db)await db.close().catch(()=>{});
  fs.rmSync(work,{recursive:true,force:true});report.finished_at=new Date().toISOString();console.log(JSON.stringify(report,null,2));
});
