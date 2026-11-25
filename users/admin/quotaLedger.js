// Per-run evidence and quota effect share one atomic user-document update.
// This is not a general retry/replay mechanism for application mutations.
const Model = require('../models/user');
const dayKey = (date) => date.toISOString().slice(0, 10);
const dateFor = (day) => new Date(`${day}T00:00:00.000Z`);
function fail(code, status = 409) { const e = new Error(code); e.status = status; throw e; }
function contextFrom(req) {
  const run_id = req.get('x-processing-run');
  if (!run_id) return null;
  const c = { run_id, project_id: req.get('x-processing-project'), owner_id: req.get('x-processing-owner'),
    generation: Number(req.get('x-processing-generation')), image_cost: Number(req.get('x-processing-images')),
    video_cost: Number(req.get('x-processing-videos')), executor_id: req.params.user };
  if (!/^[a-f0-9-]{36}$/.test(c.run_id) || ![c.project_id, c.owner_id, c.executor_id].every(v => /^[a-f0-9]{24}$/.test(v)) ||
      ![c.generation,c.image_cost,c.video_cost].every(v => Number.isSafeInteger(v) && v >= 0)) fail('Invalid processing context',400);
  return c;
}
function binding(a,b) {
  return ['run_id','project_id','owner_id','executor_id','generation','image_cost','video_cost'].every(k => a[k]===b[k]);
}
async function mutate(id, change) {
  for (let attempt=0; attempt<8; attempt++) {
    const user=await Model.findById(id).select('+quotaLedger +quotaRevision +legacyQuotaRevision').lean();
    if (!user) fail('Account not found',404);
    const effect=change(user);
    if (!effect.update) return effect.result;
    const filter={_id:user._id,type:user.type,quotaRevision:user.quotaRevision===undefined?{$exists:false}:user.quotaRevision};
    const result=await Model.updateOne(filter,{$set:effect.update,$inc:{quotaRevision:1}});
    if (result.modifiedCount===1) return effect.result;
  }
  fail('Quota changed concurrently; inspect before retrying',503);
}
async function admit(id, amount, context, now=new Date()) {
  if (!Number.isSafeInteger(amount) || amount<0 || amount!==context.image_cost+context.video_cost) fail('Invalid processing cost',400);
  return mutate(id,user => {
    const ledger=user.quotaLedger||[];
    const existing=ledger.find(r=>r.run_id===context.run_id);
    if (existing) {
      if (!binding(existing,context) || existing.compensation) fail('Processing receipt conflicts');
      return {result:existing};
    }
    const day=dayKey(now); const operations=(user.operations||[]).map(o=>({...o}));
    const today=operations.find(o=>dayKey(o.day)===day); const used=today?.processed||0;
    if (!(user.type==='premium' || amount===0 || (user.type==='free' && used+amount<=Number(process.env.FREE_DAILY_OP||5)))) fail('No more daily operations available',403);
    const receipt={...context, day, profile:user.type, requested:amount,
      charged:user.type==='free'?amount:0, legacy_revision:user.legacyQuotaRevision||0, compensation:null};
    if (amount) {
      if (today) today.processed+=amount; else operations.push({day:dateFor(day),processed:amount});
    }
    return {update:{operations,quotaLedger:[...ledger,receipt]},result:receipt};
  });
}
async function refund(id, amount, context, identifier) {
  return mutate(id,user=>{
    const ledger=(user.quotaLedger||[]).map(r=>({...r}));
    const receipt=ledger.find(r=>r.run_id===context.run_id);
    if (!receipt || !binding(receipt,context) || receipt.requested!==amount) fail('Original debit evidence required');
    if (receipt.compensation) {
      const m=receipt.compensation;
      if (!m.id || m.amount!==receipt.charged || m.day!==receipt.day || !Number.isSafeInteger(m.before) ||
          !Number.isSafeInteger(m.after) || m.before<m.amount || m.after!==m.before-m.amount) fail('Compensation evidence conflicts');
      return {result:m};
    }
    if (receipt.charged && (user.legacyQuotaRevision||0)!==receipt.legacy_revision) fail('Untracked quota changes require reconciliation');
    const operations=(user.operations||[]).map(o=>({...o}));
    const original=operations.find(o=>dayKey(o.day)===receipt.day);
    if (receipt.charged && (!original || original.processed<receipt.charged)) fail('Original balance requires reconciliation');
    const before=original?.processed||0;
    if (original) original.processed-=receipt.charged;
    const marker={id:identifier,amount:receipt.charged,day:receipt.day,before,after:before-receipt.charged};
    receipt.compensation=marker;
    return {update:{operations,quotaLedger:ledger},result:marker};
  });
}
async function legacy(id,amount,kind,now=new Date()) {
  if (!Number.isSafeInteger(amount) || amount<0) fail('Invalid operations number',400);
  return mutate(id,user=>{
    const day=dayKey(now); const operations=(user.operations||[]).map(o=>({...o}));
    const today=operations.find(o=>dayKey(o.day)===day);const used=today?.processed||0;
    if (kind==='refund' && user.type==='premium') return {result:true};
    if (kind!=='refund' && !(user.type==='premium' || amount===0 || (user.type==='free' && used+amount<=Number(process.env.FREE_DAILY_OP||5)))) fail('No more daily operations available',701);
    const after=kind==='refund'?Math.max(0,used-amount):used+amount;
    if (today) today.processed=after; else if (kind!=='refund') operations.push({day:dateFor(day),processed:after});
    return {update:{operations,legacyQuotaRevision:(user.legacyQuotaRevision||0)+(after!==used?1:0)},result:true};
  });
}
module.exports={admit,refund,legacy,contextFrom};
