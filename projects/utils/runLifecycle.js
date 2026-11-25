// Minimum execution evidence for OPS-C1 A; no automatic replay of a failed run.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {pipeline}=require('node:stream/promises');
const axios=require('axios'),FormData=require('form-data'),mime=require('mime-types');
const Run=require('../models/processingRun'),Artifact=require('../models/processingArtifact');
const Project=require('../controllers/project'),ProjectModel=require('../models/project');
const Process=require('../controllers/process'),ProcessModel=require('../models/process'),Result=require('../controllers/result');
const {getCallerId}=require('./caller');
const {imageTools,isVideoMedia,videoOps,videoPipeline,unsupportedVideoTools,validateFrameExtraction}=require('./video');
const {makeToolsFingerprint}=require('./cacheKey');
const {get_image_internal_url}=require('./imageStorage');
const {dispatchProcessBatch}=require('./processBatch');
const {send_msg_tool}=require('./project_msg');
const agent=require('../tls/pkiTls').clientAgent();
const s3Agent=new (require('node:https').Agent)({ca:fs.readFileSync('/run/secrets/pki/ca.crt'),servername:'seaweedfs',maxCachedSessions:0});
const root=path.resolve(__dirname,'../images/runs');
function fail(message,status=409){const e=new Error(message);e.status=status;throw e;}
function headers(run){return {'x-processing-run':run._id,'x-processing-project':String(run.project_id),
 'x-processing-owner':String(run.user_id),'x-processing-generation':String(run.token),
 'x-processing-images':String(run.cost.image),'x-processing-videos':String(run.cost.video)};}
