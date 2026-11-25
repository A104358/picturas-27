// Processing artifacts have a predeclared run namespace. Upload ingestion is separate.
const express=require('express'),multer=require('multer'),crypto=require('node:crypto'),path=require('node:path');
const {BUCKET,objectKey,ensureBucket}=require('../services/storage');
const s3=require('../services/s3Client');
const router=express.Router();
router.post('/:userId/:projectId/:runId/:artifactId',multer({storage:multer.memoryStorage(),limits:{files:1}}).single('file'),async(req,res)=>{
  const {userId,projectId,runId,artifactId}=req.params;
  const ext=path.extname(req.file?.originalname||'').toLowerCase();
  if (![userId,projectId].every(v=>/^[a-f0-9]{24}$/.test(v)) || !/^[a-f0-9-]{36}$/.test(runId) ||
      !/^[a-f0-9-]{24,80}$/.test(artifactId) || !/^\.[a-z0-9]{1,10}$/.test(ext) || !req.file) return res.status(400).json({error:'Invalid processing artifact'});
  const sha256=crypto.createHash('sha256').update(req.file.buffer).digest('hex');
  if (sha256!==req.get('x-artifact-sha256')) return res.status(400).json({error:'Artifact checksum mismatch'});
  const name=`run-${runId}-${artifactId}${ext}`;
  try {
    await ensureBucket();
    await s3.putObject({Bucket:BUCKET,Key:objectKey(userId,projectId,'out',name),Body:req.file.buffer,
      ContentType:req.file.mimetype,Metadata:{'processing-run':runId,'sha256':sha256}}).promise();
    return res.status(201).json({data:{imageKey:`${projectId}/out/${name}`}});
  } catch (_) { return res.status(503).json({error:'Processing storage unavailable'}); }
});
module.exports=router;
