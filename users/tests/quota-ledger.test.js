const {test,beforeEach}=require('node:test');
const assert=require('node:assert/strict');
// No installation credentials are needed for the model-backed CAS unit tests.
process.env.FIELD_ENCRYPTION_KEY=require('node:crypto').randomBytes(32).toString('hex');
const Model=require('../models/user');
const quota=require('../admin/quotaLedger');
let state,writes;
const copy=x=>structuredClone(x);
const context=(run='first')=>({run_id:run,project_id:'project',owner_id:'owner',executor_id:'editor',generation:7,image_cost:2,video_cost:3});
const yesterday=new Date('2026-11-23T23:59:59Z');
beforeEach(()=>{
 state={_id:'editor',type:'free',operations:[],quotaLedger:[],quotaRevision:0,legacyQuotaRevision:0};writes=0;
 Model.findById=id=>({select:()=>({lean:async()=>id===state._id?copy(state):null})});
 Model.updateOne=async(query,update)=>{
  if(query.quotaRevision!==state.quotaRevision)return {modifiedCount:0};
  Object.assign(state,copy(update.$set));state.quotaRevision++;writes++;return {modifiedCount:1};
 };
});
test('parallel admissions of one run apply one atomic debit and receipt',async()=>{
 const receipts=await Promise.all([quota.admit('editor',5,context(),yesterday),quota.admit('editor',5,context(),yesterday)]);
 assert.equal(writes,1);assert.equal(state.operations[0].processed,5);assert.equal(state.quotaLedger.length,1);
 assert.deepEqual(receipts[0],receipts[1]);
});
test('refund is bound to original executor/day with both image and video costs',async()=>{
 await quota.admit('editor',5,context(),yesterday);
 state.operations.push({day:new Date('2026-11-24T00:00:00Z'),processed:3});
 const marker=await quota.refund('editor',5,context(),'case:first');
 assert.equal(marker.day,'2026-11-23');assert.equal(marker.amount,5);
 assert.deepEqual(state.operations.map(o=>o.processed),[0,3]);
 await assert.rejects(quota.refund('owner',5,context(),'case:first'),/Account not found/);
});
test('lost refund acknowledgement or another case cannot repeat the effect',async()=>{
 await quota.admit('editor',5,context(),yesterday);
 const first=await quota.refund('editor',5,context(),'case:first');const count=writes;
 const repeated=await quota.refund('editor',5,context(),'new-case:first');
 assert.deepEqual(repeated,first);assert.equal(writes,count);assert.equal(state.operations[0].processed,0);
});
test('changed run binding, cost or executor is refused before mutation',async()=>{
 await quota.admit('editor',5,context(),yesterday);const count=writes;
 for(const changed of [{owner_id:'other'},{generation:8},{image_cost:1,video_cost:4},{executor_id:'owner'}])
  await assert.rejects(quota.admit('editor',5,{...context(),...changed},yesterday),/conflicts/);
 assert.equal(writes,count);
});
test('unknown receipt, legacy balance changes and underflow never create credit',async()=>{
 await assert.rejects(quota.refund('editor',5,context(),'case'),/evidence/);
 await quota.admit('editor',5,context(),yesterday);const count=writes;
 state.legacyQuotaRevision=1;
 await assert.rejects(quota.refund('editor',5,context(),'case'),/Untracked/);
 state.legacyQuotaRevision=0;state.operations[0].processed=4;
 await assert.rejects(quota.refund('editor',5,context(),'case'),/balance/);assert.equal(writes,count);
});
test('premium has zero financial compensation and anonymous rejects paid effects',async()=>{
 state.type='premium';await quota.admit('editor',5,context(),yesterday);
 const result=await quota.refund('editor',5,context(),'case');assert.equal(result.amount,0);assert.equal(state.operations[0].processed,5);
 state.type='anonymous';await assert.rejects(quota.admit('editor',5,context('next'),yesterday),/daily operations/);
});
test('a compensated run cannot be admitted again automatically',async()=>{
 await quota.admit('editor',5,context(),yesterday);await quota.refund('editor',5,context(),'case');
 await assert.rejects(quota.admit('editor',5,context(),yesterday),/conflicts/);
});
test('quota context rejects malformed or missing binding fields',()=>{
 const values={'x-processing-run':'12345678-1234-1234-1234-123456789012','x-processing-project':'1'.repeat(24),
  'x-processing-owner':'2'.repeat(24),'x-processing-generation':'1','x-processing-images':'2','x-processing-videos':'3'};
 const req={params:{user:'3'.repeat(24)},get:key=>values[key]};
 assert.equal(quota.contextFrom(req).image_cost,2);
 delete values['x-processing-owner'];assert.throws(()=>quota.contextFrom(req),/Invalid/);
});
test('password changes cannot overwrite a concurrent quota snapshot',async()=>{
  const controller=require('../controllers/user');let written;
  Model.updateOne=async(_query,update)=>{written=update;return {modifiedCount:1};};
  await controller.updatePassword('editor',{name:'fixture',password:'disposable fixture password',
    operations:[{day:yesterday,processed:0}],quotaLedger:[],quotaRevision:0,legacyQuotaRevision:0});
  for(const field of ['operations','quotaLedger','quotaRevision','legacyQuotaRevision'])assert.equal(field in written,false);
  assert.equal(typeof written.password_hash,'string');assert.equal('password' in written,false);
});
test('ordinary profile changes also preserve quota-owned fields',async()=>{
  const controller=require('../controllers/user');let written;
  Model.updateOne=async(_query,update)=>{written=update;return {modifiedCount:1};};
  await controller.update('editor',{name:'fixture',operations:[],quotaLedger:[],quotaRevision:0,legacyQuotaRevision:0});
  assert.deepEqual(written,{name:'fixture'});
});