const sourceFingerprint=project=>crypto.createHash('sha256').update(JSON.stringify(project.imgs.map(i=>[String(i._id),i.og_img_key]))).digest('hex');
async function hashFile(file){const h=crypto.createHash('sha256');for await(const chunk of fs.createReadStream(file))h.update(chunk);return h.digest('hex');}
async function rememberCommit(project){
 if(project.committedRun)await Run.updateOne({_id:project.committedRun.run_id},{$set:{commitProof:project.committedRun}});
}
function applyHandler({advancedToolNum}) {
 return async(req,res)=>{
  let run;
  try {
   const project=await Project.getOne(req.params.user,req.params.project);
   if(!project)fail('Project not found',404);
   if(project.processingRunId||project.reconciliationHold)fail('Finish or reconcile the current execution first');
   if(!project.tools.length||!project.imgs.length)fail('Select media and tools before processing',400);
   const invalid=validateFrameExtraction(project.tools);if(invalid)fail(invalid,400);
   const hasVideos=project.imgs.some(isVideoMedia);
   if(hasVideos&&unsupportedVideoTools(project).length)fail('Effects not available for video',400);
   if(!hasVideos&&!imageTools(project).length)fail('The selected effects require video',400);
   const {adv_ops}=advancedToolNum(project);const video=videoOps(project);
   if(!adv_ops&&!video&&project.committedRun&&project.committedRun.source_fingerprint===sourceFingerprint(project)&&
      makeToolsFingerprint(project.tools)===makeToolsFingerprint(project.committedTools||[]))return res.status(201).json({completed:true});
   await rememberCommit(project);
   const id=crypto.randomUUID(),token=(project.activeToken||0)+1;
   const runRoot=path.join(root,id),tools=project.tools.map(t=>t.toObject?t.toObject():t);
   const jobs=[];
   for(const img of project.imgs){
    if(!isVideoMedia(img)&&!imageTools(project).length)continue;
    jobs.push({img_id:String(img._id),msg_id:'request-'+crypto.randomUUID(),media_type:img.media_type||'image',
     input:path.join(runRoot,'src',path.basename(img.og_uri)),output:path.join(runRoot,'out',path.basename(img.new_uri))});
   }
   run=await Run.create({_id:id,user_id:project.user_id,project_id:project._id,runner_id:getCallerId(req),token,
    phase:'prepared',debit_state:'not_requested',cost:{image:adv_ops,video},tools,jobs,message_ids:jobs.map(j=>j.msg_id),
    previousCommit:{token:project.committedToken||0,proof:project.committedRun||null,tools:project.committedTools||[]},
    previousCharged:project.chargedAdvancedTools||0,sources:project.imgs.map(i=>({img_id:String(i._id),key:i.og_img_key,sha256:i.og_sha256||null}))});
   project.prevCommittedToken=project.committedToken||0;project.prevCommittedTools=project.committedTools||[];
   project.prevCommittedRun=project.committedRun||null;project.activeToken=token;project.processingRunId=id;
   project.pendingAdvancedOps=adv_ops+video;
   const updated=await Project.updateIfVersion(req.params.user,req.params.project,project,req.expectedVersion,true);
   if(!updated){await Run.updateOne({_id:id},{$set:{phase:'rejected'}});fail('Project version conflict');}
   res.set('X-Project-Version',String(updated.version));
   await Run.updateOne({_id:id},{$set:{phase:'admitting',debit_state:'requested'}});
   let receipt;
   try { receipt=(await axios.get(`https://users:10001/${run.runner_id}/process/${adv_ops+video}`,{httpsAgent:agent,headers:headers(run)})).data; }
   catch(error){
    if(error.response&&error.response.status>=400&&error.response.status<500){
     await Run.updateOne({_id:id},{$set:{phase:'rejected',debit_state:'rejected'}});
     await ProjectModel.updateOne({_id:project._id,processingRunId:id,activeToken:token},{$set:{processingRunId:null,pendingAdvancedOps:0}});
     fail('No more daily operations available',error.response.status);
    }
    await Run.updateOne({_id:id},{$set:{phase:'indeterminate',debit_state:'unknown'}});
    await ProjectModel.updateOne({_id:project._id,processingRunId:id},{$set:{reconciliationHold:true}});
    fail('Admission is uncertain; reconcile before retrying',503);
   }
   if(!receipt||receipt.run_id!==id)fail('Admission evidence unavailable',503);
   run.quotaReceipt=receipt;run.debit_state='confirmed';run.phase='running';await run.save();
   await fs.promises.mkdir(path.join(runRoot,'src'),{recursive:true});await fs.promises.mkdir(path.join(runRoot,'out'),{recursive:true});
   const pending=[];
   for(const job of jobs){
    const img=project.imgs.find(i=>String(i._id)===job.img_id);
    const url=(await get_image_internal_url(String(project.user_id),String(project._id),'src',img.og_img_key)).data.url;
    const response=await axios.get(url,{responseType:'stream',httpsAgent:s3Agent});
    await pipeline(response.data,fs.createWriteStream(job.input));
    const sha=await hashFile(job.input);
    if(img.og_sha256&&sha!==img.og_sha256)fail('Source integrity changed',503);
    const source=run.sources.find(s=>s.img_id===job.img_id);source.sha256=sha;
    const tool=isVideoMedia(img)?'video':imageTools(project)[0].procedure;
    const params=isVideoMedia(img)?{tools:videoPipeline(project,img._id),preview:false,
     progress:{user:String(run.runner_id),projectId:String(project._id),imgId:job.img_id}}:imageTools(project)[0].params;
    const process={user_id:run.user_id,runner_id:String(run.runner_id),project_id:run.project_id,img_id:job.img_id,
     msg_id:job.msg_id,cur_pos:0,og_img_uri:job.input,new_img_uri:job.output,cancelToken:project.cancelToken||0,token,run_id:id};
    pending.push({process,job,tool,params});
   }
   run.markModified('sources');await run.save();
   await dispatchProcessBatch(pending,{create:p=>Process.create(p),remove:p=>Process.delete(p.user_id,p.project_id,p._id),
    send:p=>send_msg_tool(p.job.msg_id,new Date().toISOString(),p.job.input,p.job.output,p.tool,p.params)});
   return res.sendStatus(201);
  }catch(error){
   if(run)try{
    if(!['rejected','indeterminate'].includes((await Run.findById(run._id).lean())?.phase))
     await Run.updateOne({_id:run._id,invalidated:false},{$set:{phase:'failed'}});
   }catch(_){ /* The prepared run is durable; admission remains blocked until inspection. */ }
   if(!res.headersSent)return res.status(error.status||503).jsonp(error.status?error.message:'Processing failed; cancel or reconcile the execution');
  }
 };
}
async function liveRun(process,project){
 if(!process.run_id)return null;
 const run=await Run.findById(process.run_id).lean();
 if(!run||run.invalidated||run.phase!=='running'||project.processingRunId!==run._id||project.activeToken!==run.token)return null;
 return run;
}
function containedOutput(file,run){
 const expected=path.join(root,run._id,'out'),directory=fs.realpathSync(expected);
 if(directory!==expected)fail('Execution directory is a symlink');
 const resolved=fs.realpathSync(path.resolve(__dirname,'..',file));
 if(!resolved.startsWith(directory+path.sep)||!fs.statSync(resolved).isFile())fail('Output is outside its execution');
 return resolved;
}
async function uploadArtifact(process,file,name,type,artifactId=String(process._id)){
 const run=await Run.findById(process.run_id).lean();if(!run||run.invalidated)fail('Execution invalidated');
 file=containedOutput(file,run);
 const sha256=await hashFile(file),size=fs.statSync(file).size,ext=path.extname(name).toLowerCase();
 const img_key=`run-${run._id}-${artifactId}${ext}`;
 const intent={run_id:run._id,artifact_id:artifactId,img_id:process.img_id,img_key,
  key:`users/${process.user_id}/projects/${process.project_id}/out/${img_key}`,sha256,size,type,file_name:name};
 await Artifact.create(intent); // Intention exists before the object can be written.
 const data=new FormData();data.append('file',fs.createReadStream(file),{filename:name,contentType:mime.lookup(name)||'application/octet-stream'});
 const response=await axios.post(`https://img_storage:11000/processing-output/${process.user_id}/${process.project_id}/${run._id}/${artifactId}`,data,
  {httpsAgent:agent,maxBodyLength:Infinity,maxContentLength:Infinity,headers:{...data.getHeaders(),'x-artifact-sha256':sha256}});
 if(response.data.data.imageKey.split('/').pop()!==img_key)fail('Unexpected artifact receipt');
 return intent;
}
async function storeResult(process,artifact){
 const row=await Result.create({type:artifact.type,file_name:artifact.file_name,img_key:artifact.img_key,img_id:process.img_id,
  project_id:process.project_id,user_id:process.user_id,token:process.token,run_id:process.run_id,sha256:artifact.sha256,size:artifact.size});
 await Artifact.updateOne({run_id:process.run_id,artifact_id:artifact.artifact_id},{$set:{result_id:row._id}});
 return row;
}
function manifest(rows,user,project){return rows.map(r=>({result_id:String(r._id),img_id:String(r.img_id),
 key:`users/${user}/projects/${project}/out/${r.img_key}`,img_key:r.img_key,sha256:r.sha256,size:r.size,type:r.type})).sort((a,b)=>a.result_id.localeCompare(b.result_id));}
async function commit(process,project){
 const run=await liveRun(process,project);if(!run)return null;
 const rows=await Result.getAllByToken(process.user_id,process.project_id,process.token);
 if(!rows.length||run.jobs.some(j=>!rows.some(r=>String(r.img_id)===j.img_id))||rows.some(r=>r.run_id!==run._id||!r.sha256))fail('Incomplete execution outputs');
 const outputs=manifest(rows,process.user_id,process.project_id);
 const proof={run_id:run._id,token:run.token,manifest_sha256:crypto.createHash('sha256').update(JSON.stringify(outputs)).digest('hex'),
  output_count:outputs.length,source_fingerprint:crypto.createHash('sha256').update(JSON.stringify(run.sources.map(s=>[s.img_id,s.key]))).digest('hex'),chargedAdvancedTools:
   run.tools.filter(t=>['cut_ai','upgrade_ai','bg_remove_ai','text_ai','obj_ai','people_ai','expand_ai'].includes(t.procedure)).length};
 const done=await Project.commitRunIfActive(process.user_id,process.project_id,process.token,run.tools,proof);
 if(done){await Run.updateOne({_id:run._id},{$set:{commitProof:proof}});await Run.updateOne({_id:run._id,invalidated:false},{$set:{phase:'committed'}});}
 return done;
}
async function trackMessage(runId,message){
 const updated=await Run.updateOne({_id:runId,invalidated:false,phase:'running'},{$addToSet:{message_ids:message}});
 if(!updated.matchedCount)fail('Execution invalidated');
}
async function cancel(req,res){
 try{
  const project=await Project.getOne(req.params.user,req.params.project);if(!project)fail('Project not found',404);
  if(project.reconciliationHold)fail('The uncertain execution requires reconciliation before cancellation');
  const token=project.activeToken||0;
  const run=await Run.findOne({project_id:project._id,token}).lean();
  if(!run&&project.pendingAdvancedOps)fail('Original debit evidence required before cancellation');
  await rememberCommit(project);
  project.activeToken=token+1;project.processingRunId=null;project.pendingAdvancedOps=0;
  if(run&&project.committedToken===token){
   project.committedToken=run.previousCommit.token;project.resultsToken=run.previousCommit.token;
   project.committedRun=run.previousCommit.proof;project.committedTools=run.previousCommit.tools;project.tools=run.previousCommit.tools;
   project.chargedAdvancedTools=run.previousCharged;
  }
  project.reconciliationHold=Boolean(run);
  const done=await Project.updateIfVersion(req.params.user,req.params.project,project,req.expectedVersion,true);
  if(!done)fail('Project version conflict');res.set('X-Project-Version',String(done.version));
  if(run){
   await Run.updateOne({_id:run._id},{$set:{invalidated:true,phase:'cancel_pending'}});
   await ProcessModel.updateMany({run_id:run._id},{$set:{reconciled:true}});
   if(run.debit_state!=='not_requested'&&run.debit_state!=='rejected'){
    await axios.post(`https://users:10001/${run.runner_id}/process/refund/${run.cost.image+run.cost.video}`,{},
     {httpsAgent:agent,headers:headers(run)});
   }
   await Run.updateOne({_id:run._id},{$set:{phase:'cancelled'}});
   await ProjectModel.updateOne({_id:project._id,activeToken:token+1},{$set:{reconciliationHold:false}});
  }
  return res.sendStatus(204);
 }catch(error){return res.status(error.status||503).jsonp(error.status?error.message:'Cancellation needs reconciliation; do not repeat the refund');}
}
module.exports={applyHandler,liveRun,uploadArtifact,storeResult,commit,trackMessage,cancel,manifest};
